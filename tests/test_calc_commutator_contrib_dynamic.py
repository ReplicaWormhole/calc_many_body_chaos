import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "calc_commutator_contrib_dynamic.py"


spec = importlib.util.spec_from_file_location("calc_commutator_contrib_dynamic", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class DynamicReportTests(unittest.TestCase):
    def test_image_path_uses_generated_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            image_dir = tmp / "generated" / "images"
            image_dir.mkdir(parents=True)
            (image_dir / "topology1.pdf").write_bytes(b"%PDF-1.5\n")
            out_path = tmp / "output" / "report.tex"
            out_path.parent.mkdir(parents=True)

            rel = module.image_path_for_index(1, out_path, image_dir)

        self.assertTrue(rel.endswith("generated/images/topology1.pdf"))

    def test_writer_includes_generated_image_paths(self):
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
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            image_dir = tmp / "generated" / "images"
            image_dir.mkdir(parents=True)
            (image_dir / "topology1.pdf").write_bytes(b"%PDF-1.5\n")
            out_path = tmp / "output" / "report.tex"
            out_path.parent.mkdir(parents=True)

            module.write_latex_report(results, out_path, nc_symbol="N_c", loop_order=3, image_dir=image_dir)
            tex = out_path.read_text(encoding="utf-8")

        self.assertIn("All L=3 Topologies", tex)
        self.assertIn("topology1.pdf", tex)
        self.assertIn(r"\includegraphics", tex)


if __name__ == "__main__":
    unittest.main()
