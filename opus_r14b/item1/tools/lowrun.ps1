# lowrun.ps1 - Opus R14-B: run one program with this PowerShell process (and so every child it starts) at a low
# priority class on a CPU mask. Children inherit BelowNormal / Idle and the affinity from the start (no race).
# usage: powershell -NoProfile -File lowrun.ps1 -Mask 0xC -Priority BelowNormal -Exe <program> -ArgLine "<args>"
#        [-Out <stdout file>] [-Err <stderr file>]     (exit code = the program's)
param(
    [string]$Mask = '0xC',
    [ValidateSet('BelowNormal', 'Idle')][string]$Priority = 'BelowNormal',
    [Parameter(Mandatory = $true)][string]$Exe,
    [string]$ArgLine = '',
    [string]$Out = '',
    [string]$Err = ''
)
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = $Priority
$me.ProcessorAffinity = [IntPtr][Convert]::ToInt64($Mask.Replace('0x', ''), 16)
$sp = @{ FilePath = $Exe; NoNewWindow = $true; Wait = $true; PassThru = $true }
if ($ArgLine) { $sp.ArgumentList = $ArgLine }
if ($Out) { $sp.RedirectStandardOutput = $Out }
if ($Err) { $sp.RedirectStandardError = $Err }
$p = Start-Process @sp
exit $p.ExitCode
