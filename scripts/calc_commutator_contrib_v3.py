#!/usr/bin/env python3
"""Generate a canonical v3 report for arbitrary loop-order topology lists."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List


V3_CORE_PATH = Path(__file__).resolve().with_name("calc_commutator_contrib_v3_core.py")


def load_v3_core():
    spec = importlib.util.spec_from_file_location("calc_commutator_contrib_v3_core_runtime", V3_CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load v3 core module from {V3_CORE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


core = load_v3_core()


def build_summary(text: str) -> Dict[str, object]:
    topologies = [core.parse_topology(block) for block in core.extract_topology_blocks(text)]
    if not topologies:
        raise ValueError("No topologies found")

    entries: List[Dict[str, object]] = []
    family_histogram: Counter[str] = Counter()
    ladder_candidates: List[int] = []
    loop_orders = {core.infer_loop_order(topo) for topo in topologies}
    if len(loop_orders) != 1:
        raise ValueError(f"Expected a single loop order in one input file, got {sorted(loop_orders)}")
    loop_order = next(iter(loop_orders))

    for index, topo in enumerate(topologies, start=1):
        entry = core.summarize_topology(topo, index)
        family_histogram[entry["family_tag"]] += 1
        if entry["structural_ladder_candidate"]:
            ladder_candidates.append(index)
        entries.append(entry)

    summary: Dict[str, object] = {
        "loop_order": loop_order,
        "topology_count": len(topologies),
        "entries": entries,
        "family_histogram": dict(sorted(family_histogram.items())),
        "structural_ladder_candidate_indices": ladder_candidates,
    }
    if loop_order == 1:
        summary["paper_l1"] = core.v2.summarize_l1_paper_sectors(topologies)
    return summary


def write_report(summary: Dict[str, object], out_path: Path) -> None:
    lines = [
        r"\documentclass{article}",
        r"\usepackage[margin=2.2cm]{geometry}",
        r"\begin{document}",
        r"\section*{Commutator Contribution V3 Summary}",
        r"This general-loop report keeps the v2 canonical external-label assignment and adds stable multi-loop graph profiles.",
        rf"Loop order: {summary['loop_order']}.",
        rf"Parsed topology count: {summary['topology_count']}.",
        r"\section*{Family histogram}",
    ]

    for family, count in summary["family_histogram"].items():
        lines.append(rf"{family}: {count}.")

    lines.extend(
        [
            r"\section*{Structural ladder candidates}",
            rf"Structural ladder-candidate indices: {summary['structural_ladder_candidate_indices']}.",
            r"The ladder-candidate flag is a broad structural heuristic: exact for the v2 `L=1` split, and intentionally broader for higher loops where v3 reports graph families rather than exact paper coefficients.",
        ]
    )

    if "paper_l1" in summary:
        lines.extend(
            [
                r"\section*{Paper L=1 Summary}",
                rf"One-rung topology indices: {summary['paper_l1']['one_rung_topology_indices']}.",
                rf"Paper one-rung total factor: {summary['paper_l1']['one_rung_total_factor']}.",
            ]
        )

    for entry in summary["entries"]:
        lines.append(rf"\section*{{Topology {entry['index']}}}")
        lines.append(rf"FeynArts topology id: {entry['topology_id']}.")
        lines.append(rf"Structural family: {entry['family_tag']}.")
        lines.append(
            rf"Profile: attachments={entry['attachment_role_profile']}, external-multiplicities={entry['external_attachment_multiplicities']}, self-loops={entry['self_loop_multiplicities']}, bridges={entry['bridge_multiplicities']}, tree-skeleton={entry['has_tree_skeleton']}, ladder-candidate={entry['structural_ladder_candidate']}."
        )

    lines.append(r"\end{document}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a canonical v3 topology summary report.")
    parser.add_argument("--input", required=True, help="Topology list input path")
    parser.add_argument("--output", required=True, help="Output report path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    text = Path(args.input).read_text(encoding="utf-8")
    summary = build_summary(text)
    write_report(summary, Path(args.output))


if __name__ == "__main__":
    main()
