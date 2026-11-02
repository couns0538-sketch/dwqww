param([Parameter(Mandatory=$true)][string]$Tag)
$ErrorActionPreference = 'Stop'
if ($Tag -notmatch '^[a-zA-Z0-9_-]+$') { throw 'Invalid tag' }
$self = [Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass = 'Idle'
$self.ProcessorAffinity = [IntPtr]12
$evidence = Join-Path $PSScriptRoot $Tag
if (Test-Path -LiteralPath $evidence) { throw 'Evidence output already exists' }
New-Item -ItemType Directory -Path $evidence | Out-Null
$env:TEMP = $evidence; $env:TMP = $evidence
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:OMP_NUM_THREADS = '1'; $env:OPENBLAS_NUM_THREADS = '1'; $env:MKL_NUM_THREADS = '1'
$stdout = Join-Path $evidence 'stdout.log'
$stderr = Join-Path $evidence 'stderr.log'
$child = Start-Process -FilePath 'D:\a10\python\python.exe' -ArgumentList @('-B', 'D:\a10\wt\skills\forge-lock-proof-set\scripts\test_contract_modes.py') -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
$rc = $child.ExitCode
@{exit_code=$rc; priority='Idle'; affinity=12; scope='fixture'; utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence 'exit.json')
Get-Content -LiteralPath $stdout
Get-Content -LiteralPath $stderr
exit $rc
