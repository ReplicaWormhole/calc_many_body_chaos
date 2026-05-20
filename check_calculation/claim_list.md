# Claim List For Manual Audit Of `source/weak.tex`

This list freezes the mechanically checkable claims for the audit pass described in [PLAN.md](/home/lev/Projects/calc_mbcwc/check_calculation/PLAN.md). The scope stops at the late-time homogeneous ladder equation and excludes pinching/on-shell reduction, one-dimensional kernel reduction, and numerical extraction of `\lambda_L`.

## C1. Free-Theory Contraction Structure
- Source:
  - `\S 2.1` / `Order \lambda^0` (`\label{free}`)
- Paper statement:
  - In the free theory, two of the three contraction patterns cancel in the commutator sum.
  - The only nonvanishing contraction is the one where the two operators on the bottom fold contract with each other and the two operators on the top fold contract with each other.
  - The result is `C_{\text{free}}(t) = -N^{-2}\int d^3\mathbf{x}\, G_R(\mathbf{x},t)^2`.
- Evidence needed:
  - `L=0` topology witness.
  - Explicit surviving SK assignments and translated propagator products.
  - Confirmation that the surviving term reduces to two retarded rails between the external pairs.
- Minimum witness set:
  - One `L=0` topology image.
  - One raw symbolic listing for the `L=0` topology.
- Dependency notes:
  - This checks contour/SK contraction structure, not the final spatial integral.

## C2. Order-`\lambda` Correction Is A Self-Energy Dressing, With Retarded Rail
- Source:
  - `\S 2.2` / `Order \lambda` (`\label{first}`)
  - Fig. `1b`
- Paper statement:
  - Integrating one interaction vertex over the two real-time folds gives the one-loop self-energy correction.
  - The sum over the fold placements and external arrangements turns the horizontal line into a retarded propagator.
- Evidence needed:
  - `L=1` topology witness set.
  - Explicit symbolic terms showing a single internal quartic vertex dressing a rail rather than producing a rung-type bridge.
  - Check that the nonvanishing translated propagators on the rail are retarded/advanced-compatible rather than same-fold Keldysh-only structures.
- Minimum witness set:
  - All `L=1` topology images and symbolic listings, because the claim concerns cancellation across fold placements.
  - Short manual note identifying which `L=1` topologies represent self-energy dressing.
- Dependency notes:
  - This tests the contour sum and propagator translation.
  - It does not test the appendix evaluation of the thermal mass itself.

## C3. Order-`\lambda^2` Splits Into Same-Fold Self-Energy Dressings And Opposite-Fold One-Rung Contributions
- Source:
  - `\S 2.3` / `Order \lambda^2` (`\label{second}`)
  - Fig. `3`
- Paper statement:
  - When both interaction vertices are on the same Lorentzian fold, one gets the next self-energy dressings.
  - When the two vertices are on opposite folds, one gets the qualitatively new one-rung contribution, plus additional self-energy corrections.
- Evidence needed:
  - `L=2` topology witness set.
  - Classification of surviving `L=2` topologies into same-fold self-energy type versus opposite-fold bridge type.
  - Explicit examples from both classes.
- Minimum witness set:
  - Selected `L=2` topology images.
  - Symbolic summaries for all surviving `L=2` topologies, with targeted inspection notes for representative self-energy and one-rung cases.
- Dependency notes:
  - This is a structural classification claim.
  - It does not require the late-time replacement of retarded pairs by on-shell delta functions.

## C4. One-Rung Combinatoric And Index-Counting Factor
- Source:
  - Fig. `5` / `\label{setup4}`
  - Eq. `(\ref{oiuwreoui})`
- Paper statement:
  - The one-rung diagram has three index structures.
  - Each gives `16 N^4`, with `16 = 4 \cdot 4` from rotating each quartic vertex in the plane.
  - After the overall `1/N^4` normalization in `C(t)`, the net factor is `48`.
