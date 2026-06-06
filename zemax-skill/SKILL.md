---
name: zemax-skill
description: Use for practical Zemax OpticStudio automation and optical-design work through ZOS-API, including Python connection triage, standalone model generation, sequential lens optimization, custom merit-function construction, MTF/distortion validation, non-sequential component setup, detector data extraction, and turning optical requirements or existing .zmx/.zos/.zar files into repeatable design-analysis loops.
---

# Zemax Skill

Use this skill when a user wants Codex to operate like a practical Zemax/ZOS-API optical-design assistant: connect to OpticStudio, inspect or build files, construct merit functions, run staged optimization, extract analyses, and summarize whether the design actually satisfies requirements.

## Core Workflow

1. Establish API viability before optical work.
   - Prefer Standalone Application for batch file generation, optimization, and analysis.
   - Use Interactive Extension only when the user explicitly wants to modify a visible OpticStudio GUI session.
   - Run `scripts/zemax_connection_smoke.py --zos-root "<OpticStudio install root>" --standalone` when the local environment is uncertain.

2. Convert requirements into measurable targets.
   - Capture aperture, field, wavelength, EFL or magnification, track length, image/object conjugates, distortion, MTF frequency, spot/wavefront limits, clearances, glass constraints, and manufacturing limits.
   - Record units and whether angles are half-angle, full-angle, chief-ray angle, or field height.
   - Do a first-order feasibility pass before optimizing in Zemax.

3. Build or open the baseline model conservatively.
   - Preserve the user's original file; write generated variants to an output directory.
   - Create a structured run log with requirements, stage settings, and measured metrics.
   - For existing files, extract baseline prescription and metrics before changing variables.

4. Construct a dedicated merit function, not just generic focus operands.
   - Encode the user's actual targets: EFFL or PMAG, TOTR, MTF operands, distortion operands, field balance, glass/edge/center constraints, and ray/clear-aperture constraints.
   - Increase weights on edge fields when the real acceptance risk is corner performance.
   - Optimize in stages: feasibility, image quality, field balance, distortion/MTF push, manufacturability.

5. Validate after every stage.
   - Export or read MTF, spot, ray fan, wavefront, distortion, and prescription metrics.
   - Compare against the original requirements, not only against the merit value.
   - Report tradeoffs plainly: a lower merit value can still worsen distortion, manufacturability, or field balance.

## References

Load only the reference needed for the current request:

- `references/zos-api-patterns.md`: Python.NET, Standalone/Interactive connection, enum/cell access, analysis export, and recurring ZOS-API pitfalls.
- `references/optimization-workflow.md`: staged sequential-lens optimization, merit-function strategy, metrics, and lessons from failed/partial MTF pushes.
- `references/patent-reproduction-workflow.md`: patent-to-Zemax reproduction workflow, source-truth separation, model-glass material handling, stop/reference surface choices, and US10281683-specific lessons.
- `references/nsc-workflow.md`: non-sequential mode setup, NSCE object creation, detector extraction, and flux/pupil-validation workflow.

## Practical Defaults

- Use the bundled Python runtime if system `python` is missing.
- On this Windows workstation, a known working OpticStudio root was `D:\Program Files\ANSYS Inc\v251\Zemax OpticStudio`; still re-detect or accept the user's path before assuming it.
- Treat Standalone API success as the strongest signal for automation: valid app, valid license, and non-null `PrimarySystem`.
- If Interactive Extension connects but `IsValidLicenseForAPI` is false or `PrimarySystem` is missing, switch to Standalone for batch work.
- For patent reproductions, use Zemax Model glass solves when the patent discloses `n_d` and `V_d`; do not substitute catalog glasses unless the user asks for a manufacturable redesign.
- Never keep optimizing only because the merit improves. Stop and reassess if MTF, distortion, track length, or clearances move away from the specification.

## Reporting Contract

When finishing a Zemax task, report:

- connection mode and resolved OpticStudio root;
- input file and output file paths;
- exact constraints placed in the merit function;
- before/after metrics by field and wavelength where relevant;
- which requirements are satisfied, marginal, or failed;
- next optical-design move if the current structure cannot meet the target.
