param(
    [Parameter(Mandatory=$true)][string]$OutModel,
    [Parameter(Mandatory=$true)][string]$LogPath,
    [string]$InteropPath = 'D:\Program Files\Optical Research Associates\LightTools 8.6.0\Utilities.NET\Interop.LTJumpStart.dll'
)

$ErrorActionPreference = 'Stop'
Add-Type -Path $InteropPath
$lt = [LightTools.LTAPI](New-Object LightTools.LTAPIClass)
function LT-Cmd($text) { $t=[string]$text; return $lt.Cmd([ref]$t) }
function LT-Str($text) { $t=[string]$text; return $lt.Str([ref]$t) }
function LT-SetOption($name,$value) { $n=[string]$name; return $lt.SetOption([ref]$n,[int16]$value) }

$lt.Begin() | Out-Null
try {
    LT-SetOption 'ShowDialogs' 0 | Out-Null
    LT-SetOption 'ShowFileDialogBox' 0 | Out-Null
    LT-SetOption 'ConfirmDeleteModel' 0 | Out-Null
    $status = LT-Cmd ('SaveAs ' + (LT-Str $OutModel))
    "save_active_status=$status out_model=$OutModel" | Set-Content -LiteralPath $LogPath -Encoding UTF8
    if ($status -ne 0) { throw "SaveAs active model failed status=$status" }
}
finally {
    try { LT-SetOption 'ShowDialogs' 1 | Out-Null } catch {}
    try { LT-SetOption 'ShowFileDialogBox' 1 | Out-Null } catch {}
    try { $lt.End() | Out-Null } catch {}
}
