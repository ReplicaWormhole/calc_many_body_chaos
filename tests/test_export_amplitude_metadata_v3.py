import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "export_amplitude_metadata_v3.wls"


class ExportAmplitudeMetadataV3Tests(unittest.TestCase):
    def test_exports_l2_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "amplitude_metadata_l2.json"
            subprocess.run(
                ["WolframKernel", "-script", str(SCRIPT_PATH), "2", str(out_path)],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            data = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(data["loop_order"], 2)
        self.assertGreater(data["bare_topology_count"], 0)
        self.assertGreater(data["amplitude_count"], 0)
        self.assertTrue(data["amplitude_counts_by_topology_id"])
        self.assertEqual(sum(data["amplitude_counts_by_topology_id"].values()), data["amplitude_count"])


if __name__ == "__main__":
    unittest.main()
