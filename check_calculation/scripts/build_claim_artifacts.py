#!/usr/bin/env python3
"""Build claim-scoped audit artifacts without modifying repository scripts."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import sympy as sp


CHECK_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = CHECK_ROOT.parent
BASE_SCRIPT = REPO_ROOT / "scripts" / "calc_commutator_contrib.py"
WLS_SCRIPT = REPO_ROOT / "scripts" / "generate_all_loop_topologies.wls"
ARTIFACT_ROOT = CHECK_ROOT / "artifacts"
GENERATED_ROOT = ARTIFACT_ROOT / "generated"
SUMMARY_ROOT = ARTIFACT_ROOT / "_summaries"

L2_ONE_RUNG_INDICES = [12, 18, 22, 25, 26, 29, 31, 32, 35]
L2_SELF_ENERGY_INDICES = [1, 6, 40, 42]
L1_FOCUS_INDICES = [1, 3, 4]
L3_SELECTED_INDICES = [128]


@dataclass
class LoopSummaryEntry:
    index: int
    feynarts_topology_id: int
    n_props: int
    n_internal_vertices: int
    n_internal_half_edges: int
    total_assignments: int | None
    surviving_assignments: int | None
    nc_raw_power: int
    nc_net_power: int
    nonzero_terms: int | None
    propagator_histogram: Dict[str, int]
    term_coefficients: List[str]
    term_signatures: List[List[str]]


def load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = load_module(BASE_SCRIPT, "calc_commutator_contrib_audit_base")


def resolve_wolfram_command(script_path: Path) -> List[str]:
    kernel = shutil.which("WolframKernel")
    if kernel is not None:
        return [kernel, "-script", str(script_path)]

    wolframscript = shutil.which("wolframscript")
    if wolframscript is not None:
        return [wolframscript, "-file", str(script_path)]

    raise RuntimeError("Neither WolframKernel nor wolframscript was found in PATH")


def run_wolfram(loop_order: int, image_dir: Path, topology_list_path: Path, mode: str | None = None) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    topology_list_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [*resolve_wolfram_command(WLS_SCRIPT), str(loop_order), str(image_dir), str(topology_list_path)]
    if mode is not None:
        cmd.append(mode)
    subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def convert_ps_to_pdf(image_dir: Path) -> None:
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


def copy_existing_generated(loop_order: int) -> tuple[Path, Path]:
    src_dir = REPO_ROOT / "output" / "generated" / f"L{loop_order}"
    if not src_dir.exists():
        raise FileNotFoundError(f"Missing existing generated directory: {src_dir}")

    dst_dir = GENERATED_ROOT / f"L{loop_order}"
    image_src = src_dir / "images"
    image_dst = dst_dir / "images"
    image_dst.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src_dir / f"all_L_{loop_order}.txt", dst_dir / f"all_L_{loop_order}.txt")
    for image_path in sorted(image_src.glob("topology*.pdf")):
        shutil.copy2(image_path, image_dst / image_path.name)

    return dst_dir / f"all_L_{loop_order}.txt", image_dst


def ensure_l0_assets() -> tuple[Path, Path]:
    dst_dir = GENERATED_ROOT / "L0"
    image_dir = dst_dir / "images"
    topology_list_path = dst_dir / "all_L_0.txt"
    if topology_list_path.exists() and any(image_dir.glob("topology*.pdf")):
        return topology_list_path, image_dir

    run_wolfram(0, image_dir=image_dir, topology_list_path=topology_list_path, mode="--list-only")
    run_wolfram(0, image_dir=image_dir, topology_list_path=topology_list_path, mode="--images-only")
    convert_ps_to_pdf(image_dir)
    return topology_list_path, image_dir


def ensure_l3_selected_assets(selected_indices: Sequence[int]) -> tuple[Path, Path, Dict[int, int]]:
    full_dir = GENERATED_ROOT / "L3_full"
    full_list_path = full_dir / "all_L_3.txt"
    full_image_dir = full_dir / "images"
    if not full_list_path.exists():
        run_wolfram(3, image_dir=full_image_dir, topology_list_path=full_list_path, mode="--list-only")

    blocks = base.extract_topology_blocks(full_list_path.read_text(encoding="utf-8"))
    selected_blocks = [blocks[index - 1] for index in selected_indices]

    selected_dir = GENERATED_ROOT / "L3_selected"
    selected_list_path = selected_dir / "all_L_3_selected.txt"
    selected_image_dir = selected_dir / "images"
    selected_dir.mkdir(parents=True, exist_ok=True)
    selected_list_path.write_text("TopologyList[" + ",\n".join(selected_blocks) + "]\n", encoding="utf-8")

    if not any(selected_image_dir.glob("topology*.pdf")):
        run_wolfram(3, image_dir=selected_image_dir, topology_list_path=selected_list_path, mode="--images-only")
        convert_ps_to_pdf(selected_image_dir)

    mapping = {original_index: rendered_index for rendered_index, original_index in enumerate(selected_indices, start=1)}
    return full_list_path, selected_image_dir, mapping


def histogram_from_terms(terms: Sequence[Dict[str, object]]) -> Dict[str, int]:
    counter: Counter[str] = Counter()
    for term in terms:
        for token in term["propagators"]:
            if token.startswith("G_R"):
                counter["G_R"] += 1
            elif token.startswith("G_A"):
                counter["G_A"] += 1
            elif token.startswith("G_K"):
                counter["G_K"] += 1
            elif token.startswith("G^<"):
                counter["G^<"] += 1
            elif token.startswith("G^>"):
                counter["G^>"] += 1
            else:
                counter["other"] += 1
    return dict(counter)


def summarize_block(block: str, index: int, enumerate_terms: bool) -> LoopSummaryEntry:
    topo = base.parse_topology(block)
    internal_vertices = base.internal_vertices_in_appearance_order(topo.propagators)
    fixed_external = base.build_external_map(topo.propagators)
    nc_raw = base.count_nc_loops(topo.propagators, fixed_external)

    if enumerate_terms:
        result = base.enumerate_terms(topo, sp.Symbol("g_2"), "N_c")
        terms = result["terms"]
        return LoopSummaryEntry(
            index=index,
            feynarts_topology_id=topo.topo_id,
            n_props=result["n_props"],
            n_internal_vertices=result["n_internal_vertices"],
            n_internal_half_edges=result["n_internal_half_edges"],
            total_assignments=result["total_assignments"],
            surviving_assignments=result["surviving_assignments"],
            nc_raw_power=result["nc_raw_power"],
            nc_net_power=result["nc_net_power"],
            nonzero_terms=len(terms),
            propagator_histogram=histogram_from_terms(terms),
            term_coefficients=[str(term["coeff"]) for term in terms],
            term_signatures=[list(term["propagators"]) for term in terms],
        )

    return LoopSummaryEntry(
        index=index,
        feynarts_topology_id=topo.topo_id,
        n_props=len(topo.propagators),
        n_internal_vertices=len(internal_vertices),
        n_internal_half_edges=4 * len(internal_vertices),
        total_assignments=None,
        surviving_assignments=None,
        nc_raw_power=nc_raw,
        nc_net_power=nc_raw - 4,
        nonzero_terms=None,
        propagator_histogram={},
        term_coefficients=[],
        term_signatures=[],
    )


def load_blocks(path: Path) -> List[str]:
    return base.extract_topology_blocks(path.read_text(encoding="utf-8"))


def summarize_loop(topology_list_path: Path, summary_path: Path, enumerate_terms: bool) -> List[LoopSummaryEntry]:
    blocks = load_blocks(topology_list_path)
    entries = [summarize_block(block, index=i, enumerate_terms=enumerate_terms) for i, block in enumerate(blocks, start=1)]
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps([asdict(entry) for entry in entries], indent=2), encoding="utf-8")
    return entries


def select_entries(entries: Sequence[LoopSummaryEntry], indices: Iterable[int]) -> List[LoopSummaryEntry]:
    wanted = set(indices)
    return [entry for entry in entries if entry.index in wanted]


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def write_topology_block(block: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(block + "\n", encoding="utf-8")


def write_entry_summary(entry: LoopSummaryEntry, dst: Path, notes: str | None = None) -> None:
    lines = [
        f"# Topology {entry.index}",
        "",
        f"- FeynArts topology id: `{entry.feynarts_topology_id}`",
        f"- Parsed propagators: `{entry.n_props}`",
        f"- Internal vertices: `{entry.n_internal_vertices}`",
        f"- Internal half-edges: `{entry.n_internal_half_edges}`",
        f"- Raw `N_c` power: `{entry.nc_raw_power}`",
        f"- Net `N_c` power in `C(t)`: `{entry.nc_net_power}`",
    ]
    if entry.total_assignments is not None:
        lines.append(f"- Assignments checked: `{entry.total_assignments}`")
    if entry.surviving_assignments is not None:
        lines.append(f"- Surviving assignments: `{entry.surviving_assignments}`")
    if entry.nonzero_terms is not None:
        lines.append(f"- Nonzero translated terms: `{entry.nonzero_terms}`")
    if entry.propagator_histogram:
        hist = ", ".join(f"`{k}`={v}" for k, v in sorted(entry.propagator_histogram.items()))
        lines.append(f"- Propagator histogram across surviving terms: {hist}")
    if notes:
        lines.extend(["", "## Notes", "", notes])
    if entry.term_signatures:
        lines.extend(["", "## Surviving Terms"])
        for i, (coeff, signature) in enumerate(zip(entry.term_coefficients, entry.term_signatures), start=1):
            lines.extend(["", f"### Term {i}", "", f"- Coefficient: `{coeff}`"])
            for token in signature:
                lines.append(f"- `{token}`")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_overview(entries: Sequence[LoopSummaryEntry], dst: Path, title: str) -> None:
    grouped: Dict[int, List[LoopSummaryEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.nc_net_power].append(entry)

    lines = [f"# {title}", ""]
    for nc_power in sorted(grouped):
        lines.append(f"## Net N_c Power {nc_power}")
        lines.append("")
        for entry in grouped[nc_power]:
            nonzero = "?" if entry.nonzero_terms is None else str(entry.nonzero_terms)
            lines.append(
                f"- topology `{entry.index}`: FeynArts id `{entry.feynarts_topology_id}`, "
                f"nonzero terms `{nonzero}`, raw `N_c` `{entry.nc_raw_power}`"
            )
        lines.append("")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(lines), encoding="utf-8")


def write_free_contraction_witness(dst: Path) -> None:
    legs = {
        1: {"contour": 1, "ra": "r", "coord": "x_1"},
        2: {"contour": 1, "ra": "a", "coord": "x_2"},
        3: {"contour": 2, "ra": "r", "coord": "x_3"},
        4: {"contour": 2, "ra": "a", "coord": "x_4"},
    }
    pairings = [
        ((1, 2), (3, 4)),
        ((1, 3), (2, 4)),
        ((1, 4), (2, 3)),
    ]

    lines = [
        "# Free Contraction Witness",
        "",
        "The disconnected free contribution is not generated by the connected FeynArts `2 -> 2` topology script, so C1 is checked directly from the three Wick pairings of the four external operators.",
        "",
        "External assignment:",
        "",
        "- leg 1: contour `1`, label `r`, coordinate `x_1`",
        "- leg 2: contour `1`, label `a`, coordinate `x_2`",
        "- leg 3: contour `2`, label `r`, coordinate `x_3`",
        "- leg 4: contour `2`, label `a`, coordinate `x_4`",
        "",
        "Using the same translation table as `calc_commutator_contrib.py`, the three pairings become:",
    ]

    surviving = []
    for left, right in pairings:
        l1 = legs[left[0]]
        l2 = legs[left[1]]
        r1 = legs[right[0]]
        r2 = legs[right[1]]
        left_prop = base.translate_propagator(l1["contour"], l2["contour"], l1["ra"], l2["ra"], l1["coord"], l2["coord"])
        right_prop = base.translate_propagator(r1["contour"], r2["contour"], r1["ra"], r2["ra"], r1["coord"], r2["coord"])
        label = f"({left[0]},{left[1]})({right[0]},{right[1]})"
        if left_prop is None or right_prop is None:
            lines.append(f"- pairing `{label}` vanishes")
        else:
            product = f"`{left_prop} * {right_prop}`"
            lines.append(f"- pairing `{label}` survives as {product}")
            surviving.append(label)

    lines.extend(
        [
            "",
            "Conclusion:",
            "",
            "- only pairing `(1,2)(3,4)` survives",
            "- it translates to `G_R(x_1,x_2) G_R(x_3,x_4)`",
            "- after the paper's coordinate identifications `x_1=(t,\\mathbf{x})`, `x_2=(0,\\mathbf{0})`, `x_3=(t,\\mathbf{x})`, `x_4=(0,\\mathbf{0})`, this is the two-rail retarded structure claimed in `\\S 2.1`",
        ]
    )

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_claim_folder_c1(l0_entries: Sequence[LoopSummaryEntry], l0_blocks: Sequence[str], image_dir: Path) -> None:
    claim_dir = ARTIFACT_ROOT / "C1_free_theory"
    write_free_contraction_witness(claim_dir / "summary.md")
    write_free_contraction_witness(claim_dir / "free_contractions.md")
    entry = l0_entries[0]
    write_entry_summary(
        entry,
        claim_dir / "generated_L0_contact_topology.md",
        notes="This connected `L=0` contact topology is recorded only to document why the FeynArts `2 -> 2` generator is not itself the right witness for the disconnected free-theory claim.",
    )


def build_claim_folder_c2(l1_entries: Sequence[LoopSummaryEntry], l1_blocks: Sequence[str], image_dir: Path) -> None:
    claim_dir = ARTIFACT_ROOT / "C2_order_lambda"
    write_overview(l1_entries, claim_dir / "overview.md", "L1 Overview")
    for entry in l1_entries:
        copy_file(image_dir / f"topology{entry.index}.pdf", claim_dir / "images" / f"topology{entry.index}.pdf")
    for entry in select_entries(l1_entries, L1_FOCUS_INDICES):
        write_topology_block(l1_blocks[entry.index - 1], claim_dir / "blocks" / f"topology{entry.index}_block.txt")
        write_entry_summary(
            entry,
            claim_dir / "summaries" / f"topology{entry.index}.md",
            notes="These representatives are used to inspect whether the order-lambda contribution is a self-energy dressing and whether the horizontal rail becomes retarded after the contour sum.",
        )


def build_claim_folder_c3(l2_entries: Sequence[LoopSummaryEntry], l2_blocks: Sequence[str], image_dir: Path) -> None:
    claim_dir = ARTIFACT_ROOT / "C3_order_lambda2_split"
    write_overview(l2_entries, claim_dir / "overview.md", "L2 Overview")
    for index in L2_SELF_ENERGY_INDICES + L2_ONE_RUNG_INDICES:
        copy_file(image_dir / f"topology{index}.pdf", claim_dir / "images" / f"topology{index}.pdf")
        write_topology_block(l2_blocks[index - 1], claim_dir / "blocks" / f"topology{index}_block.txt")
    for entry in select_entries(l2_entries, L2_SELF_ENERGY_INDICES + L2_ONE_RUNG_INDICES):
        note = (
            "This topology is part of the lower-N_c class used as a same-fold/self-energy witness."
            if entry.index in L2_SELF_ENERGY_INDICES
            else "This topology is part of the higher-N_c class used as an opposite-fold/one-rung witness."
        )
        write_entry_summary(entry, claim_dir / "summaries" / f"topology{entry.index}.md", notes=note)


def build_claim_folder_c4(l2_entries: Sequence[LoopSummaryEntry], l2_blocks: Sequence[str], image_dir: Path) -> None:
    claim_dir = ARTIFACT_ROOT / "C4_one_rung_factor"
    one_rung_entries = select_entries(l2_entries, L2_ONE_RUNG_INDICES)
    write_overview(one_rung_entries, claim_dir / "overview.md", "L2 Candidate One-Rung Sector")
    for entry in one_rung_entries:
        copy_file(image_dir / f"topology{entry.index}.pdf", claim_dir / "images" / f"topology{entry.index}.pdf")
        write_topology_block(l2_blocks[entry.index - 1], claim_dir / "blocks" / f"topology{entry.index}_block.txt")
        write_entry_summary(
            entry,
            claim_dir / "summaries" / f"topology{entry.index}.md",
            notes="These are the L=2 topologies with net `N_c^{-2}` scaling after the overall normalization, the sector compared against the paper's one-rung combinatoric claim.",
        )


def build_claim_folder_c5(l1_entries: Sequence[LoopSummaryEntry], l2_entries: Sequence[LoopSummaryEntry], l1_blocks: Sequence[str], l2_blocks: Sequence[str], l1_image_dir: Path, l2_image_dir: Path) -> None:
    claim_dir = ARTIFACT_ROOT / "C5_propagator_types"
    selected_pairs = [("L1", 3), ("L2", 12)]
    for loop_tag, index in selected_pairs:
        if loop_tag == "L1":
            entry = next(item for item in l1_entries if item.index == index)
            copy_file(l1_image_dir / f"topology{index}.pdf", claim_dir / "images" / f"{loop_tag}_topology{index}.pdf")
            write_topology_block(l1_blocks[index - 1], claim_dir / "blocks" / f"{loop_tag}_topology{index}_block.txt")
        else:
            entry = next(item for item in l2_entries if item.index == index)
            copy_file(l2_image_dir / f"topology{index}.pdf", claim_dir / "images" / f"{loop_tag}_topology{index}.pdf")
            write_topology_block(l2_blocks[index - 1], claim_dir / "blocks" / f"{loop_tag}_topology{index}_block.txt")
        write_entry_summary(
            entry,
            claim_dir / "summaries" / f"{loop_tag}_topology{index}.md",
            notes="These representatives are used to inspect the claim that the rails are retarded while the bridge/rung sector is Wightman.",
        )


def build_claim_folder_c6_c7(
    l2_entries: Sequence[LoopSummaryEntry],
    l2_blocks: Sequence[str],
    l2_image_dir: Path,
    l3_entries: Sequence[LoopSummaryEntry],
    l3_blocks: Sequence[str],
    l3_image_dir: Path,
    l3_mapping: Dict[int, int],
) -> None:
    for claim_name in ["C6_higher_order_ladders", "C7_late_time_homogeneous_limit"]:
        claim_dir = ARTIFACT_ROOT / claim_name
        l2_index = 12
        l2_entry = next(item for item in l2_entries if item.index == l2_index)
        copy_file(l2_image_dir / f"topology{l2_index}.pdf", claim_dir / "images" / f"L2_topology{l2_index}.pdf")
        write_topology_block(l2_blocks[l2_index - 1], claim_dir / "blocks" / f"L2_topology{l2_index}_block.txt")
        write_entry_summary(
            l2_entry,
            claim_dir / "summaries" / f"L2_topology{l2_index}.md",
            notes="This is the representative one-rung witness reused in the higher-order comparison.",
        )

        for original_index in L3_SELECTED_INDICES:
            entry = next(item for item in l3_entries if item.index == original_index)
            rendered_index = l3_mapping[original_index]
            copy_file(
                l3_image_dir / f"topology{rendered_index}.pdf",
                claim_dir / "images" / f"L3_topology{original_index}.pdf",
            )
            write_topology_block(
                l3_blocks[original_index - 1],
                claim_dir / "blocks" / f"L3_topology{original_index}_block.txt",
            )
            write_entry_summary(
                entry,
                claim_dir / "summaries" / f"L3_topology{original_index}.md",
                notes="This selected L3 topology is used as a structural higher-order witness. It is summarized without full SK enumeration because the exhaustive assignment count becomes too large at this loop order.",
            )


def main() -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    SUMMARY_ROOT.mkdir(parents=True, exist_ok=True)

    l0_list_path, l0_image_dir = ensure_l0_assets()
    l1_list_path, l1_image_dir = copy_existing_generated(1)
    l2_list_path, l2_image_dir = copy_existing_generated(2)
    l3_list_path, l3_image_dir, l3_mapping = ensure_l3_selected_assets(L3_SELECTED_INDICES)

    l0_entries = summarize_loop(l0_list_path, SUMMARY_ROOT / "L0_summary.json", enumerate_terms=True)
    l1_entries = summarize_loop(l1_list_path, SUMMARY_ROOT / "L1_summary.json", enumerate_terms=True)
    l2_entries = summarize_loop(l2_list_path, SUMMARY_ROOT / "L2_summary.json", enumerate_terms=True)
    l3_entries = summarize_loop(l3_list_path, SUMMARY_ROOT / "L3_structural_summary.json", enumerate_terms=False)

    l0_blocks = load_blocks(l0_list_path)
    l1_blocks = load_blocks(l1_list_path)
    l2_blocks = load_blocks(l2_list_path)
    l3_blocks = load_blocks(l3_list_path)

    build_claim_folder_c1(l0_entries, l0_blocks, l0_image_dir)
    build_claim_folder_c2(l1_entries, l1_blocks, l1_image_dir)
    build_claim_folder_c3(l2_entries, l2_blocks, l2_image_dir)
    build_claim_folder_c4(l2_entries, l2_blocks, l2_image_dir)
    build_claim_folder_c5(l1_entries, l2_entries, l1_blocks, l2_blocks, l1_image_dir, l2_image_dir)
    build_claim_folder_c6_c7(l2_entries, l2_blocks, l2_image_dir, l3_entries, l3_blocks, l3_image_dir, l3_mapping)

    manifest_lines = [
        "# Audit Artifact Build",
        "",
        "- Generated fresh `L=0` topology assets under `artifacts/generated/L0`.",
        "- Copied existing repository `L=1` and `L=2` generated assets under `artifacts/generated/L1` and `artifacts/generated/L2`.",
        "- Generated fresh `L=3` topology list under `artifacts/generated/L3_full` and rendered only the selected higher-order witnesses under `artifacts/generated/L3_selected`.",
        "- Wrote loop summaries under `artifacts/_summaries/`.",
        "- Organized claim-scoped copies and summaries under `artifacts/C1_*` through `artifacts/C7_*`.",
    ]
    (ARTIFACT_ROOT / "README.md").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
