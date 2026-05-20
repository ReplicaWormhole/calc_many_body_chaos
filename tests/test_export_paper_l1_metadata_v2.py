import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "export_paper_l1_metadata_v2.wls"


class ExportPaperL1MetadataV2Tests(unittest.TestCase):
    def test_wolfram_export_writes_expected_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "paper_l1_metadata.json"
            subprocess.run(
                ["WolframKernel", "-script", str(SCRIPT_PATH), str(out_path)],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            data = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(data["loop_order"], 1)
        self.assertEqual(data["amplitude_count"], 7)
        self.assertEqual(data["paper_l1"]["one_rung_topology_ids"], [3, 5, 6])
        self.assertEqual(data["paper_l1"]["one_rung_total_factor"], 48)


if __name__ == "__main__":
    unittest.main()
