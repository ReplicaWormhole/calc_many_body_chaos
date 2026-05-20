import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "export_commutator_metadata_v3.wls"


class ExportCommutatorMetadataV3Tests(unittest.TestCase):
    def test_exports_generic_l2_amplitude_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "commutator_metadata_L2.json"
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
        self.assertEqual(data["topology_ids"], [2, 4, 6])
        self.assertGreater(data["topology_count"], 0)
        self.assertGreater(data["inserted_diagram_count"], 0)
        self.assertGreater(data["amplitude_count"], 0)
        self.assertIn("4", data["amplitude_counts_by_topology_id"])


if __name__ == "__main__":
    unittest.main()
