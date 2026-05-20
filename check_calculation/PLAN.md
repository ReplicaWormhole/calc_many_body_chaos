# Manual Claim-By-Claim Audit of `source/weak.tex`

## Summary
The audit will be manual in judgment and report-writing, with tooling used only to generate evidence. The workflow is:

1. Extract and freeze a list of mechanically checkable claims from the core derivation in `source/weak.tex`.
2. For each claim, generate the specific symbolic/topological artifacts needed to test it.
3. Inspect those artifacts manually and write the comparison in `check_calculation/report.tex`.
4. If an artifact appears not to support the claim, do a second-pass diagnosis before assigning a verdict:
   - check whether the symbolic-generation pipeline may be wrong
   - check whether the paper statement is using an implicit assumption, approximation, or projection
   - distinguish genuine mismatch from "claim only holds after later reduction"

The report is therefore not an auto-checker output. It is a hand-curated ledger backed by generated evidence stored in `check_calculation/`.

## Workflow And Outputs
- `check_calculation/claim_list.md`
  - Hand-curated list of mechanically checkable claims from the core derivation.
  - Each claim gets:
    - claim id
    - source section / equation reference
    - exact or near-exact statement from the paper
    - what evidence is needed to test it
    - dependency notes if the claim relies on an earlier approximation
- `check_calculation/artifacts/`
  - Evidence grouped by claim id, not just by loop order.
  - Each claim folder contains only the artifacts actually needed for that claim:
    - topology images
    - raw symbolic term listings
    - selected summaries of surviving SK assignments
    - any hand-written inspection notes
- `check_calculation/report.tex`
  - Written after inspection, not generated as a blind dump.
  - One subsection per claim with:
    - paper claim
    - artifact list
    - manual comparison
    - verdict: `match / partial / mismatch / unresolved`
    - if not `match`, a short diagnosis:
      - generator issue suspected
      - paper used implicit assumption
      - claim only holds after an omitted later step
      - ambiguity in wording

## Scope Of The Audit
Audit only the core derivation up to the homogeneous ladder equation, stopping before pinching/on-shell reduction.

Claims to include:
- free-theory contraction structure
- order-`\lambda` self-energy claim and retarded-rail claim
- order-`\lambda^2` split between same-fold self-energy dressings and opposite-fold one-rung contributions
- one-rung combinatoric factor and index-counting claim
- propagator-type claim: rails retarded, rungs Wightman
- emergence of the ladder family through higher orders
- justification for passing from the inhomogeneous recursion to the homogeneous ladder equation at late time

Claims to exclude in this pass:
- pinching replacements
- on-shell delta reduction
- one-dimensional kernel reduction
- numerical `\lambda_L` extraction and quoted constants

## Implementation Approach
- The tooling layer is only for evidence generation.
  - Reuse existing topology/SK scripts to generate `L=0..3` evidence.
  - Organize outputs by claim so the report can cite specific artifacts cleanly.
- The claim list is prepared first, before final report writing.
  - This forces the audit to be explicit about what is actually being checked.
- For each claim, decide the minimum witness set before generating anything.
  - Example:
    - free-theory claim: only `L=0` artifacts
    - one-rung structure claim: targeted `L=2` artifacts
    - ladder persistence claim: selected `L=2` and `L=3` representatives
- The report text is written only after inspecting artifacts.
  - No automatic verdict assignment.
  - Generated summaries may be quoted or included, but the narrative comparison is manual.
- Mismatch handling is mandatory.
  - If evidence does not align with the paper, the audit must not stop at "mismatch."
  - It must check:
    - whether the symbolic translator/classifier may be wrong
    - whether a contour sum, projection, or late-time approximation was assumed in the paper but not yet applied in the artifact
    - whether the paper's statement is shorthand for a restricted class of terms

## Test And Acceptance Criteria
- `claim_list.md` exists before `report.tex` is finalized.
- Every claim listed in `claim_list.md` has:
  - at least one linked artifact set
  - a written manual comparison in `report.tex`
  - a verdict
- No verdict is produced solely from raw script output without written inspection.
- Every `partial`, `mismatch`, or `unresolved` verdict includes a diagnosis note.
- The report clearly separates:
  - what is directly supported by generated evidence
  - what is inferred using the paper's stated approximations
  - what remains outside this pass

## Assumptions And Defaults
- The audit remains symbolic only.
- Loop evidence goes through `L=3`.
- "Ladder diagrams dominate" will be treated cautiously:
  - supported mechanically through explicit low-order evidence
  - then discussed as a structural extrapolation used by the paper
  - not overstated as a brute-force all-orders proof
- Existing scripts are allowed to help generate evidence, but the final report is a manual audit document, not an auto-generated certification.
