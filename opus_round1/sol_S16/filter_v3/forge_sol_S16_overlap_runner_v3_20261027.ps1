# Invoke with: pwsh -NoProfile -File this_script.ps1 owner_config.json
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Config,
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
& $Python -B (Join-Path $PSScriptRoot 'forge_sol_datafilter_v3_20261027.py') --config $Config
exit $LASTEXITCODE
