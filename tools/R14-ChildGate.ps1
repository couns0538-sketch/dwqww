#Requires -Version 7
param([Parameter(Mandatory=$true)][string]$Manifest)
$ErrorActionPreference='Stop'
# No payload process exists until the supervisor has assigned this gate to its job.
if ([Console]::ReadLine() -ne 'R14_READY') { exit 76 }
$command=Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
. D:\a14\tools\R14-OwnedJob.ps1
# Suspended creation plus explicit assignment closes the payload's spawn race.
exit [R14OwnedJob]::RunAssigned([string]$command.job,[string]$command.executable,[string[]]$command.arguments)
