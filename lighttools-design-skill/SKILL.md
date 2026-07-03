---
name: lighttools-design-skill
description: Reproduce optical-design papers and build Synopsys LightTools models from paper geometry, freeform surface data, LED arrays, receivers, thin films, prism textures, distance/geometry sweeps, angular or spatial luminance meshes, and simulation audits. Use when Codex needs to automate LightTools through COM or JumpStart .NET, attach to an already-open GUI session with unsaved edits, modify named optical-property percentages, import freeform CSV surfaces into .lts models, reproduce figures from optical papers, construct LED/source/receiver setups, run colli1_lc double-length or ray-trace-state scans, vary spatial luminance meter latitude, export BLUReceiver meshes, post-process LightTools TXT files, debug model stability, version .lts outputs, or document validated optical-design workflows.
---

# LightTools Design Skill

## Overview

Use this skill to turn an optical paper, processed surface dataset, or local LightTools scan task into a traceable LightTools model and validated output set. The workflow is based on successful work in `D:\comsol`: Figure 2 LED/angle-filter models with receiver meshes, Figure 14 Prism 3 / DBHM-style texture debugging, 6x6 freeform LED arrays, and distance-series angular luminance sweeps.

## Workflow

1. Extract the paper prescription before touching LightTools.
   - Capture geometry, pitch, material, source size, ray count, receiver position, mesh type, and figure/table provenance.
   - Record unknowns explicitly instead of silently filling them in.
   - Prefer a smaller verification model before full-resolution geometry.

2. Choose the modeling route.
   - For surface sources, receivers, ray trace settings, and object transforms, use LightTools COM plus JumpStart .NET.
   - For dense freeform surfaces, start from a known LightTools FreeformSolid template and replace `restorePoints` blocks, then ask LightTools to open and re-save the raw model.
   - For fragile or unsupported texture states, patch `.lts` text only when COM/JumpStart cannot express the operation, then validate by opening and saving in LightTools.

3. Automate with PowerShell wrappers.
   - LightTools COM and JumpStart interop strings often need `[ref]`.
   - Wrap `Cmd`, `Str`, `SetOption`, `DbList`, `ListSize`, `ListAtPos`, and `DbGet` before building complex scripts.
   - Disable dialogs before batch operations: `ShowDialogs`, `ShowFileDialogBox`, and `ConfirmDeleteModel`.
   - For an already-open GUI model, auto-detect an attachable PID with `LTLocator.Locator` and verify target solids before changing state.

4. Validate every saved model.
   - Open the generated `.lts` in LightTools and save a new versioned `.lts`.
   - Query object counts and key names through the database API.
   - Run a practical ray count first, export a receiver mesh or write an audit, then scale up.
   - Do not overwrite the last known-good `.lts`; use monotonically increasing suffixes.

5. For scan workflows, keep model edits, simulation runs, and post-processing separate.
   - Patch text only for properties the COM database cannot expose safely.
   - Use COM/JumpStart for geometry `LENGTH` sweeps and receiver mesh export.
   - Post-process exported TXT meshes with reusable scripts, not hand-edited spreadsheets.
   - Compare hashes when model edits appear to produce unchanged results.

6. Preserve traceability.
   - Copy source CSV/OBJ files into the model folder when importing surfaces.
   - Write an audit file with source paths, assumptions, object counts, LightTools statuses, and deviations from the paper.
   - Append successful commands and outputs to a project success log when one exists.

## Reference Selection

- Read `references/lighttools-com-automation.md` for COM connection, JumpStart setup, sources, receivers, mesh export, and versioning patterns.
- Read `references/freeform-surface-import.md` for importing two-surface freeform lenses from CSV data into FreeformSolid / Loft `.lts` models.
- Read `references/paper-reproduction-lessons.md` for paper-specific modeling lessons: Figure 2 source/receiver reproduction, Figure 14 prism textures, DBHM stability, material inheritance, and model-debugging rules.
- Read `references/distance-scan-workflow.md` for `distance.*.lts`, `colli1_lc_1` / `colli1_lc_2` sweeps, `ec_t` transmittance patches, `BLUReceiver` angular luminance mesh export, and 61x61 TXT post-processing.
- Read `references/spatial-luminance-angle-workflow.md` for active-model snapshots, ECT transmittance and ray-trace-state audits, correct spatial luminance meter `Lat/Long` geometry, L=0/L=45 runs, and 600x600 mesh comparison.
- Read `references/lighttools-com-open-verification.md` when patched `.lts` models opened through COM produce unchanged TXT hashes, when filenames contain extra dots, or when you need to prove the active LightTools model before a full sweep.
- Read `references/LightTools_Macro_经验总结.md` when writing or debugging LightTools macros for parameter sweeps, object lookup by database keys, geometry/surface/pattern changes, receiver chart export, or macro-based simulation automation.

- Read `references/active-session-double-length-workflow.md` for elevated active-session attachment, automatic PID discovery, ECT/`ec_t` percentage editing, `colli1_lc_1` / `colli1_lc_2` sweeps, standalone process3 processing, and numeric matrix validation.

## Output Standard

Deliver a model folder that contains:

- The validated `.lts` output and, when useful, the raw generated `.lts`.
- The script used to generate or patch the model.
- Source data copies for reproducibility.
- Receiver mesh CSV/plots or simulation summaries when a ray trace was run.
- An audit text file naming every assumption, validation status, and known limitation.
- For sweeps, the versioned `.lts`, scan script, raw TXT mesh outputs, processed CSV/PNG/PDF summaries, and a short hash/validation note.

When LightTools is unavailable, still produce the script and raw model edits, but clearly mark validation as pending.
