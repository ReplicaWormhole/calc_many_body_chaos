(*
  Phi4.mod
    Minimal phi^4 theory model for FeynArts
*)

M$ModelName = "Phi4";

M$ClassesDescription = {
  S[1] == {
    SelfConjugate -> True,
    Mass -> mphi,
    PropagatorLabel -> "phi",
    PropagatorType -> ScalarDash,
    PropagatorArrow -> None
  }
};

M$CouplingMatrices = {
  C[ S[1], S[1], S[1], S[1] ] == -I*lam * {{1}}
};

M$LastModelRules = {};
