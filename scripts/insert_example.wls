(* Apply InsertFields to the example topology from loop_data.txt *)
AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];
Needs["FeynArts`"];


(* Ensure the local models directory is on the path *)
Module[{scriptDir, modelDir, topoText, topo, tops, diags},
  scriptDir = DirectoryName[$InputFileName];
  modelDir = FileNameJoin[{scriptDir, "..", "models"}];
  If[!MemberQ[$Path, modelDir], AppendTo[$Path, modelDir]];

  InitializeModel["Phi4MatrixSK"];

  topoText = Import[FileNameJoin[{scriptDir, "..", "loop_data.txt"}], "Text"];
  topo = ToExpression[topoText];
  tops = {topo};

  diags = InsertFields[
    tops,
    {S[1], S[1]} -> {S[1], S[1]},
    InsertionLevel -> {Classes},
    GenericModel -> "Lorentz",
    Model -> "Phi4Matrix"
  ];

  Print["Number of diagrams: ", Length[diags]];
  Print["Diagrams (Short): ", Short[diags, 3]];
];
