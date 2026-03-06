# Project Notes For Codex Agents

## Wolfram Runtime
- Prefer `WolframKernel -script` for project Wolfram jobs.
- Do not rely on `wolframscript` for this repository's runtime pipeline unless you have re-verified it in the current environment.
- In this environment, `wolframscript` can hang even on a trivial command like `wolframscript -code 'Print[2+2]'`.
- `WolframKernel` is the known working path for `scripts/generate_all_loop_topologies.wls` and for the dynamic topology-generation pipeline.

## Dynamic Topology Generation
- `scripts/calc_commutator_contrib_dynamic.py` should launch the Wolfram step via `WolframKernel` when available.
- `scripts/generate_all_loop_topologies.wls` is expected to support arguments both from `wolframscript` and from `WolframKernel -script`.
- Keep generated outputs in the current working directory under this repository, not in `/tmp`, unless the user explicitly asks for a temporary output path.
- If end-to-end generation is slow, verify progress by checking:
  - generated image directory contents
  - generated `all_L_<L>.txt`
  - Python stdout for topology-processing progress
