#!/usr/bin/env python3
"""Genera el emblema con fondo transparente a partir de Assets/logo.jpeg.

El logo original viene sobre un fondo negro plano. Recortarlo con una máscara
circular no sirve: las bandas de ROCKERS y GUATEMALA sobresalen del aro, así
que cualquier círculo las corta. En vez de eso se separa el fondo con un
relleno por inundación desde los bordes, lo que sigue la silueta real.

Salidas (todas cuadradas, para que los tamaños del HTML sigan siendo válidos):

    site/assets/img/emblem.webp        680×680
    site/assets/img/emblem@2x.webp    1024×1024
    site/assets/img/favicon-512.png
    site/assets/img/apple-touch-icon.png
    site/favicon.ico
    site/assets/img/og.jpg            1200×630, sobre el hero

Requiere Pillow, numpy y scipy.
"""
import os

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from scipy import ndimage

SRC = 'Assets/logo.jpeg'
OUT = 'site/assets/img/'
UMBRAL_FONDO = 26      # luminancia por debajo de la cual un píxel puede ser fondo
MARGEN = 0.025         # margen transparente alrededor del arte, en proporción


def recortar_fondo(im):
    """Devuelve la imagen RGBA con el fondo exterior en transparente."""
    lum = np.asarray(im.convert('L')).astype(np.int16)
    candidato = lum < UMBRAL_FONDO

    # Componentes conectados del "posible fondo"; nos quedamos con los que
    # tocan el borde. El negro interior del emblema no toca el borde, así que
    # se conserva opaco.
    etiquetas, n = ndimage.label(candidato)
    del n
    borde = set(etiquetas[0, :]) | set(etiquetas[-1, :]) | \
            set(etiquetas[:, 0]) | set(etiquetas[:, -1])
    borde.discard(0)

    fondo = np.isin(etiquetas, list(borde))
    alfa = np.where(fondo, 0, 255).astype(np.uint8)

    rgba = im.convert('RGBA')
    canal = Image.fromarray(alfa, 'L').filter(ImageFilter.GaussianBlur(0.6))
    rgba.putalpha(canal)
    return rgba


def cuadrar(rgba):
    """Recorta al arte y lo centra en un lienzo cuadrado con margen."""
    caja = rgba.split()[3].getbbox()
    arte = rgba.crop(caja)
    lado = int(max(arte.size) * (1 + MARGEN * 2))
    lienzo = Image.new('RGBA', (lado, lado), (0, 0, 0, 0))
    lienzo.alpha_composite(arte, ((lado - arte.width) // 2,
                                  (lado - arte.height) // 2))
    return lienzo


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f'No encuentro {SRC}')

    base = cuadrar(recortar_fondo(Image.open(SRC)))
    os.makedirs(OUT, exist_ok=True)

    grande = base.resize((1024, 1024), Image.LANCZOS)
    chico = base.resize((680, 680), Image.LANCZOS)
    grande.save(OUT + 'emblem@2x.webp', 'WEBP', quality=92, method=6)
    chico.save(OUT + 'emblem.webp', 'WEBP', quality=92, method=6)

    # Íconos
    grande.resize((512, 512), Image.LANCZOS).save(OUT + 'favicon-512.png')
    fondo = Image.new('RGBA', (512, 512), (10, 10, 11, 255))
    fondo.alpha_composite(grande.resize((476, 476), Image.LANCZOS), (18, 18))
    fondo.convert('RGB').resize((180, 180), Image.LANCZOS).save(OUT + 'apple-touch-icon.png')
    grande.resize((48, 48), Image.LANCZOS).save('site/favicon.ico',
                                                sizes=[(16, 16), (32, 32), (48, 48)])

    # Open Graph: emblema sobre el hero oscurecido
    hero = Image.open(OUT + 'hero.webp').convert('RGB')
    og = ImageOps.fit(hero, (1200, 630), Image.LANCZOS)
    og = ImageEnhance.Brightness(og).enhance(.42)
    og = Image.alpha_composite(og.convert('RGBA'),
                               Image.new('RGBA', (1200, 630), (10, 10, 11, 120)))
    og.alpha_composite(grande.resize((320, 320), Image.LANCZOS), (440, 118))
    og.convert('RGB').save(OUT + 'og.jpg', quality=85)

    print(f'Emblema base: {base.size[0]}×{base.size[1]} px')
    for f in ['emblem.webp', 'emblem@2x.webp', 'favicon-512.png',
              'apple-touch-icon.png', 'og.jpg']:
        print(f'  {f:<22} {os.path.getsize(OUT + f) // 1024} KB')
    print(f'  {"favicon.ico":<22} {os.path.getsize("site/favicon.ico") // 1024} KB')


if __name__ == '__main__':
    main()
