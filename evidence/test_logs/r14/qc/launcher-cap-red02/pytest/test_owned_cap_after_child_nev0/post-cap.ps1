$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
$env:TEMP='sentinel-TEMP'
$env:PYTHONPATH='sentinel-PYTHONPATH'
$env:CUDA_VISIBLE_DEVICES='sentinel-CUDA_VISIBLE_DEVICES'
$env:HIP_VISIBLE_DEVICES='sentinel-HIP_VISIBLE_DEVICES'
$global:fixtureGetChildItem=Get-Command Microsoft.PowerShell.Management\Get-ChildItem
function Get-ChildItem {
[CmdletBinding()] param([string[]]$LiteralPath,[switch]$Recurse,[switch]$File,[switch]$Force)
if ($LiteralPath.Count -eq 1 -and $LiteralPath[0] -eq 'D:\a14' -and (Test-Path -LiteralPath 'D:\a14\evidence\test_logs\r14\qc\launcher-cap-red02\pytest\test_owned_cap_after_child_nev0\child-started')) {
return [pscustomobject]@{Length=5000000000L}
}
& $global:fixtureGetChildItem @PSBoundParameters
}
& 'D:\a14\tools\Invoke-R13.ps1' -Script 'D:\a14\evidence\test_logs\r14\qc\launcher-cap-red02\pytest\test_owned_cap_after_child_nev0\probe.py' -RunName 'cap-a7b84d4d8034' -TimeoutSeconds 30
$nativeExit=$LASTEXITCODE
$values=@{}
$values['TEMP']=$env:TEMP
$values['PYTHONPATH']=$env:PYTHONPATH
$values['CUDA_VISIBLE_DEVICES']=$env:CUDA_VISIBLE_DEVICES
$values['HIP_VISIBLE_DEVICES']=$env:HIP_VISIBLE_DEVICES
@{env=$values;priority=[string][Diagnostics.Process]::GetCurrentProcess().PriorityClass} | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath 'D:\a14\evidence\test_logs\r14\qc\launcher-cap-red02\pytest\test_owned_cap_after_child_nev0\parent.json' -Encoding utf8
exit $nativeExit
