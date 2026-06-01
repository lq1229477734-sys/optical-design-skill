param(
    [Parameter(Mandatory=$true)][string]$ModelPath,
    [Parameter(Mandatory=$true)][string]$OutRoot,
    [int[]]$Lc1Um = @(50, 60, 70),
    [int[]]$Lc2Um = @(90, 100, 110, 120, 130)
)

$ErrorActionPreference = 'Stop'
Add-Type -Path 'D:\360Safe\lighttools\Utilities.NET\Interop.LTJumpStart.dll'

New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null

$lt = [LightTools.LTAPI](New-Object LightTools.LTAPIClass)

function LT-Cmd($text) {
    $t = [string]$text
    return $lt.Cmd([ref]$t)
}
function LT-Str($text) {
    $t = [string]$text
    return $lt.Str([ref]$t)
}
function LT-SetOption($name, $value) {
    $n = [string]$name
    return $lt.SetOption([ref]$n, [int16]$value)
}
function LT-DbList($key, $filter) {
    $k = [string]$key
    $f = [string]$filter
    $s = [LightTools.LTReturnCodeEnum]::ltStatusSuccess
    return $lt.DbList([ref]$k, [ref]$f, [ref]$s)
}
function LT-ListSize($listKey) {
    $l = [string]$listKey
    $s = [LightTools.LTReturnCodeEnum]::ltStatusSuccess
    return $lt.ListSize([ref]$l, [ref]$s)
}
function LT-ListAtPos($listKey, $pos) {
    $l = [string]$listKey
    $s = [LightTools.LTReturnCodeEnum]::ltStatusSuccess
    return $lt.ListAtPos([ref]$l, [int16]$pos, [ref]$s)
}
function LT-ListByName($listKey, $name) {
    $l = [string]$listKey
    $n = [string]$name
    $s = [LightTools.LTReturnCodeEnum]::ltStatusSuccess
    return $lt.ListByName([ref]$l, [ref]$n, [ref]$s)
}
function LT-DbGet($key, $field) {
    $k = [string]$key
    $f = [string]$field
    $s = [LightTools.LTReturnCodeEnum]::ltStatusSuccess
    return $lt.DbGet([ref]$k, [ref]$f, [ref]$s, -1, -1)
}
function LT-DbSet($key, $field, $value) {
    $k = [string]$key
    $f = [string]$field
    $v = $value
    return $lt.DbSet([ref]$k, [ref]$f, [ref]$v, -1, -1)
}
function Find-Primitive($solidName) {
    $solidList = LT-DbList 'COMPONENTS[1]' 'SOLID'
    $solidKey = LT-ListByName $solidList $solidName
    if ([string]::IsNullOrWhiteSpace($solidKey)) {
        throw "Cannot find solid $solidName"
    }

    $primList = LT-DbList $solidKey 'CUBE_PRIMITIVE'
    $primKey = LT-ListByName $primList 'CubePrimitive_1'
    if ([string]::IsNullOrWhiteSpace($primKey) -and (LT-ListSize $primList) -gt 0) {
        $primKey = LT-ListAtPos $primList 1
    }
    if ([string]::IsNullOrWhiteSpace($primKey)) {
        throw "Cannot find CubePrimitive_1 under $solidName"
    }
    return $primKey
}
function Find-AngularLuminanceMesh() {
    $receiverList = LT-DbList 'Illum_Manager[1]' 'Receiver'
    $receiverKey = LT-ListByName $receiverList 'BLUReceiver'
    if ([string]::IsNullOrWhiteSpace($receiverKey)) {
        throw 'Cannot find BLUReceiver'
    }

    $meshList = LT-DbList $receiverKey 'Angular_Luminance_Mesh'
    $meshKey = LT-ListAtPos $meshList 1
    if ([string]::IsNullOrWhiteSpace($meshKey)) {
        throw 'Cannot find Angular_Luminance_Mesh under BLUReceiver'
    }
    return $meshKey
}
function Export-MeshTxt($meshKey, $path) {
    $xDim = [int](LT-DbGet $meshKey 'X_Dimension')
    $yDim = [int](LT-DbGet $meshKey 'Y_Dimension')
    [Array]$data = New-Object 'double[,]' $xDim, $yDim
    $mk = [string]$meshKey
    $filter = [string]'CellValue'
    $status = $lt.GetMeshData([ref]$mk, [ref]$data, [ref]$filter)
    if ($status -ne 0) {
        throw "GetMeshData failed for $meshKey status=$status"
    }

    $writer = [System.IO.StreamWriter]::new($path, $false, [System.Text.Encoding]::UTF8)
    try {
        $writer.WriteLine("# Angular Luminance Mesh")
        $writer.WriteLine("# MeshKey`t$meshKey")
        $writer.WriteLine("# X_Dimension`t$xDim")
        $writer.WriteLine("# Y_Dimension`t$yDim")
        for ($iy = 0; $iy -lt $yDim; $iy++) {
            $vals = New-Object string[] $xDim
            for ($ix = 0; $ix -lt $xDim; $ix++) {
                $val = $data.GetValue($ix, $iy)
                $vals[$ix] = [string]::Format([Globalization.CultureInfo]::InvariantCulture, '{0:G17}', $val)
            }
            $writer.WriteLine(($vals -join "`t"))
        }
    }
    finally {
        $writer.Dispose()
    }
}

