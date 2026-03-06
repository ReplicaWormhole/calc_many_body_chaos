#!/usr/bin/env python3
"""Generate SK contributions for all L=1 topologies and include topology images."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict, List

import sympy as sp


REPO_ROOT = Path(__file__).resolve().parent.parent
BASE_SCRIPT = Path(__file__).resolve().with_name("calc_commutator_contrib.py")


def load_base_module():
    spec = importlib.util.spec_from_file_location("calc_commutator_contrib_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load base script: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = load_base_module()


def image_path_for_index(index: int, out_path: Path) -> str:
    image_path = REPO_ROOT / "data" / f"topology{index}.pdf"
    if not image_path.exists():
        raise FileNotFoundError(f"Topology image not found: {image_path}")
    rel_path = os.path.relpath(image_path, start=out_path.parent)
    return Path(rel_path).as_posix()


def build_section_heading(entry_index: int, topo_id: int) -> str:
    return rf"\section*{{Topology {entry_index} (FeynArts Topology {topo_id})}}"


def write_latex_report(results: List[Dict[str, object]], out_path: Path, nc_symbol: str) -> None:
    lines: List[str] = []
    lines.append(r"\documentclass{article}")
    lines.append(r"\usepackage{amsmath}")
    lines.append(r"\usepackage{graphicx}")
    lines.append(r"\usepackage[margin=2.2cm]{geometry}")
    lines.append(r"\begin{document}")
    lines.append(r"\section*{SK Matrix-Model Contributions for All L=1 Topologies}")
    lines.append(
        r"External assignment (by external-propagator appearance): "
        r"$\phi_r^1(x_1)\,\phi_a^1(x_2)\,\phi_r^2(x_3)\,\phi_a^2(x_4)$, "
        r"with $x_1=(t,\mathbf{x})$, $x_2=(0,\mathbf{0})$, $x_3=(t,\mathbf{x})$, $x_4=(0,\mathbf{0})$."
    )
    lines.append(
        r"Translation table used: same-fold $G_{rr}\to G_K=\frac12(G^>+G^<)$, "
        r"$G_{ra}\to G_R$, $G_{ar}\to G_A$, $G_{aa}\to 0$; "
        r"cross-fold $G^{12}_{rr}\to G^<$, $G^{21}_{rr}\to G^>$, and any cross-fold propagator with an $a$ endpoint vanishes."
    )
    lines.append(
        r"Contour ordering convention: contour $(2)$ is later than contour $(1)$, matching \texttt{contour\_ra\_translation.txt}."
    )
    lines.append(
        rf"Each term carries explicit net matrix-size factor ${{{nc_symbol}}}^{{p-4}}$ "
        r"(raw loop count $p$ minus the overall $1/N^4$ normalization)."
    )

    for entry_index, result in enumerate(results, start=1):
        topo_id = result["topology_id"]
        lines.append(build_section_heading(entry_index, topo_id))
        lines.append(r"\begin{center}")
        lines.append(
            rf"\includegraphics[width=0.28\textwidth]{{{image_path_for_index(entry_index, out_path)}}}"
        )
        lines.append(r"\end{center}")
        lines.append(
            rf"\noindent Parsed propagators: {result['n_props']}. "
            rf"Internal vertices: {result['n_internal_vertices']}. "
            rf"Internal half-edges: {result['n_internal_half_edges']}.\\"
        )
        lines.append(
            rf"\noindent Assignments checked: {result['total_assignments']}. "
            rf"Surviving (nonzero vertex weight): {result['surviving_assignments']}.\\"
        )
        lines.append(
            rf"\noindent Raw $N_c$ power: {result['nc_raw_power']}. "
            rf"Net power in $C(t)$: {result['nc_net_power']}."
        )

        terms: List[Dict[str, object]] = result["terms"]
        if not terms:
            lines.append(r"\[\text{No surviving SK contributions for this topology.}\]")
            continue

        lines.append(r"\noindent Explicit surviving terms:")
        for term_index, term in enumerate(terms, start=1):
            coeff_ltx = term["coeff_latex"]
            nc_ltx = term["nc_factor_latex"]
            prop_prod = r" \, ".join(term["propagators"])
            if nc_ltx != "1":
                rhs = rf"{coeff_ltx}\,{nc_ltx}\,{prop_prod}"
            else:
                rhs = rf"{coeff_ltx}\,{prop_prod}"
            lines.append(r"\begin{equation*}")
            lines.append(rf"\mathcal{{T}}_{{{entry_index},{term_index}}} = {rhs}")
            lines.append(r"\end{equation*}")

    lines.append(r"\end{document}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute symbolic SK contributions for all L=1 topologies and include images."
    )
    parser.add_argument("--input", default="all_L_1.txt", help="Input text file with TopologyList[...] entries")
    parser.add_argument(
        "--output",
        default="output/commutator_contrib_all_L1.tex",
        help="Output LaTeX path",
    )
    parser.add_argument("--Nc-symbol", default="N_c", help="LaTeX symbol for matrix size")
    parser.add_argument("--g-symbol", default="g_2", help="Symbol for coupling")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    text = input_path.read_text(encoding="utf-8")
    blocks = base.extract_topology_blocks(text)
    if not blocks:
        raise ValueError("No Topology[...] entries found in input file")

    topologies = [base.parse_topology(block) for block in blocks]
    g_symbol = sp.Symbol(args.g_symbol)

    print(f"Found {len(topologies)} topolog{'y' if len(topologies)==1 else 'ies'} in {input_path}")

    results = []
    for entry_index, topo in enumerate(topologies, start=1):
        print(
            f"Processing topology entry {entry_index} "
            f"(FeynArts topology {topo.topo_id}) with {len(topo.propagators)} propagators"
        )
        results.append(base.enumerate_terms(topo, g_symbol=g_symbol, nc_symbol=args.Nc_symbol))

    write_latex_report(results, output_path, nc_symbol=args.Nc_symbol)
    print(f"Wrote LaTeX report to {output_path}")
    pdf_path = base.compile_latex(output_path)
    print(f"Compiled PDF report to {pdf_path}")


if __name__ == "__main__":
    main()
