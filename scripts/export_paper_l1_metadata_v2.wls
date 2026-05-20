(*
  export_paper_l1_metadata_v2.wls
  Run the FeynArts L=1 2->2 amplitude stage for the fixed OTOC external
  assignment and export paper-facing metadata as JSON.
*)

repoDir = DirectoryName[$InputFileName];
repoRoot = FileNameJoin[{repoDir, ".."}];

AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];
Needs["FeynArts`"];

$ModelPath = Append[$ModelPath, FileNameJoin[{repoRoot, "models"}]];

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

If[Length[rawArgs] < 1,
  Print["Usage: WolframKernel -script scripts/export_paper_l1_metadata_v2.wls <output-json-path>"];
  Exit[1];
];

outputPath = rawArgs[[1]];
CreateDirectory[DirectoryName[outputPath], CreateIntermediateDirectories -> True];

tops = CreateTopologies[
  1,
  2 -> 2,
  Adjacencies -> {4},
  ExcludeTopologies -> Tadpoles
];

process =
  {
    S[1, {Index[Colour][a1], Index[Colour2][b1], Index[Contour][1], Index[RAx][r]}],
    S[1, {Index[Colour][a2], Index[Colour2][b2], Index[Contour][1], Index[RAx][a]}]
  } ->
  {
    S[1, {Index[Colour][a3], Index[Colour2][b3], Index[Contour][2], Index[RAx][r]}],
    S[1, {Index[Colour][a4], Index[Colour2][b4], Index[Contour][2], Index[RAx][a]}]
  };

diags = InsertFields[
  tops,
  process,
  Model -> "Phi4MatrixSK",
  GenericModel -> "Lorentz",
  InsertionLevel -> {Classes}
];

ampAll = CreateFeynAmp[diags, AmplitudeLevel -> Classes];
amps = Cases[ampAll, FeynAmp[__], Infinity];
topologyIds = Sort @ DeleteDuplicates @ Cases[amps, GraphID[Topology == t_, ___] :> t, Infinity];

paperSummary = <|
  "one_rung_topology_ids" -> {3, 5, 6},
  "one_rung_per_topology_factor" -> 16,
  "one_rung_total_factor" -> 48,
  "self_energy_topology_ids" -> {1, 2, 4, 7}
|>;

payload = <|
  "loop_order" -> 1,
  "fixed_external_assignment" -> {
    "phi_r^1(x_1)",
    "phi_a^1(x_2)",
    "phi_r^2(x_3)",
    "phi_a^2(x_4)"
  },
  "amplitude_count" -> Length[amps],
  "topology_ids" -> topologyIds,
  "paper_l1" -> paperSummary
|>;

Export[outputPath, payload, "RawJSON"];
Print["Exported v2 paper L1 metadata to ", outputPath];
