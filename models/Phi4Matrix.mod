(*
  Phi4Matrix.mod
    Minimal phi^4 matrix model for FeynArts
*)

M$ModelName = "Phi4Matrix";

(* Color indices for matrix-valued scalar *)
If[!ValueQ[Nc], Nc = 3];
IndexRange[ Index[Colour] ] = NoUnfold[Range[Nc]];
IndexRange[ Index[Colour2] ] = NoUnfold[Range[Nc]];

(* Timefold (1,2) and r/a indices for SK contour bookkeeping *)
IndexRange[ Index[Time] ] = NoUnfold[{1, 2}];
IndexRange[ Index[RA] ] = NoUnfold[{r, a}];

M$ClassesDescription = {
  S[1] == {
    SelfConjugate -> True,
    Indices -> {Index[Colour], Index[Colour2], Index[Time], Index[RA]},
    Mass -> mphi,
    PropagatorLabel -> "phi",
    PropagatorType -> ScalarDash,
    PropagatorArrow -> None
  }
};

(*
  L_int = - g^2 Tr(Phi^4)
  Trace contraction: Phi_{a1 b1} Phi_{a2 b2} Phi_{a3 b3} Phi_{a4 b4}
  with deltas: b1=a2, b2=a3, b3=a4, b4=a1
*)
M$CouplingMatrices = {
  C[
    S[1, {a1_, b1_, i1_, l1_}],
    S[1, {a2_, b2_, i2_, l2_}],
    S[1, {a3_, b3_, i3_, l3_}],
    S[1, {a4_, b4_, i4_, l4_}]
  ] ==
    -I*g2 * {{
      IndexDelta[b1, a2] * IndexDelta[b2, a3] * IndexDelta[b3, a4] * IndexDelta[b4, a1] *
      SKV[i1, i2, i3, i4, l1, l2, l3, l4]
    }}
};

M$LastModelRules = {};
