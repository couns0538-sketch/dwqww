param([Parameter(Mandatory=$true)][string]$Name,[Parameter(Mandatory=$true)][string[]]$Tests)
$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
if ($Name -notmatch '^[a-z0-9_-]+$') { throw 'Invalid name' }
$out='D:\a14\evidence\test_logs\r14\'+$Name
if (Test-Path -LiteralPath $out) { throw 'Existing test evidence' }
if ((Get-PSDrive D).Free -lt (50GB+64MB) -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk floor' }
New-Item -ItemType Directory -Path $out | Out-Null
$env:TEMP='D:\a14\tmp'
$env:TMP=$env:TEMP
$env:CUDA_VISIBLE_DEVICES='-1'
$env:HIP_VISIBLE_DEVICES='-1'
$env:PYTHONNOUSERSITE='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
& D:\a14\runtime\python\python.exe -I -B -m pytest @Tests -q -p no:cacheprovider --basetemp ($out+'\tmp') *> ($out+'\output.log')
$code=$LASTEXITCODE
Get-Content -LiteralPath ($out+'\output.log') -Tail 35
exit $code
