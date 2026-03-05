#!/usr/bin/env python3
"""Generate symbolic SK contributions to the squared commutator from FeynArts topologies.

This script parses one or more Topology[...] expressions (FeynArts text format),
enumerates all internal contour/r-a assignments, keeps nonzero SK phi^4 vertex
weights, counts matrix-index Nc loops, and writes a LaTeX report.
"""

from __future__ import annotations

import argparse
import itertools
import re
import subprocess
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import sympy as sp


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


@dataclass
class TopologyData:
    topo_id: int
    propagators: List[Propagator]


@dataclass(frozen=True)
class ExternalLeg:
    contour: int
    ra: str
    idx_pair: Tuple[str, str]
    coord: str


@dataclass(frozen=True)
class PropagatorTerm:
    raw_token: str
    translated_token: str


class DSU:
    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}

    def add(self, x: str) -> None:
        if x not in self.parent:
            self.parent[x] = x

    def find(self, x: str) -> str:
        self.add(x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: str, b: str) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra != rb:
            self.parent[rb] = ra


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
            break

        first_open = text.find("[", start + len("Topology"))
        if first_open < 0:
            raise ValueError("Malformed Topology expression: missing first '['")
        first_close = _matching_bracket(text, first_open)

        j = first_close + 1
        while j < len(text) and text[j].isspace():
            j += 1
        if j >= len(text) or text[j] != "[":
            raise ValueError("Malformed Topology expression: missing second '[...]' block")
        second_close = _matching_bracket(text, j)

        blocks.append(text[start : second_close + 1])
        i = second_close + 1

    return blocks


def parse_topology(block: str) -> TopologyData:
    t_start = block.find("Topology[")
    first_open = block.find("[", t_start + len("Topology"))
    first_close = _matching_bracket(block, first_open)
    topo_id = int(block[first_open + 1 : first_close].strip())

    second_open = block.find("[", first_close + 1)
    second_close = _matching_bracket(block, second_open)
    body = block[second_open + 1 : second_close]

    propagators: List[Propagator] = []
    for m in PROP_RE.finditer(body):
        ptype = re.sub(r"\s+", "", m.group("ptype"))
        v1 = Vertex(int(m.group("v1k")), int(m.group("v1l")))
        v2 = Vertex(int(m.group("v2k")), int(m.group("v2l")))
        propagators.append(Propagator(len(propagators), ptype, v1, v2))

    if not propagators:
        raise ValueError(f"Topology {topo_id}: no propagators parsed")

    return TopologyData(topo_id=topo_id, propagators=propagators)


def is_external_ptype(ptype: str) -> bool:
    return ptype.startswith("Incoming") or ptype.startswith("Outgoing")


def internal_vertices_in_appearance_order(props: Iterable[Propagator]) -> List[Vertex]:
    ordered: List[Vertex] = []
    seen = set()
    for p in props:
        for v in (p.v1, p.v2):
            if not v.is_external and v not in seen:
                seen.add(v)
                ordered.append(v)
    return ordered


def build_external_map(props: List[Propagator]) -> Dict[Tuple[int, int], ExternalLeg]:
    ext_defs = [
        ExternalLeg(1, "r", ("a1", "b1"), "x_1"),
        ExternalLeg(1, "a", ("a2", "b2"), "x_2"),
        ExternalLeg(2, "r", ("a3", "b3"), "x_3"),
        ExternalLeg(2, "a", ("a4", "b4"), "x_4"),
    ]

    ext_edges = [p for p in props if is_external_ptype(p.ptype)]
    if len(ext_edges) != 4:
        raise ValueError(
            f"Expected exactly 4 Incoming/Outgoing propagators, got {len(ext_edges)}"
        )

    fixed: Dict[Tuple[int, int], ExternalLeg] = {}
    for i, p in enumerate(ext_edges):
        leg = ext_defs[i]
        if p.v1.is_external and not p.v2.is_external:
            fixed[(p.edge_id, 0)] = leg
        elif p.v2.is_external and not p.v1.is_external:
            fixed[(p.edge_id, 1)] = leg
        elif p.v1.is_external and p.v2.is_external:
            fixed[(p.edge_id, 0)] = leg
        else:
            raise ValueError(
                f"External propagator edge {p.edge_id} has no external endpoint: {p}"
            )

    return fixed


