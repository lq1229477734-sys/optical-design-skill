# Paper Reproduction Lessons

Use this reference when reproducing optical paper figures in LightTools.

## Figure 2 LED / Angle-Filter Pattern

Successful reproduction pattern:

- Start from a geometry approximation model.
- Disable LED geometry placeholders so they do not block rays.
- Add real `MakeSourceSurfaceCube` Lambertian sources.
- Use paper source dimensions and pitch where available.
- Add a real receiver plane and `Illuminance` mesh.
- Run a practical ray count first, then export the mesh.

Verified example values:

- 3 x 3 source grid.
- Source size: `100 um x 100 um`, modeled as `0.10 mm x 0.10 mm x 0.02 mm`.
- Source pitch: `6 mm`.
- Receiver: `18 mm x 18 mm` at `z = 1 mm`.
- Mesh: `21 x 21`.
- Practical ray count: `200000`; paper count may be much higher.

A successful run reported:

```text
BeginAllSimulations status=0 ltStatusSuccess
Sources=9
Receivers=1
receiver mesh cells=441
nonzero cells=258
max=0.26535203
avg=0.0117665
```

## Figure 14 Prism 3 / Library Texture Pattern

Lessons from the Prism 3 work:

- Built-in pyramid 3D texture exposes North/South/East/West facet angles but may not encode an independent diagonal cross-section angle.
- A Prism 3 target with x/y apex `120 deg` maps to `30 deg` facet angle and height `pitch / (2 * tan(60 deg))`.
- If a user library element is used as a texture, validate orientation and performance with reduced rays or a smaller texture zone first.
- A full `18 mm x 18 mm` film at `0.1 mm` pitch contains `32400` repeated elements and can be heavy.
- If the user library element is actually a four-prism composite, the repeated period may be `0.2 mm`, reducing full-zone cells to `90 x 90 = 8100`.

Texture registration matters:

```text
Use addPropertyZone for the property zone attachment.
Set snap mode to Align to Surface Normal.
Set cell alignment to Surface U Direction.
Avoid partial-cell ambiguity unless explicitly desired.
```

Surface choice matters. In one validated model, the thin-film direction mapped to `LeftSurface` / `RightSurface`, not `BottomSurface`.

## Material Inheritance Rule for Library Textures

LightTools user-defined texture patterns made from library elements do not import the library element optical properties. Textures inherit the substrate material when they are created.

Practical consequence:

- Do not apply a prism library texture directly to an angle-selective filter if the filter material is not the desired prism resin.
- Instead, keep the dielectric / angle filter as its own layer, add a separate microprism film/substrate, assign the resin material or index to that film, and apply the texture to the film surface.

## DBHM Stability Lessons

Supplement-derived DBHM assumptions can be modeled as separate physical films:

- Two DBHMs.
- Mixed prism pitches: `50 um` and `54 um`.
- Acrylic resin prisms bonded to glass substrates.
- Glass substrate thicknesses: `2 mm` and `3 mm`.

If height or apex is missing, state the assumption. A safe geometric assumption used `90 deg` apex:

```text
50 um pitch -> 0.025 mm height
54 um pitch -> 0.027 mm height
```

Dense prism textures over a `60 mm` aperture can make LightTools unstable during selection or display. For a stability-first revision:

- Remove dense 3D texture zones.
- Keep physical substrate cuboids.
- Register cuboids in `$ORAUnboundedRegionObj_0` using `addImmersedElement`.
- Create matching `$ORAOpenRegionObj` records.
- Link cuboids with `restoreRegion`.

This preserves the layer stack for alignment and later simulation work while avoiding selection crashes.

## Debugging Rules

- Prefer smaller zones, fewer rays, and disabled ray saving for first validation.
- Set `SaveRayData`, default ray saving, and ray-path display to off for fast-run variants.
- Treat paper-relative geometry and exact display density as separate problems.
- Keep one model version per experiment: geometry, source orientation, texture registration, material correction, and fast-run settings should each get their own `.lts` suffix.
- Write the reason for every compromise directly into the audit.
