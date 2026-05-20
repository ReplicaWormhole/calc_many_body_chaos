#!/usr/bin/env python3
"""Canonical topology helpers for the v2 commutator pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class Vertex:
    kind: int
    label: int

    @property
    def is_external(self) -> bool:
        return self.kind == 1


@dataclass(frozen=True)
class Propagator:
    edge_id: int
    ptype: str
    v1: Vertex
    v2: Vertex


@dataclass(frozen=True)
class ExternalLeg:
    contour: int
    ra: str
    idx_pair: Tuple[str, str]
    coord: str


@dataclass(frozen=True)
class TopologyData:
    topo_id: int
    propagators: List[Propagator]


PROP_RE = re.compile(
    r"""
    Propagator\s*\[\s*(?P<ptype>.*?)\s*\]\s*\[
    \s*Vertex\s*\[\s*(?P<v1k>-?\d+)\s*\]\s*\[\s*(?P<v1l>-?\d+)\s*\]\s*,
    \s*Vertex\s*\[\s*(?P<v2k>-?\d+)\s*\]\s*\[\s*(?P<v2l>-?\d+)\s*\]\s*
    \]
    """,
    re.VERBOSE | re.DOTALL,
)


def _matching_bracket(text: str, open_pos: int) -> int:
    depth = 0
    for i in range(open_pos, len(text)):
        ch = text[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError(f"Unmatched '[' starting at position {open_pos}")


def extract_topology_blocks(text: str) -> List[str]:
    blocks: List[str] = []
    i = 0
    needle = "Topology["
    while True:
        start = text.find(needle, i)
        if start < 0:
            return blocks

        first_open = text.find("[", start + len("Topology"))
        if first_open < 0:
            raise ValueError("Malformed Topology expression: missing first '['")
        first_close = _matching_bracket(text, first_open)

        second_open = text.find("[", first_close + 1)
        if second_open < 0:
            raise ValueError("Malformed Topology expression: missing second '[...]' block")
        second_close = _matching_bracket(text, second_open)

        blocks.append(text[start : second_close + 1])
        i = second_close + 1


def parse_topology(block: str) -> TopologyData:
    t_start = block.find("Topology[")
    first_open = block.find("[", t_start + len("Topology"))
    first_close = _matching_bracket(block, first_open)
    topo_id = int(block[first_open + 1 : first_close].strip())

    second_open = block.find("[", first_close + 1)
    second_close = _matching_bracket(block, second_open)
    body = block[second_open + 1 : second_close]

    propagators: List[Propagator] = []
    for match in PROP_RE.finditer(body):
        propagators.append(
            Propagator(
                edge_id=len(propagators),
                ptype=re.sub(r"\s+", "", match.group("ptype")),
                v1=Vertex(int(match.group("v1k")), int(match.group("v1l"))),
                v2=Vertex(int(match.group("v2k")), int(match.group("v2l"))),
            )
        )

    if not propagators:
        raise ValueError(f"Topology {topo_id}: no propagators parsed")

    return TopologyData(topo_id=topo_id, propagators=propagators)


def internal_vertices(props: Iterable[Propagator]) -> List[Vertex]:
    return sorted(
        {vertex for prop in props for vertex in (prop.v1, prop.v2) if not vertex.is_external},
        key=lambda vertex: (vertex.kind, vertex.label),
    )


def canonical_coordinate_map(props: Iterable[Propagator]) -> Dict[Vertex, str]:
    return {vertex: f"z_{{{i}}}" for i, vertex in enumerate(internal_vertices(props), start=1)}


def _external_leg_definitions() -> Dict[int, ExternalLeg]:
    return {
        1: ExternalLeg(1, "r", ("a1", "b1"), "x_1"),
        2: ExternalLeg(1, "a", ("a2", "b2"), "x_2"),
        3: ExternalLeg(2, "r", ("a3", "b3"), "x_3"),
        4: ExternalLeg(2, "a", ("a4", "b4"), "x_4"),
    }


def find_external_endpoint(props: List[Propagator], external_label: int) -> Tuple[int, int]:
    target = Vertex(1, external_label)
    matches: List[Tuple[int, int]] = []
    for prop in props:
        if prop.v1 == target:
            matches.append((prop.edge_id, 0))
        if prop.v2 == target:
            matches.append((prop.edge_id, 1))

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one endpoint for external vertex label {external_label}, got {len(matches)}"
        )
    return matches[0]


def build_external_map_by_label(props: List[Propagator]) -> Dict[Tuple[int, int], ExternalLeg]:
    fixed: Dict[Tuple[int, int], ExternalLeg] = {}
    for label, leg in _external_leg_definitions().items():
        fixed[find_external_endpoint(props, label)] = leg
    return fixed


def _canonical_vertex_name(vertex: Vertex, internal_names: Dict[Vertex, str]) -> str:
    if vertex.is_external:
        return f"ext{vertex.label}"
    return internal_names[vertex]


def canonical_topology_signature(topo: TopologyData) -> Tuple[int, Tuple[Tuple[str, str, str], ...]]:
    internal_names = {
        vertex: f"int{i}" for i, vertex in enumerate(internal_vertices(topo.propagators), start=1)
    }
    edge_entries = []
    for prop in topo.propagators:
        v1_name = _canonical_vertex_name(prop.v1, internal_names)
        v2_name = _canonical_vertex_name(prop.v2, internal_names)
        edge_entries.append((prop.ptype, *sorted((v1_name, v2_name))))
    return topo.topo_id, tuple(sorted(edge_entries))


def classify_l1_topology(topo: TopologyData) -> str:
    vertices = internal_vertices(topo.propagators)
    if len(vertices) != 2:
        raise ValueError(f"L1 sector classification expects 2 internal vertices, got {len(vertices)}")

    v_a, v_b = vertices
    bridge_edges = 0
    self_loops = 0

    for prop in topo.propagators:
        endpoints = {prop.v1, prop.v2}
        if prop.v1 == prop.v2 and prop.v1 in {v_a, v_b}:
            self_loops += 1
        elif endpoints == {v_a, v_b}:
            bridge_edges += 1

    if bridge_edges == 2 and self_loops == 0:
        return "one_rung"
    if bridge_edges == 1 and self_loops == 1:
        return "self_energy"
    return "other"


def summarize_l1_paper_sectors(topologies: List[TopologyData]) -> Dict[str, object]:
    one_rung_indices: List[int] = []
    self_energy_indices: List[int] = []

    for index, topo in enumerate(topologies, start=1):
        sector = classify_l1_topology(topo)
        if sector == "one_rung":
            one_rung_indices.append(index)
        elif sector == "self_energy":
            self_energy_indices.append(index)

    return {
        "one_rung_topology_indices": one_rung_indices,
        "self_energy_topology_indices": self_energy_indices,
        "one_rung_per_topology_factor": 16,
        "one_rung_total_factor": 16 * len(one_rung_indices),
    }
