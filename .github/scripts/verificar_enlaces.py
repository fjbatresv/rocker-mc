#!/usr/bin/env python3
"""Falla si alguna página apunta a un archivo inexistente dentro del destino."""
import argparse
import os
from pathlib import Path
import re
import sys

PAGINAS_POR_DESTINO = {'site': ('site/index.html', 'site/404.html'), 'landing': ('landing/index.html', 'landing/en/index.html', 'landing/404.html')}
EXTERNO = re.compile(r'^(?:https?:|//|#|mailto:|tel:|data:)')


def enlaces_locales(html):
    for ruta in re.findall(r'(?:src|href)="([^"]+)"', html):
        if not EXTERNO.match(ruta):
            ruta = ruta.split('#')[0].split('?')[0]
            if ruta:
                yield ruta


def rotos(pagina: str, raiz: str) -> tuple[int, list[str]]:
    html = Path(pagina).read_text(encoding='utf-8')
    base = Path(raiz).resolve()
    faltan = []
    rutas = 0
    for ruta in enlaces_locales(html):
        rutas += 1
        destino = (base / ruta.lstrip('/')) if ruta.startswith('/') else (Path(pagina).resolve().parent / ruta)
        try:
            destino.resolve().relative_to(base)
        except ValueError:
            faltan.append(f'{pagina} → {ruta}')
            continue
        if not destino.exists():
            faltan.append(f'{pagina} → {ruta}')
    return rutas, faltan


def rutas_relativas(html: str) -> list[str]:
    return [ruta for ruta in enlaces_locales(html) if not ruta.startswith('/')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--destino', choices=('site', 'landing', 'todos'), default='site')
    args = parser.parse_args()
    destinos = ('site', 'landing') if args.destino == 'todos' else (args.destino,)
    faltan = []
    revisados = 0
    for destino in destinos:
        raiz = destino
        for pagina in PAGINAS_POR_DESTINO[destino]:
            if not os.path.exists(pagina):
                faltan.append(f'{pagina} (la página no existe)')
                continue
            cantidad, rotos_pagina = rotos(pagina, raiz)
            revisados += cantidad
            faltan.extend(rotos_pagina)
        if destino == 'landing' and os.path.exists('landing/404.html'):
            relativas = rutas_relativas(Path('landing/404.html').read_text(encoding='utf-8'))
            faltan.extend(f'landing/404.html → {ruta} (debe usar ruta absoluta)' for ruta in relativas)
    if faltan:
        print('::error::Referencias rotas:')
        for falta in faltan:
            print(f'  {falta}')
        sys.exit(1)
    print(f'{revisados} referencias locales revisadas, ninguna rota.')


if __name__ == '__main__':
    main()
