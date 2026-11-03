param([Parameter(Mandatory=$true)][string]$Name, [string[]]$Tests=@('tests/test_r14_qc_fixes.py'))
$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
if ($Name -notmatch '^[a-z0-9_-]+$') { throw 'Invalid run name' }
if ((Get-PSDrive D).Free -lt (50GB+32MB) -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk floor' }
$root='D:\a14'
$directory=Join-Path $root ('evidence\test_logs\r14\qc\'+$Name)
if (Test-Path -LiteralPath $directory) { throw 'Never overwrite retained test logs' }
New-Item -ItemType Directory -Path $directory | Out-Null
$env:TEMP=Join-Path $directory 'tmp'
$env:TMP=$env:TEMP
New-Item -ItemType Directory -Path $env:TEMP | Out-Null
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONNOUSERSITE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:CUDA_VISIBLE_DEVICES='-1'
$env:HIP_VISIBLE_DEVICES='-1'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
Set-Location -LiteralPath $root
$python='D:\a14\runtime\python\python.exe'
$arguments=@('-I','-B','-m','pytest')+$Tests+@('-q','-p','no:cacheprovider','--basetemp',(Join-Path $directory 'pytest'))
@{python=$python;arguments=$arguments;time_vienna=((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+' Vienna')} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $directory 'command.json') -Encoding UTF8
& $python @arguments *> (Join-Path $directory 'output.log')
$exitCode=$LASTEXITCODE
@{exit_code=$exitCode;finished_vienna=((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+' Vienna')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $directory 'exit.json') -Encoding UTF8
Get-Content -LiteralPath (Join-Path $directory 'output.log') -Tail 25
exit $exitCode
