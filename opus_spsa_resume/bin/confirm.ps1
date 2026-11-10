# confirm.ps1 - entry point of the independent confirmation runner (Windows PowerShell 5.1).
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File confirm.ps1 -Command run -Protocol <p.json>
#       -Candidate <cand.json> -RunDir <dir> [-Mode dry-run|synthetic|replay|live] [-Resume] [-Live] [-MaxPairs N]
#   ... -Command select -TrainingRun <run dir> -CandidateOut <cand.json>     (fixed candidate rule)
#   ... -Command verify -RunDir <dir>
#   ... -Command audit -Protocol <p.json> -Candidate <cand.json> -Pgn <qa_gate.pgn>[,<more.pgn>]   (read-only)
# Default mode is dry-run (writes nothing, starts nothing). Idle priority and the CPU mask are set on this process first.
param(
    [ValidateSet('run', 'select', 'verify', 'audit')][string]$Command = 'run',
    [string]$Protocol = '', [string]$Candidate = '', [string]$RunDir = '',
    [ValidateSet('dry-run', 'synthetic', 'replay', 'live')][string]$Mode = 'dry-run',
    [switch]$Resume, [switch]$Live, [int]$MaxPairs = 0,
    [string]$TrainingRun = '', [string]$CandidateOut = '', [string[]]$Pgn = @(),
    [long]$Mask = 0xF000,
    [string]$Python = 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe',
    [string]$TempDir = 'D:\forge_jobs_20261107\opus3\tmp'
)
$ErrorActionPreference = 'Stop'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask; $me.Refresh()
if ([long]$me.ProcessorAffinity -ne $Mask -or "$($me.PriorityClass)" -ne 'Idle') { throw 'placement not applied' }
if ($TempDir) { New-Item -ItemType Directory -Force -Path $TempDir | Out-Null; $env:TEMP = $TempDir; $env:TMP = $TempDir }
$env:PYTHONDONTWRITEBYTECODE = '1'
$dir = Join-Path (Split-Path -Parent $PSScriptRoot) 'confirm'
switch ($Command) {
    'select' { & $Python -I -B (Join-Path $dir 'select_candidate.py') $TrainingRun $CandidateOut }
    'verify' { & $Python -I -B (Join-Path $dir 'confirm_runner.py') verify $RunDir }
    'audit'  { & $Python -I -B (Join-Path $dir 'confirm_runner.py') audit-pgn $Protocol $Candidate @($Pgn -split ',') }
    default {
        $argv = @('-I', '-B', (Join-Path $dir 'confirm_runner.py'), 'run', $Protocol, $Candidate, $RunDir, '--mode', $Mode)
        if ($Resume) { $argv += '--resume' }
        if ($Live) { $argv += '--live' }
        if ($MaxPairs -gt 0) { $argv += @('--max-pairs', "$MaxPairs") }
        & $Python $argv
    }
}
exit $LASTEXITCODE
