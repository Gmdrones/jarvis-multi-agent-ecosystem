import unittest
import jarvis

class TestJarvis(unittest.TestCase):
    def test_dashboard_exists(self):
        self.assertIn('JARVIS', jarvis.PAGE)
    def test_local_binding(self):
        self.assertIn('127.0.0.1', open(jarvis.__file__, encoding='utf-8').read())

if __name__ == '__main__': unittest.main()
