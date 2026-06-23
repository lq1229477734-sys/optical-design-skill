# LightTools Distance Scan Workflow

Use this reference for local `distance.*.lts` models that scan `colli1_lc_1`,
`colli1_lc_2`, `ec_t`, `BLUReceiver`, and angular luminance TXT/image outputs.

## Model Preservation

- Copy the source `.lts` to a versioned file before patching, e.g.
  `distance.12.ec_t50.lts`.
- Do not overwrite the original unless the user explicitly requests it.
- Keep scan output folders separate from processed result folders.

## Text Patches

Patch model text only when the COM database cannot expose the target property.

`ec_t` transmittance is stored in the optical-property block:

```text
setName: "ec_t";
...
setReflectance: 0.;
setTransmittance: 0.08;
```

Change only the nearby `setTransmittance` value, then verify with
`Select-String`. `ec_t` is typically referenced by `2D_Pattern` property zones
via `setPropertiesName: "ec_t";`.

## LightTools Automation

For this workflow, use 32-bit PowerShell when loading JumpStart:

```text
C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe
```

Load the interop assembly:

```powershell
Add-Type -Path 'D:\360Safe\lighttools\Utilities.NET\Interop.LTJumpStart.dll'
```

Always open from Console and suppress dialogs:

```powershell
LT-Cmd '\VConsole' | Out-Null
LT-SetOption 'ShowDialogs' 0 | Out-Null
LT-SetOption 'ShowFileDialogBox' 0 | Out-Null
LT-SetOption 'ConfirmDeleteModel' 0 | Out-Null
$open = LT-Cmd ('Open ' + (LT-Str $model))
```

## Geometry Sweeps

Locate solids with:

```powershell
$solidList = LT-DbList 'COMPONENTS[1]' 'SOLID'
```

Find `colli1_lc_1` and `colli1_lc_2`, then locate each `CubePrimitive_1` with:

```powershell
$primList = LT-DbList $solidKey 'CUBE_PRIMITIVE'
```

Set `LENGTH` in mm:

```text
50 um -> 0.05
70 um -> 0.07
130 um -> 0.13
```

Common scan:

```text
outer colli1_lc_1: 50, 60, 70 um
inner colli1_lc_2: 90, 100, 110, 120, 130 um
```

Use `scripts/scan_distance_double_sweep.ps1` as the reusable template.

## Receiver Mesh Export

Export angular luminance data from the receiver mesh, not from a chart window.
Chart-window commands are fragile.

```powershell
$recList = LT-DbList 'Illum_Manager[1]' 'Receiver'
$recKey = LT-ListByName $recList 'BLUReceiver'
$meshList = LT-DbList $recKey 'Angular_Luminance_Mesh'
$meshKey = LT-ListAtPos $meshList 1
```

The known mesh for this model is `61 x 61`. Use `GetMeshData(..., 'CellValue')`
and write files as `50um-90um.txt`, `50um-100um.txt`, etc.

After each scan:

- Confirm all `BeginAllSimulations` statuses are `0`.
- Confirm 15 TXT files exist for the standard 3 x 5 sweep.
- Keep the raw TXT files; do not post-process in place.

## Post-Processing

Use either the local `process3.py` or the reusable script:

```powershell
python .\lighttools-design-skill\scripts\process_angle_luminance.py `
  --folder .\distance12_lc1_50_70_lc2_90_130_angle_luminance `
  --front-min 50 --front-max 70 `
  --back-min 90 --back-max 130
```

Read TXT robustly by skipping empty lines and `#` header/comment lines. Save
outputs to a fresh folder such as `processed_results_fixed`.

Expected processed outputs include:

- `all_files_summary.csv`
- per-file `*_curve_col31.csv`
- `first_50um_subplots.png/.pdf`
- `first_60um_subplots.png/.pdf`
- `first_70um_subplots.png/.pdf`
- `ratio_45_over_0_vs_second_um_first_curves.png`
- `optical_loss_1_minus_0deg_over_513.png`
- pivot CSV files

## Diagnosing Unchanged Results

If changing `ec_t` from 8% to 50% produces identical TXT hashes:

- The file patch probably succeeded if `setTransmittance: 0.5;` is visible in
  the `ec_t` block.
- The current `BLUReceiver Angular Luminance Mesh` may be insensitive to that
  property even though `ec_t` is referenced by `2D_Pattern` zones.
- Do an extreme test before assuming the script is wrong: set `ec_t`
  transmittance to `0`, or temporarily change the `2D_Pattern` property to a
  fully absorbing property, run one or two scan points, and compare hashes.

Use file hashes to verify whether data actually changed:

```powershell
Get-FileHash old.txt,new.txt -Algorithm SHA256
```