- Evidence needed:
  - One-rung `L=2` witness topology or topologies.
  - Matrix-index loop counting from the symbolic topology data.
  - Explicit multiplicity accounting from surviving assignments or topology symmetries sufficient to compare with the claimed `48`.
- Minimum witness set:
  - Representative `L=2` one-rung topology images.
  - A dedicated helper-generated summary of index-loop powers and surviving term multiplicities for the one-rung class.
- Dependency notes:
  - This is the most interpretation-heavy finite-order claim.
  - If the symbolic pipeline exposes only part of the paper’s `48`, the report must diagnose whether the missing factor is due to FeynArts topology labeling, external-cap conventions, or an implicit planar-rotation convention in the paper.

## C5. Propagator-Type Claim: Rails Retarded, Rungs Wightman
- Source:
  - `\S 2` overview paragraph in `Section 2`
  - Fig. `3b`
  - Eq. `(\ref{oiuwreoui})` and the definition of `R(p)`
- Paper statement:
  - The contour-side rails in the ladder become retarded propagators after summing over the two sides of each fold.
  - The rung remains a product of Wightman correlators `\tilde{G}\tilde{G}`.
- Evidence needed:
  - `L=1` and `L=2` symbolic terms.
  - Explicit translation of same-fold and cross-fold propagators into `G_R`, `G_A`, `G^<`, `G^>`, and `G_K`.
  - Identification of the bridge subgraph in one-rung topologies as two cross-fold Wightman lines.
- Minimum witness set:
  - One `L=1` self-energy representative.
  - One or more `L=2` one-rung representatives.
  - A short propagator-type summary per representative.
- Dependency notes:
  - This checks the SK/contour translation layer only.
  - It does not test the analytic momentum-space rung integral in Appendix `\ref{rungapp}`.

## C6. Higher Orders Generate The Dressed Ladder Family
- Source:
  - `\S 2.4` / `Higher orders` (`\label{higher}`)
  - Fig. `6`
  - Eq. `(\ref{integrale})`
- Paper statement:
  - At higher orders, the leading diagrams consist of dressed ladders.
  - The ladder sum can be encoded by the recursion for `f(\omega,p)`.
- Evidence needed:
  - Low-order witnesses showing persistence of the ladder pattern beyond the first rung.
  - Selected `L=2` and `L=3` topologies demonstrating repeated rung insertion rather than unrelated leading structures.
  - Manual comparison from finite-order symbolic evidence to the schematic recursion.
- Minimum witness set:
  - Selected `L=2` ladder representatives.
  - Selected `L=3` representatives generated specifically for this audit.
- Dependency notes:
  - This claim can only be supported as low-order structural evidence plus extrapolation.
  - It is not an all-orders brute-force proof.

## C7. Late-Time Passage From The Inhomogeneous Recursion To The Homogeneous Ladder Equation
- Source:
  - Eq. `(\ref{integrale})`
  - Eq. `(\ref{homog})`
  - surrounding paragraph in `\S 2.4`
- Paper statement:
  - The zero-rung term in the inhomogeneous equation can be dropped for the large-time growth problem because the growing part of `f(t,p)` dominates while the inhomogeneous term decays.
  - This yields the homogeneous ladder equation governing growth exponents.
- Evidence needed:
  - Structural comparison between the explicit finite-order ladder recursion and the form of the homogeneous equation.
  - Manual argument separating what is directly visible in the finite-order evidence from what is an asymptotic late-time assumption of the paper.
- Minimum witness set:
  - The same `L=2` and `L=3` ladder witnesses used for `C6`.
  - A short derivation note connecting finite-order rung insertion to the recursive form.
- Dependency notes:
  - This is partly inferential.
  - The report must distinguish direct support from the paper’s late-time approximation.

## Excluded In This Pass
- Pinching replacements `(\ref{replacement})` and `(\ref{replacement2})` as audit targets in their own right.
- On-shell delta reduction and support arguments beyond what is needed to understand the claimed ladder structure.
- Reduction to the one-dimensional kernel and the symmetric discretized equation.
- Numerical diagonalization and quoted constants for `\lambda_L`.
