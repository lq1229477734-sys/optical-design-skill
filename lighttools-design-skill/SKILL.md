---
name: lighttools-design-skill
description: Reproduce optical-design papers and build Synopsys LightTools models from paper geometry, freeform surface data, LED arrays, receivers, thin films, prism textures, and simulation audits. Use when Codex needs to automate LightTools through COM or JumpStart .NET, import freeform CSV surfaces into .lts models, reproduce figures from optical papers, construct LED/source/receiver setups, debug LightTools model stability, version .lts outputs, or document validated optical-design workflows.
---

# LightTools Design Skill

## Overview

Use this skill to turn an optical paper or processed surface dataset into a traceable LightTools model, then validate it with simulation outputs and an audit trail. The workflow is based on successful reproductions of two paper-style tasks in `D:\comsol`: a Figure 2 LED/angle-filter model with real sources and receiver meshes, and a Figure 14 Prism 3 / DBHM-style multilayer texture workflow.

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

4. Validate every saved model.
   - Open the generated `.lts` in LightTools and save a new versioned `.lts`.
   - Query object counts and key names through the database API.
   - Run a practical ray count first, export a receiver mesh or write an audit, then scale up.
   - Do not overwrite the last known-good `.lts`; use monotonically increasing suffixes.

5. Preserve traceability.
   - Copy source CSV/OBJ files into the model folder when importing surfaces.
   - Write an audit file with source paths, assumptions, object counts, LightTools statuses, and deviations from the paper.
   - Append successful commands and outputs to a project success log when one exists.

## Reference Selection

- Read `references/lighttools-com-automation.md` for COM connection, JumpStart setup, sources, receivers, mesh export, and versioning patterns.
- Read `references/freeform-surface-import.md` for importing two-surface freeform lenses from CSV data into FreeformSolid / Loft `.lts` models.
- Read `references/paper-reproduction-lessons.md` for paper-specific modeling lessons: Figure 2 source/receiver reproduction, Figure 14 prism textures, DBHM stability, material inheritance, and model-debugging rules.
- Read `references/LightTools_Macro_经验总结.md` when writing or debugging LightTools macros for parameter sweeps, object lookup by database keys, geometry/surface/pattern changes, receiver chart export, or macro-based simulation automation.

## Output Standard

Deliver a model folder that contains:

- The validated `.lts` output and, when useful, the raw generated `.lts`.
- The script used to generate or patch the model.
- Source data copies for reproducibility.
- Receiver mesh CSV/plots or simulation summaries when a ray trace was run.
- An audit text file naming every assumption, validation status, and known limitation.

When LightTools is unavailable, still produce the script and raw model edits, but clearly mark validation as pending.
