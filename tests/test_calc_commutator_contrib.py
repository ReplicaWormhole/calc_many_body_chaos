import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "calc_commutator_contrib.py"


spec = importlib.util.spec_from_file_location("calc_commutator_contrib", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class TranslatePropagatorTests(unittest.TestCase):
    def test_same_contour_block(self):
        self.assertEqual(module.translate_propagator(1, 1, "r", "r", "x", "y"), "G_K\\left(x,y\\right)")
        self.assertEqual(module.translate_propagator(2, 2, "r", "a", "x", "y"), "G_R\\left(x,y\\right)")
        self.assertEqual(module.translate_propagator(1, 1, "a", "r", "x", "y"), "G_A\\left(x,y\\right)")
        self.assertIsNone(module.translate_propagator(2, 2, "a", "a", "x", "y"))

    def test_cross_contour_block(self):
        self.assertEqual(module.translate_propagator(1, 2, "r", "r", "x", "y"), "G^<\\left(x,y\\right)")
        self.assertEqual(module.translate_propagator(2, 1, "r", "r", "x", "y"), "G^>\\left(x,y\\right)")
        self.assertIsNone(module.translate_propagator(1, 2, "r", "a", "x", "y"))
        self.assertIsNone(module.translate_propagator(2, 1, "a", "r", "x", "y"))


if __name__ == "__main__":
    unittest.main()
