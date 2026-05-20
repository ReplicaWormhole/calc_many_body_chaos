#!/usr/bin/env python3
"""Generate a canonical v2 report for topology lists."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List


CORE_PATH = Path(__file__).resolve().with_name("calc_commutator_contrib_v2_core.py")


def load_core():
    spec = importlib.util.spec_from_file_location("calc_commutator_contrib_v2_core_runtime", CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load v2 core module from {CORE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


core = load_core()


def latex_escape(text: str) -> str:
    return text.replace("_", r"\_")


def build_summary(text: str) -> Dict[str, object]:
    topologies = [core.parse_topology(block) for block in core.extract_topology_blocks(text)]
    entries: List[Dict[str, object]] = []

    for index, topo in enumerate(topologies, start=1):
        entries.append(
            {
                "index": index,
                "topology_id": topo.topo_id,
                "sector": core.classify_l1_topology(topo) if len(core.internal_vertices(topo.propagators)) == 2 else "other",
                "signature": list(core.canonical_topology_signature(topo)[1]),
            }
        )

    return {
        "topology_count": len(topologies),
        "entries": entries,
        "paper_l1": core.summarize_l1_paper_sectors(topologies),
    }


def write_report(summary: Dict[str, object], out_path: Path) -> None:
    lines = [
        r"\documentclass{article}",
        r"\usepackage[margin=2.2cm]{geometry}",
        r"\begin{document}",
        r"\section*{Commutator Contribution V2 Summary}",
        r"V2 assigns external operators by external vertex labels, not propagator appearance order.",
        r"This report uses external vertex labels 1..4 for the fixed assignment $\phi_r^1(x_1)\,\phi_a^1(x_2)\,\phi_r^2(x_3)\,\phi_a^2(x_4)$.",
        rf"Parsed topology count: {summary['topology_count']}.",
        r"\section*{Paper L=1 Summary}",
        rf"One-rung topology indices: {summary['paper_l1']['one_rung_topology_indices']}.",
        rf"Self-energy topology indices: {summary['paper_l1']['self_energy_topology_indices']}.",
        rf"Per-topology one-rung factor: {summary['paper_l1']['one_rung_per_topology_factor']}.",
        rf"Paper one-rung total factor: {summary['paper_l1']['one_rung_total_factor']}.",
    ]

    for entry in summary["entries"]:
        lines.append(rf"\section*{{Topology {entry['index']}}}")
        lines.append(rf"FeynArts topology id: {entry['topology_id']}.")
        lines.append(rf"Sector: {latex_escape(str(entry['sector']))}.")

    lines.append(r"\end{document}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a canonical v2 topology summary report.")
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
