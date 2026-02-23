AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];
Needs["FeynArts`"];

L = 1;
top = CreateTopologies[L, 2 -> 2,
  Adjacencies -> {4},
  ExcludeTopologies -> Tadpoles
];

(* Optional preview *)
Paint[top, ColumnsXRows -> 4, PaintLevel -> {Topologies}];
