# spsa.ps1 - entry point of the opus3 SPSA harness (Windows PowerShell 5.1).
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File spsa.ps1 -Config <cfg.json> -RunDir <dir>
#       [-Mode dry-run|synthetic|replay|live] [-Resume] [-Live] [-MaxBatches N] [-MaxPairs N] [-TotalPairs N]
#       [-Command run|status|verify|export] [-Out <dir>] [-Mask 0xF000] [-Python <python.exe>] [-TempDir <dir>]
# Default mode is dry-run: validates, checks pins, prints the next fastchess command, writes nothing, starts nothing.
# Live mode additionally needs -Live, config.live.enabled = true and <RunDir>\LIVE_ACK.txt holding the config sha256.
# The process sets Idle priority and the CPU mask on itself first; every child (Python, fastchess, engines) inherits.
param(
    [string]$Config = '',
    [Parameter(Mandatory = $true)][string]$RunDir,
    [ValidateSet('dry-run', 'synthetic', 'replay', 'live')][string]$Mode = 'dry-run',
    [ValidateSet('run', 'status', 'verify', 'export')][string]$Command = 'run',
    [switch]$Resume,
    [switch]$Live,
    [int]$MaxBatches = 0,
    [int]$MaxPairs = 0,
    [int]$TotalPairs = 0,
    [string]$Out = '',
    [long]$Mask = 0xF000,
    [string]$Python = 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe',
    [string]$TempDir = 'D:\forge_jobs_20261107\opus3\tmp',
    [double]$ReserveGiB = 30
)
$ErrorActionPreference = 'Stop'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask; $me.Refresh()
if ([long]$me.ProcessorAffinity -ne $Mask -or "$($me.PriorityClass)" -ne 'Idle') { throw 'placement not applied' }
if ($TempDir) { New-Item -ItemType Directory -Force -Path $TempDir | Out-Null; $env:TEMP = $TempDir; $env:TMP = $TempDir }
$env:PYTHONDONTWRITEBYTECODE = '1'
$drive = (Split-Path -Qualifier ([IO.Path]::GetFullPath($RunDir))).TrimEnd(':')
$free = (Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='${drive}:'").FreeSpace / 1GB
if ($Command -eq 'run' -and $Mode -ne 'dry-run' -and ($free - 0.1) -lt $ReserveGiB) {
    throw ("PENDING RESOURCE: {0}: has {1:N2} GiB free, below the {2} GiB reserve" -f $drive, $free, $ReserveGiB)
}
$tool = Join-Path (Split-Path -Parent $PSScriptRoot) 'spsa\opus3_spsa.py'
$argv = @('-I', '-B', $tool, $Command)
if ($Command -eq 'run') {
    if (-not $Config) { throw '-Config is required for run' }
    $argv += @($Config, $RunDir, '--mode', $Mode)
    if ($Resume) { $argv += '--resume' }
    if ($Live) { $argv += '--live' }
    if ($MaxBatches -gt 0) { $argv += @('--max-batches', "$MaxBatches") }
    if ($MaxPairs -gt 0) { $argv += @('--max-pairs', "$MaxPairs") }
    if ($TotalPairs -gt 0) { $argv += @('--total-pairs', "$TotalPairs") }
} elseif ($Command -eq 'export') {
    if (-not $Out) { throw '-Out is required for export' }
    $argv += @($RunDir, '--out', $Out)
} else {
    $argv += $RunDir
}
& $Python $argv
exit $LASTEXITCODE