$lt.Begin() | Out-Null
try {
    LT-SetOption 'ShowDialogs' 0 | Out-Null
    LT-SetOption 'ShowFileDialogBox' 0 | Out-Null
    LT-SetOption 'ConfirmDeleteModel' 0 | Out-Null

    LT-Cmd '\VConsole' | Out-Null
    $open = LT-Cmd ('Open ' + (LT-Str (Resolve-Path $ModelPath).Path))
    if ($open -ne 0) { throw "Open failed: $open" }

    Start-Sleep -Seconds 2
    $prim1 = Find-Primitive 'colli1_lc_1'
    $prim2 = Find-Primitive 'colli1_lc_2'
    $meshKey = Find-AngularLuminanceMesh
    Write-Output "prim1=$prim1 old1=$(LT-DbGet $prim1 'LENGTH')"
    Write-Output "prim2=$prim2 old2=$(LT-DbGet $prim2 'LENGTH')"
    Write-Output "angular_mesh=$meshKey x=$(LT-DbGet $meshKey 'X_Dimension') y=$(LT-DbGet $meshKey 'Y_Dimension')"

    foreach ($l1 in $Lc1Um) {
        $s1 = LT-DbSet $prim1 'LENGTH' ($l1 * 0.001)
        if ($s1 -ne 0) { Write-Output "ERROR set colli1_lc_1 $l1 um status=$s1"; continue }

        foreach ($l2 in $Lc2Um) {
            $s2 = LT-DbSet $prim2 'LENGTH' ($l2 * 0.001)
            if ($s2 -ne 0) { Write-Output "ERROR set colli1_lc_2 $l2 um status=$s2"; continue }

            $base = "${l1}um-${l2}um"
            Get-ChildItem $OutRoot -Filter "$base*.txt" -ErrorAction SilentlyContinue | Remove-Item -Force

            LT-Cmd '\V3D' | Out-Null
            LT-Cmd 'Fit' | Out-Null
            Write-Output "simulate $base"
            $sim = LT-Cmd 'BeginAllSimulations'
            Write-Output "sim_status $base $sim"

            $txt = Join-Path $OutRoot ($base + '.txt')
            Export-MeshTxt $meshKey $txt
            Write-Output "wrote $txt"
        }
    }
}
finally {
    try { LT-SetOption 'ShowDialogs' 1 | Out-Null } catch {}
    try { LT-SetOption 'ShowFileDialogBox' 1 | Out-Null } catch {}
    try { $lt.End() | Out-Null } catch {}
}
