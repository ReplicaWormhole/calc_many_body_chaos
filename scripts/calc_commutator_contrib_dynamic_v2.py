#!/usr/bin/env python3
"""Generate FeynArts topologies on the fly and build the v2 summary report."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


REPO_ROOT = Path(__file__).resolve().parent.parent
V2_SCRIPT = Path(__file__).resolve().with_name("calc_commutator_contrib_v2.py")
WLS_SCRIPT = Path(__file__).resolve().with_name("generate_all_loop_topologies.wls")
AMPLITUDE_WLS_SCRIPT = Path(__file__).resolve().with_name("export_paper_l1_metadata_v2.wls")


def load_v2_module():
    spec = importlib.util.spec_from_file_location("calc_commutator_contrib_v2_runtime", V2_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load v2 script: {V2_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


v2 = load_v2_module()


def latex_escape(text: str) -> str:
    return text.replace("_", r"\_")


def resolve_wolfram_command(script_path: Path) -> List[str]:
    kernel = shutil.which("WolframKernel")
    if kernel is not None:
        return [kernel, "-script", str(script_path)]

    wolframscript = shutil.which("wolframscript")
    if wolframscript is not None:
        return [wolframscript, "-file", str(script_path)]

    raise RuntimeError("Neither WolframKernel nor wolframscript was found in PATH")


def run_wolfram_topology_generation(loop_order: int, image_dir: Path, topology_list_path: Path) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    topology_list_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [*resolve_wolfram_command(WLS_SCRIPT), str(loop_order), str(image_dir), str(topology_list_path)],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def run_paper_l1_metadata_export(output_path: Path) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [*resolve_wolfram_command(AMPLITUDE_WLS_SCRIPT), str(output_path)],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return json.loads(output_path.read_text(encoding="utf-8"))


def convert_ps_images_to_pdf(image_dir: Path) -> None:
    ps2pdf = shutil.which("ps2pdf")
    if ps2pdf is None:
        raise RuntimeError("ps2pdf not found in PATH")

    for ps_path in sorted(image_dir.glob("topology*.ps")):
        pdf_path = ps_path.with_suffix(".pdf")
        subprocess.run(
            [ps2pdf, str(ps_path), str(pdf_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )


def count_generated_images(image_dir: Path) -> int:
    return sum(1 for _ in image_dir.glob("topology*.pdf"))


def image_path_for_index(index: int, out_path: Path, image_dir: Path) -> str:
    image_path = image_dir / f"topology{index}.pdf"
    if not image_path.exists():
        raise FileNotFoundError(f"Topology image not found: {image_path}")
    return Path(os.path.relpath(image_path, start=out_path.parent)).as_posix()


def write_latex_report(
    summary: dict,
    out_path: Path,
    image_dir: Path,
    loop_order: int,
    amplitude_metadata: dict | None = None,
) -> None:
    lines = [
        r"\documentclass{article}",
        r"\usepackage{graphicx}",
        r"\usepackage[margin=2.2cm]{geometry}",
        r"\begin{document}",
        rf"\section*{{V2 Dynamic Summary for L={loop_order}}}",
        r"This report uses external vertex labels for the fixed assignment and canonical graph signatures.",
        rf"Topology count: {summary['topology_count']}.",
        rf"Paper one-rung total factor: {summary['paper_l1']['one_rung_total_factor']}.",
    ]

    if amplitude_metadata is not None:
        lines.append(r"\section*{Amplitude-stage metadata}")
        lines.append(rf"Amplitude count: {amplitude_metadata['amplitude_count']}.")
        lines.append(
            rf"Amplitude-export one-rung total factor: {amplitude_metadata['paper_l1']['one_rung_total_factor']}."
        )

    for entry in summary["entries"]:
        lines.append(rf"\section*{{Topology {entry['index']}}}")
        lines.append(
            rf"\includegraphics[width=0.28\textwidth]{{{image_path_for_index(entry['index'], out_path, image_dir)}}}"
        )
        lines.append(rf"Sector: {latex_escape(str(entry['sector']))}.")

    lines.append(r"\end{document}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate topologies on the fly and build the v2 report.")
    parser.add_argument("--loops", "-L", type=int, default=1, help="Loop order")
    parser.add_argument("--output", required=True, help="Output report path")
    parser.add_argument("--generated-dir", required=True, help="Generated artifact directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generated_dir = Path(args.generated_dir)
    image_dir = generated_dir / "images"
    topology_list_path = generated_dir / f"all_L_{args.loops}.txt"

    run_wolfram_topology_generation(args.loops, image_dir=image_dir, topology_list_path=topology_list_path)
    convert_ps_images_to_pdf(image_dir)
    text = topology_list_path.read_text(encoding="utf-8")
    summary = v2.build_summary(text)
    amplitude_metadata = None
    if args.loops == 1:
        amplitude_metadata = run_paper_l1_metadata_export(generated_dir / "paper_l1_metadata.json")
    write_latex_report(
        summary,
        Path(args.output),
        image_dir=image_dir,
        loop_order=args.loops,
        amplitude_metadata=amplitude_metadata,
    )


if __name__ == "__main__":
    main()
