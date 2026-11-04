$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
Remove-Item -LiteralPath 'Env:TEMP' -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'Env:TMP' -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'Env:PYTHONNOUSERSITE' -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'Env:PYTHONDONTWRITEBYTECODE' -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'Env:CUDA_VISIBLE_DEVICES' -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'Env:HIP_VISIBLE_DEVICES' -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'Env:OMP_NUM_THREADS' -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'Env:OPENBLAS_NUM_THREADS' -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'Env:MKL_NUM_THREADS' -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'Env:PIP_CACHE_DIR' -ErrorAction SilentlyContinue
$failure=$null
try {
& 'D:\a14\tools\Setup-R14Runtime.ps1' -Fixture -FixtureScript 'D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_unset_caller_environment_0\probe.py' -FixtureFailGuardAfter 0 -ChildTimeoutSeconds 30
} catch { $failure=$_.Exception.Message }
$values=@{}
$values['TEMP']=$env:TEMP
$values['TMP']=$env:TMP
$values['PYTHONNOUSERSITE']=$env:PYTHONNOUSERSITE
$values['PYTHONDONTWRITEBYTECODE']=$env:PYTHONDONTWRITEBYTECODE
$values['CUDA_VISIBLE_DEVICES']=$env:CUDA_VISIBLE_DEVICES
$values['HIP_VISIBLE_DEVICES']=$env:HIP_VISIBLE_DEVICES
$values['OMP_NUM_THREADS']=$env:OMP_NUM_THREADS
$values['OPENBLAS_NUM_THREADS']=$env:OPENBLAS_NUM_THREADS
$values['MKL_NUM_THREADS']=$env:MKL_NUM_THREADS
$values['PIP_CACHE_DIR']=$env:PIP_CACHE_DIR
@{env=$values;failure=$failure;priority=[string][Diagnostics.Process]::GetCurrentProcess().PriorityClass} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath 'D:\a14\evidence\test_logs\r14\qc\setup-pipe-red01\pytest\test_unset_caller_environment_0\parent.json' -Encoding utf8
