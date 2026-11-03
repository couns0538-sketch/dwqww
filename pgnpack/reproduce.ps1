param(
    [Parameter(Mandatory=$true)][string]$RunName,
    [Parameter(Mandatory=$true)][string]$Suite,
    [Parameter(Mandatory=$true)][string]$QC,
    [Parameter(Mandatory=$true)][string]$QCRun
)
$ErrorActionPreference='Stop'
if ($RunName -notmatch '^[A-Za-z0-9_-]+$') { throw 'Invalid run name' }
$root=Split-Path $PSScriptRoot -Parent
& (Join-Path $root 'tools/Invoke-R13.ps1') -Script (Join-Path $root 'tools/pack_scoped.py') -ScriptArguments @('--out',(Join-Path $PSScriptRoot "runs/$RunName"),'--suite',$Suite,'--qc',$QC,'--qc-run',$QCRun,'--threads','1') -RunName $RunName -TimeoutSeconds 600 -RequiredBytes 67108864
exit $LASTEXITCODE
