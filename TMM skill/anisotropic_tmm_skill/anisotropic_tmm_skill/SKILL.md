---
name: tmm-skill
description: Build, review, and debug transfer-matrix and Berreman optical simulations for isotropic and anisotropic multilayer films, DBRs, liquid-crystal stacks, rotated optical axes, polarization conversion, and pyllama-based thin-film workflows.
---

# TMM Skill

## Purpose

Help the user build, inspect, and revise transfer-matrix simulations for multilayer optical films, distributed Bragg reflectors, anisotropic thin films, liquid-crystal layers, and structures with rotated optical axes. Prioritize physically correct definitions, numerical stability, and interpretable reflection/transmission outputs.

## Default Physical Conventions

Unless the user explicitly asks for different conventions, use these defaults:

- The layer normal is the positive z direction.
- Light propagates from the entry half-space toward the exit half-space along positive z.
- The plane of incidence is the x-z plane.
- s-polarized electric field is along y.
- p-polarized electric field lies in the x-z plane.
- The tangential wave vector is `Kx = n_entry * sin(theta_in)` and `Ky = 0`.
- Wavelengths and layer thicknesses use the same length unit, preferably nm.

If the user says that the x direction is the s-polarization direction, do not blindly swap s and p in the default formulas. Explain that this skill's default convention uses s along y. If the physical sample uses s along x, rotate the material tensor or sample coordinates into the simulation coordinates, or redefine the incidence plane as y-z.

## Method Selection

### Use 2x2 TMM When

Use separate 2x2 transfer matrices for s and p only when every layer is isotropic and there is no polarization conversion.

The isotropic dielectric tensor is:

```text
epsilon = diag(n^2, n^2, n^2)
```

### Use 4x4 Berreman When

Use a 4x4 Berreman method when any of the following are present:

- `nx != ny` or `ny != nz`.
- The optical axis is rotated relative to the laboratory coordinates.
- A liquid-crystal director changes with z.
- A twisted nematic, cholesteric, or sliced rotated structure is modeled.
- Cross-polarized terms are needed, such as `R_s_to_p` or `T_p_to_s`.
- The user cares about anisotropic DBRs, polarization-selective reflection, or s/p coupling.

## Modeling Workflow

1. Ask for or infer the material parameters: `n`, or `nx`, `ny`, and `nz`.
2. Express every material as a 3x3 dielectric tensor:

```python
eps_iso = np.diag([n**2, n**2, n**2])
eps_aniso = np.diag([nx**2, ny**2, nz**2])
```

3. If a layer is rotated, use:

```python
eps_rot = R @ eps @ R.T
```

4. Build the layer list so that the first layer is the first physical layer reached by incident light.
5. Keep thickness and wavelength units consistent.
6. For many-period or high-reflectivity DBRs, prefer a scattering-matrix method, such as `method="SM"` in pyllama, to avoid numerical overflow.
7. Report total s/p reflectance and transmittance, not only diagonal matrix elements.

## Interpreting pyllama Output

Interpret the linear-polarization reflection and transmission matrices as:

```text
R = [[R_p_to_p, R_s_to_p],
     [R_p_to_s, R_s_to_s]]

T = [[T_p_to_p, T_s_to_p],
     [T_p_to_s, T_s_to_s]]
```

Therefore:

```python
R_p_total = R[0, 0] + R[1, 0]
T_p_total = T[0, 0] + T[1, 0]
R_s_total = R[0, 1] + R[1, 1]
T_s_total = T[0, 1] + T[1, 1]
```

When the user asks only for ordinary s/p curves, provide these total quantities by default.

## Required Sanity Checks

Before giving final code or conclusions, include as many of these checks as are relevant:

1. For lossless stacks, verify `R_s + T_s ~= 1` and `R_p + T_p ~= 1`.
2. In the isotropic limit `nx = ny = nz`, verify that 4x4 results agree with 2x2 TMM.
3. In the zero-thickness limit, verify that the result reduces to a single entry/exit Fresnel interface.
4. Confirm that rotating an isotropic layer does not change the result.
5. Confirm that increasing DBR period count increases stop-band reflectance and sharpens band edges.

## Common Mistakes To Prevent

- Do not put refractive index directly into the dielectric tensor; use `n**2`.
- Do not mix micrometers and nanometers.
- Do not use only `R[0,0]` or `R[1,1]` as the total reflectance when polarization conversion exists.
- Do not use 2x2 TMM for rotated anisotropic layers.
- Do not ignore the transmittance power-flow correction, especially for oblique incidence or different entry/exit refractive indices.
- Do not discuss whether x is the s-polarization direction until the coordinate system and incidence plane are defined.

## Recommended Response Structure

When the user asks for code, respond in this order:

1. State the coordinate system and physical assumptions briefly.
2. Provide complete runnable Python code.
3. Define `R_s`, `T_s`, `R_p`, and `T_p` explicitly.
4. If cross-polarization exists, explain how total quantities are summed.
5. Include an energy-conservation or physical-limit check.
6. For plots, prefer wavelength curves such as `R_s`, `R_p`, `T_s`, and `T_p`, or angle-wavelength maps where color represents R or T.
7. For complex anisotropic structures, remind the user to check convergence with slicing density and layer count.

## Recommended Code Snippets

```python
import numpy as np


def eps_iso(n):
    return np.diag([n**2, n**2, n**2])


def eps_aniso(nx, ny, nz):
    return np.diag([nx**2, ny**2, nz**2])


def rot_z(phi):
    c, s = np.cos(phi), np.sin(phi)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def rotate_eps(eps, R):
    return R @ eps @ R.T
```
