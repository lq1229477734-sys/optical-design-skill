# Anisotropic Thin-Film Reference

## Alpha-MoO3 Lorentz Model

The validated twisted-bilayer example uses principal relative permittivities

```text
epsilon_j = epsilon_inf,j * [1 + (omega_LO,j^2 - omega_TO,j^2)
            / (omega_TO,j^2 - omega^2 + i*omega*gamma_j)]
```

for COMSOL's `exp(+i*omega*t)` convention. The plus sign before `i*omega*gamma` produces passive loss with negative imaginary permittivity in this convention.

Parameters used for the 8-24 um reproduction:

| Axis | epsilon_inf | omega_LO (rad/s) | omega_TO (rad/s) | gamma (rad/s) |
| --- | ---: | ---: | ---: | ---: |
| x | 4.0 | 1.8322e14 | 1.5457e14 | 7.5398e11 |
| y | 5.2 | 1.6041e14 | 1.0273e14 | 7.5398e11 |
| z | 2.4 | 1.8925e14 | 1.8058e14 | 3.7699e11 |

Always verify these values against the user's cited paper before treating them as authoritative for another dataset or sample.

## Explicit Rotation

For a rotation around z by `theta`, use the global tensor

```text
[ ex*c^2 + ey*s^2, (ex-ey)*s*c, 0 ]
[ (ex-ey)*s*c, ex*s^2 + ey*c^2, 0 ]
[ 0,             0,              ez ]
```

where `c=cos(theta)` and `s=sin(theta)`. Reversing the sign of the off-diagonal terms changes handedness labeling but not the absolute CD.

Implicit rotated coordinate systems may appear valid while leaving LCP and RCP total transmission identical. Use the explicit tensor for fragile polarization calculations.

## Circular Polarization Convention

For a wave launched from the top and propagating toward `-z`, the template uses

```text
E = (x + pol*i*y)/sqrt(2), pol=+1 or -1
```

Record which sign is called LCP. Handedness labels depend on the viewing and time-harmonic convention; if comparing line colors with a paper, confirm its convention. Absolute CD is invariant to swapping labels.

## Expected Reproduction Check

For two 1 um alpha-MoO3 layers with a 45 degree relative rotation, normal incidence, and the parameters above, a correct model should show strong LCP/RCP separation near 14.4 um and 20.3 um. A validated 161-point COMSOL run gave approximately:

- CD = 0.3205 near 14.436 um.
- CD = 0.3117 near 20.211 um.

These values are regression targets for the template, not universal material constants.

## Failure Signatures

### Transmission exceeds one

Likely causes:

- Lorentz damping sign produces gain.
- Incident-power normalization is wrong.
- Receiver integration sign or boundary is wrong.
- The receiver includes incident or reflected power.

### LCP and RCP agree to machine precision

Likely causes:

- Top tensor was not rotated.
- Off-diagonal components were omitted.
- `pol` was not included in the source expression or parameter sweep.
- Symmetry is genuinely present; test a known chiral angle before concluding this.

### Geometry exists but is not visible

Likely causes:

- The final geometry was not built.
- The saved model differs from the file opened by the user.
- Results view hides geometry.
- Geometry dimensions or units are wrong.
- A selection was built but no solid feature was created.

### Anisotropic tensor error

Set the Wave Equation feature to relative permittivity from material and a global coordinate system. Supply either a diagonal 3-entry tensor aligned to global axes or a full 9-entry tensor.
