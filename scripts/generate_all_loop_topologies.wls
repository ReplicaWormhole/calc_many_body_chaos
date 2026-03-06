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

rawArgs =
  If[$ScriptCommandLine =!= {},
    Rest[$ScriptCommandLine],
    Module[{cmd = Rest[$CommandLine], scriptPos},
      scriptPos = FirstPosition[cmd, _?(StringQ[#] && StringMatchQ[#, "*.wls"] &)];
      If[scriptPos === Missing["NotFound"],
        {},
        Drop[cmd, scriptPos[[1]]]
      ]
    ]
  ];

flagArgs = Select[rawArgs, StringStartsQ["--"]];
args = Select[rawArgs, Not@*StringStartsQ["--"]];

listOnlyQ = MemberQ[flagArgs, "--list-only"];
imagesOnlyQ = MemberQ[flagArgs, "--images-only"];

If[listOnlyQ && imagesOnlyQ,
  Print["Use at most one of --list-only or --images-only."];
  Exit[1];
];

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

loadTopologyList[path_] :=
  Module[{text, expr},
    text = Import[path, "Text"];
    expr = ToExpression[text];
    Cases[expr, Topology[_][__], Infinity]
  ];

createTopologyList[loopOrder_] :=
  Module[{topsExpr},
    topsExpr = CreateTopologies[
      loopOrder,
      2 -> 2,
      Adjacencies -> {4},
      ExcludeTopologies -> Tadpoles
    ];
    Cases[topsExpr, Topology[_][__], Infinity]
  ];

exportTopologyList[tops_, path_] :=
  Export[path, InputForm[TopologyList @@ tops], "String"];

renderTopologyImage[top_, index_, outDir_] :=
  Module[{paint, singleTop, psPath},
    singleTop = TopologyList @@ {top};
    paint = Paint[
      singleTop,
      PaintLevel -> {Topologies},
      ColumnsXRows -> {1, 1},
      Numbering -> Simple,
      AutoEdit -> False,
      DisplayFunction -> Identity
    ];
    psPath = FileNameJoin[{outDir, "topology" <> ToString[index] <> ".ps"}];
    Export[psPath, paint, "PS"];
  ];

tops =
  If[imagesOnlyQ,
    loadTopologyList[topologyListPath],
    createTopologyList[L]
  ];

If[tops === {},
  Print["No topologies generated for L=", L];
  Exit[0];
];

If[!imagesOnlyQ,
  exportTopologyList[tops, topologyListPath];
  Print["Saved topology list to ", topologyListPath];
];

If[!listOnlyQ,
  Do[
    renderTopologyImage[tops[[i]], i, outputDir],
    {i, Length[tops]}
  ];
  Print["Generated ", Length[tops], " topology PostScript files."];
];

If[listOnlyQ,
  Print["Skipped image rendering (--list-only)."];
];

If[imagesOnlyQ,
  Print["Loaded topology list from ", topologyListPath];
];
