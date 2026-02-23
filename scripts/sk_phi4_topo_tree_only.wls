(***
  sk_phi4_topo_tree_only.wls
  Condensed: generate all tree-level (L=0) 2->2 topologies for the
  phi^4 matrix model and export as PNG/PDF.
***)

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

(* Tree-level 2->2 topologies only *)
L = 0;
top = CreateTopologies[L, 2 -> 2, ExcludeTopologies -> Tadpoles];
tops = Cases[top, Topology[_][__], Infinity];

If[tops === {},
  Print["No topologies at L=0"]; Abort[];
];

paint = Paint[
  tops,
  PaintLevel -> {Classes},
  ColumnsXRows -> 2,
  Numbering -> Simple,
  SheetHeader -> "phi^4 matrix, 2->2, L=0"
];

raster = If[ListQ[paint], Rasterize /@ paint, Rasterize[paint]];
Export[FileNameJoin[{outputDir, "sk_topo_L0_tree_only.pdf"}], raster];
Export[FileNameJoin[{outputDir, "sk_topo_L0_tree_only.png"}], raster];

Print["Done. Outputs in ", outputDir];
