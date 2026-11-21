#!/usr/bin/env python3
"""Comprueba la CSP y las URLs públicas de cada destino."""
import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys

SITIO = 'https://rockers502mc.com.gt'
CSP_LANDING = "default-src 'none'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; base-uri 'none'; form-action 'none'; upgrade-insecure-requests"


@dataclass(frozen=True)
class Destino:
    raiz: str
    sitio: str
    canonicas: tuple[tuple[str, str], ...]
    paginas: tuple[str, ...]
    prohibidos: tuple[str, ...]
    csp_meta: str | None


DESTINOS = {
    'site': Destino('site', SITIO, (('index.html', '/'),), ('index.html', '404.html'), ('rockers502.gt', 'rockers.fjbatresv.com'), None),
    'landing': Destino('landing', 'https://rockers.fjbatresv.com', (('index.html', '/'), ('en/index.html', '/en/')), ('index.html', 'en/index.html', '404.html'), ('rockers502.gt',), CSP_LANDING),
}


def problemas_csp(html: str, pagina: str) -> list[str]:
    problemas = [f'{pagina}: estilo en línea'] * len(re.findall(r'\bstyle\s*=', html, re.I))
    problemas.extend([f'{pagina}: handler en línea'] * len(re.findall(r'\bon[a-z]+\s*=', html, re.I)))
    for script in re.findall(r'<script\b([^>]*)>', html, re.I):
        if not re.search(r'\bsrc\s*=', script, re.I) and not re.search(r'\btype\s*=\s*["\']application/ld\+json["\']', script, re.I):
            problemas.append(f'{pagina}: script en línea no permitido')
    return problemas


def problemas_csp_meta(html: str, pagina: str, csp: str) -> list[str]:
    meta = re.search(r'<meta\b(?=[^>]*\bhttp-equiv=["\']Content-Security-Policy["\'])[^>]*\bcontent="([^"]*)"', html, re.I)
    return [] if meta and meta.group(1) == csp else [f'{pagina}: falta CSP meta exacta']


def problemas_enlaces_externos(html: str, pagina: str) -> list[str]:
    problemas = []
    for etiqueta in re.findall(r'<a\b[^>]*>', html, re.I):
        if re.search(r'\btarget\s*=\s*["\']_blank["\']', etiqueta, re.I):
            rel = re.search(r'\brel\s*=\s*["\']([^"\']*)["\']', etiqueta, re.I)
            if not rel or 'noopener' not in rel.group(1).lower().split():
                problemas.append(f'{pagina}: enlace target="_blank" sin rel="noopener"')
    return problemas


def problemas_url(raiz: str, sitio: str, canonicas=(('index.html', '/'),), prohibidos=('rockers502.gt', 'rockers.fjbatresv.com')) -> list[str]:
    sitio = sitio.rstrip('/')
    raiz_path = Path(raiz)
    problemas = []
    error = (raiz_path / '404.html').read_text(encoding='utf-8')
    for pagina, ruta in canonicas:
        archivo = raiz_path / pagina
        html = archivo.read_text(encoding='utf-8') if archivo.exists() else ''
        esperado = sitio + ruta
        for etiqueta, patron in (('canonical', r'<link\b(?=[^>]*\brel=["\']canonical["\'])[^>]*\bhref=["\']([^"\']+)'), ('og:url', r'<meta\b(?=[^>]*\bproperty=["\']og:url["\'])[^>]*\bcontent=["\']([^"\']+)')):
            encontrado = re.search(patron, html, re.I)
            if not encontrado or encontrado.group(1) != esperado:
                problemas.append(f'{pagina}: {etiqueta} debe ser {esperado}')
        img = re.search(r'<meta\b(?=[^>]*\bproperty=["\']og:image["\'])[^>]*\bcontent=["\']([^"\']+)', html, re.I)
        if not img or not img.group(1).startswith(sitio + '/'):
            problemas.append(f'{pagina}: og:image debe empezar con {sitio}/')
    sitemap = (raiz_path / 'sitemap.xml').read_text(encoding='utf-8')
    robots = (raiz_path / 'robots.txt').read_text(encoding='utf-8')
    esperado_locs = [sitio + ruta for _, ruta in canonicas]
    locs = re.findall(r'<loc>\s*([^<]+?)\s*</loc>', sitemap, re.I)
    if locs != esperado_locs:
        problemas.append(f'sitemap.xml: debe contener {len(esperado_locs)} <loc> esperados')
    if 'Sitemap: ' + sitio + '/sitemap.xml' not in robots:
        problemas.append('robots.txt: falta la URL del sitemap')
    if re.search(r'^Disallow:\s*/\s*$', robots, re.I | re.M):
        problemas.append('robots.txt: no debe bloquear todo el sitio')
    for carpeta, _, archivos in os.walk(raiz):
        for archivo in archivos:
            ruta = os.path.join(carpeta, archivo)
            try:
                contenido = Path(ruta).read_text(encoding='utf-8')
                for dominio in prohibidos:
                    if dominio in contenido:
                        problemas.append(f'{ruta}: contiene un dominio no permitido: {dominio}')
            except UnicodeDecodeError:
                pass
    if re.search(r'<link\b(?=[^>]*\brel=["\']canonical["\'])', error, re.I):
        problemas.append('404.html: no debe tener canonical')
    return problemas


