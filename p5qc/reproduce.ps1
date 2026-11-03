param([Parameter(Mandatory=$true)][string]$RunName)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if ($RunName -notmatch '^[A-Za-z0-9_-]+$') { throw 'Invalid run name' }
& (Join-Path $root 'tools/Invoke-R13.ps1') -Script (Join-Path $root 'tools/p5_qc.py') -ScriptArguments @('--out',(Join-Path $PSScriptRoot "runs/$RunName"),'--threads','1') -RunName $RunName -TimeoutSeconds 2400 -RequiredBytes 536870912
exit $LASTEXITCODE
