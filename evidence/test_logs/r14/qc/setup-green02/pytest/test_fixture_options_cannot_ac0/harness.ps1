$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
[Environment]::SetEnvironmentVariable('TEMP','sentinel-TEMP','Process')
[Environment]::SetEnvironmentVariable('TMP','sentinel-TMP','Process')
[Environment]::SetEnvironmentVariable('PYTHONNOUSERSITE','sentinel-PYTHONNOUSERSITE','Process')
[Environment]::SetEnvironmentVariable('PYTHONDONTWRITEBYTECODE','sentinel-PYTHONDONTWRITEBYTECODE','Process')
[Environment]::SetEnvironmentVariable('CUDA_VISIBLE_DEVICES','sentinel-CUDA_VISIBLE_DEVICES','Process')
[Environment]::SetEnvironmentVariable('HIP_VISIBLE_DEVICES','sentinel-HIP_VISIBLE_DEVICES','Process')
[Environment]::SetEnvironmentVariable('OMP_NUM_THREADS','sentinel-OMP_NUM_THREADS','Process')
[Environment]::SetEnvironmentVariable('OPENBLAS_NUM_THREADS','sentinel-OPENBLAS_NUM_THREADS','Process')
[Environment]::SetEnvironmentVariable('MKL_NUM_THREADS','sentinel-MKL_NUM_THREADS','Process')
[Environment]::SetEnvironmentVariable('PIP_CACHE_DIR','sentinel-PIP_CACHE_DIR','Process')
$failure=$null
try {
& 'D:\a14\tools\Setup-R14Runtime.ps1' -FixtureScript 'D:\a14\evidence\test_logs\r14\qc\setup-green02\pytest\test_fixture_options_cannot_ac0\probe.py' -FixtureFailGuardAfter 0 -ChildTimeoutSeconds 30
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
@{env=$values;failure=$failure;priority=[string][Diagnostics.Process]::GetCurrentProcess().PriorityClass} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath 'D:\a14\evidence\test_logs\r14\qc\setup-green02\pytest\test_fixture_options_cannot_ac0\parent.json' -Encoding utf8
