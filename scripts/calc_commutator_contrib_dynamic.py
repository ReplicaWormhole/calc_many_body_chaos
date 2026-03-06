#!/usr/bin/env python3
"""Generate FeynArts topologies on the fly and compute SK contributions."""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import sympy as sp


REPO_ROOT = Path(__file__).resolve().parent.parent
BASE_SCRIPT = Path(__file__).resolve().with_name("calc_commutator_contrib.py")
WLS_SCRIPT = Path(__file__).resolve().with_name("generate_all_loop_topologies.wls")


def load_base_module():
    spec = importlib.util.spec_from_file_location("calc_commutator_contrib_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load base script: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = load_base_module()


def resolve_wolfram_command(script_path: Path) -> List[str]:
    kernel = shutil.which("WolframKernel")
    if kernel is not None:
        return [kernel, "-script", str(script_path)]

    wolframscript = shutil.which("wolframscript")
    if wolframscript is not None:
        return [wolframscript, "-file", str(script_path)]

    raise RuntimeError(
        "Neither WolframKernel nor wolframscript was found in PATH; cannot generate topologies on the fly"
    )


def run_wolfram_topology_generation(
    loop_order: int, image_dir: Path, topology_list_path: Path, mode: str | None = None
) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    topology_list_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        *resolve_wolfram_command(WLS_SCRIPT),
        str(loop_order),
        str(image_dir),
        str(topology_list_path),
    ]
    if mode is not None:
        cmd.append(mode)
    try:
        subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired as exc:
        tail = "\n".join((exc.stdout or "").splitlines()[-60:])
        raise RuntimeError(
            f"Wolfram topology generation timed out for L={loop_order} after 300s:\n{tail}"
        ) from exc
    except subprocess.CalledProcessError as exc:
        tail = "\n".join((exc.stdout or "").splitlines()[-60:])
        raise RuntimeError(
            f"Wolfram topology generation failed for L={loop_order}:\n{tail}"
        ) from exc