def incident_endpoints_by_vertex(props: List[Propagator]) -> Dict[Vertex, List[Tuple[int, int]]]:
    vertices = internal_vertices_in_appearance_order(props)
    out: Dict[Vertex, List[Tuple[int, int]]] = {v: [] for v in vertices}
    for p in props:
        if not p.v1.is_external:
            out[p.v1].append((p.edge_id, 0))
        if not p.v2.is_external:
            out[p.v2].append((p.edge_id, 1))
    return out


def count_nc_loops(props: List[Propagator], fixed_external: Dict[Tuple[int, int], ExternalLeg]) -> int:
    endpoint_idx: Dict[Tuple[int, int], Tuple[str, str]] = {}
    all_symbols: List[str] = []

    for p in props:
        for side in (0, 1):
            k = (p.edge_id, side)
            if k in fixed_external:
                endpoint_idx[k] = fixed_external[k].idx_pair
            else:
                endpoint_idx[k] = (f"i_{p.edge_id}_{side}_a", f"i_{p.edge_id}_{side}_b")
            all_symbols.extend(endpoint_idx[k])

    dsu = DSU()
    for sym in all_symbols:
        dsu.add(sym)

    # Propagator double-line constraints.
    for p in props:
        a0, b0 = endpoint_idx[(p.edge_id, 0)]
        a1, b1 = endpoint_idx[(p.edge_id, 1)]
        dsu.union(a0, b1)
        dsu.union(b0, a1)

    # Quartic trace contractions at internal vertices (appearance-order cyclic rule).
    inc = incident_endpoints_by_vertex(props)
    for v, legs in inc.items():
        if len(legs) != 4:
            raise ValueError(
                f"Internal vertex {v} has degree {len(legs)}; expected 4 (phi^4)"
            )
        for i in range(4):
            e_cur = legs[i]
            e_nxt = legs[(i + 1) % 4]
            beta_cur = endpoint_idx[e_cur][1]
            alpha_next = endpoint_idx[e_nxt][0]
            dsu.union(beta_cur, alpha_next)

    external_symbols = {
        "a1",
        "b1",
        "a2",
        "b2",
        "a3",
        "b3",
        "a4",
        "b4",
    }

    comp: Dict[str, set] = defaultdict(set)
    for sym in set(all_symbols):
        comp[dsu.find(sym)].add(sym)

    internal_components = [s for s in comp.values() if s.isdisjoint(external_symbols)]
    return len(internal_components)


def translate_propagator(c1: int, c2: int, l1: str, l2: str, x1: str, x2: str) -> str | None:
    args = f"\\left({x1},{x2}\\right)"
    if c1 == c2:
        if l1 == "r" and l2 == "r":
            return f"G_K{args}"
        if l1 == "r" and l2 == "a":
            return f"G_R{args}"
        if l1 == "a" and l2 == "r":
            return f"G_A{args}"
        if l1 == "a" and l2 == "a":
            return None
    elif c1 == 1 and c2 == 2:
        if l1 == "r" and l2 == "r":
            return f"G^< {args}".replace(" ", "")
        return None
    elif c1 == 2 and c2 == 1:
        if l1 == "r" and l2 == "r":
            return f"G^> {args}".replace(" ", "")
        return None
    raise ValueError(f"Unsupported contour/ra combination: c1={c1}, c2={c2}, l1={l1}, l2={l2}")


def build_propagator_term(
    c1: int,
    c2: int,
    l1: str,
    l2: str,
    x1: str,
    x2: str,
) -> PropagatorTerm | None:
    raw_token = f"G^{{{c1}{c2}}}_{{{l1}{l2}}}\\left({x1},{x2}\\right)"
    translated_token = translate_propagator(c1, c2, l1, l2, x1, x2)
    if translated_token is None:
        return None
    return PropagatorTerm(raw_token=raw_token, translated_token=translated_token)


