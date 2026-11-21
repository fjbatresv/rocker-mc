#!/usr/bin/env python3
"""Comprueba la CSP y las URLs públicas de las páginas del sitio."""
import argparse
import os
from pathlib import Path
import re
import sys

SITIO = 'https://rockers502mc.com.gt'
PAGINAS = ('site/index.html', 'site/404.html')


def problemas_csp(html: str, pagina: str) -> list[str]:
    problemas = [f'{pagina}: estilo en línea'] * len(re.findall(r'\bstyle\s*=', html, re.I))
    problemas.extend([f'{pagina}: handler en línea'] * len(re.findall(r'\bon[a-z]+\s*=', html, re.I)))
    for script in re.findall(r'<script\b([^>]*)>', html, re.I):
        if not re.search(r'\bsrc\s*=', script, re.I) and not re.search(r'\btype\s*=\s*["\']application/ld\+json["\']', script, re.I):
            problemas.append(f'{pagina}: script en línea no permitido')
    return problemas


def problemas_enlaces_externos(html: str, pagina: str) -> list[str]:
    problemas = []
    for etiqueta in re.findall(r'<a\b[^>]*>', html, re.I):
        if re.search(r'\btarget\s*=\s*["\']_blank["\']', etiqueta, re.I):
            rel = re.search(r'\brel\s*=\s*["\']([^"\']*)["\']', etiqueta, re.I)
            if not rel or 'noopener' not in rel.group(1).lower().split():
                problemas.append(f'{pagina}: enlace target="_blank" sin rel="noopener"')
    return problemas


def problemas_url(raiz: str, sitio: str) -> list[str]:
    sitio = sitio.rstrip('/')
    problemas = []
    index = (Path(raiz) / 'index.html').read_text(encoding='utf-8')
    error = (Path(raiz) / '404.html').read_text(encoding='utf-8')
    sitemap = (Path(raiz) / 'sitemap.xml').read_text(encoding='utf-8')
    robots = (Path(raiz) / 'robots.txt').read_text(encoding='utf-8')
    esperado = sitio + '/'
    for etiqueta, patron in (('canonical', r'<link\b(?=[^>]*\brel=["\']canonical["\'])[^>]*\bhref=["\']([^"\']+)["\']'), ('og:url', r'<meta\b(?=[^>]*\bproperty=["\']og:url["\'])[^>]*\bcontent=["\']([^"\']+)["\']')):
        encontrado = re.search(patron, index, re.I)
        if not encontrado or encontrado.group(1) != esperado:
            problemas.append(f'index.html: {etiqueta} debe ser {esperado}')
    img = re.search(r'<meta\b(?=[^>]*\bproperty=["\']og:image["\'])[^>]*\bcontent=["\']([^"\']+)["\']', index, re.I)
    if not img or not img.group(1).startswith(esperado):
        problemas.append('index.html: og:image debe empezar con ' + esperado)
    locs = re.findall(r'<loc>\s*([^<]+?)\s*</loc>', sitemap, re.I)
    if locs != [esperado]:
        problemas.append(f'sitemap.xml: debe contener un único <loc>{esperado}</loc>')
    if 'Sitemap: ' + sitio + '/sitemap.xml' not in robots:
        problemas.append('robots.txt: falta la URL del sitemap')
    if re.search(r'^Disallow:\s*/\s*$', robots, re.I | re.M):
        problemas.append('robots.txt: no debe bloquear todo el sitio')
    for carpeta, _, archivos in os.walk(raiz):
        for archivo in archivos:
            ruta = os.path.join(carpeta, archivo)
            try:
                with open(ruta, encoding='utf-8') as entrada:
                    contenido = entrada.read()
                    for dominio in ('rockers502.gt', 'rockers.fjbatresv.com'):
                        if dominio in contenido:
                            problemas.append(f'{ruta}: contiene un dominio no permitido: {dominio}')
            except UnicodeDecodeError:
                pass
    if re.search(r'<link\b(?=[^>]*\brel=["\']canonical["\'])', error, re.I):
        problemas.append('404.html: no debe tener canonical')
    return problemas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sitio', default=SITIO)
    args = parser.parse_args()
    problemas = []
    for pagina in PAGINAS:
        with open(pagina, encoding='utf-8') as archivo:
            html = archivo.read()
        problemas += problemas_csp(html, pagina)
        problemas += problemas_enlaces_externos(html, pagina)
    problemas += problemas_url('site', args.sitio)
    if problemas:
        print('::error::Problemas de seguridad y URLs:')
        print('\n'.join('  ' + problema for problema in problemas))
        sys.exit(1)
    print('Seguridad y URLs: sin problemas.')


if __name__ == '__main__':
    main()
