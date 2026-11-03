$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
$root='D:\a14\evidence\test_logs\r14\qc\setup-red01\pytest\test_setup_preserves_caller_en0'
$runtime=Join-Path $root 'runtime'
$downloads=Join-Path $runtime 'downloads'
$pythonRoot=Join-Path $runtime 'python'
if ((Get-PSDrive D).Free -lt (50GB+512MB) -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk admission refused' }
New-Item -ItemType Directory -Force -Path $downloads,$pythonRoot | Out-Null
$env:TEMP=Join-Path $root 'tmp'
$env:TMP=$env:TEMP
$env:PYTHONNOUSERSITE='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:CUDA_VISIBLE_DEVICES='-1'
$env:HIP_VISIBLE_DEVICES='-1'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:PIP_CACHE_DIR=Join-Path $runtime 'pip-cache'
$archive=Join-Path $downloads 'python-3.12.10-embed-amd64.zip'
if (-not (Test-Path -LiteralPath $archive)) {
    Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip' -OutFile $archive
}
if (-not (Test-Path -LiteralPath (Join-Path $pythonRoot 'python.exe'))) { Expand-Archive -LiteralPath $archive -DestinationPath $pythonRoot }
$utf8=New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $pythonRoot 'python312._pth'), "python312.zip`n.`nLib\site-packages`nD:\a14\tools`nimport site`n",$utf8)
$bootstrap=Join-Path $downloads 'get-pip.py'
if (-not (Test-Path -LiteralPath $bootstrap)) { Invoke-WebRequest -UseBasicParsing -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile $bootstrap }
$python=Join-Path $pythonRoot 'python.exe'
& $python -I -B $bootstrap --no-cache-dir --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { throw 'pip bootstrap failed' }
& $python -I -B -m pip install --no-cache-dir --disable-pip-version-check setuptools wheel
if ($LASTEXITCODE -ne 0) { throw 'owned build dependencies failed' }
& $python -I -B -m pip install --no-build-isolation --no-cache-dir --disable-pip-version-check python-chess numpy pytest psutil
if ($LASTEXITCODE -ne 0) { throw 'runtime dependencies failed' }
& $python -I -B -m pip freeze --all
if ($LASTEXITCODE -ne 0) { throw 'runtime inventory failed' }
Get-FileHash -Algorithm MD5 -LiteralPath $python,$archive,$bootstrap | ConvertTo-Json
