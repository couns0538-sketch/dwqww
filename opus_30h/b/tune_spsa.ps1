# tune_spsa.ps1 - Opus 30-h job: re-runnable entry point of the SPSA tuner (tune_spsa.py). Starts a new run, or resumes
# the run in -RunDir when it already exists (after a crash, a reboot, a deadline or a stop) - the run's own config and
# params copy are used, only -Threads / -Cpus may change.
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File tune_spsa.ps1 -Config <config.json> -RunDir <dir>
#        [-Until 'YYYY-MM-DD HH:MM'] [-Threads 2] [-Cpus '0,1'] [-MaxPairs N] [-TotalPairs N]
#        powershell ... -File tune_spsa.ps1 -RunDir <dir> -Stop      (ask the running tuner to stop after its batch)
#        powershell ... -File tune_spsa.ps1 -RunDir <dir> -Status
# Exit code = the tuner's (0 done / stopped, 2 bad arguments, 3 a batch failed three times).
param(
    [string]$Config = '',
    [Parameter(Mandatory = $true)][string]$RunDir,
    [string]$Until = '',
    [int]$Threads = 0,
    [string]$Cpus = '',
    [int]$MaxPairs = 0,
    [int]$TotalPairs = 0,
    [switch]$Stop,
    [switch]$Status
)
$py = 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
$tuner = Join-Path $PSScriptRoot 'tune_spsa.py'
if (-not (Test-Path -LiteralPath $py)) { [Console]::Error.WriteLine("tune_spsa.ps1: python not found: $py"); exit 2 }
if ($Stop) { & $py -I -B $tuner stop $RunDir; exit $LASTEXITCODE }
if ($Status) { & $py -I -B $tuner status $RunDir; exit $LASTEXITCODE }
$resume = Test-Path -LiteralPath (Join-Path $RunDir 'config.json')
if (-not $Config) {
    if (-not $resume) { [Console]::Error.WriteLine('tune_spsa.ps1: -Config is needed for a new run'); exit 2 }
    $Config = Join-Path $RunDir 'config.json'   # a resume may use the run's own copy
}
$argv = @('-I', '-B', $tuner, 'run', $Config, $RunDir)
if ($resume) { $argv += '--resume' }
if ($Until) { $argv += @('--until', $Until) }
if ($Threads -gt 0) { $argv += @('--threads', "$Threads") }
if ($Cpus) { $argv += @('--cpus', $Cpus) }
if ($MaxPairs -gt 0) { $argv += @('--max-pairs', "$MaxPairs") }
if ($TotalPairs -gt 0) { $argv += @('--total-pairs', "$TotalPairs") }
Write-Output ("tune_spsa.ps1: {0} {1}" -f $(if ($resume) { 'resume' } else { 'new run' }), $RunDir)
& $py @argv
exit $LASTEXITCODE
