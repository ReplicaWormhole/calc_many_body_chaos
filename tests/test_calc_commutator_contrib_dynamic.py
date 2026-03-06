import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "calc_commutator_contrib_dynamic.py"


spec = importlib.util.spec_from_file_location("calc_commutator_contrib_dynamic", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class DynamicReportTests(unittest.TestCase):
    def test_resolve_wolfram_command_prefers_kernel(self):
        with mock.patch.object(module.shutil, "which", side_effect=lambda name: {
            "WolframKernel": "/usr/bin/WolframKernel",
            "wolframscript": "/usr/bin/wolframscript",
        }.get(name)):
            cmd = module.resolve_wolfram_command(Path("/tmp/test.wls"))

        self.assertEqual(cmd, ["/usr/bin/WolframKernel", "-script", "/tmp/test.wls"])

    def test_resolve_wolfram_command_falls_back_to_wolframscript(self):
        with mock.patch.object(module.shutil, "which", side_effect=lambda name: {
            "wolframscript": "/usr/bin/wolframscript",
        }.get(name)):
            cmd = module.resolve_wolfram_command(Path("/tmp/test.wls"))

        self.assertEqual(cmd, ["/usr/bin/wolframscript", "-file", "/tmp/test.wls"])

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

    def test_count_generated_images_counts_pdfs_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image_dir = Path(tmpdir)
            (image_dir / "topology1.pdf").write_bytes(b"%PDF-1.5\n")
            (image_dir / "topology2.pdf").write_bytes(b"%PDF-1.5\n")
            (image_dir / "topology2.ps").write_text("%!PS\n", encoding="utf-8")

            count = module.count_generated_images(image_dir)

        self.assertEqual(count, 2)

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

    def test_ensure_generated_artifacts_checks_matching_image_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            topology_list_path = tmp / "all_L_0.txt"
            image_dir = tmp / "images"
            image_dir.mkdir()
            topology_list_path.write_text(
                "TopologyList[Topology[1][Propagator[Incoming][Vertex[1][1], Vertex[3][1]], "
                "Propagator[Incoming][Vertex[1][2], Vertex[3][1]], "
                "Propagator[Outgoing][Vertex[3][1], Vertex[1][3]], "
                "Propagator[Outgoing][Vertex[3][1], Vertex[1][4]]]]",
                encoding="utf-8",
            )
            (image_dir / "topology1.pdf").write_bytes(b"%PDF-1.5\n")

            count = module.ensure_generated_artifacts(topology_list_path, image_dir, require_images=True)

        self.assertEqual(count, 1)

    def test_ensure_generated_artifacts_raises_on_image_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            topology_list_path = tmp / "all_L_1.txt"
            image_dir = tmp / "images"
            image_dir.mkdir()
            topology_list_path.write_text(
                "TopologyList["
                "Topology[1][Propagator[Incoming][Vertex[1][1], Vertex[3][1]], "
                "Propagator[Incoming][Vertex[1][2], Vertex[3][1]], "
                "Propagator[Outgoing][Vertex[3][1], Vertex[1][3]], "
                "Propagator[Outgoing][Vertex[3][1], Vertex[1][4]]], "
                "Topology[2][Propagator[Incoming][Vertex[1][1], Vertex[3][1]], "
                "Propagator[Incoming][Vertex[1][2], Vertex[3][1]], "
                "Propagator[Outgoing][Vertex[3][1], Vertex[1][3]], "
                "Propagator[Outgoing][Vertex[3][1], Vertex[1][4]]]]",
                encoding="utf-8",
            )
            (image_dir / "topology1.pdf").write_bytes(b"%PDF-1.5\n")

            with self.assertRaisesRegex(RuntimeError, "Generated image count mismatch"):
                module.ensure_generated_artifacts(topology_list_path, image_dir, require_images=True)

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
