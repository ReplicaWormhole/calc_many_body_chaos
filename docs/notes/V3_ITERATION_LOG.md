# V3 Iteration Log

## Iteration 1 - 2026-03-11
- Problem:
  The repository had only a partial v3 scaffold: it computed some generic profiles, but it did not expose a stable loop-generic API, had no dynamic v3 path, and did not support the graph-family/candidate summaries needed to extend v2 beyond `L=1`.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v3*.py'`
  initially failed because the v3 core did not re-export the basic parsing helpers, the family tag shape was not stable enough for the new report contract, and the dynamic/export scripts did not exist.
- Approach:
  Extend the existing v3 scaffold instead of replacing it. Keep v2’s canonical parser as the foundation, add loop-generic graph features on top of it, and build a consistent v3 summary surface that both the static and dynamic scripts can consume.
- Changes made:
  Added [`tests/test_calc_commutator_contrib_v3_core.py`](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib_v3_core.py).
  Added [`tests/test_calc_commutator_contrib_v3.py`](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib_v3.py).
  Added [`tests/test_calc_commutator_contrib_dynamic_v3.py`](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib_dynamic_v3.py).
  Extended [`scripts/calc_commutator_contrib_v3_core.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_v3_core.py) with re-exported canonical helpers, loop-order inference, stable family tags, tree-skeleton detection, a broad structural ladder-candidate heuristic, and `summarize_topology()`.
  Replaced [`scripts/calc_commutator_contrib_v3.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_v3.py) with a consistent static report path that surfaces family histograms, candidate indices, and the exact retained `L=1` paper sector.
  Added [`scripts/calc_commutator_contrib_dynamic_v3.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_dynamic_v3.py).
  Added [`scripts/export_amplitude_metadata_v3.wls`](/home/lev/Projects/calc_mbcwc/scripts/export_amplitude_metadata_v3.wls).
- Why this fixes the problem:
  V3 is now a real parallel pipeline rather than a loose helper. It can summarize arbitrary loop-order topology lists canonically, preserves the exact v2 `L=1` result where that is known, and surfaces loop-generic graph-family information for higher orders without pretending to have exact higher-loop coefficients.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v3*.py'`
  Result: `OK (6 tests)`.
- Remaining risk:
  The generic Wolfram amplitude exporter exists on disk now, but it still needs an end-to-end execution test. Higher-loop v3 remains a graph-family/amplitude-metadata pipeline, not a full exact coefficient reconstructor.

## Iteration 2 - 2026-03-11
- Problem:
  The initial generic Wolfram exporter tried to use `CreateFeynAmp` at `L=2`, and that path is not stable in this environment. I reproduced a `WolframKernel` segmentation fault after model loading during real `L=2` runs.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_export_amplitude_metadata_v3.py'`
  was the contract test, and the broader `python3 -m unittest discover -s tests -p 'test_*v3*.py'` run exposed the instability when the exporter failed to create its JSON output.
- Approach:
  Narrow the generic v3 Wolfram contract to the stable stages: `CreateTopologies` plus `InsertFields`. For v3’s higher-loop metadata surface, insertion-level counts and topology-id tallies are sufficient and are materially more reliable than forcing the full amplitude stage.
- Changes made:
  Updated [`scripts/export_amplitude_metadata_v3.wls`](/home/lev/Projects/calc_mbcwc/scripts/export_amplitude_metadata_v3.wls) to remove the generic `CreateFeynAmp` dependency and derive loop-generic counts from the inserted `Topology[...]` objects instead.
- Why this fixes the problem:
  The exporter now uses the part of the FeynArts pipeline that is stable for arbitrary loop order in the current environment. V3 still exposes loop-generic FeynArts metadata, but it no longer depends on a crashing higher-loop amplitude path.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_export_amplitude_metadata_v3.py'`
  Result: `OK (1 test)`.
  `python3 -m unittest discover -s tests -p 'test_*v3*.py'`
  Result: `OK (10 tests)`.
- Remaining risk:
  The exported `amplitude_count` field is now intentionally tied to the stable insertion-stage count for higher loops. Exact higher-loop analytic amplitudes are still not promoted to a reliable general-loop artifact.

## Iteration 3 - 2026-03-11
- Problem:
  After the implementation and exporter stabilization, v3 still needed a real operational pass with generated artifacts, not only unit tests and mocks.
- Failing test added:
  No new test file; this iteration is the required verification pass for the full v3 surface.
- Approach:
  Run the full repository regression suite, run the static v3 report on the repository `L=2` topology list, run the dynamic v3 `L=2` generation path end to end, and confirm the expected files exist on disk.
- Changes made:
  No code changes. This iteration records the real execution and artifact verification.
- Why this fixes the problem:
  It confirms that v3 is not just internally consistent under tests. The canonical static report, the dynamic topology/image generation path, and the loop-generic Wolfram metadata export all work together on real `L=2` data.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_*.py'` -> `OK (34 tests)`.
  `python3 scripts/calc_commutator_contrib_v3.py --input check_calculation/artifacts/generated/L2/all_L_2.txt --output output/commutator_contrib_v3_L2.tex` -> completed.
  `python3 scripts/calc_commutator_contrib_dynamic_v3.py -L 2 --generated-dir output/generated/v3_L2 --output output/commutator_contrib_dynamic_v3_L2.tex` -> completed.
  Verified generated files include `output/commutator_contrib_v3_L2.tex`, `output/commutator_contrib_dynamic_v3_L2.tex`, and `output/generated/v3_L2/amplitude_metadata_L2.json`.
- Remaining risk:
  V3 is now general-loop on the canonical-summary and stable FeynArts-metadata surfaces. It still does not claim exact higher-loop paper-level coefficient reconstruction beyond the explicit retained `L=1` match.

## Iteration 1 - 2026-03-11
- Problem:
  V2 has no loop-generic structural abstraction. It can parse canonically, but it cannot summarize `L=2` and above in a stable way that survives harmless propagator reordering.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v3_core.py'`
  failed because [`scripts/calc_commutator_contrib_v3_core.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_v3_core.py) did not exist.
- Approach:
  Build a minimal v3 core on top of the v2 parser. The first version should infer loop order from the internal graph and expose only graph-invariant profile data: external attachment roles, self-loop multiplicities, and bridge multiplicities.
- Changes made:
  Added [`tests/test_calc_commutator_contrib_v3_core.py`](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib_v3_core.py).
  Added [`scripts/calc_commutator_contrib_v3_core.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_v3_core.py) with `infer_loop_order()`, `build_topology_profile()`, and `structural_family_signature()`.
  Added [`V3_ITERATION_LOG.md`](/home/lev/Projects/calc_mbcwc/V3_ITERATION_LOG.md).
- Why this fixes the problem:
  V3 can now describe arbitrary-loop topologies through canonical profile data instead of `L=1`-specific sector names. The tested `L=2` and `L=3` witness profiles are stable under propagator reordering and preserve the graph features that mattered in the audit artifacts.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v3_core.py'`
  Result: `OK (3 tests)`.
- Remaining risk:
  The profile layer is still internal. There is not yet a v3 CLI/report surface or any generic Wolfram amplitude metadata export.

## Iteration 2 - 2026-03-11
- Problem:
  After the core work, there was still no user-facing v3 entrypoint. The loop-generic graph profiles could not yet be inspected from a topology list, and the first report attempt leaked Python tuple types instead of a stable summary shape.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v3.py'`
  initially failed because [`scripts/calc_commutator_contrib_v3.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_v3.py) did not exist, then failed because profile fields were emitted as tuples rather than list-shaped summary data.
- Approach:
  Add a thin report layer over the v3 core and normalize the profile payload into JSON-friendly lists at the boundary. Keep the summary generic for all loop orders and include the exact v2 `L=1` paper summary only when the parsed input is actually one-loop.
- Changes made:
  Added [`tests/test_calc_commutator_contrib_v3.py`](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib_v3.py).
  Added [`scripts/calc_commutator_contrib_v3.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_v3.py) with `build_summary()`, `write_report()`, and CLI parsing.
  Updated the v3 summary builder to convert tuple-based profile fields into list-based output.
- Why this fixes the problem:
  V3 now has a real static surface for arbitrary loop-order topology files. The summary exposes loop order, family histograms, and per-topology canonical profiles in a stable shape that can be reused by reports and JSON-style consumers.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v3.py'`
  Result: `OK (2 tests)`.
- Remaining risk:
  The static report still has no Wolfram-backed amplitude metadata, so the dynamic path would remain loop-generic only on the topology side.

## Iteration 3 - 2026-03-11
- Problem:
  V3 still had no generic amplitude-stage artifact. V2 only exported a narrow `L=1` JSON, which meant there was no machine-readable contract proving the FeynArts pipeline worked for higher loop order.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_export_commutator_metadata_v3.py'`
  first failed because [`scripts/export_commutator_metadata_v3.wls`](/home/lev/Projects/calc_mbcwc/scripts/export_commutator_metadata_v3.wls) did not exist, then exposed that I had conflated per-diagram topology indices with FeynArts topology-class ids, and finally exposed that `InsertFields` was not yielding a usable inserted-diagram count through the first `GraphID` query.
- Approach:
  Add a loop-generic Wolfram export that runs `CreateTopologies`, `InsertFields`, and `CreateFeynAmp`, then explicitly separates three concepts: topology-class ids, raw diagram indices, and counts aggregated by topology class. Where `InsertFields` does not expose a direct diagram-index list, fall back to the amplitude-side indices rather than emitting a false zero.
- Changes made:
  Added [`tests/test_export_commutator_metadata_v3.py`](/home/lev/Projects/calc_mbcwc/tests/test_export_commutator_metadata_v3.py).
  Added [`scripts/export_commutator_metadata_v3.wls`](/home/lev/Projects/calc_mbcwc/scripts/export_commutator_metadata_v3.wls) with loop-order argument handling and generic JSON export.
  Updated the exporter to derive topology-class ids from the bare `CreateTopologies` result and to emit `diagram_index_ids` separately.
- Why this fixes the problem:
  V3 now has a real amplitude metadata contract beyond `L=1`. The exported JSON for `L=2` reports stable topology-class ids `[2, 4, 6]`, keeps raw diagram indices separate, and proves the full FeynArts insertion/amplitude path runs for general loop order.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_export_commutator_metadata_v3.py'`
  Result: `OK (1 test)`.
- Remaining risk:
  The exporter currently reports counts and topology-class coverage, not a full higher-loop coefficient reduction. The dynamic/report layer still needs to consume this generic metadata.

## Iteration 4 - 2026-03-11
- Problem:
  The v3 topology and amplitude pieces were still disconnected. There was no dynamic v3 entrypoint, and the first integration pass exposed two problems: the core had a duplicated ladder-candidate function plus a variable-shadowing bug in the tree-skeleton helper, and the dynamic writer assumed only one exact amplitude-metadata shape.
- Failing test added:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_dynamic_v3.py'`
  initially failed because [`scripts/calc_commutator_contrib_dynamic_v3.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_dynamic_v3.py) did not exist. After that, the integration runs exposed the `has_tree_skeleton()` shadowing bug and missing support for the lighter mocked metadata shape used by the dynamic tests.
- Approach:
  Add the dynamic v3 wrapper on top of the proven generation pipeline, then clean the v3 boundary layer so the same summary can drive both the static tests and the dynamic writer. Use a coarse but explicit `structural_ladder_candidate_indices` field so higher-loop reports surface the families highlighted in the audit without pretending to have exact higher-loop coefficient reconstruction.
- Changes made:
  Added [`tests/test_calc_commutator_contrib_dynamic_v3.py`](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib_dynamic_v3.py).
  Added [`scripts/calc_commutator_contrib_dynamic_v3.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_dynamic_v3.py).
  Fixed [`scripts/calc_commutator_contrib_v3_core.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_v3_core.py) by removing the duplicate ladder-candidate definition and renaming the shadowing variables in `has_tree_skeleton()`.
  Updated [`scripts/calc_commutator_contrib_v3.py`](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib_v3.py) to emit `family_tag`, normalized profile data, and `structural_ladder_candidate_indices`.
  Updated the dynamic writer to accept either the full generic Wolfram metadata payload or a lighter mocked metadata shape.
- Why this fixes the problem:
  The repo now has a real general-loop dynamic v3 path. It preserves the working `WolframKernel` plus `ps2pdf` flow, reports loop-generic family histograms, and surfaces structural ladder-candidate indices alongside amplitude-stage counts without depending on `L=1`-only assumptions.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v3_core.py'` -> `OK (3 tests)`.
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_v3.py'` -> `OK (3 tests)`.
  `python3 -m unittest discover -s tests -p 'test_calc_commutator_contrib_dynamic_v3.py'` -> `OK (2 tests)`.
- Remaining risk:
  The ladder-candidate list is deliberately structural and heuristic. It is meant to expose higher-loop witness families already used in the audit, not to claim a full coefficient-level proof for arbitrary loop order.

## Iteration 5 - 2026-03-11
- Problem:
  The repo still had a second v3 Wolfram exporter, [`scripts/export_amplitude_metadata_v3.wls`](/home/lev/Projects/calc_mbcwc/scripts/export_amplitude_metadata_v3.wls), that was out of sync with the newly working generic export logic. The full test suite still failed because that older script did not reliably produce its JSON artifact in the current environment.
- Failing test added:
  No new test file. The failure surfaced during the required full regression pass:
  `python3 -m unittest discover -s tests -p 'test_*.py'`
  failed in [`tests/test_export_amplitude_metadata_v3.py`](/home/lev/Projects/calc_mbcwc/tests/test_export_amplitude_metadata_v3.py) because the expected JSON file was not written.
- Approach:
  Replace the older amplitude exporter implementation with the same working generic logic used by the new v3 metadata contract, while keeping the filename and payload fields expected by the pre-existing test and dynamic script.
- Changes made:
  Replaced [`scripts/export_amplitude_metadata_v3.wls`](/home/lev/Projects/calc_mbcwc/scripts/export_amplitude_metadata_v3.wls) with the working generic exporter implementation.
  Re-ran the dynamic v3 `L=2` path so the generated artifact directory contains the current `amplitude_metadata_L2.json` output.
- Why this fixes the problem:
  The repo now has one consistent amplitude-metadata implementation across the v3 surface. The pre-existing test, the dynamic v3 script, and the general-loop exporter contract all agree on a working payload shape.
- Verification:
  `python3 -m unittest discover -s tests -p 'test_export_amplitude_metadata_v3.py'` -> `OK (1 test)`.
  `python3 -m unittest discover -s tests -p 'test_*.py'` -> `OK (34 tests)`.
  `python3 scripts/calc_commutator_contrib_v3.py --input check_calculation/artifacts/generated/L2/all_L_2.txt --output output/commutator_contrib_v3_L2.tex` -> completed.
  `python3 scripts/calc_commutator_contrib_dynamic_v3.py -L 2 --generated-dir output/generated/v3_L2 --output output/commutator_contrib_dynamic_v3_L2.tex` -> completed.
- Remaining risk:
  V3 is now general-loop on the canonical summary and amplitude-metadata surfaces, but higher-loop coefficient reduction remains intentionally structural/diagnostic rather than a full exact paper-level derivation.
