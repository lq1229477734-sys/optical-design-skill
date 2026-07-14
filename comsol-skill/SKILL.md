---
name: comsol-skill
description: Automate COMSOL Multiphysics Wave Optics thin-film models and scans through Java batch execution, including isotropic and anisotropic multilayers, explicit rotated permittivity tensors, periodic unit cells, normal-incidence LCP/RCP sources, receiver power integration, wavelength sweeps, result export, plotting, and geometry/mesh/debug validation. Use when Codex must create, modify, solve, or audit COMSOL .mph optical models; reproduce thin-film spectra from papers; diagnose invisible geometry, wrong source/receiver boundaries, nonphysical transmission, missing circular dichroism, slow sweeps, or anisotropic tensor errors; or produce COMSOL-derived CSV and figures without GUI computer control.
---

# COMSOL Wave Optics

Build reproducible COMSOL models through Java API and `comsolbatch`. Prefer deterministic batch files over GUI automation.

## Core Workflow

1. Locate COMSOL executables and confirm the installed version.
2. Inspect the open or supplied `.mph` model before modifying it. Preserve unrelated user content.
3. Translate the optical stack into explicit domains, named selections, materials, physics, mesh, study, and result expressions.
4. Build geometry first and verify domain, boundary, and edge IDs before assigning physics.
5. Run a coarse 21-33 point wavelength scan. Require completion within minutes before increasing resolution.
6. Validate physical invariants and expected spectral features.
7. Run the final scan, normally 101-201 points, then export COMSOL results and plot them.
8. Save the base model and each solved polarization model separately.

For twisted anisotropic films or paper reproduction, read [references/anisotropic-thin-films.md](references/anisotropic-thin-films.md) before editing code. For command construction and diagnostics, read [references/comsol-batch-workflow.md](references/comsol-batch-workflow.md).

## Model Construction Rules

- Create each optical layer as its own domain. Assign materials with explicit domain selections.
- Put the incident boundary above the stack and the transmission receiver below it for normal incidence.
- Use `Box` selections with `condition=inside`; the default intersection behavior can silently select side boundaries.
- Measure final geometry entities after unions. Never assume IDs remain stable after geometry changes.
- Use scattering boundaries for incident and outgoing plane waves when periodic ports are unreliable.
- For propagation toward `-z`, use a circular source such as `E0i={1/sqrt(2), pol*i/sqrt(2), 0}` with `pol=+1/-1`.
- Integrate transmitted power on the bottom receiver with `Ptrans=-intop_rx(ewfd.Poavz)`.
- Normalize by incident plane-wave power over the unit-cell area.
- Use periodic continuity on corresponding side boundaries at normal incidence.

## Anisotropic Material Rules

- Convert paper Lorentz models to COMSOL's time convention. With COMSOL's `exp(+i*omega*t)` convention, passive loss requires `Im(epsilon)<0`; use the conjugated damping sign when the paper assumes `exp(-i*omega*t)`.
- Prefer an explicit full 3-by-3 rotated tensor over implicit material coordinate-system rotation when circular dichroism matters.
- For an in-plane rotation `theta`, construct:

```text
eps_xx = eps_x*cos(theta)^2 + eps_y*sin(theta)^2
eps_yy = eps_x*sin(theta)^2 + eps_y*cos(theta)^2
eps_xy = (eps_x-eps_y)*sin(theta)*cos(theta)
```

- Supply the full tensor in COMSOL order: `{xx,xy,xz,yx,yy,yz,zx,zy,zz}`.
- Do not accept numerically identical LCP/RCP spectra when the reference predicts circular dichroism. Check the off-diagonal tensor first.

## Fast Mesh Strategy

For laterally uniform films under normal incidence, avoid resolving the entire 5-by-5 um area at subwavelength lateral spacing.

- Map the bottom face.
- Sweep the mapped mesh through all stacked domains.
- Keep several elements through each film thickness.
- Start with roughly 5-by-5 lateral cells and 3-5 elements per layer.
- Confirm mesh quality and run a convergence check near important peaks.

The validated alpha-MoO3 example reduced the model from 18,750 elements and 467,161 DOF to 300 swept elements and 8,404 DOF. A 161-point polarization scan then took about 41 seconds instead of more than a day.

## Validation Gates

Do not report a scan as successful until all applicable checks pass:

- Geometry is visible and layer dimensions are correct.
- Source and receiver are on opposite horizontal exterior boundaries.
- Material domains are distinct and complete.
- Mesh has positive quality and enough thickness resolution.
- Every frequency converges.
- Passive structures satisfy approximately `0 <= T <= 1`; investigate values above 1 before plotting.
- LCP/RCP definitions are recorded.
- Expected symmetry limits hold, such as zero CD for aligned or mirror-symmetric stacks.
- Reference peak positions are reproduced within the resolution and modeling assumptions.
- Exported tables contain numeric rows, not only headers.

Never label transfer-matrix or synthetic data as COMSOL output. Keep provenance explicit.

## Bundled Scripts

- `scripts/CreateTwistedAMoO3ComsolScan.java`: validated 5-by-5 um, two-layer alpha-MoO3, 45-degree, 8-24 um model template.
- `scripts/InspectGeometryEntities.java`: print final boundary and edge measures before hard-coding selections.
- `scripts/ExportComsolTransmission.java`: export `Tcomsol` from solved LCP/RCP models; configure paths with environment variables.
- `scripts/plot_comsol_transmission.py`: combine exported tables into CSV and publication-ready PNG/SVG/PDF plots.

Copy scripts into the active workspace before modifying them. Keep generated `.class`, `.mph`, recovery, preference, and plot-cache files out of the skill repository.

## Expected Deliverables

Return:

- Base `.mph` model.
- Solved LCP and RCP `.mph` files when polarization comparison is requested.
- Combined CSV with wavelength, frequency, both transmissions, signed difference, and absolute CD.
- PNG plus editable SVG or PDF plot.
- Concise audit containing geometry, material model, polarization convention, mesh size/DOF, solve time, and validation results.
