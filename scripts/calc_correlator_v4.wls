AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];
Needs["FeynArts`"];

(* Load FeynArts and add the local model path *)
$ModelPath = Append[$ModelPath, "/home/lev/Projects/calc_mbcwc/models"];

(* Generate topologies: 1-loop, 2->2, only 4-point adjacencies, no tadpoles *)
tops = CreateTopologies[1, 2 -> 2, Adjacencies -> {4}, ExcludeTopologies -> Tadpoles];

(* Fixed external fields; we will permute their ordering across incoming/outgoing slots *)
extFields = {
  S[1, {Index[Colour][a1], Index[Colour2][b1], Index[Contour][1], Index[RAx][r]}],
  S[1, {Index[Colour][a2], Index[Colour2][b2], Index[Contour][1], Index[RAx][a]}],
  S[1, {Index[Colour][a3], Index[Colour2][b3], Index[Contour][2], Index[RAx][r]}],
  S[1, {Index[Colour][a4], Index[Colour2][b4], Index[Contour][2], Index[RAx][a]}]
};

perms = Permutations[extFields];

(* Restrict to ladder topologies *)
targetTopologies = {3, 5, 6};

nonzeroCount = 0;

Do[
  Module[{proc, diags, ampAll, amps, ampsFiltered, ampsEval, nonzeroAmps},
    proc = {perms[[i, 1]], perms[[i, 2]]} -> {perms[[i, 3]], perms[[i, 4]]};

    diags = InsertFields[
      tops,
      proc,
      Model -> "Phi4MatrixSK",
      GenericModel -> "Lorentz",
      InsertionLevel -> {Classes}
    ];

    ampAll = CreateFeynAmp[diags, AmplitudeLevel -> Classes];
    (* Convert to class-level amplitudes so insertion rules are applied *)
    ampClass = PickLevel[ampAll, Classes] /. M$LastModelRules;
    amps = Cases[ampClass, FeynAmp[__], Infinity];

    ampsFiltered = Select[
      amps,
      MatchQ[#, FeynAmp[GraphID[Topology == t_, ___], ___] /; MemberQ[targetTopologies, t]] &
    ];

    ampsEval = Simplify /@ ampsFiltered;

    nonzeroAmps = Select[ampsEval, # =!= 0 &];

    If[Length[nonzeroAmps] > 0,
      nonzeroCount = nonzeroCount + 1;
      Print["Permutation ", i, ": ", proc];
      Print["Nonzero T3/T5/T6 amplitude(s):"];
      Do[
        Print[nonzeroAmps[[j]]],
        {j, Length[nonzeroAmps]}
      ];
    ];
  ],
  {i, Length[perms]}
];

Print["Total permutations with nonzero ladder amplitudes: ", nonzeroCount];
