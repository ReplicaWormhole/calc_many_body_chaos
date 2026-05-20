import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "calc_commutator_contrib_dynamic_v2.py"


spec = importlib.util.spec_from_file_location("calc_commutator_contrib_dynamic_v2", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class DynamicV2ReportTests(unittest.TestCase):
    def test_resolve_wolfram_command_prefers_kernel(self):
        with mock.patch.object(module.shutil, "which", side_effect=lambda name: {
            "WolframKernel": "/usr/bin/WolframKernel",
            "wolframscript": "/usr/bin/wolframscript",
        }.get(name)):
            cmd = module.resolve_wolfram_command(Path("/tmp/test.wls"))

        self.assertEqual(cmd, ["/usr/bin/WolframKernel", "-script", "/tmp/test.wls"])

    def test_writer_includes_generated_images_and_v2_summary(self):
        summary = module.v2.build_summary((ROOT / "all_L_1.txt").read_text(encoding="utf-8"))
        amplitude_metadata = {
            "loop_order": 1,
            "amplitude_count": 7,
            "paper_l1": {"one_rung_total_factor": 48},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            image_dir = tmp / "generated" / "images"
            image_dir.mkdir(parents=True)
            for i in range(1, 8):
                (image_dir / f"topology{i}.pdf").write_bytes(b"%PDF-1.5\n")
            out_path = tmp / "output" / "report.tex"
            out_path.parent.mkdir(parents=True)

            module.write_latex_report(
                summary,
                out_path,
                image_dir=image_dir,
                loop_order=1,
                amplitude_metadata=amplitude_metadata,
            )
            text = out_path.read_text(encoding="utf-8")

        self.assertIn("V2 Dynamic Summary", text)
        self.assertIn("topology1.pdf", text)
        self.assertIn("external vertex labels", text)
        self.assertIn("48", text)
        self.assertIn("Amplitude-stage metadata", text)
        self.assertIn("7", text)

    def test_convert_ps_images_to_pdf_uses_ps2pdf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image_dir = Path(tmpdir)
            ps_path = image_dir / "topology1.ps"
            ps_path.write_text("%!PS\n", encoding="utf-8")
            pdf_path = image_dir / "topology1.pdf"

            def fake_run(cmd, check, stdout, stderr, text):
                self.assertEqual(cmd, ["/usr/bin/ps2pdf", str(ps_path), str(pdf_path)])
                pdf_path.write_bytes(b"%PDF-1.5\n")
                return mock.Mock()

            with mock.patch.object(module.shutil, "which", return_value="/usr/bin/ps2pdf"):
                with mock.patch.object(module.subprocess, "run", side_effect=fake_run):
                    module.convert_ps_images_to_pdf(image_dir)

        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
