# pinned.ps1 - run one program at Idle on CPUs 12-15 with the job's environment; children inherit.
# usage (from the Bash tool, per the PS 5.1 pitfalls of the speed tools):
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File pinned.ps1 -Exe <exe> -ArgLine '<args>' [-Cwd <dir>] [-Log <file>]
# Fails closed if the pin does not read back. The program must exit by itself: this script never kills anything.
param(
    [Parameter(Mandatory = $true)][string]$Exe,
    [string]$ArgLine = '',
    [string]$Cwd = '',
    [string]$Log = '',
    [string]$OutFile = '',
    [string]$ErrFile = ''
)
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$x = [Diagnostics.Process]::GetCurrentProcess()
if ([int64]$x.ProcessorAffinity -ne 0xF000 -or $x.PriorityClass -ne [Diagnostics.ProcessPriorityClass]::Idle) {
    Write-Output 'FAIL pin did not read back'
    exit 90
}
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
if ($Cwd) { Set-Location -LiteralPath $Cwd }
$psi = New-Object Diagnostics.ProcessStartInfo
$psi.FileName = $Exe
$psi.Arguments = $ArgLine
$psi.UseShellExecute = $false
$psi.WorkingDirectory = (Get-Location).Path
$psi.RedirectStandardOutput = $false
$psi.RedirectStandardError = $false
if ($Log) {
    # A cmd redirect keeps PS 5.1 from turning native stderr lines into errors.
    $psi.FileName = 'cmd.exe'
    $psi.Arguments = '/d /c ""' + $Exe + '" ' + $ArgLine + ' > "' + $Log + '" 2>&1"'
}
if ($OutFile) {
    # stdout and stderr to separate files
    $errTarget = if ($ErrFile) { $ErrFile } else { 'NUL' }
    $psi.FileName = 'cmd.exe'
    $psi.Arguments = '/d /c ""' + $Exe + '" ' + $ArgLine + ' > "' + $OutFile + '" 2> "' + $errTarget + '""'
}
$p = [Diagnostics.Process]::Start($psi)
$p.WaitForExit()
exit $p.ExitCode
