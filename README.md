# calc_mbcwc

Research workspace for matrix phi^4 Schwinger-Keldysh (SK) calculations using
FeynArts/Wolfram tools and a growing Python benchmark pipeline. The repository
contains model files, Wolfram Language scripts for generating diagrams and
amplitudes, Python checks for the Stanford phi^4 benchmark, and organized
research notes/output.

## Contents
- `models/` FeynArts model files (`.mod`) for phi^4 matrix and SK variants.
- `scripts/` Wolfram Language (`.wls`) and Python scripts for diagram generation, insertions, amplitude inspection, and the Stanford benchmark.
- `notebooks/mathematica/` Mathematica notebooks that were previously mixed into `scripts/`.
- `docs/journal/` dated project status entries, including the compiled 2026-05-20 journal PDF.
- `docs/notes/` background notes such as `basic_formulas.tex` and `basic_formulas.pdf`.
- `docs/plans/` implementation notes/plans for script variants.
- `source/` reference PDFs/TeX sources used by the calculation audit.
- `output/` active generated-output directory for new runs.
- `artifacts/` archived generated outputs and LaTeX build byproducts.
- `runs/` named run records for reproducible benchmark or commutator studies.
- `references/` paper-specific reference material.
- `src/` reserved for importable Python package code as the pipeline grows.
- `tests/` current Python regression tests.
- `check_calculation/` existing claim-audit workspace; kept in place because tests and references use its paths.
- `old/` Archived or superseded work.
- `legacy/` scratch or odd historical files retained without deletion.

## Prerequisites
- Wolfram Language installed. Prefer `WolframKernel -script` in this repository.
- FeynArts 3.11 installed locally.
- Local model path configured to point to `models/`.

## Running scripts
Most scripts assume an absolute FeynArts install path and a local model path. Example from `scripts/calc_correlator_v4.wls`:

- `AppendTo[$Path, "/home/lev/Projects/mathematica/FeynArts-3.11"];`
- `$ModelPath = Append[$ModelPath, "/home/lev/Projects/calc_mbcwc/models"];`

Update these paths to match your machine before running.

Run a script with:

```bash
WolframKernel -script scripts/calc_correlator_v4.wls
```

## Notes
- Scripts typically generate 1-loop 2->2 topologies and insert fields for the `Phi4MatrixSK` model.
- Some scripts permute external field assignments and filter nonzero amplitudes for specific topologies (e.g. ladder topologies).
- Plans in `docs/plans/` describe the intended behavior of specific script versions.
- Historical generated output was moved to `artifacts/legacy_output/output_2026-05-20/`; new generated output should continue to use `output/`.

## Quick start
1. Install FeynArts 3.11 and ensure `WolframKernel` is available.
2. Update the FeynArts and model paths in the script you want to run.
3. Execute with `WolframKernel -script <script>`.
4. Run the Python benchmark with `python3 -m unittest tests/test_stanford_phi4_kernel.py`.

## License
No explicit license is currently defined.
