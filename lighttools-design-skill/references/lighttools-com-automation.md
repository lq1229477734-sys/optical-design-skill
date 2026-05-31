# LightTools COM Automation

Use this reference when building or validating LightTools models through COM, PowerShell, and JumpStart .NET.

## Environment Pattern

Known working installation paths from the source workspace:

- LightTools executable: `D:\360Safe\lighttools\lt.exe`
- Docs: `D:\360Safe\lighttools\Docs`
- JumpStart interop: `D:\360Safe\lighttools\Utilities.NET\Interop.LTJumpStart.dll`
- JumpStart helpers: `D:\360Safe\lighttools\Utilities.NET\LTJumpStartNET.dll`

Verified ProgIDs:

- `LightTools.LTAPI3`
- `LightTools.LTAPI`

Python did not have `pywin32` in the original workspace, so the robust path was:

```text
Python -> PowerShell -> LightTools COM
```

## PowerShell Wrapper Template

Use wrappers because many interop calls require `ByRef` strings.

```powershell
Add-Type -Path 'D:\360Safe\lighttools\Utilities.NET\Interop.LTJumpStart.dll'
Add-Type -Path 'D:\360Safe\lighttools\Utilities.NET\LTJumpStartNET.dll'

$lt = [LightTools.LTAPI](New-Object LightTools.LTAPIClass)

function LT-Cmd($text) {
    $s = [string]$text
    return $lt.Cmd([ref]$s)
}
function LT-Str($text) {
    $s = [string]$text
    return $lt.Str([ref]$s)
}
function LT-SetOption($name, $value) {
    $n = [string]$name
    return $lt.SetOption([ref]$n, [int16]$value)
}
function LT-DbList($key, $filter) {
    $k = [string]$key
    $f = [string]$filter
    $status = [LightTools.LTReturnCodeEnum]::ltStatusSuccess
    return $lt.DbList([ref]$k, [ref]$f, [ref]$status)
}
function LT-ListSize($listKey) {
    $l = [string]$listKey
    $status = [LightTools.LTReturnCodeEnum]::ltStatusSuccess
    return $lt.ListSize([ref]$l, [ref]$status)
}
function LT-ListAtPos($listKey, $pos) {
    $l = [string]$listKey
    $status = [LightTools.LTReturnCodeEnum]::ltStatusSuccess
    return $lt.ListAtPos([ref]$l, [int16]$pos, [ref]$status)
}
function LT-DbGet($key, $field) {
    $k = [string]$key
    $f = [string]$field
    $status = [LightTools.LTReturnCodeEnum]::ltStatusSuccess
    return $lt.DbGet([ref]$k, [ref]$f, [ref]$status, -1, -1)
}
```

Disable dialogs in automation:

```powershell
LT-SetOption 'ShowDialogs' 0 | Out-Null
LT-SetOption 'ShowFileDialogBox' 0 | Out-Null
LT-SetOption 'ConfirmDeleteModel' 0 | Out-Null
```

## Open, Save, and Version

Opening a saved model before adding sources is more reliable than starting from a dirty COM session.

```powershell
$openStatus = LT-Cmd ('Open ' + (LT-Str $modelPath))
if ($openStatus -ne 0) { throw "Open failed with status $openStatus" }

$saveStatus = LT-Cmd ('SaveAs ' + (LT-Str $outModel))
if ($saveStatus -ne 0) { throw "SaveAs failed with status $saveStatus" }
```

Use `name.1.lts`, `name.2.lts`, `name.3.lts`, etc. Do not overwrite known-good files unless the user explicitly asks.

## Surface Sources

Use JumpStart `MakeSourceSurfaceCube` for real LED sources instead of ray-traceable geometry placeholders.

```powershell
[LTJumpStartNET.LTSources]::MakeSourceSurfaceCube(
    $lt,
    0.10, 0.10, 0.02,
    [ref]$srcName,
    0, 0, 1, 0, 0, 0
) | Out-Null
```

The six emission flags are:

```text
emitLeft, emitBack, emitTop, emitFront, emitBottom, emitRight
```

Move and power the source:

```powershell
[LTJumpStartNET.LTTransform]::MoveVector($lt, $srcName, $x, $y, $z) | Out-Null
[LTJumpStartNET.LTSources]::SetSourcePower($lt, $srcName, 1.0, 'Watts', 'Radiometric') | Out-Null
```

Check local coordinate conventions before choosing emitting face. One successful 6x6 preview needed `RightSurface` as the upward emitting side, not `TopSurface`.

## Receivers and Mesh Export

Create a dummy plane and attach a receiver:

```powershell
[LTJumpStartNET.LTGeometry]::MakeDummyPlane(
    $lt,
    0, 0, 1.0,
    0, 0, 1,
    'No',
    'Rectangular',
    18.0, 18.0,
    [ref]$receiverPlane,
    0, 0, 0
) | Out-Null

[LTJumpStartNET.LTReceiver]::MakeReceiver($lt, $receiverPlane, '', [ref]$receiverName) | Out-Null
[LTJumpStartNET.LTReceiver]::SetReceiverMeshLimits(
    $lt,
    $receiverName,
    'Illuminance',
    -9.0, 9.0, 21,
    -9.0, 9.0, 21,
    'No Symmetry',
    'FORWARD'
) | Out-Null
```

Run simulation:

```powershell
$simStatus = LT-Cmd '\V3D BeginAllSimulations'
```

Export receiver mesh with native LTAPI `GetMeshData`; this was more reliable than JumpStart `GetMeshDataKey`.

```powershell
$meshKey = [string]('RECEIVER[' + $receiverName + '].MESH[1]')
[Array]$rows = New-Object 'double[,]' 21,21
$cellFilter = [string]'CellValue'
$meshStatus = $lt.GetMeshData([ref]$meshKey, [ref]$rows, [ref]$cellFilter)
```

## Audit Checks

After every successful run, capture:

- Open and SaveAs status strings.
- Counts and names of solids, sources, receivers, and textures.
- Ray count and ray-save settings.
- Receiver mesh nonzero cells, maximum, average, and output path.
- Any paper deviations or stability compromises.
