# Native Windows/MSYS2 UCRT64 GNU g++ pure-PGO worker.
# Invoke this script as a child of the reviewed Job 1 resource supervisor.
[CmdletBinding()]
param(
    [ValidateSet('all','baseline','check-baseline','generate','train','check-instrumented','use','check-use','validate')][string]$Phase,
    [string]$Source = (Join-Path $PSScriptRoot 'forge_sol_lock_source_20261025'),
    [string]$Out = (Join-Path $PSScriptRoot ('forge_sol_pgo_run_20261025_' + [DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss'))),
    [string]$Recipe = (Join-Path $PSScriptRoot 'forge_sol_lock_pc_recipe_20261025.ps1'),
    [string]$Gpp = 'C:\msys64\ucrt64\bin\g++.exe',
    [string]$Python = 'C:\Python314\python.exe',
    [string]$CMake = 'C:\msys64\ucrt64\bin\cmake.exe'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrEmpty($Phase)) {
    # Public entry: create the real native envelope and run the complete job.
    # -Phase is an internal interface for callers already inside that envelope.
    & (Join-Path $PSScriptRoot 'forge_sol_pgo_winqual_script_20261025.ps1') -Source $Source -Out $Out -Recipe $Recipe -Gpp $Gpp -Python $Python -CMake $CMake
    exit $LASTEXITCODE
}
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'Native Windows required; a Linux/Wine result cannot verify the PC recipe.'
}
if ($env:FORGE_PGO_REVIEWED_ENVELOPE -ne 'ACTIVE') {
    throw 'Launch through the reviewed Job 1 supervisor; this worker enforces no resource limits itself.'
}
foreach ($file in @($Gpp,$Python,$Recipe,(Join-Path $PSScriptRoot 'forge_sol_pgo_worker_20261025.py'))) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Required file missing: $file" }
}
# Preserve exact recovered UCRT64 compiler/runtime selection. Python launches
# direct g++ argv without shell parsing, and retains explicit -static -pthread.
$env:PATH = (Split-Path -Parent $Gpp) + ';' + $env:PATH
& $Python (Join-Path $PSScriptRoot 'forge_sol_pgo_worker_20261025.py') --platform pc-msys2 --phase $Phase --source $Source --out $Out --recipe $Recipe --cxx $Gpp --cmake $CMake
if ($LASTEXITCODE -ne 0) { throw "PGO phase $Phase failed with exit $LASTEXITCODE; retain its evidence." }