def enumerate_terms(
    topo: TopologyData,
    g_symbol: sp.Symbol,
    nc_symbol: str,
) -> Dict[str, object]:
    props = topo.propagators
    fixed_external = build_external_map(props)

    internal_vertices = internal_vertices_in_appearance_order(props)
    inc = incident_endpoints_by_vertex(props)

    for v, legs in inc.items():
        if len(legs) != 4:
            raise ValueError(
                f"Topology {topo.topo_id}: internal vertex {v} has degree {len(legs)}, expected 4"
            )

    # Internal coordinates z_1, z_2, ... mapped by vertex appearance order.
    z_map = {v: f"z_{{{i + 1}}}" for i, v in enumerate(internal_vertices)}

    # Variables to sum over.
    contour_vars = internal_vertices
    branch_vars: List[Tuple[int, int]] = []
    for p in props:
        for side, v in ((0, p.v1), (1, p.v2)):
            if not v.is_external:
                branch_vars.append((p.edge_id, side))

    nc_raw = count_nc_loops(props, fixed_external)
    nc_net = nc_raw - 4

    total_assignments = (2 ** len(contour_vars)) * (2 ** len(branch_vars))
    print(
        f"[topology {topo.topo_id}] internal vertices={len(contour_vars)}, "
        f"internal half-edges={len(branch_vars)}, assignments={total_assignments}"
    )

    aggregated: Dict[Tuple[int, Tuple[str, ...]], sp.Expr] = defaultdict(lambda: sp.Integer(0))
    surviving_assignments = 0

    progress_step = 200000 if total_assignments >= 200000 else None
    checked = 0

    for c_values in itertools.product((1, 2), repeat=len(contour_vars)):
        c_assign = dict(zip(contour_vars, c_values))

        for l_values in itertools.product(("r", "a"), repeat=len(branch_vars)):
            checked += 1
            if progress_step and checked % progress_step == 0:
                print(
                    f"[topology {topo.topo_id}] processed {checked}/{total_assignments} assignments"
                )

            l_assign = dict(zip(branch_vars, l_values))

            coeff = sp.Integer(1)
            for v in internal_vertices:
                legs = inc[v]
                l_labels = [l_assign[e] for e in legs]
                n_a = sum(1 for x in l_labels if x == "a")
                if n_a == 1:
                    v_weight = 4
                elif n_a == 3:
                    v_weight = 1
                else:
                    coeff = sp.Integer(0)
                    break
                coeff *= -sp.I * g_symbol * sp.Integer(v_weight)

            if coeff == 0:
                continue

            surviving_assignments += 1

            prop_terms: List[PropagatorTerm] = []
            for p in props:
                c1 = fixed_external[(p.edge_id, 0)].contour if (p.edge_id, 0) in fixed_external else c_assign[p.v1]
                c2 = fixed_external[(p.edge_id, 1)].contour if (p.edge_id, 1) in fixed_external else c_assign[p.v2]
                l1 = fixed_external[(p.edge_id, 0)].ra if (p.edge_id, 0) in fixed_external else l_assign[(p.edge_id, 0)]
                l2 = fixed_external[(p.edge_id, 1)].ra if (p.edge_id, 1) in fixed_external else l_assign[(p.edge_id, 1)]

                x1 = fixed_external[(p.edge_id, 0)].coord if (p.edge_id, 0) in fixed_external else z_map[p.v1]
                x2 = fixed_external[(p.edge_id, 1)].coord if (p.edge_id, 1) in fixed_external else z_map[p.v2]

                prop_term = build_propagator_term(c1, c2, l1, l2, x1, x2)
                if prop_term is None:
                    coeff = sp.Integer(0)
                    break
                prop_terms.append(prop_term)

            if coeff == 0:
                continue

            key = (nc_net, tuple(sorted(t.translated_token for t in prop_terms)))
            aggregated[key] += coeff

    terms_out: List[Dict[str, object]] = []
    for (net_pow, prop_sig), coeff in sorted(
        aggregated.items(), key=lambda kv: (-kv[0][0], kv[0][1])
    ):
        coeff = sp.simplify(coeff)
        if coeff == 0:
            continue
        terms_out.append(
            {
                "coeff": coeff,
                "coeff_latex": sp.latex(coeff),
                "nc_net_power": net_pow,
                "nc_factor_latex": (
                    "1" if net_pow == 0 else f"{nc_symbol}^{{{net_pow}}}"
                ),
                "propagators": list(prop_sig),
            }
        )

    return {
        "topology_id": topo.topo_id,
        "n_props": len(props),
        "n_internal_vertices": len(internal_vertices),
        "n_internal_half_edges": len(branch_vars),
        "total_assignments": total_assignments,
        "surviving_assignments": surviving_assignments,
        "nc_raw_power": nc_raw,
        "nc_net_power": nc_net,
        "terms": terms_out,
    }


