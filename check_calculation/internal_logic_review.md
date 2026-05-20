# Internal Logic Review Of The Calculation Pipeline

## Bottom line

The current project does **not** accurately redo the calculation in `source/weak.tex` as a reliable, graph-invariant symbolic derivation.

What it does reasonably well is:

- generate and inspect low-order `2 -> 2` quartic topologies,
- assign SK contour and `r/a` labels,
- expose qualitative structures such as retarded rails and Wightman bridges.

What it does **not** do reliably is:

- compute those structures in a way that is invariant under harmless reordering of the same topology text,
- reconstruct exact large-`N` combinatorics,
- recover amplitude-level coefficients from FeynArts data.

In other words: this is currently a useful **structural classifier**, not a trustworthy **rederivation engine**.

## Findings

### 1. Critical: the result depends on the textual order of propagators, not just the graph

The core pipeline uses propagator appearance order in places where the physics should depend only on the underlying topology.

Relevant code:

- [scripts/calc_commutator_contrib.py](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib.py#L172)
- [scripts/calc_commutator_contrib.py](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib.py#L161)
- [scripts/calc_commutator_contrib.py](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib.py#L238)
- [scripts/calc_commutator_contrib.py](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib.py#L325)

The main problems are:

- `build_external_map()` assigns the four external operators by the **order external propagators appear in the file**, not by external vertex labels `Vertex[1][1]` ... `Vertex[1][4]`.
- `internal_vertices_in_appearance_order()` and `incident_endpoints_by_vertex()` preserve the raw parser order and later use it as if it were physical structure.
- `count_nc_loops()` applies the quartic cyclic trace contraction rule using that incidental order.
- `z_map` in `enumerate_terms()` also depends on the internal-vertex appearance order, so coordinate naming is not representation-invariant.

This is not a theoretical concern; it changes outputs.

Deterministic reproductions I ran:

- Reversing the six propagator records in `all_L_1.txt` entry 1 changes the result from `2` translated terms to `0`, while leaving the same FeynArts topology id.
- For `all_L_1.txt` entry 3, if the same propagators are permuted as `[4, 1, 0, 5, 2, 3]` and the external-leg map is fixed manually by external vertex label, `count_nc_loops()` changes from `0` to `1`.

That second reproduction is important: even after removing the external-leg-order ambiguity, the `N_c` counting still changes under a pure propagator reorder. That points directly at the cyclic-order logic in `count_nc_loops()`.

Impact:

- the reported `N_c` powers are not trustworthy,
- the set of surviving translated terms is not trustworthy,
- any conclusion drawn from exact topology-by-topology output can change if the same graph is serialized differently.

### 2. Critical: the code does not have the data needed to recover exact diagrammatic coefficients

The project uses `CreateTopologies` and then parses bare `Topology[...]` expressions, but it never goes through a Feynman-amplitude stage that would attach symmetry or insertion multiplicities.

Relevant code:

- [scripts/generate_all_loop_topologies.wls](/home/lev/Projects/calc_mbcwc/scripts/generate_all_loop_topologies.wls#L76)
- [scripts/generate_all_loop_topologies.wls](/home/lev/Projects/calc_mbcwc/scripts/generate_all_loop_topologies.wls#L87)
- [scripts/calc_commutator_contrib.py](/home/lev/Projects/calc_mbcwc/scripts/calc_commutator_contrib.py#L345)

What the current pipeline does is:

- enumerate contour assignments,
- apply a local SK vertex weight,
- group terms by translated propagator products.

What it does **not** do is:

- extract a symmetry factor,
- account for insertion multiplicities from `InsertFields`,
- derive a full Feynman amplitude from FeynArts.

This is the architectural reason the audit report could isolate a candidate one-rung sector but could not reconstruct the paper's exact factor `48`.

Impact:

- coefficient-level agreement with `source/weak.tex` is not currently meaningful,
- exact combinatoric statements should not be treated as validated by this pipeline,
- the project can support qualitative structure claims, but not exact prefactor claims.

### 3. Medium: the review tooling reports incorrect metadata at `L=3`

In the artifact builder, the non-enumerated branch estimates use an incorrect formula:

- [check_calculation/scripts/build_claim_artifacts.py](/home/lev/Projects/calc_mbcwc/check_calculation/scripts/build_claim_artifacts.py#L204)

When `enumerate_terms=False`, the code sets

```text
n_internal_half_edges = 2 * len(internal_vertices) + 4
```

For quartic vertices with four external legs, the correct count of internal half-edge labels used by the base enumerator is `4 * V`, not `2 * V + 4`.

Example:

- for `V = 3`, the base enumerator uses `12` internal half-edges,
- the structural-summary path reports `10`.

Impact:

- the `L3_structural_summary.json` metadata is inconsistent with the real enumeration model,
- any report text that reasons from that field is using the wrong combinatorial size.

This does not change the base `enumerate_terms()` result, but it does weaken the accuracy of the audit artifacts.

### 4. Medium: the current tests do not cover the failure modes that matter

I ran the existing suite with:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

All 13 tests pass, but they are mostly smoke tests around:

- the translation table,
- report writing,
- dynamic-path wiring.

Relevant files:

- [tests/test_calc_commutator_contrib.py](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib.py#L18)
- [tests/test_calc_commutator_contrib_dynamic.py](/home/lev/Projects/calc_mbcwc/tests/test_calc_commutator_contrib_dynamic.py#L20)
- [tests/test_generate_all_loop_topologies_script.py](/home/lev/Projects/calc_mbcwc/tests/test_generate_all_loop_topologies_script.py#L9)

What is missing:

- graph-invariance tests under propagator reordering,
- tests that external assignments follow external vertex labels rather than file order,
- tests for `N_c` loop-count invariance,
- tests that would distinguish structural classification from true amplitude reconstruction.

Impact:

- the current green test suite should not be read as evidence that the symbolic derivation logic is correct.

## Assessment against the paper

Against `source/weak.tex`, the implementation is best interpreted as a partial structural probe.

It can support statements like:

- "there exists a planar-enhanced sector at order `lambda^2`",
- "some low-order terms contain retarded rails and Wightman bridges",
- "ladder-like graph families exist at higher loop order".

It cannot currently support statements like:

- "this exact topology output reproduces the paper's large-`N` counting",
- "this exact prefactor matches the paper's rung coefficient",
- "the per-topology terms are canonical outputs of the graph rather than artifacts of parser order".

## Recommended fixes

1. Make external-leg assignment label-based.
   Use the external vertex labels `Vertex[1][1]` ... `Vertex[1][4]` directly instead of external-propagator appearance order.

2. Remove appearance-order dependence from index counting.
   The quartic cyclic contraction pattern must come from explicit vertex-leg data or another canonical graph-level convention, not the parser encounter order.

3. Separate "structural scan" from "amplitude reconstruction".
   If exact coefficients matter, the pipeline needs symmetry/insertion data from a FeynArts amplitude stage, not only `CreateTopologies`.

4. Add invariance tests before trusting new results.
   The first regression tests should permute propagators in a topology block and assert identical external mapping, `N_c` power, and translated term content.

## Practical conclusion

If the question is "is this code faithfully redoing the paper's calculation?", my answer is:

**No.**

If the question is "is this code useful for low-order qualitative topology reconnaissance?", my answer is:

**Yes, but only with that narrower claim.**
