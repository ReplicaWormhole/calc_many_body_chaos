import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "calc_commutator_contrib_all_L1.py"


spec = importlib.util.spec_from_file_location("calc_commutator_contrib_all_L1", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class AllL1ReportTests(unittest.TestCase):
    def test_extracts_all_l1_topologies(self):
        text = (ROOT / "all_L_1.txt").read_text(encoding="utf-8")
        blocks = module.base.extract_topology_blocks(text)
        self.assertEqual(len(blocks), 7)

    def test_writer_includes_all_images(self):
        results = [
            {
                "topology_id": 2,
                "n_props": 6,
                "n_internal_vertices": 2,
                "n_internal_half_edges": 8,
                "total_assignments": 256,
                "surviving_assignments": 12,
                "nc_raw_power": 4,
                "nc_net_power": 0,
                "terms": [
                    {
                        "coeff_latex": "4 i g_{2}",
                        "nc_factor_latex": "1",
                        "propagators": ["G_R\\left(x_1,z_1\\right)"],
                    }
                ],
            }
            for _ in range(7)
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "output" / "report.tex"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            module.write_latex_report(results, out_path, nc_symbol="N_c")
            tex = out_path.read_text(encoding="utf-8")

        self.assertEqual(tex.count(r"\includegraphics"), 7)
        self.assertIn("topology1.pdf", tex)
        self.assertIn("topology7.pdf", tex)


if __name__ == "__main__":
    unittest.main()
