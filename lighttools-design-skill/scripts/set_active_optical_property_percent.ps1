param(
    [string]$PropertyName = 'ec_t',
    [double]$TransmittancePercent,
    [int]$LightToolsPid = 0,
    [string]$RequiredSolid1 = 'colli1_lc_1',
    [string]$RequiredSolid2 = 'colli1_lc_2'
)

$ErrorActionPreference = 'Stop'
$locator = New-Object -ComObject 'LTLocator.Locator'
$lt = $null
$candidateIds = @()
if ($LightToolsPid -gt 0) { $candidateIds += $LightToolsPid }
$candidateIds += @(Get-Process lt -ErrorAction SilentlyContinue | ForEach-Object { [int]$_.Id })

foreach ($candidatePid in @($candidateIds | Select-Object -Unique)) {
    try {
        $candidate = $locator.GetLTAPI([int]$candidatePid)
        if ($null -eq $candidate) { continue }
        $solids = $candidate.DbList('COMPONENTS[1]', 'SOLID')
        if (-not $solids) { continue }
        if ($candidate.ListByName($solids, $RequiredSolid1) -and
            $candidate.ListByName($solids, $RequiredSolid2)) {
            $lt = $candidate
            $LightToolsPid = [int]$candidatePid
            break
        }
    } catch {}
}
if ($null -eq $lt) { throw 'No matching attachable LightTools session found' }

$root = 'LENS_MANAGER[1]'
$filter = 'PROPERTY'
$status = 0
$properties = $lt.DbList([ref]$root, [ref]$filter, [ref]$status)
if ($status -ne 0 -or -not $properties) { throw "PROPERTY list status=$status" }
$list = [string]$properties
$name = [string]$PropertyName
$status = 0
$propertyKey = $lt.ListByName([ref]$list, [ref]$name, [ref]$status)
if ($status -ne 0 -or -not $propertyKey) { throw "Property '$PropertyName' not found" }

$key = [string]$propertyKey
$field = 'TRANSMITTANCE PERCENT'
$status = 0
$before = $lt.DbGet([ref]$key, [ref]$field, [ref]$status, -1, -1)
if ($status -ne 0) { throw "DbGet before status=$status" }
$value = [double]$TransmittancePercent
$setStatus = $lt.DbSet([ref]$key, [ref]$field, [ref]$value, -1, -1)
$status = 0
$after = $lt.DbGet([ref]$key, [ref]$field, [ref]$status, -1, -1)

Write-Output "pid=$LightToolsPid property=$PropertyName field=$field before=$before set_status=$setStatus after=$after read_status=$status"
if ($setStatus -ne 0 -or $status -ne 0 -or
    [math]::Abs([double]$after - $TransmittancePercent) -gt 1e-9) {
    throw 'Set/readback verification failed'
}