def write_latex_report(results: List[Dict[str, object]], out_path: Path, nc_symbol: str, g_symbol: str) -> None:
    lines: List[str] = []
    lines.append(r"\documentclass{article}")
    lines.append(r"\usepackage{amsmath}")
    lines.append(r"\usepackage[margin=2.2cm]{geometry}")
    lines.append(r"\begin{document}")
    lines.append(r"\section*{SK Matrix-Model Contributions to the Squared Commutator}")
    lines.append(
        r"External assignment (by external-propagator appearance): "
        r"$\phi_r^1(x_1)\,\phi_a^1(x_2)\,\phi_r^2(x_3)\,\phi_a^2(x_4)$, "
        r"with $x_1=(t,\mathbf{x})$, $x_2=(0,\mathbf{0})$, $x_3=(t,\mathbf{x})$, $x_4=(0,\mathbf{0})$."
    )
    lines.append(
        r"Propagator notation: $G^{c_1 c_2}_{\ell_1\ell_2}(z,y)$ "
        r"(upper indices: time folds, lower indices: r/a labels)."
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

    for r in results:
        topo_id = r["topology_id"]
        lines.append(rf"\section*{{Topology {topo_id}}}")
        lines.append(
            rf"\noindent Parsed propagators: {r['n_props']}. "
            rf"Internal vertices: {r['n_internal_vertices']}. "
            rf"Internal half-edges: {r['n_internal_half_edges']}.\\"
        )
        lines.append(
            rf"\noindent Assignments checked: {r['total_assignments']}. "
            rf"Surviving (nonzero vertex weight): {r['surviving_assignments']}.\\"
        )
        lines.append(
            rf"\noindent Raw $N_c$ power: {r['nc_raw_power']}. "
            rf"Net power in $C(t)$: {r['nc_net_power']}."
        )

        terms: List[Dict[str, object]] = r["terms"]
        if not terms:
            lines.append(r"\[\text{No surviving SK contributions for this topology.}\]")
            continue

        lines.append(r"\noindent Explicit surviving terms:")
        for i, t in enumerate(terms, start=1):
            coeff_ltx = t["coeff_latex"]
            nc_ltx = t["nc_factor_latex"]
            prop_prod = r" \, ".join(t["propagators"])
            if nc_ltx != "1":
                rhs = rf"{coeff_ltx}\,{nc_ltx}\,{prop_prod}"
            else:
                rhs = rf"{coeff_ltx}\,{prop_prod}"
            lines.append(r"\begin{equation*}")
            lines.append(rf"\mathcal{{T}}_{{{i}}} = {rhs}")
            lines.append(r"\end{equation*}")

    lines.append(r"\end{document}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def compile_latex(tex_path: Path) -> Path:
    latexmk = shutil.which("latexmk")
    if latexmk is None:
        raise RuntimeError("latexmk not found in PATH; cannot compile LaTeX output")

    cmd = [
        latexmk,
        "-pdf",
        "-interaction=nonstopmode",
        "-halt-on-error",
        tex_path.name,
    ]
    try:
        subprocess.run(
            cmd,
            cwd=tex_path.parent,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        tail = "\n".join((exc.stdout or "").splitlines()[-40:])
        raise RuntimeError(f"LaTeX compilation failed for {tex_path.name}:\n{tail}") from exc
    pdf_path = tex_path.with_suffix(".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"LaTeX compilation finished but PDF not found: {pdf_path}")
    return pdf_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute symbolic SK contributions for OTOC from FeynArts topologies."
    )
    parser.add_argument("--input", default="loop_data.txt", help="Input text file with Topology[...] entries")
    parser.add_argument(
        "--output", default="output/commutator_contrib.tex", help="Output LaTeX path"
    )
    parser.add_argument("--Nc-symbol", default="N_c", help="LaTeX symbol for matrix size")
    parser.add_argument("--g-symbol", default="g_2", help="Symbol for coupling")
    parser.add_argument(
        "--no-compile",
        action="store_true",
        help="Generate .tex but skip automatic PDF compilation",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    text = input_path.read_text(encoding="utf-8")
    blocks = extract_topology_blocks(text)
    if not blocks:
        raise ValueError("No Topology[...] entries found in input file")

    topologies = [parse_topology(b) for b in blocks]
    g_symbol = sp.Symbol(args.g_symbol)

    print(f"Found {len(topologies)} topolog{'y' if len(topologies)==1 else 'ies'} in {input_path}")

    results = []
    for topo in topologies:
        print(f"Processing topology {topo.topo_id} with {len(topo.propagators)} propagators")
        results.append(enumerate_terms(topo, g_symbol=g_symbol, nc_symbol=args.Nc_symbol))

    write_latex_report(results, output_path, nc_symbol=args.Nc_symbol, g_symbol=args.g_symbol)
    print(f"Wrote LaTeX report to {output_path}")
    if args.no_compile:
        print("Skipping PDF compilation (--no-compile set)")
    else:
        pdf_path = compile_latex(output_path)
        print(f"Compiled PDF report to {pdf_path}")


if __name__ == "__main__":
    main()
