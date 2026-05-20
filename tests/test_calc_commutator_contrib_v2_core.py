import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "calc_commutator_contrib_v2_core.py"


spec = importlib.util.spec_from_file_location("calc_commutator_contrib_v2_core", MODULE_PATH)
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


class V2CanonicalTopologyTests(unittest.TestCase):
    def test_build_external_map_uses_external_vertex_labels(self):
        block = (
            "Topology[2]["
            "Propagator[Outgoing][Vertex[1][4], Vertex[4][6]], "
            "Propagator[Incoming][Vertex[1][2], Vertex[4][5]], "
            "Propagator[Internal][Vertex[4][5], Vertex[4][6]], "
            "Propagator[Outgoing][Vertex[1][3], Vertex[4][5]], "
            "Propagator[Loop[1]][Vertex[4][6], Vertex[4][6]], "
            "Propagator[Incoming][Vertex[1][1], Vertex[4][5]]]"
        )

        topo = module.parse_topology(block)
        fixed = module.build_external_map_by_label(topo.propagators)

        leg1 = fixed[module.find_external_endpoint(topo.propagators, 1)]
        leg2 = fixed[module.find_external_endpoint(topo.propagators, 2)]
        leg3 = fixed[module.find_external_endpoint(topo.propagators, 3)]
        leg4 = fixed[module.find_external_endpoint(topo.propagators, 4)]

        self.assertEqual((leg1.contour, leg1.ra, leg1.coord), (1, "r", "x_1"))
        self.assertEqual((leg2.contour, leg2.ra, leg2.coord), (1, "a", "x_2"))
        self.assertEqual((leg3.contour, leg3.ra, leg3.coord), (2, "r", "x_3"))
        self.assertEqual((leg4.contour, leg4.ra, leg4.coord), (2, "a", "x_4"))

    def test_canonical_signature_ignores_propagator_order(self):
        text = (ROOT / "all_L_1.txt").read_text(encoding="utf-8")
        original_block = module.extract_topology_blocks(text)[0]
        permuted_block = reordered_block(original_block, [5, 2, 0, 4, 1, 3])

        original = module.parse_topology(original_block)
        permuted = module.parse_topology(permuted_block)

        self.assertEqual(
            module.canonical_topology_signature(original),
            module.canonical_topology_signature(permuted),
        )
        self.assertEqual(
            module.canonical_coordinate_map(original.propagators),
            module.canonical_coordinate_map(permuted.propagators),
        )

    def test_classifies_l1_paper_sectors(self):
        text = (ROOT / "all_L_1.txt").read_text(encoding="utf-8")
        sectors = []
        for block in module.extract_topology_blocks(text):
            topo = module.parse_topology(block)
            sectors.append(module.classify_l1_topology(topo))

        self.assertEqual(
            sectors,
            [
                "self_energy",
                "self_energy",
                "one_rung",
                "self_energy",
                "one_rung",
                "one_rung",
                "self_energy",
            ],
        )

    def test_l1_sector_summary_matches_paper_one_rung_factor(self):
        text = (ROOT / "all_L_1.txt").read_text(encoding="utf-8")
        topologies = [module.parse_topology(block) for block in module.extract_topology_blocks(text)]

        summary = module.summarize_l1_paper_sectors(topologies)

        self.assertEqual(summary["one_rung_topology_indices"], [3, 5, 6])
        self.assertEqual(summary["one_rung_per_topology_factor"], 16)
        self.assertEqual(summary["one_rung_total_factor"], 48)
        self.assertEqual(summary["self_energy_topology_indices"], [1, 2, 4, 7])


if __name__ == "__main__":
    unittest.main()
