import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "calc_commutator_contrib_dynamic_v3.py"


spec = importlib.util.spec_from_file_location("calc_commutator_contrib_dynamic_v3", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class DynamicV3ReportTests(unittest.TestCase):
    def test_resolve_wolfram_command_prefers_kernel(self):
        with mock.patch.object(module.shutil, "which", side_effect=lambda name: {
            "WolframKernel": "/usr/bin/WolframKernel",
            "wolframscript": "/usr/bin/wolframscript",
        }.get(name)):
            cmd = module.resolve_wolfram_command(Path("/tmp/test.wls"))

        self.assertEqual(cmd, ["/usr/bin/WolframKernel", "-script", "/tmp/test.wls"])

    def test_writer_includes_amplitude_metadata_and_candidates(self):
        summary = module.v3.build_summary(
            (ROOT / "check_calculation" / "artifacts" / "generated" / "L2" / "all_L_2.txt").read_text(
                encoding="utf-8"
            )
        )
        amplitude_metadata = {
            "loop_order": 2,
            "bare_topology_count": 6,
            "amplitude_count": 42,
            "amplitude_counts_by_topology_id": {"2": 8, "4": 30, "6": 4},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            image_dir = tmp / "generated" / "images"
            image_dir.mkdir(parents=True)
            for i in range(1, 43):
                (image_dir / f"topology{i}.pdf").write_bytes(b"%PDF-1.5\n")
            out_path = tmp / "output" / "report.tex"
            out_path.parent.mkdir(parents=True)

            module.write_latex_report(
                summary,
                out_path,
                image_dir=image_dir,
                loop_order=2,
                amplitude_metadata=amplitude_metadata,
            )
            text = out_path.read_text(encoding="utf-8")

        self.assertIn("V3 Dynamic Summary for L=2", text)
        self.assertIn("Amplitude-stage metadata", text)
        self.assertIn("42", text)
        self.assertIn("Structural ladder-candidate indices", text)
        self.assertIn("topology12.pdf", text)


if __name__ == "__main__":
    unittest.main()
