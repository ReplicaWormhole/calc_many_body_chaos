AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];
Needs["FeynArts`"];

(* Load FeynArts and add the local model path *)
$ModelPath = Append[$ModelPath, "/home/lev/Projects/calc_mbcwc/models"];

(* Two-point topologies: tree-level 1->1 (single propagator) *)
tops2 = CreateTopologies[0, 1 -> 1];

(* Fixed external fields *)
extFields = {
  S[1, {Index[Colour][a1], Index[Colour2][b1], Index[Contour][1], Index[RAx][r]}],
  S[1, {Index[Colour][a2], Index[Colour2][b2], Index[Contour][1], Index[RAx][a]}],
  S[1, {Index[Colour][a3], Index[Colour2][b3], Index[Contour][2], Index[RAx][r]}],
  S[1, {Index[Colour][a4], Index[Colour2][b4], Index[Contour][2], Index[RAx][a]}]
};

Do[
  Module[{fIn, fOut, proc, diags, ampAll, ampClass, amps},
    fIn = extFields[[i]];
    fOut = extFields[[j]];
    proc = {fIn} -> {fOut};

    Print["Two-point process ", i, " -> ", j, ": ", proc];

    diags = InsertFields[
      tops2,
      proc,
      Model -> "Phi4MatrixSK",
      GenericModel -> "Lorentz",
      InsertionLevel -> {Classes}
    ];

    ampAll = CreateFeynAmp[diags, AmplitudeLevel -> Classes];
    ampClass = PickLevel[ampAll, Classes] /. M$LastModelRules;
    amps = Cases[ampClass, FeynAmp[__], Infinity];

    If[Length[amps] == 0,
      Print["No amplitude found."],
      Do[
        Print[amps[[k]]],
        {k, Length[amps]}
      ]
    ];
  ],
  {i, Length[extFields]},
  {j, Length[extFields]}
];
