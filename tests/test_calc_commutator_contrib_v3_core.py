import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "calc_commutator_contrib_v3_core.py"


spec = importlib.util.spec_from_file_location("calc_commutator_contrib_v3_core", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def reordered_block(block: str, order: list[int]) -> str:
    topo = module.parse_topology(block)
    props = [topo.propagators[i] for i in order]
    prop_text = ", ".join(
        f"Propagator[{p.ptype}][Vertex[{p.v1.kind}][{p.v1.label}], Vertex[{p.v2.kind}][{p.v2.label}]]"
        for p in props
    )
    return f"Topology[{topo.topo_id}][{prop_text}]"


class V3CoreTests(unittest.TestCase):
    def test_infers_loop_order_for_l0_l1_l2(self):
        l0_text = (ROOT / "check_calculation" / "artifacts" / "generated" / "L0" / "all_L_0.txt").read_text(
            encoding="utf-8"
        )
        l1_text = (ROOT / "all_L_1.txt").read_text(encoding="utf-8")
        l2_text = (
            ROOT / "check_calculation" / "artifacts" / "generated" / "L2" / "all_L_2.txt"
        ).read_text(encoding="utf-8")

        l0_topo = module.parse_topology(module.extract_topology_blocks(l0_text)[0])
        l1_topo = module.parse_topology(module.extract_topology_blocks(l1_text)[0])
        l2_topo = module.parse_topology(module.extract_topology_blocks(l2_text)[0])

        self.assertEqual(module.infer_loop_order(l0_topo), 0)
        self.assertEqual(module.infer_loop_order(l1_topo), 1)
        self.assertEqual(module.infer_loop_order(l2_topo), 2)

    def test_family_tag_is_reorder_invariant(self):
        text = (ROOT / "check_calculation" / "artifacts" / "generated" / "L2" / "all_L_2.txt").read_text(
            encoding="utf-8"
        )
        original_block = module.extract_topology_blocks(text)[11]
        permuted_block = reordered_block(original_block, [7, 4, 0, 6, 1, 5, 2, 3])

        original = module.parse_topology(original_block)
        permuted = module.parse_topology(permuted_block)

        self.assertEqual(module.family_tag(original), "ext:2-1-1|bridges:1-1|loops:1-1")
        self.assertEqual(module.family_tag(original), module.family_tag(permuted))
        self.assertEqual(
            module.summarize_topology(original, 12)["family_tag"],
            module.summarize_topology(permuted, 12)["family_tag"],
        )

    def test_structural_ladder_candidate_matches_known_witnesses(self):
        l1_text = (ROOT / "all_L_1.txt").read_text(encoding="utf-8")
        l2_text = (ROOT / "check_calculation" / "artifacts" / "generated" / "L2" / "all_L_2.txt").read_text(
            encoding="utf-8"
        )
        l3_text = (
            ROOT / "check_calculation" / "artifacts" / "generated" / "L3_full" / "all_L_3.txt"
        ).read_text(encoding="utf-8")

        l1_topo3 = module.parse_topology(module.extract_topology_blocks(l1_text)[2])
        l2_topo12 = module.parse_topology(module.extract_topology_blocks(l2_text)[11])
        l2_topo1 = module.parse_topology(module.extract_topology_blocks(l2_text)[0])
        l2_topo40 = module.parse_topology(module.extract_topology_blocks(l2_text)[39])
        l3_topo128 = module.parse_topology(module.extract_topology_blocks(l3_text)[127])

        self.assertTrue(module.is_structural_ladder_candidate(l1_topo3))
        self.assertTrue(module.is_structural_ladder_candidate(l2_topo12))
        self.assertTrue(module.is_structural_ladder_candidate(l3_topo128))
        self.assertFalse(module.is_structural_ladder_candidate(l2_topo1))
        self.assertFalse(module.is_structural_ladder_candidate(l2_topo40))


if __name__ == "__main__":
    unittest.main()
