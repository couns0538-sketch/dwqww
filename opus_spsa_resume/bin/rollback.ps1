# rollback.ps1 - deterministic rollback (Windows PowerShell 5.1).
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File rollback.ps1 -Config <cfg.json> -Baseline
#       prints the baseline (lock values; gate switches at 0) and writes nothing
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File rollback.ps1 -RunDir <dir> -ToCkpt <n>
#       appends a logged rollback record and writes a new checkpoint with theta and k of checkpoint n (never rewrites)
param(
    [string]$Config = '', [switch]$Baseline, [string]$RunDir = '', [int]$ToCkpt = -1,
    [long]$Mask = 0xF000,
    [string]$Python = 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
)
$ErrorActionPreference = 'Stop'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
$env:PYTHONDONTWRITEBYTECODE = '1'
$tool = Join-Path (Split-Path -Parent $PSScriptRoot) 'spsa\opus3_spsa.py'
if ($Baseline) {
    if (-not $Config) { throw '-Baseline needs -Config' }
    & $Python -I -B $tool rollback $Config --baseline
} else {
    if (-not $RunDir -or $ToCkpt -lt 0) { throw 'use -Config <cfg> -Baseline, or -RunDir <dir> -ToCkpt <n>' }
    & $Python -I -B $tool rollback $RunDir --to-ckpt "$ToCkpt"
}
exit $LASTEXITCODE
