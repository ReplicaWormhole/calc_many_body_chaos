(* Phi4Matrix.mod: minimal phi^4 matrix model for FeynArts. *)
M$ModelName = "Phi4Matrix";
(* Indices for matrix-valued scalar. *)
(* Ensure Nc is defined, defaulting to 3. *)
If[!ValueQ[Nc], Nc = 3];
IndexRange[ Index[Colour] ] = NoUnfold[Range[Nc]];
IndexRange[ Index[Colour2] ] = NoUnfold[Range[Nc]];
(* SK contour indices (timefold and r/a). *)
IndexRange[ Index[Time] ] = NoUnfold[{1, 2}];
IndexRange[ Index[RAx] ] = NoUnfold[{r, a}];

(* Field content. *)
M$ClassesDescription = {
  S[1] == {
    SelfConjugate -> True,
    Indices -> {Index[Colour], Index[Colour2], Index[Time], Index[RAx]},
    Mass -> mphi,
    PropagatorLabel -> "phi",
    PropagatorType -> ScalarDash,
    PropagatorArrow -> None
  }
};

(* Interaction:
(*
  L_int = - g^2 Tr(Phi^4)
  Trace contraction: Phi_{a1 b1} Phi_{a2 b2} Phi_{a3 b3} Phi_{a4 b4}
  with deltas: b1=a2, b2=a3, b3=a4, b4=a1
*)
(*
  L_int = - g^2 Tr(Phi^4)
  Trace contraction: Phi_{a1 b1} Phi_{a2 b2} Phi_{a3 b3} Phi_{a4 b4}
  with deltas: b1=a2, b2=a3, b3=a4, b4=a1
*)

(* Couplings. *)
M$CouplingMatrices = {
  C[
    S[1, {a1, b1, i1, l1}],
    S[1, {a2, b2, i2, l2}],
    S[1, {a3, b3, i3, l3}],
    S[1, {a4, b4, i4, l4}]
  ] ==
    -I*g2 * {{
      IndexDelta[b1, a2] * IndexDelta[b2, a3] * IndexDelta[b3, a4] * IndexDelta[b4, a1] *
      SKV[i1, i2, i3, i4, l1, l2, l3, l4]
    }}
};

(* No additional model rules. *)
M$LastModelRules = {};
