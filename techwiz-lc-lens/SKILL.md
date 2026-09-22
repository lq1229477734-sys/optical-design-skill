---
name: techwiz-lc-lens
description: Build, modify, troubleshoot, and post-process TechWiz LCD 3D v15 liquid-crystal cylindrical-lens projects, including GRIN/TN/segmented-electrode designs, voltage sweeps, OPD/focal-length/parabolic-error analysis, and step-response analysis. Use for TechWiz .prj/.str/.elt/.stk/.sdb projects and binary LC result files; do not use for unrelated optical solvers or generic LC theory alone.
---

# TechWiz LC Lens

Produce a traceable TechWiz project, preserve the validated file-format conventions, and separate generated inputs from solver-produced evidence. Communicate in the user's language and always report physical quantities with units.

## Choose the operating mode

- For a new or parameterized planar LC cylindrical lens, read [references/configuration.md](references/configuration.md), then use `scripts/new_lc_lens_project.py` with a TechWiz-validated template.
- For file-format edits, materials, or GUI mismatch errors, read [references/file_formats.md](references/file_formats.md).
- For electrode design choices or comparison with the supplied benchmark cases, read [references/designs_and_results.md](references/designs_and_results.md). Treat those results as case-specific evidence, not universal performance.
- For completed LC director results, run `scripts/analyze_lens.py --help` or `scripts/analyze_response.py --help` and inspect their CSV/text outputs.

## Non-negotiable invariants

- TechWiz LCD 3D v15 has no verified command-line solver in this workflow. Generate and inspect project files programmatically, but have the user run Mesh Generation and LC/Optical Analysis in TechWiz unless a separately verified automation path is available.
- Do not synthesize a `.str` from an undocumented format. Start from a Layout-generated or previously solved template; the included generator changes only the proven planar-lens structure.
- Keep units explicit: `.str` coordinates/thicknesses are metres; JSON geometry is µm; `.elt` uses V; `.sdb` uses s/V; `.stk` uses µm/deg; result time tags are ms.
- Preserve CRLF for TechWiz text files. Ensure `.prj` rubbing-zone names exactly match `.str` `ZONE NAME` values.
- Keep `BOT_COM = DC 0`, exactly one non-DC `Main` electrode, and all polygons belonging to one electrical node inside the same `ELECTRODE` block.
- Refuse to overwrite generated project inputs unless the target has been reviewed and the caller explicitly passes `--force`. Never delete solver results as part of generation.
- A generated project is not a validated simulation. Record the template, configuration, TechWiz log status, convergence, selected time step, and result files used for every reported result.

## Project workflow

1. Establish requirements: pitch/aperture, LC gap and material tensor, alignment, electrode grouping, wavelength/polarization, drive waveform, mesh, steady-state duration, and metrics.
2. Reuse a TechWiz-opened template compatible with the intended cell. Use the generator only for the supported planar uniform-alignment layout; use Layout's native GDS/TDB → electrode properties → SIM → 3D Structure Generation path for TN or materially different geometry.
3. Generate into a new directory. Diff `.str`, `.elt`, `.prj`, `.stk`, and `.sdb` against the template before opening TechWiz.
4. Ask the user to open the generated `.prj`; run Mesh Generation; verify X/Y periodic boundaries, layer count, material assignment, zone names, and nonzero electrode count.
5. In LC Analysis, verify `BOT_COM`, one `Main` sweep/signal electrode, DC sub-electrodes, time settings, and signal selection. If TechWiz 15 ignores a prewritten `.elt`, re-enter the table and use **Save as… Electrode Information File** to overwrite the intended INPUT file.
6. Inspect the `.log` for mismatch or convergence errors. Do not report low-voltage or unfinished points as valid simply because files exist.
7. Run the postprocessor and report both optical performance and evidence quality. Keep raw results outside the skill repository.

## Verified GUI conventions

- Baseline planar-lens mesh: X/Y periodic, `Mesh_Length = 1.5 µm`, `Mesh_Length_Max = 3 µm`, LC 16 layers. These are starting values, not convergence proof; tighten them and compare metrics for new geometries.
- A 25 µm cell can require 0.5–1 s to relax. The validated baseline uses `TimeFinal = 1 s`, `TimeStep = 1 ms`; a 30 ms run is generally not steady state. `SWEEP(SATURATION)` may stop early when its criterion is satisfied.
- For the uniform planar lens, top and bottom alignment `2°/90°` gives a Y-directed state. For the validated material's input polarizer, `Phi` is the absorption axis: `Phi = 0°` passes Y polarization. Stack order is top-to-bottom, so the input polarizer appears below `LC_Cell` in the file.
- For a 90° TN cell, use the verified native-layout workflow and the intended crossed-polarizer stack; do not reuse the uniform-alignment generator without re-deriving alignment and polarization.
- Threshold-adjacent points may fail to converge. Treat the threshold as material/geometry dependent; the approximately 1.5 V observation applies only to the supplied benchmark material.

## Post-processing contract

`analyze_lens.py` reads `<project>_MESH.dat` and voltage-tagged director files. For Y-polarized normal incidence it uses

`1 / n_eff² = n_z² / n_o² + (1 - n_z²) / n_e²`

then integrates `OPD(x) = ∫(n_eff - n_o) dz` and fits `OPD = c0 + c2 x²` inside the configured aperture. It reports OPD depth, phase in waves, `f = -1/(2c2)`, normalized parabolic RMSE, OPD RMSE, and centre/edge indices. Confirm this polarization/index model before applying the script to TN, biaxial, oblique-incidence, or polarization-converting cases.

`analyze_response.py` uses OPD depth and linear interpolation for 10–90% rise and 90–10% decay. It reads switch times from generated signal metadata or explicit CLI options. Extend the simulated time if the response never reaches the thresholds; do not substitute the final sample for a missing crossing.

## Reporting

Include:

- project/config/template identity and TechWiz version;
- geometry, LC material, alignment, electrode voltages, wavelength/polarization, mesh, and simulated duration;
- a table of voltage, final time, OPD depth, phase waves, focal length, and normalized RMSE;
- response crossings and averaging windows when applicable;
- convergence failures, stale/missing outputs, assumptions, and whether mesh/time convergence was actually tested;
- a comparison baseline only when geometry, material, wavelength, aperture, and metric definition are comparable.
