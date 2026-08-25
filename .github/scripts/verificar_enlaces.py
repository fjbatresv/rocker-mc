#!/usr/bin/env python3
"""Falla el despliegue si alguna página apunta a un archivo que no existe.

Recorre los `src` y `href` locales de las páginas HTML y comprueba que cada
uno resuelva dentro de site/. Evita publicar una imagen renombrada, un CSS
movido o una ruta mal escrita.
"""
import os
import re
import sys

PAGINAS = ('site/index.html', 'site/404.html')
EXTERNO = re.compile(r'^(?:https?:|//|#|mailto:|tel:|data:)')


def enlaces_locales(html):
    for ruta in re.findall(r'(?:src|href)="([^"]+)"', html):
        if EXTERNO.match(ruta):
            continue
        ruta = ruta.split('#')[0].split('?')[0]
        if ruta:
            yield ruta


def main():
    faltan = []
    revisados = 0

    for pagina in PAGINAS:
        if not os.path.exists(pagina):
            faltan.append(f'{pagina} (la página no existe)')
            continue
        html = open(pagina, encoding='utf-8').read()
        for ruta in enlaces_locales(html):
            revisados += 1
            destino = os.path.join('site', ruta.lstrip('/'))
            if not os.path.exists(destino):
                faltan.append(f'{pagina} → {ruta}')

    if faltan:
        print('::error::Referencias rotas:')
        for f in faltan:
            print(f'  {f}')
        sys.exit(1)

    print(f'{revisados} referencias locales revisadas, ninguna rota.')


if __name__ == '__main__':
    main()
