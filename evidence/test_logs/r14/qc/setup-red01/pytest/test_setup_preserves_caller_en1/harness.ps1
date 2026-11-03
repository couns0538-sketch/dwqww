$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
$env:TEMP='sentinel-TEMP'
$env:TMP='sentinel-TMP'
$env:PYTHONNOUSERSITE='sentinel-PYTHONNOUSERSITE'
$env:PYTHONDONTWRITEBYTECODE='sentinel-PYTHONDONTWRITEBYTECODE'
$env:CUDA_VISIBLE_DEVICES='sentinel-CUDA_VISIBLE_DEVICES'
$env:HIP_VISIBLE_DEVICES='sentinel-HIP_VISIBLE_DEVICES'
$env:OMP_NUM_THREADS='sentinel-OMP_NUM_THREADS'
$env:OPENBLAS_NUM_THREADS='sentinel-OPENBLAS_NUM_THREADS'
$env:MKL_NUM_THREADS='sentinel-MKL_NUM_THREADS'
$env:PIP_CACHE_DIR='sentinel-PIP_CACHE_DIR'
function global:D:\a14\evidence\test_logs\r14\qc\setup-red01\pytest\test_setup_preserves_caller_en1\runtime\python\python.exe { & 'D:\a14\runtime\python\python.exe' -I -B 'D:\a14\evidence\test_logs\r14\qc\setup-red01\pytest\test_setup_preserves_caller_en1\probe.py'; $global:LASTEXITCODE=$LASTEXITCODE }
$failure=$null
try {
& 'D:\a14\evidence\test_logs\r14\qc\setup-red01\pytest\test_setup_preserves_caller_en1\setup.ps1'
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
@{env=$values;failure=$failure;priority=[string][Diagnostics.Process]::GetCurrentProcess().PriorityClass} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath 'D:\a14\evidence\test_logs\r14\qc\setup-red01\pytest\test_setup_preserves_caller_en1\parent.json' -Encoding utf8
