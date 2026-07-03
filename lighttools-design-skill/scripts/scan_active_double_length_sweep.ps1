param(
    [int]$LightToolsPid = 0,
    [string]$OutRoot = (Join-Path (Get-Location) 'active_double_length_angle_luminance'),
    [int[]]$Lc1Values = @(3,4,5,6),
    [int[]]$Lc2Values = @(8,9,10,11,12)
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null
$locator = New-Object -ComObject 'LTLocator.Locator'
$lt = $null
$candidateIds = @()
if ($LightToolsPid -gt 0) { $candidateIds += $LightToolsPid }
$candidateIds += @(Get-Process lt -ErrorAction SilentlyContinue | ForEach-Object { [int]$_.Id })
$candidateIds = @($candidateIds | Select-Object -Unique)
foreach ($candidatePid in $candidateIds) {
    try {
        $candidate = $locator.GetLTAPI([int]$candidatePid)
        if ($null -eq $candidate) { continue }
        $candidateSolids = $candidate.DbList('COMPONENTS[1]', 'SOLID')
        if (-not $candidateSolids) { continue }
        $candidateLc1 = $candidate.ListByName($candidateSolids, 'colli1_lc_1')
        $candidateLc2 = $candidate.ListByName($candidateSolids, 'colli1_lc_2')
        if ($candidateLc1 -and $candidateLc2) {
            $lt = $candidate
            $LightToolsPid = [int]$candidatePid
            Write-Output "auto_attached_pid=$LightToolsPid"
            break
        }
    } catch {}
}
if ($null -eq $lt) {
    throw 'Cannot find an attachable LightTools session containing colli1_lc_1 and colli1_lc_2'
}

function Find-Primitive([string]$solidName) {
    $solids = $lt.DbList('COMPONENTS[1]', 'SOLID')
    $solid = $lt.ListByName($solids, $solidName)
    if (-not $solid) { throw "Cannot find $solidName" }
    $prims = $lt.DbList($solid, 'CUBE_PRIMITIVE')
    $prim = $lt.ListByName($prims, 'CubePrimitive_1')
    if (-not $prim -and $lt.ListSize($prims) -gt 0) { $prim = $lt.ListAtPos($prims, 1) }
    if (-not $prim) { throw "Cannot find primitive under $solidName" }
    return $prim
}

function Find-AngularMesh {
    $receivers = $lt.DbList('Illum_Manager[1]', 'Receiver')
    $receiver = $lt.ListByName($receivers, 'BLUReceiver')
    if (-not $receiver -and $lt.ListSize($receivers) -gt 0) { $receiver = $lt.ListAtPos($receivers, 1) }
    $meshes = $lt.DbList($receiver, 'Angular_Luminance_Mesh')
    $mesh = $lt.ListAtPos($meshes, 1)
    if (-not $mesh) { throw 'Cannot find angular luminance mesh' }
    return $mesh
}

function Export-Mesh([string]$mesh, [string]$path) {
    $xDim = [int]$lt.DbGet($mesh, 'X_Dimension')
    $yDim = [int]$lt.DbGet($mesh, 'Y_Dimension')
    [Array]$data = New-Object 'double[,]' $xDim, $yDim
    $mk = [string]$mesh
    $filter = [string]'CellValue'
    $status = $lt.GetMeshData([ref]$mk, [ref]$data, [ref]$filter)
    if ($status -ne 0) { throw "GetMeshData status=$status" }
    $writer = [IO.StreamWriter]::new($path, $false, [Text.Encoding]::UTF8)
    try {
        $writer.WriteLine('# Angular Luminance Mesh')
        $writer.WriteLine("# Active LightTools PID`t$LightToolsPid")
        $writer.WriteLine("# MeshKey`t$mesh")
        $writer.WriteLine("# X_Dimension`t$xDim")
        $writer.WriteLine("# Y_Dimension`t$yDim")
        for ($iy=0; $iy -lt $yDim; $iy++) {
            $values = for ($ix=0; $ix -lt $xDim; $ix++) {
                [string]::Format([Globalization.CultureInfo]::InvariantCulture, '{0:G17}', $data.GetValue($ix,$iy))
            }
            $writer.WriteLine($values -join "`t")
        }
    } finally { $writer.Dispose() }
}

$prim1 = Find-Primitive 'colli1_lc_1'
$prim2 = Find-Primitive 'colli1_lc_2'
$mesh = Find-AngularMesh
Write-Output "pid=$LightToolsPid prim1=$prim1 old1=$($lt.DbGet($prim1,'LENGTH')) prim2=$prim2 old2=$($lt.DbGet($prim2,'LENGTH')) mesh=$mesh x=$($lt.DbGet($mesh,'X_Dimension')) y=$($lt.DbGet($mesh,'Y_Dimension'))"

foreach ($lc1 in $Lc1Values) {
    $s1 = $lt.DbSet($prim1, 'LENGTH', $lc1 * 0.001)
    if ($s1 -ne 0) { throw "DbSet lc1=$lc1 status=$s1" }
    foreach ($lc2 in $Lc2Values) {
        $s2 = $lt.DbSet($prim2, 'LENGTH', $lc2 * 0.001)
        if ($s2 -ne 0) { throw "DbSet lc2=$lc2 status=$s2" }
        $base = "${lc2}um-${lc1}um"
        Write-Output "simulate $base"
        $sim = $lt.Cmd('BeginAllSimulations')
        Write-Output "sim_status $base $sim"
        if ($sim -ne 0) { throw "Simulation $base status=$sim" }
        $txt = Join-Path $OutRoot "$base.txt"
        Export-Mesh $mesh $txt
        Write-Output "wrote $txt"
    }
}
