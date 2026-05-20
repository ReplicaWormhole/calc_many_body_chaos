import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "calc_commutator_contrib_v2.py"


spec = importlib.util.spec_from_file_location("calc_commutator_contrib_v2", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class V2ReportTests(unittest.TestCase):
    def test_build_summary_for_all_l1_matches_paper_factor(self):
        summary = module.build_summary((ROOT / "all_L_1.txt").read_text(encoding="utf-8"))

        self.assertEqual(summary["topology_count"], 7)
        self.assertEqual(summary["paper_l1"]["one_rung_total_factor"], 48)
        self.assertEqual(summary["entries"][2]["sector"], "one_rung")
        self.assertEqual(summary["entries"][0]["sector"], "self_energy")

    def test_report_uses_label_based_assignment_language(self):
        summary = module.build_summary((ROOT / "all_L_1.txt").read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.tex"
            module.write_report(summary, out_path)
            text = out_path.read_text(encoding="utf-8")

        self.assertIn("external vertex labels", text)
        self.assertIn("one-rung total factor", text)
        self.assertIn("48", text)
        self.assertIn("Topology 3", text)


if __name__ == "__main__":
    unittest.main()
