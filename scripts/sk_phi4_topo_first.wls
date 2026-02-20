(*
  sk_phi4_topo_first.wls
  Topology-first OTOC pipeline for phi^4 matrix model:
  - generate 2->2 topologies only (no field insertions)
  - compute Nc power from double-line index loops
  - keep leading and subleading in N
  - build SK r/a expressions with fixed external assignment
  - export PNG/PDF + .m data
*)

repoDir = DirectoryName[$InputFileName];
outputDir = FileNameJoin[{repoDir, "..", "output"}];
If[!DirectoryQ[outputDir], CreateDirectory[outputDir]];

AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];

Block[{cp = $ContextPath},
  $ContextPath = DeleteCases[$ContextPath, "Global`"];
  Needs["FeynArts`"];
  $ContextPath = cp;
];
If[!MemberQ[$ContextPath, "FeynArts`"], AppendTo[$ContextPath, "FeynArts`"]];

Print["Output dir: ", outputDir];

(* --- r/a vertex coefficients from L_+ - L_- --- *)
raVertexCoeff[nA_Integer] := Module[{r, a, expr, coeff},
  expr = Expand[(r + a/2)^4 - (r - a/2)^4];
  coeff = Coefficient[expr, a, nA];
  coeff = coeff /. r -> 1; (* normalize by r powers *)
  coeff
];

(* Only odd nA survive for phi^4 *)
vertexCoeffMap = <|
  1 -> raVertexCoeff[1],
  3 -> raVertexCoeff[3]
|>;

(* External assignment: fixed OTOC ordering *)
externalAssignment = {
  <|"c" -> 1, "l" -> r, "idx" -> {a1, b1}|>,
  <|"c" -> 1, "l" -> a, "idx" -> {a2, b2}|>,
  <|"c" -> 2, "l" -> r, "idx" -> {a3, b3}|>,
  <|"c" -> 2, "l" -> a, "idx" -> {a4, b4}|>
};

(* Helpers *)
ClearAll[extractProps, extractVertices, isExternalVertex];
extractProps[top_] := Cases[top, Propagator[_][v1_, v2_] :> {v1, v2}, Infinity];
extractVertices[top_] := Union[Flatten[extractProps[top]]];
isExternalVertex[v_] := MatchQ[v, Vertex[1][_]];

