param(
    [string]$Compiler = 'C:\msys64\ucrt64\bin\g++.exe',
    [string]$OutputName = 'chain_native.exe'
)
$ErrorActionPreference = 'Stop'
if ((Get-PSDrive D).Free -lt 50GB -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk floor breached' }
if ($OutputName -notmatch '^[a-zA-Z0-9_.-]+\.exe$') { throw 'Output must be a simple executable name' }
$root = $PSScriptRoot
$build = Join-Path $root 'build'
$temp = Join-Path $build 'tmp'
if (Test-Path -LiteralPath (Join-Path $build $OutputName)) { throw 'Output already exists; use a fresh candidate name' }
New-Item -ItemType Directory -Force -Path $temp | Out-Null
$saved = @{}
foreach ($name in @('TEMP','TMP','PATH','CUDA_VISIBLE_DEVICES','HIP_VISIBLE_DEVICES','OMP_NUM_THREADS')) {
    $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
$process = [System.Diagnostics.Process]::GetCurrentProcess()
$oldPriority = $process.PriorityClass
try {
    $process.PriorityClass = 'Idle'
    $env:TEMP = $temp; $env:TMP = $temp
    $env:PATH = (Split-Path -Parent $Compiler) + ';' + $env:PATH
    $env:CUDA_VISIBLE_DEVICES = '-1'; $env:HIP_VISIBLE_DEVICES = '-1'; $env:OMP_NUM_THREADS = '1'
    [pscustomobject]@{compiler=$Compiler;input=(Join-Path $root 'chain_native.cpp');output=(Join-Path $build $OutputName);stage='build_start'} | ConvertTo-Json -Compress
    & $Compiler '-std=c++17' '-O2' '-static' '-Wall' '-Wextra' '-Wpedantic' (Join-Path $root 'chain_native.cpp') '-o' (Join-Path $build $OutputName)
    if ($LASTEXITCODE -ne 0) { throw "Compiler exit $LASTEXITCODE" }
    [pscustomobject]@{stage='build_complete';exit_code=$LASTEXITCODE} | ConvertTo-Json -Compress
} finally {
    foreach ($name in $saved.Keys) { [Environment]::SetEnvironmentVariable($name, $saved[$name], 'Process') }
    $process.PriorityClass = $oldPriority
}
