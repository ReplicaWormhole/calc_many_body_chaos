# Plan: Create `calc_correlator_v3.wls` With Delta‑Index Introspection

## Summary
Create a new script `scripts/calc_correlator_v3.wls` (leaving v2 unchanged). It will insert the `Phi4MatrixSK` model into 1‑loop 2→2 topologies with the fixed OTOC external assignment, select the first inserted diagram, and print both the coupling‑level and amplitude‑level `IndexDelta` structures for that diagram.

## Preconditions
- `wolframscript` is available (checked: `WolframScript 1.13.0`).

## Scope
In scope:
- New file `scripts/calc_correlator_v3.wls`.
- Use `Phi4MatrixSK.mod` from `models/`.
- Fixed OTOC external assignment from v2.
- Select the first inserted diagram only.
- Print coupling‑level and amplitude‑level delta index structure.

Out of scope:
- Full OTOC computation `C(t)` from `basic_formulas.tex`.
- Summing over multiple diagrams.
- Refactors or new utilities.

## Implementation Steps (Decision‑Complete)
1. **Create new script** `scripts/calc_correlator_v3.wls` by copying v2 structure and updating:
   - `AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];`
   - `Needs["FeynArts`"];`
   - `$ModelPath` append to include `/home/lev/Projects/calc_mbcwc/models`.

2. **Generate topologies** (same as v2):
   - `tops = CreateTopologies[1, 2 -> 2, Adjacencies -> {4}, ExcludeTopologies -> Tadpoles];`

3. **Insert fields with fixed OTOC external assignment** (same as v2):
   - `{S[1,{a1,b1,1,r}], S[1,{a2,b2,1,a}]} -> {S[1,{a3,b3,2,r}], S[1,{a4,b4,2,a}]}`  
   - `Model -> "Phi4MatrixSK"`, `GenericModel -> "Lorentz"`, `InsertionLevel -> {Classes}`.

4. **Select a single diagram**
   - `diag1 = First@Cases[diags, FeynmanDiagram[__], Infinity];`
   - Print the number of inserted diagrams and confirm selection.

5. **Coupling‑level delta structure**
   - `couplings = Cases[diag1, _C, Infinity];`
   - `couplingDeltas = Cases[couplings, IndexDelta[__], Infinity];`
   - Apply `M$LastModelRules` to evaluate `VRA` for readability.
   - Print `couplings` and `couplingDeltas`.

6. **Amplitude‑level delta structure**
   - `amp1 = CreateFeynAmp[diag1];`
   - `ampDeltas = Cases[amp1, IndexDelta[__], Infinity];`
   - Print a short amplitude summary and `ampDeltas`.

7. **Output formatting**
   - Print clear headers:
     - `"Diagram selection"`, `"Coupling-level IndexDelta"`, `"Amplitude-level IndexDelta"`.

## Public APIs / Interfaces
No public API changes. New script file only.

## Test Cases and Scenarios
1. Run `wolframscript -file scripts/calc_correlator_v3.wls`.
2. Expected:
   - Diagram count printed.
   - Non-empty `IndexDelta[...]` lists from coupling and amplitude views.
   - `VRA` evaluated to numeric coefficients (4 or 1) when applicable.

## Assumptions and Defaults
- The first inserted diagram is an acceptable example for inspection.
- The model’s `IndexDelta` structure is the primary target for display; no index expansion beyond that.
- All file paths (FeynArts install and model path) remain valid.