(* Compute Nc power without building full SK sums *)
ClearAll[nPowerForTopology];
nPowerForTopology[top_] := Module[
  {props, verts, internalVerts, extVerts, extProps, extPropPos, extMap,
   edgeIds, edgeEnds, indexPairs, vertexLegsIdx, traceDeltas, propDeltas,
   pairs, allIdx, externalIdx, graph, comps, isolated, internalComps},

  props = Cases[top, Propagator[type_][v1_, v2_] :> {type, v1, v2}, Infinity];
  verts = Union[Flatten[props[[All, {2, 3}]]]];
  internalVerts = Select[verts, !isExternalVertex[#] &];
  extVerts = Select[verts, isExternalVertex[#] &];

  extProps = Select[props, (#[[1]] === Incoming || #[[1]] === Outgoing) &];
  extPropPos = Flatten@Position[props[[All, 1]], _?(# === Incoming || # === Outgoing &)];
  extMap = AssociationThread[extPropPos, externalAssignment];

  edgeIds = Range[Length[props]];
  edgeEnds = AssociationThread[edgeIds, props[[All, {2, 3}]]];

  indexPairs = Table[
    { {Unique["a"], Unique["b"]}, {Unique["a"], Unique["b"]} },
    {Length[props]}
  ];

  (* Apply external index assignments *)
  Do[
    If[KeyExistsQ[extMap, k],
      With[{extAssign = extMap[k], v1 = props[[k, 2]], v2 = props[[k, 3]]},
        If[isExternalVertex[v1], indexPairs[[k, 1]] = extAssign["idx"]];
        If[isExternalVertex[v2], indexPairs[[k, 2]] = extAssign["idx"]];
      ]
    ],
    {k, Length[props]}
  ];

  (* Vertex index legs: for each vertex, list of matrix-index pairs of incident half-edges *)
  vertexLegsIdx = Association@Map[
    Function[v,
      v -> Flatten@Table[
        With[{e = edgeIds[[k]], v1 = edgeEnds[edgeIds[[k]]][[1]], v2 = edgeEnds[edgeIds[[k]]][[2]]},
          Which[
            v === v1, indexPairs[[k, 1]],
            v === v2, indexPairs[[k, 2]],
            True, Sequence @@ {}
          ]
        ],
        {k, Length[edgeIds]}
      ]
    ],
    internalVerts
  ];

  traceDeltas = Times @@ Table[
    With[{legs = Partition[vertexLegsIdx[v], 2]},
      If[Length[legs] =!= 4, 1,
        IndexDelta[legs[[1, 2]], legs[[2, 1]]] *
        IndexDelta[legs[[2, 2]], legs[[3, 1]]] *
        IndexDelta[legs[[3, 2]], legs[[4, 1]]] *
        IndexDelta[legs[[4, 2]], legs[[1, 1]]]
      ]
    ],
    {v, internalVerts}
  ];

  propDeltas = Times @@ Table[
    With[{idx1 = indexPairs[[k, 1]], idx2 = indexPairs[[k, 2]]},
      IndexDelta[idx1[[1]], idx2[[2]]] * IndexDelta[idx1[[2]], idx2[[1]]]
    ],
    {k, Length[props]}
  ];

  pairs = Cases[traceDeltas * propDeltas, IndexDelta[x_, y_] :> {x, y}, Infinity];

  allIdx = DeleteDuplicates@Flatten[indexPairs];
  externalIdx = DeleteDuplicates@Flatten[externalAssignment[[All, "idx"]]];

  graph = Graph[UndirectedEdge @@@ pairs];
  comps = ConnectedComponents[graph];
  isolated = Complement[allIdx, Union[Flatten[pairs]]];
  comps = Join[comps, List /@ isolated];
  internalComps = Select[comps, Intersection[#, externalIdx] === {} &];
  Length[internalComps]
];

(* Full SK expression per topology *)
ClearAll[skExpressionForTopology];
skExpressionForTopology[top_] := Module[
  {props, verts, internalVerts, extVerts, extProps, extPropPos, extMap,
   edgeIds, edgeEnds, lvars, cvars, vertexLegs, vertexLegsIdx,
   vertexFactors, propFactors, expr, sums, fixedL, freeL,
   indexPairs, allIdx, externalIdx, nPower},

  props = Cases[top, Propagator[type_][v1_, v2_] :> {type, v1, v2}, Infinity];
  verts = Union[Flatten[props[[All, {2, 3}]]]];
  internalVerts = Select[verts, !isExternalVertex[#] &];
  extVerts = Select[verts, isExternalVertex[#] &];

  extProps = Select[props, (#[[1]] === Incoming || #[[1]] === Outgoing) &];
  extPropPos = Flatten@Position[props[[All, 1]], _?(# === Incoming || # === Outgoing &)];
  extMap = AssociationThread[extPropPos, externalAssignment];

  edgeIds = Range[Length[props]];
  edgeEnds = AssociationThread[edgeIds, props[[All, {2, 3}]]];

  lvars = Table[Unique["l"], {Length[props]}, {2}];
  cvars = AssociationThread[internalVerts, Table[Unique["c"], {Length[internalVerts]}]];

  indexPairs = Table[
    { {Unique["a"], Unique["b"]}, {Unique["a"], Unique["b"]} },
    {Length[props]}
  ];

  vertexLegs = Association@Map[
    Function[v,
      v -> Flatten@Table[
        With[{e = edgeIds[[k]], v1 = edgeEnds[edgeIds[[k]]][[1]], v2 = edgeEnds[edgeIds[[k]]][[2]]},
          Which[
            v === v1, lvars[[k, 1]],
            v === v2, lvars[[k, 2]],
            True, Sequence @@ {}
          ]
        ],
        {k, Length[edgeIds]}
      ]
    ],
    internalVerts
  ];

  vertexLegsIdx = Association@Map[
    Function[v,
      v -> Flatten@Table[
        With[{e = edgeIds[[k]], v1 = edgeEnds[edgeIds[[k]]][[1]], v2 = edgeEnds[edgeIds[[k]]][[2]]},
          Which[
            v === v1, indexPairs[[k, 1]],
            v === v2, indexPairs[[k, 2]],
            True, Sequence @@ {}
          ]
        ],
        {k, Length[edgeIds]}
      ]
    ],
    internalVerts
  ];

  TraceDeltas[legs_List] := Module[{pairs, n},
    n = Length[legs];
    If[n =!= 4, 1,
      pairs = {
        IndexDelta[legs[[1, 2]], legs[[2, 1]]],
        IndexDelta[legs[[2, 2]], legs[[3, 1]]],
        IndexDelta[legs[[3, 2]], legs[[4, 1]]],
        IndexDelta[legs[[4, 2]], legs[[1, 1]]]
      };
      Times @@ pairs
    ]
  ];

  vertexFactors = Times @@ Table[
    With[{legs = vertexLegs[v], legsIdx = Partition[vertexLegsIdx[v], 2]},
      If[legs === {}, 1,
        With[{nA = Count[legs, a]},
          If[KeyExistsQ[vertexCoeffMap, nA],
            -I*g2*vertexCoeffMap[nA] * TraceDeltas[legsIdx],
            0
          ]
        ]
      ]
    ],
    {v, internalVerts}
  ];

  fixedL = {};

  propFactors = Times @@ Table[
    With[{type = props[[k, 1]], v1 = props[[k, 2]], v2 = props[[k, 3]]},
      Module[{c1, c2, l1, l2, extAssign},
        l1 = lvars[[k, 1]]; l2 = lvars[[k, 2]];

        c1 = If[KeyExistsQ[cvars, v1], cvars[v1], None];
        c2 = If[KeyExistsQ[cvars, v2], cvars[v2], None];

        If[KeyExistsQ[extMap, k],
          extAssign = extMap[k];
          If[isExternalVertex[v1],
            c1 = extAssign["c"]; l1 = extAssign["l"]; AppendTo[fixedL, l1];
            indexPairs[[k, 1]] = extAssign["idx"]
          ];
          If[isExternalVertex[v2],
            c2 = extAssign["c"]; l2 = extAssign["l"]; AppendTo[fixedL, l2];
            indexPairs[[k, 2]] = extAssign["idx"]
          ];
        ];

        With[{idx1 = indexPairs[[k, 1]], idx2 = indexPairs[[k, 2]]},
          G[c1, c2][l1, l2] * IndexDelta[idx1[[1]], idx2[[2]]] * IndexDelta[idx1[[2]], idx2[[1]]]
        ]
      ]
    ],
    {k, Length[props]}
  ];

  expr = vertexFactors * propFactors;

  sums = Fold[
    Function[e, Sum[e, {cvars[#], {1, 2}}] &],
    expr,
    Keys[cvars]
  ];

  freeL = Complement[DeleteDuplicates@Flatten@lvars, DeleteDuplicates@fixedL];
  sums = Fold[
    Function[e, Sum[e, {#, {r, a}}] &],
    sums,
    freeL
  ];

  allIdx = DeleteDuplicates@Flatten[indexPairs];
  externalIdx = DeleteDuplicates@Flatten[externalAssignment[[All, "idx"]]];

  nPower = Module[{pairs, graph, comps, isolated, internalComps},
    pairs = Cases[sums, IndexDelta[x_, y_] :> {x, y}, Infinity];
    graph = Graph[UndirectedEdge @@@ pairs];
    comps = ConnectedComponents[graph];
    isolated = Complement[allIdx, Union[Flatten[pairs]]];
    comps = Join[comps, List /@ isolated];
    internalComps = Select[comps, Intersection[#, externalIdx] === {} &];
    Length[internalComps]
  ];

  <|"Expr" -> sums, "NPower" -> nPower, "Topo" -> top|>
];

Do[
  Print["Generating L=", L, " topologies..."];
  top = CreateTopologies[L, 2 -> 2, ExcludeTopologies -> Tadpoles];
  tops = Cases[top, Topology[_][__], Infinity];

  If[tops === {},
    Print["No topologies at L=", L];
    Continue[];
  ];

  (* First pass: NPower only *)
  nPowers = nPowerForTopology /@ tops;
  maxN = Max[nPowers];

  keepIdx = Flatten@Position[nPowers, _?(# == maxN || # == maxN - 1 &)];
  keptTops = tops[[keepIdx]];

  Print["L=", L, ": total=", Length[tops], ", kept=", Length[keptTops], ", maxN=", maxN];

  (* Paint retained topologies *)
  paint = Paint[
    keptTops,
    PaintLevel -> {Classes},
    ColumnsXRows -> 2,
    Numbering -> Simple,
    SheetHeader -> "phi^4 matrix, 2->2, L=" <> ToString[L]
  ];

  raster = If[ListQ[paint], Rasterize /@ paint, Rasterize[paint]];
  Export[FileNameJoin[{outputDir, "sk_topo_L" <> ToString[L] <> ".pdf"}], raster];
  Export[FileNameJoin[{outputDir, "sk_topo_L" <> ToString[L] <> ".png"}], raster];

  (* Full SK expressions only for retained topologies *)
  skExprs = skExpressionForTopology /@ keptTops;
  Put[skExprs, FileNameJoin[{outputDir, "sk_topo_L" <> ToString[L] <> ".m"}]];
,
  {L, 0, 2}
];

Print["Done. Outputs in ", outputDir];
