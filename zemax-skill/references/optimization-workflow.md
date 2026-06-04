# Sequential Optimization Workflow

## Requirement Normalization

Before touching Zemax variables, normalize the optical brief into numeric targets:

- conjugates: finite/infinite, object distance, image distance, target magnification or EFL;
- system envelope: total track, back focal length, stop position, clear apertures;
- performance: MTF frequency and threshold, RMS spot, wavefront, distortion, field balance;
- fields and wavelengths: explicit field indices, angles/heights, wavelength weights;
- manufacturability: glass set, min/max center and edge thickness, air gaps, radii, element diameters.

If the baseline file exists, measure baseline performance first. The baseline is the control for every later claim.

## Staged Optimization

Use stages instead of one large undifferentiated optimization:

1. Feasibility: focus, conjugates, approximate EFL/PMAG, total track, no obvious invalid geometry.
2. Image quality: spot/wavefront/ray fan and moderate MTF targets.
3. Field balance: raise edge-field weights and prevent center-only improvement.
4. Distortion and MTF push: add strong distortion operands while pushing the relevant MTF frequency.
5. Manufacturability: tighten thickness, air gap, glass, diameter, and clearance constraints.

After each stage, export raw analyses and a compact metric summary.

## Merit Function Strategy

Include first-order constraints when they matter:

- `EFFL` for focal length;
- `PMAG` for finite-conjugate magnification;
- `TOTR` for total track.

Include geometry constraints early:

- `MNCT`, `MXCT` for center thickness;
- `MNET` for edge thickness;
- `MNCG`, `MXCG` for air gaps or clearances;
- aperture and diameter constraints where the design is mechanically bounded.

Use MTF operands at the actual acceptance frequency. For tangential and sagittal balance, use both `MTFA` and `MTFT` when appropriate. Edge and corner fields often need higher weights.

Use distortion operands such as `DIMX` and `DIST` on nonzero fields when distortion is a requirement. Do not rely on spot or focus operands to preserve distortion.

## Lessons From Practical Runs

A default automated merit function can make a lens look much better by spot size while harming distortion badly. Always compare before/after distortion and MTF against the requirement.

If a design cannot reach the required MTF after a focused MTF push while preserving track, distortion, and manufacturability, recommend a structural change instead of endless local optimization. Typical moves include:

- add an element or split power;
- change glass families, especially higher-index positive elements when curvature is excessive;
- relocate the stop or rebalance negative menisci;
- introduce an asphere only after a strong spherical baseline has been tested.

## Final Assessment Template

Report a concise table:

| Metric | Baseline | Final | Target | Status |
|---|---:|---:|---:|---|
| EFL or PMAG | | | | |
| Total track | | | | |
| Min MTF at frequency | | | | |
| Max RMS spot | | | | |
| Max distortion | | | | |

Then state whether the limitation is optimization setup, glass/power distribution, element count, packaging, or missing physical modeling.
