(*
  generate_all_loop_topologies.wls
  Generate all 2->2 FeynArts topologies at loop order L,
  export one PDF per topology, and save the full TopologyList expression.

  Usage:
    wolframscript -file scripts/generate_all_loop_topologies.wls 1
    wolframscript -file scripts/generate_all_loop_topologies.wls 2 /path/to/outdir
    wolframscript -file scripts/generate_all_loop_topologies.wls 3 /path/to/outdir /path/to/all_L_3.txt
*)

repoDir = DirectoryName[$InputFileName];
repoRoot = FileNameJoin[{repoDir, ".."}];

AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];
Needs["FeynArts`"];

args = Rest[$ScriptCommandLine];

If[Length[args] < 1,
  Print["Usage: wolframscript -file scripts/generate_all_loop_topologies.wls <L> [output-dir] [topology-list-path]"];
  Exit[1];
];

L = ToExpression[args[[1]]];
If[!IntegerQ[L] || L < 0,
  Print["Loop order L must be a non-negative integer. Got: ", args[[1]]];
  Exit[1];
];

outputDir =
  If[Length[args] >= 2,
    args[[2]],
    FileNameJoin[{repoRoot, "data", "L" <> ToString[L]}]
  ];

topologyListPath =
  If[Length[args] >= 3,
    args[[3]],
    FileNameJoin[{repoRoot, "all_L_" <> ToString[L] <> ".txt"}]
  ];

If[!DirectoryQ[outputDir], CreateDirectory[outputDir, CreateIntermediateDirectories -> True]];

Print["Loop order: ", L];
Print["Output dir: ", outputDir];

topsExpr = CreateTopologies[
  L,
  2 -> 2,
  Adjacencies -> {4},
  ExcludeTopologies -> Tadpoles
];

tops = Cases[topsExpr, Topology[_][__], Infinity];

If[tops === {},
  Print["No topologies generated for L=", L];
  Exit[0];
];

Do[
  Export[
    FileNameJoin[{outputDir, "topology" <> ToString[i] <> ".pdf"}],
    Paint[tops[[i]]]
  ],
  {i, Length[tops]}
];
Export[topologyListPath, InputForm[TopologyList @@ tops], "String"];

Print["Generated ", Length[tops], " topology PDFs."];
Print["Saved topology list to ", topologyListPath];