def problemas_hreflang(raiz: str, sitio: str, canonicas) -> list[str]:
    problemas = []
    esperado = {'es': sitio.rstrip('/') + '/', 'en': sitio.rstrip('/') + '/en/', 'x-default': sitio.rstrip('/') + '/'}
    for pagina, _ in canonicas:
        archivo = Path(raiz) / pagina
        if not archivo.exists():
            continue
        html = archivo.read_text(encoding='utf-8')
        for idioma, href in esperado.items():
            patron = rf'<link\b(?=[^>]*\brel=["\']alternate["\'])(?=[^>]*\bhreflang=["\']{re.escape(idioma)}["\'])[^>]*\bhref=["\']([^"\']+)'
            # Atributos pueden aparecer en cualquier orden.
            tag = next((t for t in re.findall(r'<link\b[^>]*>', html, re.I) if re.search(r'\brel=["\']alternate["\']', t, re.I) and re.search(rf'\bhreflang=["\']{re.escape(idioma)}["\']', t, re.I)), '')
            match = re.search(r'\bhref=["\']([^"\']+)', tag, re.I)
            if not match or match.group(1) != href:
                problemas.append(f'{pagina}: hreflang {idioma} debe ser {href}')
    return problemas


def verificar(destino: Destino, sitio: str | None = None) -> list[str]:
    problemas = []
    for pagina in destino.paginas:
        ruta = Path(destino.raiz) / pagina
        if not ruta.exists():
            continue
        html = ruta.read_text(encoding='utf-8')
        problemas += problemas_csp(html, str(ruta))
        problemas += problemas_enlaces_externos(html, str(ruta))
        if destino.csp_meta:
            problemas += problemas_csp_meta(html, str(ruta), destino.csp_meta)
    problemas += problemas_url(destino.raiz, sitio or destino.sitio, destino.canonicas, destino.prohibidos)
    if len(destino.canonicas) > 1:
        problemas += problemas_hreflang(destino.raiz, sitio or destino.sitio, destino.canonicas)
    return problemas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--destino', choices=(*DESTINOS, 'todos'), default='site')
    parser.add_argument('--sitio')
    args = parser.parse_args()
    if args.sitio and args.destino == 'todos':
        parser.error('--sitio solo se acepta con un destino concreto')
    destinos = DESTINOS.values() if args.destino == 'todos' else (DESTINOS[args.destino],)
    problemas = sum((verificar(destino, args.sitio) for destino in destinos), [])
    if problemas:
        print('::error::Problemas de seguridad y URLs:')
        print('\n'.join('  ' + problema for problema in problemas))
        sys.exit(1)
    print('Seguridad y URLs: sin problemas.')


if __name__ == '__main__':
    main()
