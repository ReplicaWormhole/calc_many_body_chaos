AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];
Needs["FeynArts`"];

(* Load FeynArts and add the local model path *)
$ModelPath = Append[$ModelPath, "/home/lev/Projects/calc_mbcwc/models"];

(* Generate topologies: 1-loop, 2->2, only 4-point adjacencies, no tadpoles *)
tops = CreateTopologies[1, 2 -> 2, Adjacencies -> {4}, ExcludeTopologies -> Tadpoles];

(* Insert fields from Phi4MatrixSK.mod with fixed OTOC external assignment.
   Repeat for 3 additional permutations of the external ordering. *)
processes = {
  {S[1, {Index[Colour][a1], Index[Colour2][b1], Index[Contour][1], Index[RAx][r]}],
   S[1, {Index[Colour][a2], Index[Colour2][b2], Index[Contour][1], Index[RAx][a]}]} ->
    {S[1, {Index[Colour][a3], Index[Colour2][b3], Index[Contour][2], Index[RAx][r]}],
     S[1, {Index[Colour][a4], Index[Colour2][b4], Index[Contour][2], Index[RAx][a]}]},
  {S[1, {Index[Colour][a2], Index[Colour2][b2], Index[Contour][1], Index[RAx][a]}],
   S[1, {Index[Colour][a1], Index[Colour2][b1], Index[Contour][1], Index[RAx][r]}]} ->
    {S[1, {Index[Colour][a3], Index[Colour2][b3], Index[Contour][2], Index[RAx][r]}],
     S[1, {Index[Colour][a4], Index[Colour2][b4], Index[Contour][2], Index[RAx][a]}]},
  {S[1, {Index[Colour][a1], Index[Colour2][b1], Index[Contour][1], Index[RAx][r]}],
   S[1, {Index[Colour][a2], Index[Colour2][b2], Index[Contour][1], Index[RAx][a]}]} ->
    {S[1, {Index[Colour][a4], Index[Colour2][b4], Index[Contour][2], Index[RAx][a]}],
     S[1, {Index[Colour][a3], Index[Colour2][b3], Index[Contour][2], Index[RAx][r]}]},
  {S[1, {Index[Colour][a2], Index[Colour2][b2], Index[Contour][1], Index[RAx][a]}],
   S[1, {Index[Colour][a1], Index[Colour2][b1], Index[Contour][1], Index[RAx][r]}]} ->
    {S[1, {Index[Colour][a4], Index[Colour2][b4], Index[Contour][2], Index[RAx][a]}],
     S[1, {Index[Colour][a3], Index[Colour2][b3], Index[Contour][2], Index[RAx][r]}]}
};

Do[
  Module[{diags, numDiags, ampAll, amps, couplingsAll, couplingDeltasAll,
          extIndexRules, ampsEval, ampDeltasAll, targetTopologies, ampsFiltered},
    Print["Process ", i, ": ", processes[[i]]];
    diags = InsertFields[
      tops,
      processes[[i]],
      Model -> "Phi4MatrixSK",
      GenericModel -> "Lorentz",
      InsertionLevel -> {Classes}
    ];
    Print["Inserted diagram expressions (raw):"];
    Print[diags];

    numDiags = Length[Cases[diags, Insertions[_][__], Infinity]];
    Print["Diagram selection"];
    Print["Number of inserted diagrams: ", numDiags];
    If[numDiags == 0,
      Print["No inserted diagrams found."];
      Continue[];
    ];

    (* Build amplitudes and extract FeynAmp objects *)
    ampAll = CreateFeynAmp[diags, AmplitudeLevel -> Classes];
    amps = Cases[ampAll, FeynAmp[__], Infinity];
    If[Length[amps] == 0,
      Print["No FeynAmp objects found."];
      Continue[];
    ];

    (* Coupling-level delta structure (from amplitudes) *)
    Print["Coupling-level IndexDelta (all diagrams)"];
    couplingsAll = (Cases[#, _C, Infinity] /. M$LastModelRules) & /@ amps;
    couplingDeltasAll = Cases[#, IndexDelta[__], Infinity] & /@ couplingsAll;

    Print["Couplings (VRA evaluated), per diagram:"]; 
    Do[
      Print["Diagram ", j, ": ", couplingsAll[[j]]],
      {j, Length[couplingsAll]}
    ];
    Print["IndexDelta terms in couplings, per diagram:"]; 
    Do[
      Print["Diagram ", j, ": ", couplingDeltasAll[[j]]],
      {j, Length[couplingDeltasAll]}
    ];

    (* Amplitude-level delta structure *)
    Print["Amplitude-level IndexDelta (all diagrams)"];
    extIndexRules = {
      SequenceForm["Con", 1] -> 1,
      SequenceForm["Con", 2] -> 1,
      SequenceForm["Con", 3] -> 2,
      SequenceForm["Con", 4] -> 2,
      SequenceForm["RAx", 1] -> r,
      SequenceForm["RAx", 2] -> a,
      SequenceForm["RAx", 3] -> r,
      SequenceForm["RAx", 4] -> a
    };
    ampsEval = (# /. extIndexRules /. M$LastModelRules) & /@ amps;
    ampDeltasAll = Cases[#, IndexDelta[__], Infinity] & /@ ampsEval;

    targetTopologies = {3, 5, 6};
    ampsFiltered = Select[
      ampsEval,
      MatchQ[#, FeynAmp[GraphID[Topology == t_, ___], ___] /; MemberQ[targetTopologies, t]] &
    ];

    Print["Amplitude (T3, T5, T6 only):"]; 
    If[Length[ampsFiltered] == 0,
      Print["No amplitudes found for T3, T5, T6."],
      Do[
        Print["Diagram ", j, ": ", ampsFiltered[[j]]],
        {j, Length[ampsFiltered]}
      ]
    ];

    Print["IndexDelta terms in amplitude (T3, T5, T6 only):"]; 
    If[Length[ampsFiltered] == 0,
      Print["No amplitudes found for T3, T5, T6."],
      Do[
        Print["Diagram ", j, ": ", Cases[ampsFiltered[[j]], IndexDelta[__], Infinity]],
        {j, Length[ampsFiltered]}
      ]
    ];
  ],
  {i, Length[processes]}
];
