 # Use contour_ra_translation.txt as the SK Propagator Rule

  ## Summary

  Keep scripts/calc_commutator_contrib.py in the r/a basis and make
  contour_ra_translation.txt the authoritative translation table for all two-point
  functions. The script should no longer treat G^{IJ}_{\ell_1\ell_2} as a passive label;
  it should immediately rewrite each propagator using your stated rules for diagonal and
  off-diagonal contour blocks, with contour (2) later than contour (1) and fixed external
  insertion
  [
  \langle \phi_r^{1}(x,t)\phi_a^{1}(0)\phi_r^{2}(x,t)\phi_a^{2}(0)\rangle .
  ]

  ## Implementation Changes

  - Add a translation layer in scripts/calc_commutator_contrib.py that maps every
    symbolic propagator
    [
    G^{IJ}_{\ell_1\ell_2}(x,y)
    ]
    to one of:
      - 1/2 (G^> + G^<) for rr on the same contour,
      - G_R for same-contour ra,
      - G_A for same-contour ar,
      - 0 for same-contour aa,
      - G^< for cross-contour 12, rr,
      - G^> for cross-contour 21, rr,
      - 0 for every cross-contour propagator with at least one a endpoint.
  - Treat contour_ra_translation.txt as the source of truth for these identities:
      - ideally load or encode the table directly from that file’s content,
      - keep the assumption “contour 2 is later than contour 1” explicit in the code and
        in the report text.
  - Preserve the current vertex enumeration and odd-a SK vertex weights:
      - 3a + 1r -> 1,
      - 1a + 3r -> 4,
      - all other vertex assignments vanish.
  - Change aggregation so equivalent translated terms combine after the propagator
    rewrite:
      - terms differing only by raw G^{IJ}_{\ell_1\ell_2} labels but translating to the
        same G_R, G_A, G^>, G^<, or Keldysh factor should be summed together,
      - zero propagators should eliminate the whole assignment before it reaches the
        final report.
  - Keep explicit endpoint coordinates as they are now:
      - external endpoints remain x_1, x_2, x_3, x_4,
      - internal vertices remain z_1, z_2, ...,
      - no conversion to branch fields phi_1, phi_2 in the calculation pipeline.
  - Extend coverage from the current single input topology to all fixed-OTOC 2 -> 2
    diagrams the workflow feeds into this script:
      - fixed external ordering only for v1,
      - no external-permutation support unless added later as a separate parameter.

  ## Output Behavior

  - The report should show translated physical correlators, not raw G^{IJ}_{\ell_1\ell_2}
    tokens.
  - Use a consistent notation block near the top:
      - G_K := 1/2 (G^> + G^<) if you want a shorthand for same-contour rr,
      - G_R, G_A, G^>, G^<,
      - explicit statement that all mixed-contour correlators with any a endpoint vanish.
  - Keep enough structure in the output to inspect which topologies survive and which
    vanish because of contour/r,a cancellations. This is the basis for later checking
    whether ladder diagrams dominate; that dominance is not hard-coded in this step.

  ## Test Plan

  - Unit-test the translation table against the contents of contour_ra_translation.txt:
      - same-contour rr/ra/ar/aa,
      - cross-contour 12 and 21,
      - all mixed-contour entries involving a vanish.
  - Regression-test the fixed example in loop_data.txt:
      - the script still parses the topology,
      - translated output contains only the allowed physical correlators,
      - assignments with forbidden mixed-contour a endpoints drop out.
  - Add consistency tests that specific identities you called out hold in practice:
      - expressions equivalent to ⟨phi_x^{2}(z') phi_a^{1}(z)⟩ vanish,
      - same-contour ra and ar produce G_R and G_A respectively.
  - Run coverage over all targeted fixed-OTOC 2 -> 2 diagrams and confirm:
   - every topology is processed,
      - cancellations happen through the translation table,
      - no surviving term contains untranslated G^{IJ}_{\ell_1\ell_2} objects.

  ## Assumptions And Defaults

  - Fixed correlator is ⟨phi_r^{1}(x,t)\phi_a^{1}(0)\phi_r^{2}(x,t)\phi_a^{2}(0)⟩.
  - Contour (2) is later than contour (1).
  - contour_ra_translation.txt is authoritative if it disagrees with older comments/
    scripts in the repo.
  - This step ends at a correct translated symbolic expression; late-time asymptotics and
    an automated “ladders dominate” analysis remain a later phase.


