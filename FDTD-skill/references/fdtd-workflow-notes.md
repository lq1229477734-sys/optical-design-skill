# FDTD Workflow Notes

## Environment Lessons

- Lumerical projects are binary `.fsp` files. To create an identical copy, use filesystem copying or open/save through `lumapi`; do not attempt text patching.
- `lumapi.FDTD()` opens an API session. It does not attach to an arbitrary already-open FDTD GUI window.
- On Windows, Lumerical 2025 R2 may be installed under:
  `D:\Program Files\ANSYS Inc\v252\Lumerical`
- The launcher may live outside the Lumerical root:
  `D:\Program Files\ANSYS Inc\v252\OpticsLauncher\bin\launcher.exe`
- The bundled Python can be:
  `D:\Program Files\ANSYS Inc\v252\Lumerical\python-3.13.1\python.exe`

## Robust Runner Pattern

Use a Python runner around `.lsf` files:

```python
lumapi = import_lumapi()
fdtd = lumapi.FDTD(filename=str(project), hide=True)
try:
    fdtd.feval(str(script))
finally:
    fdtd.close()
```

Before importing `lumapi`, insert the API path and add DLL directories:

```python
api_dir = os.path.join(root, "api", "python")
bin_dir = os.path.join(root, "bin")
sys.path.insert(0, api_dir)
os.add_dll_directory(api_dir)
os.add_dll_directory(bin_dir)
```

## Safe Mode and Analysis Mode

Avoid this inside `.lsf`:

```js
rm("output.txt");
```

It may fail with:

```text
The rm command is disabled in safe mode.
```

Delete stale files from Python instead:

```python
if output.exists():
    output.unlink()
```

When a project opens with existing results, editing objects can fail with:

```text
you cannot modify most simulation objects while in analysis mode
```

Start the `.lsf` with:

```js
switchtolayout;
```

## Fast One-Thickness Scan Pattern

For a slow thickness/wavelength/phase scan:

- Fix one thickness, for example `dv = 50e-09`.
- Keep material data wavelength points from the source text files.
- Use a single loop over phases:

```js
phases = [90, -90];
for (ip = 1:length(phases)) {
    select("source_1");
    set("phase", phases(ip));
    for (iw = 1:length(wa)) {
        ...
        run;
        t_value = transmission("t");
        write(out_file, num2str(phases(ip)) + " " + num2str(dv) + " " + num2str(wav_nm(iw)) + " " + num2str(t_value));
        switchtolayout;
    }
}
```

Prefer one explicit output table:

```text
phase_deg thickness_m wavelength_nm transmission
```

This is easier to analyze than separate files such as `t_zuo_an_wa.txt` and `t_you_an_wa.txt`.

## Interpreting Transmission

Lumerical `transmission("monitor")` is signed by monitor normal and power-flow direction. Negative values often mean the monitor normal is opposite the propagation direction. For reports:

- Preserve `transmission_raw`.
- Add `transmission_abs = abs(transmission_raw)`.
- Plot `transmission_abs` unless the sign convention itself matters.

## BP/hBN/MoO3 Example Notes

A typical project package can include:

- `.fsp`: base model with geometry, sources, monitors, and material objects.
- `.lsf`: scan script.
- `nxy2_bp13.txt`: BP anisotropic data with columns `wavelength_nm nx kx ny ky nz kz`.
- `nxy_hbn.txt`: hBN/isotropic data with columns `wavelength_nm n k`.

The scan updates:

- `BP_M` with diagonal anisotropic refractive index and imaginary index.
- A second material object such as `mos2` with isotropic `n/k`.
- `source` and `source_1` wavelength start/stop to single wavelength points.
- `source_1` phase to compare `+90` and `-90` conditions.

## Deliverables Checklist

For repeatable work, deliver:

- The generated `.lsf` script.
- The Python runner.
- The output `.txt` or `.csv`.
- A plot `.png`.
- A short note about thickness, wavelength grid, phase settings, and sign convention.
