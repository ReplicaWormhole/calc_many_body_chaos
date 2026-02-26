AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];
Needs["FeynArts`"];

$ModelPath = Append[$ModelPath, "/home/lev/Projects/calc_mbcwc/models"];

(* Topology: 1-loop, 2->2, 4-point adjacencies, no tadpoles *)
tops = CreateTopologies[1, 2 -> 2, Adjacencies -> {4}, ExcludeTopologies -> Tadpoles];

(* Insert fields for phi^4 matrix SK model at Classes level *)
diags = InsertFields[
  tops,
  {S[1], S[1]} -> {S[1], S[1]},
  Model -> "Phi4MatrixSK",
  GenericModel -> "Lorentz",
  InsertionLevel -> {Classes}
];

(* Build amplitudes *)
amps = CreateFeynAmp[diags];

(* Fix external contour/RA assignment:
   phi^1_r(t,x) phi^1_a(0) phi^2_r(t,x) phi^2_a(0)
   (ordering follows external legs 1..4) *)
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

(* Sum over internal R/A indices and evaluate VRA only when r/a are explicit *)
allRA = DeleteDuplicates@Cases[amps, SequenceForm["RAx", _], Infinity];
extRA = SequenceForm["RAx", #] & /@ Range[4];
intRA = Complement[allRA, extRA];
intRASyms = Symbol /@ ("ra" <> ToString /@ Range[Length[intRA]]);
raSymRules = Thread[intRA -> intRASyms];

VRAeval = VRA[ra1:(r | a), ra2:(r | a), ra3:(r | a), ra4:(r | a)] :>
  Module[{nA = Count[{ra1, ra2, ra3, ra4}, a]},
    Which[nA == 1, 4, nA == 3, 1, True, 0]
  ];

ampsWithRules = amps /. extIndexRules /. raSymRules;
ampsWithRules = Fold[Sum[#1, {#2, {r, a}}] &, ampsWithRules, intRASyms];
ampsWithRules = ampsWithRules /. VRAeval;

Print["Number of diagrams (topologies): ", Length[Cases[diags, Topology[_][__], Infinity]]];
Print["Number of amplitudes: ", Length[ampsWithRules]];

If[Length[ampsWithRules] > 0,
  Print["First amplitude:"];
  Print[ampsWithRules[[1]]];
];
