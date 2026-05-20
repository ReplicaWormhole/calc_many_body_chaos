#!/usr/bin/env python3
"""Canonical multi-loop topology profiles for the v3 commutator pipeline."""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


V2_CORE_PATH = Path(__file__).resolve().with_name("calc_commutator_contrib_v2_core.py")


def load_v2():
    spec = importlib.util.spec_from_file_location("calc_commutator_contrib_v2_core_runtime_v3", V2_CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load v2 core module from {V2_CORE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


v2 = load_v2()

Vertex = v2.Vertex
Propagator = v2.Propagator
TopologyData = v2.TopologyData
ExternalLeg = v2.ExternalLeg
extract_topology_blocks = v2.extract_topology_blocks
parse_topology = v2.parse_topology
internal_vertices = v2.internal_vertices
canonical_topology_signature = v2.canonical_topology_signature


@dataclass(frozen=True)
class TopologyProfile:
    loop_order: int
    n_internal_vertices: int
    n_internal_edges: int
    external_attachment_multiplicities: tuple[int, ...]
    attachment_role_profile: tuple[tuple[int, int], ...]
    self_loop_multiplicities: tuple[int, ...]
    bridge_multiplicities: tuple[int, ...]
    has_tree_skeleton: bool


def _internal_edges(topo: v2.TopologyData) -> List[v2.Propagator]:
    return [prop for prop in topo.propagators if not prop.v1.is_external and not prop.v2.is_external]


def infer_loop_order(topo: v2.TopologyData) -> int:
    internal_vertex_list = v2.internal_vertices(topo.propagators)
    if not internal_vertex_list:
        return 0

    internal_edges = [
        prop for prop in topo.propagators if not prop.v1.is_external and not prop.v2.is_external
    ]
    return len(internal_edges) - len(internal_vertex_list) + 1


def external_attachment_multiplicities(topo: v2.TopologyData) -> tuple[int, ...]:
    counts: Counter[v2.Vertex] = Counter()

    for prop in topo.propagators:
        if prop.v1.is_external and not prop.v2.is_external:
            counts[prop.v2] += 1
        elif prop.v2.is_external and not prop.v1.is_external:
            counts[prop.v1] += 1

    values = [counts[vertex] for vertex in v2.internal_vertices(topo.propagators) if counts[vertex] > 0]
    return tuple(sorted(values, reverse=True))


def attachment_role_profile(topo: v2.TopologyData) -> tuple[tuple[int, int], ...]:
    counts: Counter[v2.Vertex] = Counter()
    outgoing: Counter[v2.Vertex] = Counter()

    for prop in topo.propagators:
        if prop.v1.is_external and not prop.v2.is_external:
            target = prop.v2
            label = prop.v1.label
        elif prop.v2.is_external and not prop.v1.is_external:
            target = prop.v1
            label = prop.v2.label
        else:
            continue

        if label in {1, 2}:
            counts[target] += 1
        elif label in {3, 4}:
            outgoing[target] += 1

    profile = []
    for vertex in v2.internal_vertices(topo.propagators):
        profile.append((counts[vertex], outgoing[vertex]))
    return tuple(sorted(profile))


def self_loop_multiplicities(topo: v2.TopologyData) -> tuple[int, ...]:
    counter: Counter[v2.Vertex] = Counter()
    for prop in topo.propagators:
        if prop.v1 == prop.v2 and not prop.v1.is_external:
            counter[prop.v1] += 1
    return tuple(sorted((count for count in counter.values() if count > 0), reverse=True))


def bridge_multiplicities(topo: v2.TopologyData) -> tuple[int, ...]:
    counter: Counter[tuple[v2.Vertex, v2.Vertex]] = Counter()
    for prop in topo.propagators:
        if prop.v1.is_external or prop.v2.is_external or prop.v1 == prop.v2:
            continue
        edge = tuple(sorted((prop.v1, prop.v2), key=lambda vertex: (vertex.kind, vertex.label)))
        counter[edge] += 1
    return tuple(sorted(counter.values(), reverse=True))


def build_topology_profile(topo: v2.TopologyData) -> TopologyProfile:
    internal_edges = _internal_edges(topo)
    return TopologyProfile(
        loop_order=infer_loop_order(topo),
        n_internal_vertices=len(v2.internal_vertices(topo.propagators)),
        n_internal_edges=len(internal_edges),
        external_attachment_multiplicities=external_attachment_multiplicities(topo),
        attachment_role_profile=attachment_role_profile(topo),
        self_loop_multiplicities=self_loop_multiplicities(topo),
        bridge_multiplicities=bridge_multiplicities(topo),
        has_tree_skeleton=has_tree_skeleton(topo),
    )


def family_tag(topo: v2.TopologyData) -> str:
    profile = build_topology_profile(topo)
    attachments = "-".join(str(value) for value in profile.external_attachment_multiplicities) or "0"
    bridges = "-".join(str(value) for value in profile.bridge_multiplicities) or "0"
    self_loops = "-".join(str(value) for value in profile.self_loop_multiplicities) or "0"
    return f"ext:{attachments}|bridges:{bridges}|loops:{self_loops}"


def structural_family_signature(topo: v2.TopologyData) -> str:
    return family_tag(topo)


def simple_internal_graph_edges(topo: v2.TopologyData) -> tuple[tuple[v2.Vertex, v2.Vertex], ...]:
    edges = set()
    for prop in topo.propagators:
        if prop.v1.is_external or prop.v2.is_external or prop.v1 == prop.v2:
            continue
        edges.add(tuple(sorted((prop.v1, prop.v2), key=lambda vertex: (vertex.kind, vertex.label))))
    return tuple(sorted(edges, key=lambda pair: ((pair[0].kind, pair[0].label), (pair[1].kind, pair[1].label))))


def has_tree_skeleton(topo: v2.TopologyData) -> bool:
    vertices = v2.internal_vertices(topo.propagators)
    if not vertices:
        return False

    edges = simple_internal_graph_edges(topo)
    if len(edges) != len(vertices) - 1:
        return False

    adjacency: Dict[v2.Vertex, set[v2.Vertex]] = {vertex: set() for vertex in vertices}
    for left_vertex, right_vertex in edges:
        adjacency[left_vertex].add(right_vertex)
        adjacency[right_vertex].add(left_vertex)

    seen = set()
    stack = [vertices[0]]
    while stack:
        vertex = stack.pop()
        if vertex in seen:
            continue
        seen.add(vertex)
        stack.extend(adjacency[vertex] - seen)
    return seen == set(vertices)


def is_structural_ladder_candidate(topo: v2.TopologyData) -> bool:
    loop_order = infer_loop_order(topo)
    if loop_order == 0:
        return False
    if loop_order == 1:
        return v2.classify_l1_topology(topo) == "one_rung"
    profile = build_topology_profile(topo)
    return (
        profile.has_tree_skeleton
        and bool(profile.self_loop_multiplicities)
        and bool(profile.external_attachment_multiplicities)
        and max(profile.external_attachment_multiplicities) >= 2
    )


def summarize_topology(topo: v2.TopologyData, index: int) -> Dict[str, object]:
    profile = build_topology_profile(topo)
    return {
        "index": index,
        "topology_id": topo.topo_id,
        "loop_order": profile.loop_order,
        "n_internal_vertices": profile.n_internal_vertices,
        "n_internal_edges": profile.n_internal_edges,
        "external_attachment_multiplicities": list(profile.external_attachment_multiplicities),
        "attachment_role_profile": [list(pair) for pair in profile.attachment_role_profile],
        "self_loop_multiplicities": list(profile.self_loop_multiplicities),
        "bridge_multiplicities": list(profile.bridge_multiplicities),
        "has_tree_skeleton": profile.has_tree_skeleton,
        "family_tag": family_tag(topo),
        "structural_ladder_candidate": is_structural_ladder_candidate(topo),
        "signature": list(v2.canonical_topology_signature(topo)[1]),
    }
