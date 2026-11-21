import tempfile
import unittest
from pathlib import Path

from verificar_enlaces import rotos


class VerificarEnlacesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        (self.raiz / 'en').mkdir()
        (self.raiz / 'assets').mkdir()
        (self.raiz / 'assets/a.css').touch()

    def test_ruta_relativa_desde_subcarpeta(self):
        pagina = self.raiz / 'en/index.html'
        pagina.write_text('<link href="../assets/a.css">', encoding='utf-8')
        self.assertEqual(rotos(str(pagina), str(self.raiz))[1], [])

    def test_ruta_absoluta_desde_raiz(self):
        pagina = self.raiz / 'index.html'
        pagina.write_text('<link href="/assets/a.css">', encoding='utf-8')
        self.assertEqual(rotos(str(pagina), str(self.raiz))[1], [])

    def test_ruta_que_escapa_de_la_raiz(self):
        pagina = self.raiz / 'en/index.html'
        pagina.write_text('<link href="../../x">', encoding='utf-8')
        self.assertEqual(len(rotos(str(pagina), str(self.raiz))[1]), 1)


if __name__ == '__main__':
    unittest.main()
