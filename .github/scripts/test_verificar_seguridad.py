import tempfile
import unittest
from pathlib import Path

from verificar_seguridad import DESTINOS, CSP_LANDING, problemas_csp, problemas_csp_meta, problemas_enlaces_externos, problemas_url


def sitio_valido(raiz):
    raiz = Path(raiz)
    raiz.mkdir(parents=True, exist_ok=True)
    (raiz / 'index.html').write_text('<link rel="canonical" href="https://rockers502mc.com.gt/"><meta property="og:url" content="https://rockers502mc.com.gt/"><meta property="og:image" content="https://rockers502mc.com.gt/img.jpg">', encoding='utf-8')
    (raiz / '404.html').write_text('<p>No encontrado</p>', encoding='utf-8')
    (raiz / 'sitemap.xml').write_text('<url><loc>https://rockers502mc.com.gt/</loc></url>', encoding='utf-8')
    (raiz / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: https://rockers502mc.com.gt/sitemap.xml\n', encoding='utf-8')
    return str(raiz)


class VerificarSeguridadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_sitio_con_y_sin_barra(self):
        raiz = sitio_valido(self.tmp.name)
        self.assertEqual(problemas_url(raiz, 'https://rockers502mc.com.gt'), [])
        self.assertEqual(problemas_url(raiz, 'https://rockers502mc.com.gt/'), [])

    def test_scripts(self):
        ok = '<script src="assets/js/main.js" defer></script><script type="application/ld+json">{}</script>'
        self.assertEqual(problemas_csp(ok, 'x.html'), [])
        self.assertEqual(len(problemas_csp('<script type="module">alert(1)</script>', 'x.html')), 1)
        self.assertEqual(len(problemas_csp('<script>alert(1)</script>', 'x.html')), 1)
        self.assertEqual(len(problemas_csp('<button onclick="x()">', 'x.html')), 1)

    def test_style_en_linea(self):
        self.assertEqual(len(problemas_csp('<p style="margin:0">', 'x.html')), 1)

    def test_robots_bloqueado(self):
        raiz = Path(sitio_valido(self.tmp.name))
        (raiz / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
        self.assertTrue(problemas_url(str(raiz), 'https://rockers502mc.com.gt'))

    def test_dominio_viejo(self):
        raiz = Path(sitio_valido(self.tmp.name))
        (raiz / 'extra.txt').write_text('https://rockers502.gt/', encoding='utf-8')
        self.assertTrue(problemas_url(str(raiz), 'https://rockers502mc.com.gt'))

    def test_subdominio_de_portafolio_bloqueado(self):
        raiz = Path(sitio_valido(self.tmp.name))
        (raiz / 'extra.txt').write_text('https://rockers.fjbatresv.com/', encoding='utf-8')
        self.assertTrue(problemas_url(str(raiz), 'https://rockers502mc.com.gt'))

    def test_credito_personal_no_bloqueado(self):
        raiz = Path(sitio_valido(self.tmp.name))
        (raiz / 'extra.txt').write_text('<a href="https://fjbatresv.com">Javier Batres</a>', encoding='utf-8')
        self.assertEqual(problemas_url(str(raiz), 'https://rockers502mc.com.gt'), [])

    def test_canonical_en_404(self):
        raiz = Path(sitio_valido(self.tmp.name))
        (raiz / '404.html').write_text('<link rel="canonical" href="https://x/">', encoding='utf-8')
        self.assertTrue(problemas_url(str(raiz), 'https://rockers502mc.com.gt'))

    def test_target_blank_sin_noopener(self):
        self.assertEqual(len(problemas_enlaces_externos('<a target="_blank" href="https://x">', 'x.html')), 1)

    def test_landing_dos_locs(self):
        raiz = Path(self.tmp.name)
        (raiz / 'index.html').write_text('<link rel="canonical" href="https://rockers.fjbatresv.com/"><meta property="og:url" content="https://rockers.fjbatresv.com/"><meta property="og:image" content="https://rockers.fjbatresv.com/img.jpg">', encoding='utf-8')
        (raiz / 'en').mkdir()
        (raiz / 'en/index.html').write_text('<link rel="canonical" href="https://rockers.fjbatresv.com/en/"><meta property="og:url" content="https://rockers.fjbatresv.com/en/"><meta property="og:image" content="https://rockers.fjbatresv.com/img.jpg">', encoding='utf-8')
        (raiz / '404.html').write_text('<p>404</p>', encoding='utf-8')
        (raiz / 'robots.txt').write_text('Allow: /\nSitemap: https://rockers.fjbatresv.com/sitemap.xml\n', encoding='utf-8')
        sitemap = '<loc>https://rockers.fjbatresv.com/</loc><loc>https://rockers.fjbatresv.com/en/</loc>'
        (raiz / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
        args = (str(raiz), 'https://rockers.fjbatresv.com', DESTINOS['landing'].canonicas, DESTINOS['landing'].prohibidos)
        self.assertEqual(problemas_url(*args), [])
        (raiz / 'sitemap.xml').write_text('<loc>https://rockers.fjbatresv.com/</loc>', encoding='utf-8')
        self.assertTrue(problemas_url(*args))

    def test_landing_puede_enlazar_al_club(self):
        raiz = Path(sitio_valido(self.tmp.name))
        (raiz / 'index.html').write_text('<link rel="canonical" href="https://rockers502mc.com.gt/"><meta property="og:url" content="https://rockers502mc.com.gt/"><meta property="og:image" content="https://rockers502mc.com.gt/img.jpg"><a href="https://rockers502mc.com.gt/">Club</a>', encoding='utf-8')
        self.assertEqual(problemas_url(str(raiz), 'https://rockers502mc.com.gt', prohibidos=('rockers502.gt',)), [])

    def test_csp_meta(self):
        meta = f'<meta http-equiv="Content-Security-Policy" content="{CSP_LANDING}">'
        self.assertEqual(problemas_csp_meta(meta, 'index.html', CSP_LANDING), [])
        self.assertEqual(len(problemas_csp_meta('', 'index.html', CSP_LANDING)), 1)
        self.assertEqual(len(problemas_csp_meta(meta.replace("'self'", "'self' 'unsafe-inline'", 1), 'index.html', CSP_LANDING)), 1)

    def test_destinos_por_defecto(self):
        self.assertEqual(DESTINOS['site'].sitio, 'https://rockers502mc.com.gt')
        self.assertIn('rockers.fjbatresv.com', DESTINOS['site'].prohibidos)


if __name__ == '__main__':
    unittest.main()
