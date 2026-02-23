AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];
Needs["FeynArts`"];

$ModelPath = Append[$ModelPath, "/home/lev/Projects/calc_mbcwc/models"];

(* Single 2->2 topology, no tadpoles *)
top = CreateTopologies[1, 2 -> 2, Adjacencies -> {4}, ExcludeTopologies -> Tadpoles];

(* Fixed OTOC external assignment: in (1r,1a), out (2r,2a) *)
ins = InsertFields[
  top,
  {S[1, {a1, b1, 1, r}], S[1, {a2, b2, 1, a}]} ->
    {S[1, {a3, b3, 2, r}], S[1, {a4, b4, 2, a}]},
  Model -> "Phi4MatrixSK",
  GenericModel -> "Lorentz",
  InsertionLevel -> {Classes}
];

Print["InsertFields head: ", Head[ins]];
Print["Number of inserted diagrams: ", Length[Cases[ins, FeynmanDiagram[__], Infinity]]];

(* Show a coupling factor to confirm IndexDelta structure *)
Print["Sample coupling factor:"];
Print[ins /. FeynmanDiagram[__] :> Sequence[] // Cases[#, _C, Infinity] & // Take[#, UpTo[1]] &];
