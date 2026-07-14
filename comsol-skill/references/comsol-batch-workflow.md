# COMSOL Batch Workflow

## Executables

Typical Windows paths:

```powershell
$bin = 'C:\Program Files\COMSOL\COMSOL60\Multiphysics\bin\win64'
$compile = Join-Path $bin 'comsolcompile.exe'
$batch = Join-Path $bin 'comsolbatch.exe'
```

Discover the actual installation instead of assuming the version or drive.

## Stable Batch Flags

Use writable, task-local preference and recovery directories:

```powershell
& $batch `
  -autosave off `
  -recoverydir '<workspace>\comsol_recovery' `
  -prefsdir '<workspace>\comsol_prefs' `
  -inputfile '<model-or-class>' `
  -outputfile '<output.mph>' `
  -batchlogout
```

These flags avoid locked user-profile paths and recovery popups.

## Build and Solve

Compile the Java model builder:

```powershell
& $compile .\CreateTwistedAMoO3ComsolScan.java
& $batch <stable-flags> -inputfile .\CreateTwistedAMoO3ComsolScan.class -outputfile .\BASE.mph -batchlogout
```

COMSOL may suffix the output model with the active model tag. Inspect the actual filename before launching the study.

Run each polarization separately to preserve provenance:

```powershell
& $batch <stable-flags> -inputfile .\BASE_ModelTag.mph -outputfile .\LCP.mph -study std1 -pname pol -plist 1 -batchlogout
& $batch <stable-flags> -inputfile .\BASE_ModelTag.mph -outputfile .\RCP.mph -study std1 -pname pol -plist -1 -batchlogout
```

## Coarse-to-Fine Policy

1. Build geometry and mesh only.
2. Run 21-33 frequency points.
3. Measure solve time, DOF, memory, convergence, and result range.
4. Stop and reduce redundant lateral mesh if projected final time is excessive.
5. Increase to 101-201 points only after the coarse model passes validation.

Do not let a clearly over-meshed preview continue for hours. For a uniform planar stack, lateral field variation is absent at normal incidence; spend resolution through the thickness instead.

## Entity Inspection

Use `GeomMeasureFinal` after `geom.run()` to print areas, lengths, and bounding boxes. Confirm:

- Bottom receiver boundary has the expected xy area and minimum z.
- Top source boundary has the expected xy area and maximum z.
- Side boundaries are paired layer by layer.
- Vertical edges used by sweep distributions have the expected z intervals.

`Box` selections must use `condition=inside`. Without it, a thin z box can select side faces intersecting the box.

## Result Export

A numerical node created before solving may not automatically bind to the batch solution. On load:

1. Create a fresh `EvalGlobal` node.
2. Set `data=dset1` explicitly.
3. Set `expr=Tcomsol`.
4. Attach a new table.
5. Call `setResult()` before saving the table.

If the exported file contains only comments, the result node is not bound to a solved dataset.

## Audit Checklist

- Record COMSOL version.
- Record mesh elements, minimum quality, and DOF.
- Record frequency count and solve time.
- Check output `.mph` size and timestamp.
- Check table row count equals frequency count.
- Check `min(T)` and `max(T)`.
- Check expected peaks and symmetry limits.
- Open the final PNG and visually inspect labels, overlap, and axis range.
