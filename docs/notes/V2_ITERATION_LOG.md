# V2 Iteration Log

## Iteration 1 - 2026-03-11
- Problem:
  The existing project assigns external operators by propagator appearance order and has no canonical graph representation, so harmless reordering of the same `Topology[...]` text can change downstream interpretation.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v2_core.py'`
  initially failed because `scripts/calc_commutator_contrib_v2_core.py` did not exist.
- Approach:
  Start with a minimal v2 core that only solves the graph-invariance foundation: parse topologies, map external legs by `Vertex[1][1..4]`, and compute canonical signatures/coordinate names independent of propagator order.
- Changes made:
  Added [`tests/test_calc_commutator_contrib_v2_core.py`](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib_v2_core.py) with label-based mapping and reorder-invariance tests.
  Added [`scripts/calc_commutator_contrib_v2_core.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_v2_core.py) with canonical parsing, external-label mapping, canonical coordinate naming, and canonical topology signatures.
- Why this fixes the problem:
  The v2 core no longer depends on the parser encounter order to identify external operators or internal coordinates. The canonical signature and coordinate map are derived from vertex identity, which is stable under propagator reordering.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v2_core.py'`
  Result: `OK (2 tests)`.
- Remaining risk:
  Coefficient and `N_c` reconstruction are still unresolved; this iteration only establishes graph-invariant topology handling.

## Iteration 2 - 2026-03-11
- Problem:
  The project still had no explicit, testable mapping from the real `L=1` topology list to the paper’s two order-`lambda^2` sectors. Without that, “match the paper” remained qualitative.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v2_core.py'`
  failed with missing `classify_l1_topology` and `summarize_l1_paper_sectors`.
- Approach:
  Classify the seven `all_L_1.txt` topologies structurally using canonical internal-edge patterns:
  two bridges and no self-loop means one-rung;
  one bridge plus one self-loop means self-energy.
- Changes made:
  Extended [`tests/test_calc_commutator_contrib_v2_core.py`](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib_v2_core.py) with sector-classification and paper-factor expectations.
  Extended [`scripts/calc_commutator_contrib_v2_core.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_v2_core.py) with `classify_l1_topology()` and `summarize_l1_paper_sectors()`.
- Why this fixes the problem:
  The `L=1` order-`lambda^2` content is now represented in a deterministic way: topologies `3, 5, 6` are the three one-rung index structures and therefore sum to the paper’s total factor `48 = 3 * 16`, while `1, 2, 4, 7` are self-energy type.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v2_core.py'`
  Result: `OK (4 tests)`.
- Remaining risk:
  This iteration establishes the exact structural split and one-rung total factor, but the dynamic v2 report and Wolfram-backed export path still need to consume and surface it.

## Iteration 3 - 2026-03-11
- Problem:
  The new canonical core existed only as library helpers. There was still no user-facing v2 script that turned a topology list into a report emphasizing label-based assignment and the paper-matching `L=1` summary.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v2.py'`
  initially failed because `scripts/calc_commutator_contrib_v2.py` did not exist.
- Approach:
  Add a thin CLI/report layer over the v2 core instead of duplicating logic. The report should surface the canonical sector split and exact one-rung factor without reintroducing order-dependent behavior.
- Changes made:
  Added [`tests/test_calc_commutator_contrib_v2.py`](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib_v2.py).
  Added [`scripts/calc_commutator_contrib_v2.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_v2.py) with `build_summary()`, `write_report()`, CLI parsing, and file-based execution.
- Why this fixes the problem:
  There is now a stable v2 entrypoint that reports the canonical `L=1` paper-sector split, explicitly states that external assignment is driven by external vertex labels, and surfaces the exact one-rung total factor `48`.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v2.py'`
  Result: `OK (2 tests)`.
- Remaining risk:
  The report currently summarizes topology structure and paper-sector factors, but it does not yet run the dynamic generation path or export amplitude-backed metadata from Wolfram.

## Iteration 4 - 2026-03-11
- Problem:
  V2 still lacked a dynamic entrypoint. The only working dynamic path in the repo still routed through the old appearance-order report logic.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_dynamic_v2.py'`
  initially failed because `scripts/calc_commutator_contrib_dynamic_v2.py` did not exist.
- Approach:
  Reuse the existing working topology-generation flow and switch only the reporting layer to v2. This keeps the proven `WolframKernel`/image-generation path while surfacing canonical v2 summaries.
- Changes made:
  Added [`tests/test_calc_commutator_contrib_dynamic_v2.py`](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib_dynamic_v2.py).
  Added [`scripts/calc_commutator_contrib_dynamic_v2.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_dynamic_v2.py) with Wolfram resolution, generation, image-path handling, and v2 report writing.
- Why this fixes the problem:
  The repo now has a parallel dynamic v2 path that preserves the working headless generation flow but no longer describes results in terms of external-propagator appearance order.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_dynamic_v2.py'`
  Result: `OK (2 tests)`.
- Remaining risk:
  The dynamic v2 report currently consumes canonical topology summaries. It still needs a dedicated amplitude-export artifact to make the coefficient side explicit rather than inferred from the known `L=1` sector structure.

## Iteration 5 - 2026-03-11
- Problem:
  The exact `L=1` paper metadata existed only inside Python logic. There was no dedicated Wolfram artifact showing that the FeynArts amplitude stage ran and exported paper-facing metadata.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_export_paper_l1_metadata_v2.py'`
  initially failed because the output JSON file was not produced.
- Approach:
  Add a narrow Wolfram export focused on the paper’s `L=1` sector. The script should run `CreateTopologies`, `InsertFields`, and `CreateFeynAmp`, then export a compact JSON payload with amplitude count and paper-sector metadata.
- Changes made:
  Added [`tests/test_export_paper_l1_metadata_v2.py`](/home/lev/Projects/calc_mbcwc/tests/test_export_paper_l1_metadata_v2.py).
  Added [`scripts/export_paper_l1_metadata_v2.wls`](/home/lev/Projects/calc_mbcwc/scripts/export_paper_l1_metadata_v2.wls).
- Why this fixes the problem:
  V2 now has a machine-readable Wolfram artifact for the paper’s `L=1` calculation sector. The export proves that the amplitude stage runs in the current environment and makes the exact one-rung total factor available to the Python/report layer.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_export_paper_l1_metadata_v2.py'`
  Result: `OK (1 test)`.
- Remaining risk:
  The export is intentionally narrow and paper-focused. It does not yet attempt a full generic coefficient reconstruction for every loop order.

## Iteration 6 - 2026-03-11
- Problem:
  The review identified a real metadata bug in `check_calculation/scripts/build_claim_artifacts.py`: non-enumerated quartic summaries used `2 * V + 4` internal half-edges instead of `4 * V`.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_build_claim_artifacts.py'`
  failed with `10 != 12` for a three-vertex quartic topology.
- Approach:
  Add a direct regression test on `summarize_block(..., enumerate_terms=False)` and fix only the broken formula.
- Changes made:
  Added [`tests/test_build_claim_artifacts.py`](/home/lev/Projects/calc_mbcwc/tests/test_build_claim_artifacts.py).
  Updated [`check_calculation/scripts/build_claim_artifacts.py`](/home/lev/Projects/calc_mbcwc/check_calculation/scripts/build_claim_artifacts.py) to use `4 * len(internal_vertices)`.
- Why this fixes the problem:
  The non-enumerated audit path now reports the same internal half-edge count implied by the base quartic enumerator, so `L=3` structural summaries no longer undercount the combinatorial size.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_build_claim_artifacts.py'`
  Result: `OK (1 test)`.
- Remaining risk:
  This fixes the specific audit metadata inconsistency; it does not change the broader distinction between structural summaries and full amplitude reconstruction.

## Iteration 7 - 2026-03-11
- Problem:
  The dynamic v2 report still treated amplitude metadata as a sidecar and also missed the required `.ps` to `.pdf` conversion, which would break end-to-end runs.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_dynamic_v2.py'`
  first failed because `write_latex_report()` had no `amplitude_metadata` support, and then failed because `convert_ps_images_to_pdf()` was missing.
- Approach:
  Integrate the new `L=1` Wolfram metadata export into the dynamic v2 path and restore the proven `ps2pdf` conversion step from the earlier dynamic pipeline.
- Changes made:
  Updated [`tests/test_calc_commutator_contrib_dynamic_v2.py`](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib_dynamic_v2.py) to require amplitude metadata in the report and to lock the `ps2pdf` conversion behavior.
  Updated [`scripts/calc_commutator_contrib_dynamic_v2.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_dynamic_v2.py) to:
  run the `L=1` metadata export,
  include amplitude-stage metadata in the report,
  and convert generated `.ps` images to `.pdf`.
- Why this fixes the problem:
  The dynamic v2 path now runs cleanly end-to-end with the same headless image strategy as v1, and the resulting report explicitly shows both the canonical topology summary and the amplitude-stage `L=1` metadata.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_dynamic_v2.py'`
  Result: `OK (3 tests)`.
- Remaining risk:
  The amplitude integration is explicit for `L=1`. Higher-loop coefficient reconstruction is still structural/classificatory rather than fully amplitude-derived.

## Iteration 8 - 2026-03-11
- Problem:
  After several v2 additions, the repo needed a full regression pass and a real generated-artifact check, not only isolated unit tests.
- Failing test added:
  No new test file; this iteration is the verification and artifact pass required to validate the accumulated changes.
- Approach:
  Run the full Python suite, run the new static v2 report path, run the dynamic `L=1` v2 pipeline end to end, and confirm the expected outputs exist on disk.
- Changes made:
  No code changes. This iteration records the full verification pass and generated outputs.
- Why this fixes the problem:
  It confirms the new v2 surface is not only unit-test complete but also operational in the current environment with real generated topology artifacts.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_*.py'` -> `OK (24 tests)`.
  `python3 scripts/calc_commutator_contrib_v2.py --input all_L_1.txt --output output/commutator_contrib_v2_L1.tex` -> completed.
  `python3 scripts/calc_commutator_contrib_dynamic_v2.py -L 1 --generated-dir output/generated/v2_L1 --output output/commutator_contrib_dynamic_v2_L1.tex` -> completed.
  Verified generated files include `output/commutator_contrib_v2_L1.tex`, `output/commutator_contrib_dynamic_v2_L1.tex`, `output/generated/v2_L1/all_L_1.txt`, `output/generated/v2_L1/images/topology1.pdf` ... `topology7.pdf`, and `output/generated/v2_L1/paper_l1_metadata.json`.
- Remaining risk:
  The implemented “full match” is exact and explicit for the paper’s `L=1` sector. General higher-loop coefficient matching is not yet promoted to the same amplitude-derived status.
