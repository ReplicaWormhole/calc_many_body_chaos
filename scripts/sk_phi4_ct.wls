(*
  sk_phi4_ct.wls
  Generate phi^4 matrix-model 4-pt diagrams up to 3 loops,
  build SK r/a expressions for the squared commutator structure.
*)

repoDir = DirectoryName[$InputFileName];
modelDir = FileNameJoin[{repoDir, "..", "models"}];
outputDir = FileNameJoin[{repoDir, "..", "output"}];
If[!DirectoryQ[outputDir], CreateDirectory[outputDir]];

AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];

Block[{cp = $ContextPath},
  $ContextPath = DeleteCases[$ContextPath, "Global`"];
  Needs["FeynArts`"];
  $ContextPath = cp;
];
If[!MemberQ[$ContextPath, "FeynArts`"], AppendTo[$ContextPath, "FeynArts`"]];

AppendTo[FeynArts`$ModelPath, modelDir];

Print["Model path: ", modelDir];
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

(* Assign external legs: incoming/outgoing order *)
externalAssignment = {
  <|"c" -> 1, "l" -> r, "idx" -> {a1, b1}|>,
  <|"c" -> 1, "l" -> a, "idx" -> {a2, b2}|>,
  <|"c" -> 2, "l" -> r, "idx" -> {a3, b3}|>,
  <|"c" -> 2, "l" -> a, "idx" -> {a4, b4}|>
};

(* Helpers for extracting topology structure *)
ClearAll[extractProps, extractVertices];
extractProps[top_] := Cases[top, Propagator[_][v1_, v2_] :> {v1, v2}, Infinity];
extractVertices[top_] := Union[Flatten[extractProps[top]]];

isExternalVertex[v_] := MatchQ[v, Vertex[1][_]];

(* Build a symbolic SK expression per topology *
   - Assign contour c[v] for internal vertices (sum over 1,2)
   - Assign branch l[edge, v] for each half-edge (sum over r,a)
   - External legs fixed by externalAssignment order
*)

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

  (* Map external propagators by order of appearance to externalAssignment *)
  extProps = Select[props, (#[[1]] === Incoming || #[[1]] === Outgoing) &];
  extPropPos = Flatten@Position[props[[All, 1]], _?(# === Incoming || # === Outgoing &)];
  extMap = AssociationThread[extPropPos, externalAssignment];

  (* Edge identifiers *)
  edgeIds = Range[Length[props]];
  edgeEnds = AssociationThread[edgeIds, props[[All, {2, 3}]]];

  (* Branch variables per half-edge: l[edge, v] *)
  lvars = Table[Unique["l"], {Length[props], 2}];

  (* Contour variables per internal vertex: c[v] *)
  cvars = AssociationThread[internalVerts, Table[Unique["c"], {Length[internalVerts]}]];

  (* Matrix index pairs per half-edge: {a,b} at each endpoint *)
  indexPairs = Table[
    {
      {Unique["a"], Unique["b"]},
      {Unique["a"], Unique["b"]}
    },
    {Length[props]}
  ];


  (* Vertex legs: for each vertex, list of branch variables of incident half-edges *)
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

  (* Vertex factor based on number of a legs (odd only) plus trace deltas *)
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

  (* Propagator factors with explicit contour + branch indices *)
  propFactors = Times @@ Table[
    With[{type = props[[k, 1]], v1 = props[[k, 2]], v2 = props[[k, 3]]},
      Module[{c1, c2, l1, l2, extAssign},
        l1 = lvars[[k, 1]]; l2 = lvars[[k, 2]];

        c1 = If[KeyExistsQ[cvars, v1], cvars[v1], None];
        c2 = If[KeyExistsQ[cvars, v2], cvars[v2], None];

        (* External assignments fix c,l at external vertex ends *)
        If[KeyExistsQ[extMap, k],
          extAssign = extMap[k];
          If[isExternalVertex[v1],
            c1 = extAssign["c"]; l1 = extAssign["l"]; AppendTo[fixedL, l1];
            indexPairs[[k, 1]] = extAssign["idx"];
          ];
          If[isExternalVertex[v2],
            c2 = extAssign["c"]; l2 = extAssign["l"]; AppendTo[fixedL, l2];
            indexPairs[[k, 2]] = extAssign["idx"];
          ];
        ];

        (* Build propagator factor symbolically with matrix deltas *)
        With[{idx1 = indexPairs[[k, 1]], idx2 = indexPairs[[k, 2]]},
          G[c1, c2][l1, l2] * IndexDelta[idx1[[1]], idx2[[2]]] * IndexDelta[idx1[[2]], idx2[[1]]]
        ]
      ]
    ],
    {k, Length[props]}
  ];

  expr = vertexFactors * propFactors;

  (* Sums over contour indices for internal vertices *)
  sums = Fold[
    Function[e, Sum[e, {cvars[#], {1, 2}}] &],
    expr,
    Keys[cvars]
  ];

  (* Sums over branch indices for all half-edges not fixed by external assignment *)
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

  <|"Expr" -> sums, "NPower" -> nPower|>
];

(* Loop over L=0..3 and generate diagrams + expressions *)
Do[
  Print["Generating L=", L, " topologies..."];
  top = CreateTopologies[L, 2 -> 2, ExcludeTopologies -> Tadpoles];

  ins = InsertFields[
    top,
    {S[1], S[1]} -> {S[1], S[1]},
    Model -> "Phi4Matrix",
    GenericModel -> "Lorentz",
    InsertionLevel -> {Classes}
  ];

  insTopos = Cases[ins, Topology[_][__], Infinity];
  paintInput = If[insTopos === {}, top, ins];
  If[insTopos === {}, Print["Warning: no inserted diagrams; painting topologies only."]];

  (* Paint diagrams *)
  paint = Paint[
    paintInput,
    PaintLevel -> {Classes},
    ColumnsXRows -> 2,
    Numbering -> Simple,
    SheetHeader -> "phi^4 matrix, 2->2, L=" <> ToString[L],
    DisplayFunction -> Identity
  ];
  Print["Paint head (L=", L, "): ", Head[paint]];
  Print["Paint length (L=", L, "): ", If[ListQ[paint], Length[paint], 1]];

  If[MatchQ[paint, _Graphics | _Graphics3D | _GraphicsBox | _List],
    Export[FileNameJoin[{outputDir, "sk_phi4_4pt_L" <> ToString[L] <> ".pdf"}], paint];
    Export[FileNameJoin[{outputDir, "sk_phi4_4pt_L" <> ToString[L] <> ".png"}], paint];
    ,
    Print["Warning: Paint returned non-graphics for L=", L, ": ", paint]
  ];

  (* Build SK expressions for each topology *)
  skExprs = skExpressionForTopology /@ If[insTopos === {}, Cases[top, Topology[_][__], Infinity], insTopos];
  Put[skExprs, FileNameJoin[{outputDir, "sk_phi4_4pt_L" <> ToString[L] <> ".m"}]];
,
  {L, 0, 3}
];

(* --- TeX output --- *)
texFile = FileNameJoin[{outputDir, "sk_phi4_4pt_RA.tex"}];
texBody = StringRiffle[{
  "\\documentclass{article}",
  "\\usepackage{amsmath}",
  "\\begin{document}",
  "\\section*{SK r/a phi^4 matrix OTOC}",
  "External insertion: $\\phi^{1}_{r}(t,x)\\phi^{1}_{a}(0)\\phi^{2}_{r}(t,x)\\phi^{2}_{a}(0)$.",
  "\\section*{Translation Rules}",
  "Contour basis:",
  "$G^{11}=G_T,\\;G^{22}=G_{\\bar T},\\;G^{12}=G^<,\\;G^{21}=G^>$.",
  "r/a basis:",
  "$G_{rr}=G_K,\\;G_{ra}=G_R,\\;G_{ar}=G_A,\\;G_{aa}=0$."
}, "\n"];

texExprs = "";
Do[
  exprFile = FileNameJoin[{outputDir, "sk_phi4_4pt_L" <> ToString[L] <> ".m"}];
  If[FileExistsQ[exprFile],
    exprList = Get[exprFile];
    texExprs = texExprs <> "\\n\\\\section*{L=" <> ToString[L] <> "}";
    texExprs = texExprs <> "\\n\\\\begin{align}";
    texExprs = texExprs <> StringRiffle[
      ToString /@ (TeXForm /@ (exprList[[All, "Expr"]])),
      "\\\\\\n"
    ];
    texExprs = texExprs <> "\\n\\\\end{align}";
    texExprs = texExprs <> "\\n\\\\noindent N\\,\\text{powers}: " <>
      ToString[TeXForm[exprList[[All, "NPower"]]]] <> "\\n";
  ];
,
  {L, 0, 3}
];

tex = texBody <> texExprs <> "\n\\end{document}\n";
Export[texFile, tex, "String"];

Print["Done. Outputs in ", outputDir];
