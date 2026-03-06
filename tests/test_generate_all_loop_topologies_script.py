from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_all_loop_topologies.wls"


class GenerateAllLoopTopologiesScriptTests(unittest.TestCase):
    def test_script_contains_expected_generation_flow(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('CreateTopologies[', text)
        self.assertIn('2 -> 2', text)
        self.assertIn('Adjacencies -> {4}', text)
        self.assertIn('ExcludeTopologies -> Tadpoles', text)
        self.assertIn('topology" <> ToString[index] <> ".ps"', text)
        self.assertIn('Export[psPath, paint, "PS"]', text)
        self.assertIn('AutoEdit -> False', text)
        self.assertIn('"all_L_" <> ToString[L] <> ".txt"', text)
        self.assertIn('[topology-list-path]', text)
        self.assertIn('--list-only', text)
        self.assertIn('--images-only', text)


if __name__ == "__main__":
    unittest.main()
