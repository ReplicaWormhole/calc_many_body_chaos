AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];
Needs["FeynArts`"];

L = 1;
top = CreateTopologies[L, 2 -> 2,
  Adjacencies -> {4},
  ExcludeTopologies -> Tadpoles
];

(* Optional preview *)
Paint[top, ColumnsXRows -> 4, PaintLevel -> {Topologies}];

(*1) Load FeynArts and add the local model path*)
$ModelPath = Append[$ModelPath, "/home/lev/Projects/calc_mbcwc/models"];

(*2) Generate topologies:1-loop,2->2,only 4-point adjacencies,\
no tadpoles*)
tops = CreateTopologies[1, 2 -> 2, Adjacencies -> {4}, 
   ExcludeTopologies -> Tadpoles];

(*3) Insert fields from Phi4MatrixSK.mod with fixed OTOC external assignment*)
(* Incoming: contour 1 (r,a), Outgoing: contour 2 (r,a) *)
diags = InsertFields[
  tops,
  {S[1, {a1, b1, 1, r}], S[1, {a2, b2, 1, a}]} ->
    {S[1, {a3, b3, 2, r}], S[1, {a4, b4, 2, a}]},
  Model -> "Phi4MatrixSK",
  GenericModel -> "Lorentz",
  InsertionLevel -> {Classes}
]
