# calc_mbcwc

Research workspace for matrix phi^4 Schwinger-Keldysh (SK) calculations using FeynArts/Wolfram tools. The repo contains model files, Wolfram Language scripts for generating diagrams and amplitudes, and supporting notes/output.

## Contents
- `models/` FeynArts model files (`.mod`) for phi^4 matrix and SK variants.
- `scripts/` Wolfram Language (`.wls`) and Mathematica notebooks for diagram generation, insertions, and amplitude inspection.
- `plans/` Implementation notes/plans for script variants.
- `source/` Reference PDFs/TeX sources.
- `output/` Generated outputs (kept intentionally simple).
- `old/` Archived or superseded work.
- `basic_formulas.tex` and `basic_formulas.pdf` Background notes.

## Prerequisites
- Wolfram Language / WolframScript installed.
- FeynArts 3.11 installed locally.
- Local model path configured to point to `models/`.

## Running scripts
Most scripts assume an absolute FeynArts install path and a local model path. Example from `scripts/calc_correlator_v4.wls`:

- `AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];`
- `$ModelPath = Append[$ModelPath, "/home/lev/Projects/calc_mbcwc/models"];`

Update these paths to match your machine before running.

Run a script with:

```bash
wolframscript -file scripts/calc_correlator_v4.wls
```

## Notes
- Scripts typically generate 1-loop 2->2 topologies and insert fields for the `Phi4MatrixSK` model.
- Some scripts permute external field assignments and filter nonzero amplitudes for specific topologies (e.g. ladder topologies).
- Plans in `plans/` describe the intended behavior of specific script versions.

## Quick start
1. Install FeynArts 3.11 and ensure WolframScript is available.
2. Update the FeynArts and model paths in the script you want to run.
3. Execute with `wolframscript -file <script>`.

## License
No explicit license is currently defined.
