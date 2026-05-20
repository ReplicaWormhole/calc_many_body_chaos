# Session Notes

## Current State
- `scripts/calc_commutator_contrib.py` translates contour/`r,a` propagators using `contour_ra_translation.txt`.
- Same-contour propagators map as:
  - `G_rr -> G_K = 1/2 (G^> + G^<)`
  - `G_ra -> G_R`
  - `G_ar -> G_A`
  - `G_aa -> 0`
- Cross-contour propagators map as:
  - `G^{12}_{rr} -> G^<`
  - `G^{21}_{rr} -> G^>`
  - any cross-contour propagator with an `a` endpoint vanishes.

## Added Scripts
- `scripts/calc_commutator_contrib_all_L1.py`
  - reads `all_L_1.txt`
  - computes translated SK contributions for all 7 entries
  - writes one combined TeX/PDF report
  - places `data/topology1.pdf` ... `data/topology7.pdf` above each topology section
- `scripts/generate_all_loop_topologies.wls`
  - generates all `2 -> 2` FeynArts topologies for loop order `L`
  - now supports staged generation:
    - `--list-only` writes only `all_L_<L>.txt`
    - `--images-only` renders topology images from a saved topology list
  - headless image generation currently exports PostScript first
  - writes `all_L_<L>.txt`
  - now accepts:
    - `L`
    - output image dir
    - topology-list output path
- `scripts/calc_commutator_contrib_dynamic.py`
  - Python driver intended to call `WolframKernel`/FeynArts on demand
  - generates topology data on the fly
  - parses generated topology list
  - computes SK contributions
  - writes one combined TeX/PDF report with generated topology images
  - now runs topology generation in two stages:
    - topology-list generation
    - image generation
  - now converts generated `.ps` topology images to `.pdf` on the Python side via `ps2pdf`

## Generated Outputs
- `output/commutator_contrib_translated.tex`
- `output/commutator_contrib_translated.pdf`
- `output/commutator_contrib_all_L1.tex`
- `output/commutator_contrib_all_L1.pdf`
- `check_calculation/internal_logic_review.md`

## Tests Added
- `tests/test_calc_commutator_contrib.py`
- `tests/test_calc_commutator_contrib_all_L1.py`
- `tests/test_generate_all_loop_topologies_script.py`
- `tests/test_calc_commutator_contrib_dynamic.py`

## Verified Commands
- `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib*.py'`
- `python3 -m unittest discover -s tests -p 'test_generate_all_loop_topologies_script.py'`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 scripts/calc_commutator_contrib.py --input loop_data.txt --output output/commutator_contrib_translated.tex`
- `python3 scripts/calc_commutator_contrib_all_L1.py --input all_L_1.txt --output output/commutator_contrib_all_L1.tex`
- `python3 scripts/calc_commutator_contrib_dynamic.py -L 0 --generated-dir /tmp/calc_mbcwc_verify/L0 --output /tmp/calc_mbcwc_verify/commutator_contrib_dynamic_L0.tex`
- `python3 scripts/calc_commutator_contrib_dynamic.py -L 1 --generated-dir /tmp/calc_mbcwc_verify/L1 --output /tmp/calc_mbcwc_verify/commutator_contrib_dynamic_L1.tex`

## Headless Wolfram Findings
- `wolframscript` is not reliable in this environment; `WolframKernel -script` is the working batch path.
- `CreateTopologies[...]` is fast in headless mode.
- `Paint[...]` itself returns a `FeynArtsGraphics[...]` object quickly in headless mode.
- The unstable/slow part is image export in headless mode:
  - `Rasterize[...]` hangs
  - direct headless PDF export was also problematic
  - FeynArts PostScript export (`Export[..., paint, "PS"]`) works reliably
- The main `L=2` slowdown was not raw PostScript export cost; it was FeynArts entering the interactive shape-editor path for unshaped topologies.
  - In headless mode this appeared as `Shape::wait: Starting Java and the topology editor.`
  - The fix was to pass `AutoEdit -> False` to `Paint[...]` in `scripts/generate_all_loop_topologies.wls`, forcing automatic non-interactive shaping instead of launching Java/JLink.
- Because of that, the current batch strategy is:
  - Wolfram generates `all_L_<L>.txt`
  - Wolfram exports topology images as `.ps`
  - Python converts `.ps` to `.pdf` using `ps2pdf`

## Runtime Status
- `L=0` now completes end-to-end in headless mode:
  - topology list generated
  - topology image generated
  - contribution `.tex` written
- `L=1` now completes end-to-end in headless mode:
  - 7 topologies parsed
  - 7 images generated
  - contribution `.tex` written
- `L=2` now completes end-to-end in headless mode.
  - `--images-only` now finishes in about 5.7 seconds for 42 topologies.
  - Full `python3 scripts/calc_commutator_contrib_dynamic.py -L 2 --generated-dir output/generated/L2_verify --output output/commutator_contrib_dynamic_L2_verify.tex` finished in about 22.4 seconds.
  - The generated directory contains `all_L_2.txt` plus 42 `.ps` and 42 converted `.pdf` topology images.

## Important Decisions
- Keep the SK calculation in the `r/a` basis; do not expand the computation pipeline to `phi_1`, `phi_2`.
- Treat `contour_ra_translation.txt` as authoritative.
- For `all_L_1.txt`, image matching is by list order, not by FeynArts `Topology[n]` label.
- The fixed external assignment is:
  - `<phi_r^1(x,t) phi_a^1(0) phi_r^2(x,t) phi_a^2(0)>`

## Internal Logic Review
- Wrote a review at `check_calculation/internal_logic_review.md`.
- Main conclusion: the current implementation is useful for low-order structural inspection, but it is not yet a faithful rederivation of the calculation in `source/weak.tex`.
- Critical issue: `scripts/calc_commutator_contrib.py` is not graph-invariant.
  - External assignment currently depends on external propagator appearance order.
  - `N_c` loop counting also depends on incidental propagator ordering at internal vertices.
  - Reordering the same `Topology[...]` text can change the reported surviving terms and, in some cases, the reported `N_c` power.
- Critical issue: the pipeline does not include symmetry-factor / insertion-multiplicity information from a FeynArts amplitude stage, so exact coefficient claims should not be trusted.
- Medium issue: `check_calculation/scripts/build_claim_artifacts.py` reports incorrect `L=3` internal-half-edge metadata when `enumerate_terms=False`.
- Test status: the full current suite passes, but it does not cover graph-invariance or exact large-`N` counting correctness.

## Current Blocker
- Current blocker: the symbolic pipeline should not be treated as coefficient-accurate until the graph-order dependence is removed.
- The remaining unverified area is not only higher-loop runtime scaling; it is also the correctness of external-leg assignment, `N_c` counting, and coefficient reconstruction.

## Next Step
- First fix the graph-invariance bugs in `scripts/calc_commutator_contrib.py`.
- Add regression tests that permute propagators within the same topology block and require identical external mapping, `N_c` power, and translated terms.
- Only after that should coefficient-level comparisons to the paper be treated as meaningful.
