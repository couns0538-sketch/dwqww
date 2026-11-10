# rollback.ps1 - deterministic rollback (Windows PowerShell 5.1).
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File rollback.ps1 -Config <cfg.json> -Baseline
#       prints the baseline (lock values; gate switches at 0) and writes nothing
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File rollback.ps1 -RunDir <dir> -ToCkpt <n> [-ReopenComplete]
#       appends a logged rollback record and writes a new checkpoint with theta and k of checkpoint n (never rewrites).
#       A COMPLETE run is refused unless -ReopenComplete is given, and a reopened run can never yield a candidate
#       (confirm/select_candidate.py: no re-tuning until lucky).
param(
    [string]$Config = '', [switch]$Baseline, [string]$RunDir = '', [int]$ToCkpt = -1, [switch]$ReopenComplete,
    [long]$Mask = 0xF000,
    [string]$Python = 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
)
$ErrorActionPreference = 'Stop'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask; $me.Refresh()
if ([long]$me.ProcessorAffinity -ne $Mask -or "$($me.PriorityClass)" -ne 'Idle') { throw 'placement not applied' }
$env:PYTHONDONTWRITEBYTECODE = '1'
$tool = Join-Path (Split-Path -Parent $PSScriptRoot) 'spsa\opus3_spsa.py'
if ($Baseline) {
    if (-not $Config) { throw '-Baseline needs -Config' }
    & $Python -I -B $tool rollback $Config --baseline
} else {
    if (-not $RunDir -or $ToCkpt -lt 0) { throw 'use -Config <cfg> -Baseline, or -RunDir <dir> -ToCkpt <n>' }
    $rargs = @('-I', '-B', $tool, 'rollback', $RunDir, '--to-ckpt', "$ToCkpt")
    if ($ReopenComplete) { $rargs += '--reopen-complete' }
    & $Python $rargs
}
exit $LASTEXITCODE
