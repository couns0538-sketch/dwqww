param([Parameter(Mandatory=$true)][string]$RunName)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
& (Join-Path $root 'tools/Invoke-R13.ps1') -Script (Join-Path $root 'tools/run_tests.py') -RunName $RunName -TimeoutSeconds 1800 -RequiredBytes 536870912 -WithDatafilterRuntime
exit $LASTEXITCODE
