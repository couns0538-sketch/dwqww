# pin.ps1 - pinned launcher of job fable4cpu (PowerShell 5.1, ASCII only).
# This host pins ITSELF to -Mask (inside 0x707F) at BelowNormal first and reads both back. Windows hands the
# parent's affinity mask and a BelowNormal priority class to every child, so the target never runs unpinned.
# Heavy steps refuse to start when D: is under the floor. Deletes nothing.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File pin.ps1 -Mask 0x1000 -Exe <path> [-ArgLine "<args>"]
#                  [-OutFile <stdout+stderr file>] [-InFile <stdin file>] [-WorkDir <dir>] [-MinFreeGiB 31.0]
# Exit code: the child's exit code; 90-95 are launcher failures.
param(
    [Parameter(Mandatory = $true)][string]$Exe,
    [string]$ArgLine = '',
    [string]$InFile = '',
    [string]$OutFile = '',
    [string]$WorkDir = '',
    [long]$Mask = 0x707F,
    [double]$MinFreeGiB = 31.0
)
$ErrorActionPreference = 'Stop'
$Lane = 0x707F
$JobRoot = 'D:\forge_jobs_20261110\fable4cpu'
if ($Mask -le 0 -or ($Mask -band (-bnot $Lane)) -ne 0) { Write-Output ('pin.ps1: mask 0x{0:X} is not inside 0x707F' -f $Mask); exit 94 }
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.ProcessorAffinity = [IntPtr]$Mask
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
$me.Refresh()
if (([int64]$me.ProcessorAffinity) -ne $Mask) { Write-Output 'pin.ps1: affinity was not applied'; exit 90 }
if ($me.PriorityClass -ne [System.Diagnostics.ProcessPriorityClass]::BelowNormal) { Write-Output 'pin.ps1: priority was not applied'; exit 91 }
$tmp = Join-Path $JobRoot 'tmp'
if (-not (Test-Path -LiteralPath $tmp)) { Write-Output "pin.ps1: missing $tmp"; exit 92 }
$env:TEMP = $tmp
$env:TMP = $tmp
$env:GIT_NO_LAZY_FETCH = '1'
if (-not (Test-Path -LiteralPath $Exe)) { Write-Output "pin.ps1: missing exe $Exe"; exit 93 }
$free = (New-Object System.IO.DriveInfo('D')).AvailableFreeSpace / 1GB
if ($free -lt $MinFreeGiB) {
    $msg = ('pin.ps1: NOT STARTED (disk guard): D: has {0:N2} GiB free, under {1:N1}' -f $free, $MinFreeGiB)
    if ($OutFile -ne '') { try { [System.IO.File]::WriteAllText($OutFile, $msg + "`r`n", [System.Text.Encoding]::ASCII) } catch { } }
    Write-Output $msg
    exit 95
}
$line = '"' + $Exe + '" ' + $ArgLine
if ($InFile -ne '') { $line += ' < "' + $InFile + '"' }
if ($OutFile -ne '') { $line += ' > "' + $OutFile + '" 2>&1' }
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $env:ComSpec
$psi.Arguments = '/d /s /c "' + $line + '"'
$psi.UseShellExecute = $false
if ($WorkDir -ne '') { $psi.WorkingDirectory = $WorkDir }
$p = [System.Diagnostics.Process]::Start($psi)
$p.WaitForExit()
exit $p.ExitCode
