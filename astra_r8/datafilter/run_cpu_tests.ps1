param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$py = 'F:/nnue_pytorch/venv/Scripts/python.exe'
[System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:CUDA_VISIBLE_DEVICES = '-1'
$env:HIP_VISIBLE_DEVICES = '-1'
$env:ROCR_VISIBLE_DEVICES = '-1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Refusing existing test output directory' }
& $py -c 'import sys; sys.path.insert(0,sys.argv[1]); from resource_policy import storage_guard; print(storage_guard(sys.argv[2],allowance=100_000_000))' $PSScriptRoot $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Test output preflight failed' }
$run = New-Item -ItemType Directory -Path $OutputDirectory
$env:TEMP = (New-Item -ItemType Directory -Path (Join-Path $run.FullName 'tmp')).FullName
$env:TMP = $env:TEMP
$env:TORCHINDUCTOR_CACHE_DIR = Join-Path $env:TEMP 'inductor'
$env:TRITON_CACHE_DIR = Join-Path $env:TEMP 'triton'
& $py -m pytest (Join-Path $PSScriptRoot 'tests') -q -p no:cacheprovider --basetemp (Join-Path $run.FullName 'pytest') *> (Join-Path $run.FullName 'pytest.log')
$testExit = $LASTEXITCODE
Get-Content -LiteralPath (Join-Path $run.FullName 'pytest.log') -Tail 18
& $py -c 'import sys; sys.path.insert(0,sys.argv[1]); from resource_policy import storage_guard; print(storage_guard(sys.argv[2],allowance=0))' $PSScriptRoot $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Post-test output reserve check failed' }
exit $testExit
