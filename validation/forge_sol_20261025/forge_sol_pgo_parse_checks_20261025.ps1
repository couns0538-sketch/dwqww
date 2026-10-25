# Portable syntax/type checks only. Never constructs a native Session.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
foreach ($name in @('forge_sol_pgo_build_20261025.ps1','forge_sol_pgo_winqual_script_20261025.ps1')) {
    $tokens = $null; $errors = $null
    $null = [Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot $name),[ref]$tokens,[ref]$errors)
    if ($errors.Count) { $errors | ForEach-Object { Write-Host $_.Message }; exit 1 }
    Write-Host "PARSE PASS $name"
}
Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'forge_sol_pgo_native_resource_20261025.cs'))) -Language CSharp
Write-Host 'C# TYPE COMPILE PASS; no Session constructor, Win32 call, chess engine, GCC or timing executed'
