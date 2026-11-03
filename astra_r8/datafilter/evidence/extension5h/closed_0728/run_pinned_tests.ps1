param([Parameter(Mandatory=$true)][string]$Name, [Parameter(Mandatory=$true)][string[]]$Targets)
$ErrorActionPreference = 'Stop'
$repo = 'D:/grok-pc-data/dwqww/astra-r8-datafilter'
$core = Join-Path $repo 'astra_r8/datafilter'
$proof = Join-Path 'C:/astra8_data/extension5h_20261103' $Name
$python = 'F:/nnue_pytorch/venv/Scripts/python.exe'
[System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:CUDA_VISIBLE_DEVICES = ''
$env:HIP_VISIBLE_DEVICES = ''
$env:ROCR_VISIBLE_DEVICES = ''
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
if (Test-Path -LiteralPath $proof) { throw 'Existing proof directory' }
& $python -B -c 'import sys;sys.path.insert(0,sys.argv[1]);from resource_policy import storage_guard;print(storage_guard(sys.argv[2],allowance=50_000_000))' $core $proof
if ($LASTEXITCODE -ne 0) { throw 'Resource guard failed' }
New-Item -ItemType Directory -Path $proof | Out-Null
$env:TEMP = $proof
$env:TMP = $proof
$env:TORCHINDUCTOR_CACHE_DIR = Join-Path $proof 'inductor'
$env:TRITON_CACHE_DIR = Join-Path $proof 'triton'
function Get-SourcePins {
    $pins = [ordered]@{}
    Get-ChildItem -LiteralPath $core -Filter '*.py' | Sort-Object FullName | ForEach-Object { $pins[$_.FullName] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() }
    Get-ChildItem -LiteralPath (Join-Path $core 'tests') -Filter '*.py' | Sort-Object FullName | ForEach-Object { $pins[$_.FullName] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() }
    return $pins
}
$before = Get-SourcePins
$before | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $proof 'source_before.json') -Encoding utf8
$arguments = @('-B','-m','pytest','-q','-p','no:cacheprovider',"--basetemp=$proof/cases") + $Targets
@{executable=$python;arguments=$arguments;priority='BelowNormal';compute_threads=1;gpu_disabled=$true} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $proof 'command.json') -Encoding utf8
$started = [DateTime]::UtcNow
$watch = [Diagnostics.Stopwatch]::StartNew()
& $python @arguments *> (Join-Path $proof 'pytest.log')
$testExit = $LASTEXITCODE
$watch.Stop()
$after = Get-SourcePins
$after | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $proof 'source_after.json') -Encoding utf8
$stable = ($before | ConvertTo-Json -Compress) -eq ($after | ConvertTo-Json -Compress)
@{started_utc=$started.ToString('o');finished_utc=[DateTime]::UtcNow.ToString('o');seconds=$watch.Elapsed.TotalSeconds;exit_code=$testExit;source_stable=$stable;log_sha256=(Get-FileHash -LiteralPath (Join-Path $proof 'pytest.log') -Algorithm SHA256).Hash.ToLower()} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $proof 'exit.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $proof 'pytest.log') -Tail 24
& $python -B -c 'import sys,json;sys.path.insert(0,sys.argv[1]);from resource_policy import storage_guard;print(json.dumps(storage_guard(sys.argv[2],allowance=0),indent=2))' $core $proof > (Join-Path $proof 'resource.json')
if ($LASTEXITCODE -ne 0 -or -not $stable) { throw 'Post-test resource/source check failed' }
exit $testExit
