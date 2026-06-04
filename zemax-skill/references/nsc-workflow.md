# Non-Sequential Workflow

## Build Strategy

For non-sequential systems, start with an analytic or surrogate budget before building the full NSC model. Use it to estimate source power, pupil capture, footprint sizes, mirror/source positions, detector sizes, and ray counts.

Then build the NSC model incrementally:

1. Switch to NSC mode with `system.MakeNonSequential()`.
2. Add only source, aperture, detector, and one optical element first.
3. Trace rays and verify detector data access.
4. Add fold mirrors, polarization placeholders, scatter, coatings, and source arrays in separate passes.
5. Save every milestone as a separate `.zos`/`.zmx` file with a status JSON.

## NSCE Object Creation

Use `system.NCE`, `InsertNewObjectAt`, `GetObjectTypeSettings`, and `ChangeType`.

Prefer enum/object type identifiers such as:

- `SourceDiode`
- `DetectorRectangle`
- `Rectangle`
- `OffAxisMirror`

Localized UI names may differ, so avoid matching only the displayed Chinese or English object label.

When setting NSCE cells, probe the object methods and available columns on the target installation if assignment is unclear. Save the probe result as JSON so later passes do not rediscover the same mapping.

## Detector Data

Detector output may arrive as a `.NET System.Double[,]` object. Read it with `.GetValue(ix, iy)` rather than assuming Python list indexing.

Keep both:

- raw detector grid or exported detector file;
- derived metrics such as total flux, flux inside pupil radius, outside/inside ratio, centroid, and uniformity.

## Flux and Pupil Validation

For display, backlight, and pupil systems, normalize comparisons to useful eye-pupil flux. Report:

- total source power;
- detector total flux;
- fraction inside the target pupil;
- flux outside the pupil;
- outside/inside ratio;
- field or source-element balance.

Analytic first checks can use cone or Lambertian fractions, but label them as surrogate estimates. Zemax detector integration is the validation source once the NSC model is running.

## Practical NSC Risks

- Object parameter cells can be easy to mis-map; build small probes before bulk insertion.
- Folded mirrors and off-axis freeform elements need coordinate-frame checks and detector sanity images.
- A direct-pupil calibration model can validate source-to-pupil mapping separately from the folded relay.
- Do not overclaim paper reproduction when the original prescription, coatings, scatter model, or freeform coefficients are undisclosed; state which parts are equivalent, surrogate, or measured in Zemax.
