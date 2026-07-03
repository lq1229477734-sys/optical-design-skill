# Active-session double-length workflow

Use this workflow when the user has unsaved LightTools GUI edits and asks Codex to modify an optical property, sweep `colli1_lc_1` / `colli1_lc_2`, export `BLUReceiver` angular luminance, and process the TXT meshes.

## Attach to the correct GUI session

Run the client with the same Windows privilege level and bitness as LightTools. This installation normally needs elevated 32-bit PowerShell:

```powershell
C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe
```

Use `LTLocator.Locator.GetLTAPI(PID)`. Do not hard-code a PID across LightTools restarts. Enumerate `lt` processes and accept only a session whose `COMPONENTS[1]` database contains both target solids. `scripts/scan_active_double_length_sweep.ps1` implements this selection.

`GetLTAPI` returning null means the process is not externally attachable from the current client context. Retry with matching/elevated privileges before opening a model in a separate automation-owned session.

## Modify an active optical property

LightTools GUI labels and internal names can differ. The property called ECT in conversation was stored as `ec_t`.

Use `DbKeyDump(propertyKey, fileName)` to discover exact writable fields. Its second argument is an output filename, not a returned string. For smooth optical properties the stable field is:

```text
TRANSMITTANCE PERCENT
```

Values use percent units: `1` means 1%, and `65` means 65%. Always read before, write, then read back. Use `scripts/set_active_optical_property_percent.ps1`.

## Run the double LENGTH sweep

- Resolve each solid by name from `COMPONENTS[1] -> SOLID`.
- Resolve `CubePrimitive_1` with `CUBE_PRIMITIVE`, falling back to the first primitive.
- Convert micrometres to model millimetres with `value_um * 0.001`.
- Set `LENGTH` through `DbSet`.
- Require `BeginAllSimulations` status 0.
- Export `BLUReceiver -> Angular_Luminance_Mesh` through `GetMeshData('CellValue')`; do not depend on the active chart window.
- Name files `lc2-lc1`, for example `9um-3um.txt`.

The in-application macro `scripts/scan_active_double_length_9_12_3_6.ltb` is a chart-export fallback. Open the desired angular-luminance chart first and update `CHART_VIEW_CMD$` when localized chart names differ.

## Process angular luminance

`scripts/process3_standalone.py` is designed to be copied into the TXT folder and run there. It:

1. reads all `first_um-second_um.txt` files;
2. skips blank and `#` header lines;
3. transposes each 61 x 61 matrix;
4. extracts one-based column 31;
5. calculates 0-degree luminance, interpolated 45-degree luminance, 45/0 ratio, and optical loss;
6. writes curve CSVs, summary/pivot CSVs, PNGs, and PDFs under `processed_results_fixed`.

The transpose preserves the established `process3` convention. Because a 61 x 61 matrix has the same shape before and after transpose, verify orientation by comparing extracted row/column values, not shape alone.

## Validate data, not headers

TXT hashes can differ solely because headers contain dynamic PID or mesh keys. Strip comments and compare numeric matrices. Treat a parameter change as ineffective when the global maximum absolute numeric difference is zero.

If 45/0 appears insensitive to the second sweep parameter:

- compare full 61 x 61 meshes;
- compare the extracted center row and center column;
- inspect 0-degree and 45-degree terms separately;
- plot ratios at 20, 30, 35, or 40 degrees.

In one validated scan, `colli1_lc_1` changed the full mesh while 45-degree luminance stayed constant, so 45/0 was controlled mainly by `colli1_lc_2`. Do not misdiagnose this as a failed sweep without the full-matrix comparison.
