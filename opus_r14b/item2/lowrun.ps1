# lowrun.ps1 - Opus R14-B: run one program with this PowerShell process (and so every child it starts) at a low
# priority class on a CPU mask. Children inherit BelowNormal / Idle and the affinity from the start (no race).
# usage: powershell -NoProfile -File lowrun.ps1 -Mask 0xC -Priority BelowNormal -Exe <program> -ArgLine "<args>"
#        [-In <stdin file>] [-Out <stdout file>] [-Err <stderr file>]
# Exit code = the program's; 127 when it cannot be started (missing file, bad redirect path, an existing redirect
# target, a bad CPU mask) - never 0 for a program that did not run (fixed 2026-11-02 20:27: Start-Process errors used
# to end with exit 0). Never overwrites: an -Out / -Err file that exists is refused (bug hunt #15).
param(
    [string]$Mask = '0xC',
    [ValidateSet('BelowNormal', 'Idle')][string]$Priority = 'BelowNormal',
    [Parameter(Mandatory = $true)][string]$Exe,
    [string]$ArgLine = '',
    [string]$In = '',
    [string]$Out = '',
    [string]$Err = ''
)
# A mask that is not hexadecimal, 0 or beyond the PC's CPUs used to print an exception and then run the program on
# every CPU with exit 0 (bug hunt #15): refuse it.
try { $m = [Convert]::ToInt64($Mask, 16) } catch { $m = 0 }
if ($m -le 0) {
    [Console]::Error.WriteLine("lowrun: -Mask '$Mask' is not a hexadecimal CPU mask naming at least one CPU")
    exit 127
}
foreach ($f in @($Out, $Err)) {  # Start-Process would run the program with an invalid handle and report success
    $dir = if ($f) { Split-Path -Parent $f } else { '' }
    if ($dir -and -not (Test-Path -LiteralPath $dir -PathType Container)) {
        [Console]::Error.WriteLine("lowrun: folder of the redirect target $f does not exist")
        exit 127
    }
    if ($f -and (Test-Path -LiteralPath $f)) {  # Start-Process empties an existing target before the program runs
        [Console]::Error.WriteLine("lowrun: redirect target $f exists (never overwritten: use a new name)")
        exit 127
    }
}
if ($In -and -not (Test-Path -LiteralPath $In -PathType Leaf)) {
    [Console]::Error.WriteLine("lowrun: stdin file $In does not exist")
    exit 127
}
$me = [System.Diagnostics.Process]::GetCurrentProcess()
try {
    $me.PriorityClass = $Priority
    $me.ProcessorAffinity = [IntPtr]$m
} catch {
    [Console]::Error.WriteLine("lowrun: cannot set priority $Priority / CPU mask ${Mask}: $($_.Exception.Message)")
    exit 127
}
$sp = @{ FilePath = $Exe; NoNewWindow = $true; Wait = $true; PassThru = $true; ErrorAction = 'Stop' }
if ($ArgLine) { $sp.ArgumentList = $ArgLine }
if ($In) { $sp.RedirectStandardInput = $In }
if ($Out) { $sp.RedirectStandardOutput = $Out }
if ($Err) { $sp.RedirectStandardError = $Err }
try {
    $p = Start-Process @sp
} catch {
    [Console]::Error.WriteLine("lowrun: cannot start ${Exe}: $($_.Exception.Message)")
    exit 127
}
if ($null -eq $p -or $null -eq $p.ExitCode) {
    [Console]::Error.WriteLine("lowrun: no exit code for ${Exe}")
    exit 127
}
exit $p.ExitCode
