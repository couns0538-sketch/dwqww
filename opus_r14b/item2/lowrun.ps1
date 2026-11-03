# lowrun.ps1 - Opus R14-B: run one program with this PowerShell process (and so every child it starts) at a low
# priority class on a CPU mask. Children inherit BelowNormal / Idle and the affinity from the start (no race).
# usage: powershell -NoProfile -File lowrun.ps1 -Mask 0xC -Priority BelowNormal -Exe <program> -ArgLine "<args>"
#        [-In <stdin file>] [-Out <stdout file>] [-Err <stderr file>]
# Exit code = the program's; 127 when it cannot be started (missing file, bad redirect path) - never 0 for a program
# that did not run (fixed 2026-11-02 20:27: Start-Process errors used to end with exit 0).
param(
    [string]$Mask = '0xC',
    [ValidateSet('BelowNormal', 'Idle')][string]$Priority = 'BelowNormal',
    [Parameter(Mandatory = $true)][string]$Exe,
    [string]$ArgLine = '',
    [string]$In = '',
    [string]$Out = '',
    [string]$Err = ''
)
foreach ($f in @($Out, $Err)) {  # Start-Process would run the program with an invalid handle and report success
    $dir = if ($f) { Split-Path -Parent $f } else { '' }
    if ($dir -and -not (Test-Path -LiteralPath $dir -PathType Container)) {
        [Console]::Error.WriteLine("lowrun: folder of the redirect target $f does not exist")
        exit 127
    }
}
if ($In -and -not (Test-Path -LiteralPath $In -PathType Leaf)) {
    [Console]::Error.WriteLine("lowrun: stdin file $In does not exist")
    exit 127
}
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = $Priority
$me.ProcessorAffinity = [IntPtr][Convert]::ToInt64($Mask.Replace('0x', ''), 16)
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
