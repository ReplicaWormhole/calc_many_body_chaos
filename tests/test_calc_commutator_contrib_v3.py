import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "calc_commutator_contrib_v3.py"


spec = importlib.util.spec_from_file_location("calc_commutator_contrib_v3", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class V3ReportTests(unittest.TestCase):
    def test_build_summary_for_l1_keeps_exact_paper_sector(self):
        summary = module.build_summary((ROOT / "all_L_1.txt").read_text(encoding="utf-8"))

        self.assertEqual(summary["loop_order"], 1)
        self.assertEqual(summary["topology_count"], 7)
        self.assertEqual(summary["paper_l1"]["one_rung_total_factor"], 48)
        self.assertEqual(summary["entries"][2]["family_tag"], "ext:2-2|bridges:2|loops:0")

    def test_build_summary_for_l2_reports_general_loop_features(self):
        summary = module.build_summary(
            (ROOT / "check_calculation" / "artifacts" / "generated" / "L2" / "all_L_2.txt").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(summary["loop_order"], 2)
        self.assertEqual(summary["topology_count"], 42)
        self.assertIn("ext:2-1-1|bridges:1-1|loops:1-1", summary["family_histogram"])
        self.assertIn(12, summary["structural_ladder_candidate_indices"])
        self.assertIn(40, [entry["index"] for entry in summary["entries"]])

    def test_report_includes_family_histogram_and_candidates(self):
        summary = module.build_summary(
            (ROOT / "check_calculation" / "artifacts" / "generated" / "L2" / "all_L_2.txt").read_text(
                encoding="utf-8"
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.tex"
            module.write_report(summary, out_path)
            text = out_path.read_text(encoding="utf-8")

        self.assertIn("Commutator Contribution V3 Summary", text)
        self.assertIn("family histogram", text.lower())
        self.assertIn("Structural ladder-candidate indices", text)
        self.assertIn("Topology 12", text)


if __name__ == "__main__":
    unittest.main()
