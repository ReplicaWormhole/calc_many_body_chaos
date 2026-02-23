(* File header comment start. *)
(*
(* File name marker. *)
  Phi4MatrixSK.mod
(* Short description of the model. *)
    Minimal phi^4 matrix model with SK r/a basis and two timefolds
(* File header comment end. *)
*)

(* Declare the FeynArts model name. *)
M$ModelName = "Phi4MatrixSK";

(* Matrix color indices.
   Note: Nc is kept symbolic; set Nc explicitly before loading
   the model if you need explicit index expansion. *)
If[!ValueQ[Nc], Nc = 3];
IndexRange[ Index[Colour] ] = NoUnfold[Range[Nc]];
IndexRange[ Index[Colour2] ] = NoUnfold[Range[Nc]];

(* Two timefolds (contours). *)
IndexRange[ Index[Contour] ] = NoUnfold[{1, 2}];

(* r/a basis indices. Use a 3+ char type name to avoid StringTake issues. *)
IndexRange[ Index[RAx] ] = NoUnfold[{r, a}];

(* Field classes. *)
M$ClassesDescription = {
  S[1] == {
    SelfConjugate -> True,
    Indices -> {Index[Colour], Index[Colour2], Index[Contour], Index[RAx]},
    Mass -> mphi,
    PropagatorLabel -> "phi",
    PropagatorType -> ScalarDash,
    PropagatorArrow -> None
  }
};

(***
  Interaction: S_int = S_1 - S_2 with
    phi_1 = phi_r + (1/2) phi_a
    phi_2 = phi_r - (1/2) phi_a
  This yields: phi_1^4 - phi_2^4 = 4 phi_r^3 phi_a + phi_r phi_a^3
  So only odd-a vertices appear:
    3r + 1a -> coefficient 4
    1r + 3a -> coefficient 1
***)

M$CouplingMatrices = {
  C[
    S[1, {a1, b1, c1, ra1}],
    S[1, {a2, b2, c2, ra2}],
    S[1, {a3, b3, c3, ra3}],
    S[1, {a4, b4, c4, ra4}]
  ] ==
    -I*g2 * {{
      IndexDelta[b1, a2] * IndexDelta[b2, a3] * IndexDelta[b3, a4] * IndexDelta[b4, a1] *
      IndexDelta[c1, c2] * IndexDelta[c2, c3] * IndexDelta[c3, c4] *
      VRA[ra1, ra2, ra3, ra4]
    }}
};

M$LastModelRules = {
  VRA[ra1_, ra2_, ra3_, ra4_] :>
    Module[{nA = Count[{ra1, ra2, ra3, ra4}, a]},
      Which[
        nA == 1, 4,
        nA == 3, 1,
        True, 0
      ]
    ]
};
