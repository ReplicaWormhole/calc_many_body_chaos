(*
  Generate 1-loop 1->2 topologies in phi^4 and attempt insertions.
  Exports bare topologies as PDF/PNG and reports that insertions vanish.
*)

repoDir = DirectoryName[$InputFileName];
modelDir = FileNameJoin[{repoDir, "..", "models"}];
outputDir = FileNameJoin[{repoDir, "..", "output"}];
If[!DirectoryQ[outputDir], CreateDirectory[outputDir]];

AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];
AppendTo[$Path, "/home/lev/Projects/mathematica/FormCalc"];

Block[{cp = $ContextPath},
  $ContextPath = DeleteCases[$ContextPath, "Global`"];
  Needs["FeynArts`"];
  Needs["FormCalc`"];
  $ContextPath = cp;
];

AppendTo[FeynArts`$ModelPath, modelDir];

Print["Model path: ", modelDir];
Print["Output dir: ", outputDir];

(* 1->2 at 1 loop: bare topologies *)
top12 = CreateTopologies[1, 1 -> 2, ExcludeTopologies -> Tadpoles];

paint12 = Paint[
  top12,
  ColumnsXRows -> 2,
  Numbering -> Simple,
  SheetHeader -> "1->2, 1-loop topologies"
];

Export[FileNameJoin[{outputDir, "phi4_1to2_1loop_topologies.pdf"}], paint12];
Export[FileNameJoin[{outputDir, "phi4_1to2_1loop_topologies.png"}], paint12];

Print["Exported bare 1->2 topologies."];

(* Insert fields in phi^4 (1->2) *)
ins12 = InsertFields[
  top12,
  S[1] -> {S[1], S[1]},
  Model -> "Phi4",
  GenericModel -> "Lorentz",
  InsertionLevel -> {Classes}
];

Print["Inserted 1->2 diagrams: ", Length[ins12]];

If[Length[ins12] > 0,
  amps12 = CreateFeynAmp[ins12, Truncated -> False, PreFactor -> 1];
  calc12 = CalcFeynAmp[amps12];

  (* Attach external propagators to form unamputated correlator *)
  p1 = FourMomentum[External, 1];
  p2 = FourMomentum[External, 2];
  p3 = FourMomentum[External, 3];

  full12 = calc12 *
    PropagatorDenominator[p1, mphi] *
    PropagatorDenominator[p2, mphi] *
    PropagatorDenominator[p3, mphi];

  Print["Full correlator (1->2, symbolic): "];
  Print[full12];
  Put[TraditionalForm[full12], FileNameJoin[{outputDir, "phi4_1to2_full_correlator_trad.m"}]];
  Print["Saved TraditionalForm correlator to output/phi4_1to2_full_correlator_trad.m"];
  Put[full12, FileNameJoin[{outputDir, "phi4_1to2_full_correlator.m"}]];
  Print["Saved correlator to output/phi4_1to2_full_correlator.m"];
,
  Print["No 1->2 diagrams at 1-loop in phi^4 (expected)."]
];

(* 2->2 at 1 loop: bare topologies *)
top22 = CreateTopologies[1, 2 -> 2, ExcludeTopologies -> Tadpoles];

paint22 = Paint[
  top22,
  ColumnsXRows -> 2,
  Numbering -> Simple,
  SheetHeader -> "2->2, 1-loop topologies"
];

Export[FileNameJoin[{outputDir, "phi4_2to2_1loop_topologies.pdf"}], paint22];
Export[FileNameJoin[{outputDir, "phi4_2to2_1loop_topologies.png"}], paint22];

Print["Exported bare 2->2 topologies."];

(* Insert fields in phi^4 (2->2) *)
ins22 = InsertFields[
  top22,
  S[1] -> {S[1], S[1]},
  Model -> "Phi4",
  GenericModel -> "Lorentz",
  InsertionLevel -> {Classes}
];

Print["Inserted 2->2 diagrams: ", Length[ins22]];

If[Length[ins22] > 0,
  amps22 = CreateFeynAmp[ins22, Truncated -> False, PreFactor -> 1];
  calc22 = CalcFeynAmp[amps22];

  (* Attach external propagators to form unamputated correlator *)
  q1 = FourMomentum[External, 1];
  q2 = FourMomentum[External, 2];
  q3 = FourMomentum[External, 3];
  q4 = FourMomentum[External, 4];

  full22 = calc22 *
    PropagatorDenominator[q1, mphi] *
    PropagatorDenominator[q2, mphi] *
    PropagatorDenominator[q3, mphi] *
    PropagatorDenominator[q4, mphi];

  Print["Full correlator (2->2, symbolic): "];
  Print[full22];
  Put[TraditionalForm[full22], FileNameJoin[{outputDir, "phi4_2to2_full_correlator_trad.m"}]];
  Print["Saved TraditionalForm correlator to output/phi4_2to2_full_correlator_trad.m"];
  Put[full22, FileNameJoin[{outputDir, "phi4_2to2_full_correlator.m"}]];
  Print["Saved correlator to output/phi4_2to2_full_correlator.m"];
,
  Print["No 2->2 diagrams at 1-loop in phi^4 (unexpected)."]
];
