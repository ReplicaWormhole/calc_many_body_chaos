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
  - exports one PDF per topology
  - writes `all_L_<L>.txt`
  - now accepts:
    - `L`
    - output image dir
    - topology-list output path
- `scripts/calc_commutator_contrib_dynamic.py`
  - Python driver intended to call `wolframscript`/FeynArts on demand
  - generates topology data on the fly
  - parses generated topology list
  - computes SK contributions
  - writes one combined TeX/PDF report with generated topology images

## Generated Outputs
- `output/commutator_contrib_translated.tex`
- `output/commutator_contrib_translated.pdf`
- `output/commutator_contrib_all_L1.tex`
- `output/commutator_contrib_all_L1.pdf`

## Tests Added
- `tests/test_calc_commutator_contrib.py`
- `tests/test_calc_commutator_contrib_all_L1.py`
- `tests/test_generate_all_loop_topologies_script.py`
- `tests/test_calc_commutator_contrib_dynamic.py`

## Verified Commands
- `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib*.py'`
- `python3 -m unittest discover -s tests -p 'test_generate_all_loop_topologies_script.py'`
- `python3 scripts/calc_commutator_contrib.py --input loop_data.txt --output output/commutator_contrib_translated.tex`
- `python3 scripts/calc_commutator_contrib_all_L1.py --input all_L_1.txt --output output/commutator_contrib_all_L1.tex`

## Important Decisions
- Keep the SK calculation in the `r/a` basis; do not expand the computation pipeline to `phi_1`, `phi_2`.
- Treat `contour_ra_translation.txt` as authoritative.
- For `all_L_1.txt`, image matching is by list order, not by FeynArts `Topology[n]` label.
- The fixed external assignment is:
  - `<phi_r^1(x,t) phi_a^1(0) phi_r^2(x,t) phi_a^2(0)>`

## Current Blocker
- The end-to-end runtime test for:
  - `python3 scripts/calc_commutator_contrib_dynamic.py -L 1`
  did not finish cleanly in this environment.
- The long-running process appeared to stall before generated files were written.
- Python-side unit tests passed, but the Wolfram/FeynArts runtime path still needs direct debugging.

## Next Step
- Debug `scripts/calc_commutator_contrib_dynamic.py` by isolating the Wolfram subprocess call:
  - run `scripts/generate_all_loop_topologies.wls` directly with explicit output paths
  - confirm whether the hang is in `wolframscript`, `Paint`, or path/output handling
  - once generation succeeds, rerun the dynamic Python pipeline for `L=1`
