# Patent Reproduction Workflow

Use this workflow when turning an optical patent into a Zemax model. The goal is
traceable reproduction first, not immediate performance optimization.

## 1. Separate Source Truth From Modeling Choices

Create a prescription table that records exactly what the patent discloses:

- radius, thickness, element, surface, and comments;
- conic and asphere coefficients with source table/page references;
- material values as disclosed;
- clear aperture or semi-diameter, if disclosed;
- stop, filter, cover glass, and sensor positions.

Record every modeling choice that is not explicitly disclosed. Examples:

- dummy/reference surfaces;
- chosen semi-diameters when the patent only shows a drawing;
- temporary profile fixes made to avoid layout overlap;
- approximated filter or sensor thickness.

## 2. Materials: Prefer Model Glass For Patent Values

If a patent gives `n_d` and `V_d`, use a Zemax Model glass solve instead of a
nearby catalog glass. A catalog substitution changes the design and should be
reserved for manufacturable redesign.

ZOS-API pattern:

```powershell
$solve = $surface.MaterialCell.CreateSolveType([ZOSAPI.Editors.SolveType]::MaterialModel)
$solve.IndexNd = 1.545
$solve.AbbeVd = 56.0
[void]$surface.MaterialCell.SetSolveData($solve)
```

Verify by reloading the saved file:

```powershell
$data = $surface.MaterialCell.GetSolveData()
$surface.MaterialCell.Solve
$data.IndexNd
$data.AbbeVd
```

Do not rely only on assigning `surface.Material = "MODEL 1.545 56.0 0.0"`.
That can leave the Zemax UI model-glass fields at zero on some versions.

## 3. Stop Placement And Reference Surfaces

Preserve surface semantics. If the patent places the aperture stop at a location
near a lens edge, introduce a dummy/stop surface rather than converting the lens
front surface itself into the stop.

Useful pattern:

- object surface;
- dummy reference surface;
- independent STOP surface;
- optical lens front surface.

This allows the stop to sit near a sagged rim plane while the optical surface
remains physically meaningful.

## 4. Geometry Sanity Before Ray Quality

Before optimizing, inspect:

- total track length and image plane;
- lens center thickness and edge thickness;
- air gaps and filter/sensor clearance;
- surface sag at the chosen semi-diameter;
- whether the drawing and layout are qualitatively consistent.

Patent drawings are not exact sag plots, but obvious contradictions are useful
warning signs. Recheck table extraction, clear apertures, and sign conventions
before trusting the model.

## 5. Baseline First, Optimization Later

The first Zemax file should be a baseline:

- correct aperture type;
- correct fields and wavelengths;
- correct materials;
- correct stop and sensor/filter positions;
- no broad optimization variables.

Only after baseline analysis should variables be enabled.

## 6. Recommended Optimization Stages

1. Structure protection: constrain total track, center/edge thickness, air
   spaces, and filter clearance.
2. Gentle image quality: optimize d-line only at moderate frequency, usually
   before pushing all F/d/C wavelengths.
3. Field balance: increase edge-field weights and watch distortion.
4. Color and final MTF: introduce F/d/C and higher MTF targets.

Never report merit value alone. Include prescription deltas, MTF/spot/distortion
comparison, and whether the optimized layout still resembles the patent.

## 7. US10281683-Specific Notes

For US10281683B2 lens system 110:

- L1/L3/L5/L6: `n_d = 1.545`, `V_d = 56.0`.
- L2/L4: `n_d = 1.661`, `V_d = 20.4`.
- Filter: `n_d = 1.517`, `V_d = 64.2`.
- Use F/d/C wavelengths and make the d line primary.
- Use entrance pupil diameter for the aperture.
- Preserve the independent stop near the L1 front rim plane; do not turn the L1
  front surface into the STOP.
