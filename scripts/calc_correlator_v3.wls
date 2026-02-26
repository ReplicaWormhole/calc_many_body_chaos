AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];
Needs["FeynArts`"];

(* Load FeynArts and add the local model path *)
$ModelPath = Append[$ModelPath, "/home/lev/Projects/calc_mbcwc/models"];

(* Generate topologies: 1-loop, 2->2, only 4-point adjacencies, no tadpoles *)
tops = CreateTopologies[1, 2 -> 2, Adjacencies -> {4}, ExcludeTopologies -> Tadpoles];

(* Insert fields from Phi4MatrixSK.mod with fixed OTOC external assignment *)
diags = InsertFields[
  tops,
  {S[1, {Index[Colour][a1], Index[Colour2][b1], Index[Contour][1], Index[RAx][r]}],
   S[1, {Index[Colour][a2], Index[Colour2][b2], Index[Contour][1], Index[RAx][a]}]} ->
    {S[1, {Index[Colour][a3], Index[Colour2][b3], Index[Contour][2], Index[RAx][r]}],
     S[1, {Index[Colour][a4], Index[Colour2][b4], Index[Contour][2], Index[RAx][a]}]},
  Model -> "Phi4MatrixSK",
  GenericModel -> "Lorentz",
  InsertionLevel -> {Classes}
];
Print["Inserted diagram expressions (raw):"];
Print[diags];

numDiags = Length[Cases[diags, FeynmanDiagram[__], Infinity]];
Print["Diagram selection"];
Print["Number of inserted diagrams: ", numDiags];

If[numDiags == 0,
  Print["No inserted diagrams with fixed external indices. Retrying with generic S[1] externals."];
  diags = InsertFields[
    tops,
    {S[1], S[1]} -> {S[1], S[1]},
    Model -> "Phi4MatrixSK",
    GenericModel -> "Lorentz",
    InsertionLevel -> {Classes}
  ];
  numDiags = Length[Cases[diags, FeynmanDiagram[__], Infinity]];
  Print["Number of inserted diagrams (generic externals): ", numDiags];
];

If[numDiags == 0,
  Print["No inserted diagrams found."];
  Quit[1];
];

diag1 = First@Cases[diags, FeynmanDiagram[__], Infinity];

(* Coupling-level delta structure *)
Print["Coupling-level IndexDelta"];
couplings = Cases[diag1, _C, Infinity];
couplings = couplings /. M$LastModelRules;
couplingDeltas = Cases[couplings, IndexDelta[__], Infinity];
Print["Couplings (VRA evaluated):"]; 
Print[couplings];
Print["IndexDelta terms in couplings:"]; 
Print[couplingDeltas];

(* Amplitude-level delta structure *)
Print["Amplitude-level IndexDelta"];
amp1 = CreateFeynAmp[diag1];
extIndexRules = {
  SequenceForm["Con", 1] -> 1,
  SequenceForm["Con", 2] -> 1,
  SequenceForm["Con", 3] -> 2,
  SequenceForm["Con", 4] -> 2,
  SequenceForm["RAx", 1] -> r,
  SequenceForm["RAx", 2] -> a,
  SequenceForm["RAx", 3] -> r,
  SequenceForm["RAx", 4] -> a
};
amp1 = amp1 /. extIndexRules /. M$LastModelRules;
ampDeltas = Cases[amp1, IndexDelta[__], Infinity];
Print["Amplitude (first element):"]; 
Print[First@amp1];
Print["IndexDelta terms in amplitude:"]; 
Print[ampDeltas];