def convert_ps_images_to_pdf(image_dir: Path) -> None:
    ps2pdf = shutil.which("ps2pdf")
    if ps2pdf is None:
        raise RuntimeError("ps2pdf not found in PATH; cannot convert topology images to PDF")

    ps_paths = sorted(image_dir.glob("topology*.ps"))
    if not ps_paths:
        raise FileNotFoundError(f"No topology PostScript files found in {image_dir}")

    for ps_path in ps_paths:
        pdf_path = ps_path.with_suffix(".pdf")
        try:
            subprocess.run(
                [ps2pdf, str(ps_path), str(pdf_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            tail = "\n".join((exc.stdout or "").splitlines()[-60:])
            raise RuntimeError(f"ps2pdf failed for {ps_path}:\n{tail}") from exc


def count_generated_images(image_dir: Path) -> int:
    return sum(1 for _ in image_dir.glob("topology*.pdf"))


def ensure_generated_artifacts(topology_list_path: Path, image_dir: Path, require_images: bool) -> int:
    if not topology_list_path.exists():
        raise FileNotFoundError(f"Generated topology list not found: {topology_list_path}")

    text = topology_list_path.read_text(encoding="utf-8")
    block_count = len(base.extract_topology_blocks(text))
    if block_count == 0:
        raise ValueError(f"No Topology[...] entries found in generated file {topology_list_path}")

    if require_images:
        image_count = count_generated_images(image_dir)
        if image_count != block_count:
            raise RuntimeError(
                f"Generated image count mismatch for {image_dir}: found {image_count}, expected {block_count}"
            )

    return block_count


def image_path_for_index(index: int, out_path: Path, image_dir: Path) -> str:
    image_path = image_dir / f"topology{index}.pdf"
    if not image_path.exists():
        raise FileNotFoundError(f"Topology image not found: {image_path}")
    rel_path = os.path.relpath(image_path, start=out_path.parent)
    return Path(rel_path).as_posix()


def write_latex_report(
    results: List[Dict[str, object]],
    out_path: Path,
    nc_symbol: str,
    loop_order: int,
    image_dir: Path,
) -> None:
    lines: List[str] = []
    lines.append(r"\documentclass{article}")
    lines.append(r"\usepackage{amsmath}")
    lines.append(r"\usepackage{graphicx}")
    lines.append(r"\usepackage[margin=2.2cm]{geometry}")
    lines.append(r"\begin{document}")
    lines.append(rf"\section*{{SK Matrix-Model Contributions for All L={loop_order} Topologies}}")
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
        lines.append(rf"\section*{{Topology {entry_index} (FeynArts Topology {topo_id})}}")
        lines.append(r"\begin{center}")
        lines.append(
            rf"\includegraphics[width=0.28\textwidth]{{{image_path_for_index(entry_index, out_path, image_dir)}}}"
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
            rhs = rf"{coeff_ltx}\,{prop_prod}" if nc_ltx == "1" else rf"{coeff_ltx}\,{nc_ltx}\,{prop_prod}"
            lines.append(r"\begin{equation*}")
            lines.append(rf"\mathcal{{T}}_{{{entry_index},{term_index}}} = {rhs}")
            lines.append(r"\end{equation*}")

    lines.append(r"\end{document}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate FeynArts topologies on the fly and compute translated SK contributions."
    )
    parser.add_argument("--loops", "-L", type=int, default=1, help="Loop order L for CreateTopologies")
    parser.add_argument(
        "--output",
        default=None,
        help="Output LaTeX path; defaults to output/commutator_contrib_dynamic_L<loops>.tex",
    )
    parser.add_argument(
        "--generated-dir",
        default=None,
        help="Directory for generated topology PDFs and topology list; defaults to output/generated/L<loops>",
    )
    parser.add_argument("--Nc-symbol", default="N_c", help="LaTeX symbol for matrix size")
    parser.add_argument("--g-symbol", default="g_2", help="Symbol for coupling")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.loops < 0:
        raise ValueError(f"Loop order must be non-negative, got {args.loops}")

    output_path = (
        Path(args.output)
        if args.output is not None
        else REPO_ROOT / "output" / f"commutator_contrib_dynamic_L{args.loops}.tex"
    )
    generated_dir = (
        Path(args.generated_dir)
        if args.generated_dir is not None
        else REPO_ROOT / "output" / "generated" / f"L{args.loops}"
    )
    image_dir = generated_dir / "images"
    topology_list_path = generated_dir / f"all_L_{args.loops}.txt"

    print(f"Generating L={args.loops} topology list via Wolfram/FeynArts")
    run_wolfram_topology_generation(
        args.loops,
        image_dir=image_dir,
        topology_list_path=topology_list_path,
        mode="--list-only",
    )
    topology_count = ensure_generated_artifacts(topology_list_path, image_dir, require_images=False)

    print(f"Rendering {topology_count} topology image(s)")
    run_wolfram_topology_generation(
        args.loops,
        image_dir=image_dir,
        topology_list_path=topology_list_path,
        mode="--images-only",
    )
    convert_ps_images_to_pdf(image_dir)
    ensure_generated_artifacts(topology_list_path, image_dir, require_images=True)

    text = topology_list_path.read_text(encoding="utf-8")
    blocks = base.extract_topology_blocks(text)

    topologies = [base.parse_topology(block) for block in blocks]
    g_symbol = sp.Symbol(args.g_symbol)
    print(f"Found {len(topologies)} topolog{'y' if len(topologies)==1 else 'ies'} in generated file")

    results = []
    for entry_index, topo in enumerate(topologies, start=1):
        print(
            f"Processing topology entry {entry_index} "
            f"(FeynArts topology {topo.topo_id}) with {len(topo.propagators)} propagators"
        )
        results.append(base.enumerate_terms(topo, g_symbol=g_symbol, nc_symbol=args.Nc_symbol))

    write_latex_report(results, output_path, nc_symbol=args.Nc_symbol, loop_order=args.loops, image_dir=image_dir)
    print(f"Wrote LaTeX report to {output_path}")
    pdf_path = base.compile_latex(output_path)
    print(f"Compiled PDF report to {pdf_path}")


if __name__ == "__main__":
    main()
