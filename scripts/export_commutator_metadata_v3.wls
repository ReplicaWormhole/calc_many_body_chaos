(*
  export_commutator_metadata_v3.wls
  Run the FeynArts topology, insertion, and amplitude stages for a fixed
  matrix-SK 2->2 commutator process and export loop-generic metadata as JSON.
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

If[Length[rawArgs] < 2,
  Print["Usage: WolframKernel -script scripts/export_commutator_metadata_v3.wls <loop-order> <output-json-path>"];
  Exit[1];
];

loopOrder = ToExpression[rawArgs[[1]]];
outputPath = rawArgs[[2]];

CreateDirectory[DirectoryName[outputPath], CreateIntermediateDirectories -> True];

tops = CreateTopologies[
  loopOrder,
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

topologyClassByIndex = Cases[tops, Topology[t_][__] :> t, Infinity];
insertedTopologyIndices = Cases[diags, GraphID[Topology == t_, ___] :> t, Infinity];
amplitudeTopologyIndices = Cases[amps, GraphID[Topology == t_, ___] :> t, Infinity];

If[Length[insertedTopologyIndices] == 0,
  insertedTopologyIndices = amplitudeTopologyIndices;
];

insertedTopologyClassIds =
  Select[
    Replace[insertedTopologyIndices, i_Integer :> topologyClassByIndex[[i]], {1}],
    IntegerQ
  ];
amplitudeTopologyClassIds =
  Select[
    Replace[amplitudeTopologyIndices, i_Integer :> topologyClassByIndex[[i]], {1}],
    IntegerQ
  ];

topologyCounts = Counts[amplitudeTopologyClassIds];
paperL1Summary =
  If[loopOrder === 1,
    <|
      "one_rung_topology_ids" -> {3, 5, 6},
      "one_rung_per_topology_factor" -> 16,
      "one_rung_total_factor" -> 48,
      "self_energy_topology_ids" -> {1, 2, 4, 7}
    |>,
    Nothing
  ];

payload = <|
  "loop_order" -> loopOrder,
  "fixed_external_assignment" -> {
    "phi_r^1(x_1)",
    "phi_a^1(x_2)",
    "phi_r^2(x_3)",
    "phi_a^2(x_4)"
  },
  "topology_count" -> Length[tops],
  "inserted_diagram_count" -> Length[insertedTopologyIndices],
  "amplitude_count" -> Length[amps],
  "topology_ids" -> Sort @ DeleteDuplicates @ amplitudeTopologyClassIds,
  "inserted_topology_ids" -> Sort @ DeleteDuplicates @ insertedTopologyClassIds,
  "diagram_index_ids" -> Sort @ DeleteDuplicates @ amplitudeTopologyIndices,
  "amplitude_counts_by_topology_id" -> KeyMap[ToString, topologyCounts]
|>;

If[loopOrder === 1,
  payload = Append[payload, "paper_l1" -> paperL1Summary];
];

Export[outputPath, payload, "RawJSON"];
Print["Exported v3 metadata for L=", loopOrder, " to ", outputPath];
