import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "check_calculation" / "scripts" / "build_claim_artifacts.py"


spec = importlib.util.spec_from_file_location("build_claim_artifacts", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class BuildClaimArtifactsTests(unittest.TestCase):
    def test_structural_summary_uses_quartic_internal_half_edge_count(self):
        block = (
            "Topology[9]["
            "Propagator[Incoming][Vertex[1][1], Vertex[4][5]], "
            "Propagator[Incoming][Vertex[1][2], Vertex[4][5]], "
            "Propagator[Outgoing][Vertex[1][3], Vertex[4][6]], "
            "Propagator[Outgoing][Vertex[1][4], Vertex[4][7]], "
            "Propagator[Internal][Vertex[4][5], Vertex[4][6]], "
            "Propagator[Internal][Vertex[4][5], Vertex[4][7]], "
            "Propagator[Internal][Vertex[4][6], Vertex[4][7]], "
            "Propagator[Internal][Vertex[4][6], Vertex[4][7]]]"
        )

        entry = module.summarize_block(block, index=1, enumerate_terms=False)

        self.assertEqual(entry.n_internal_vertices, 3)
        self.assertEqual(entry.n_internal_half_edges, 12)


if __name__ == "__main__":
    unittest.main()
