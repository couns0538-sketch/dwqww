$ErrorActionPreference='Stop'
$env:TEMP='unchanged'
function Get-ChildItem { param($LiteralPath,[switch]$Recurse,[switch]$File,[switch]$Force)
[pscustomobject]@{Length=5000000000L}
}
try { & 'D:\a14\tools\Invoke-R13.ps1' -Script 'D:\a14\evidence\test_logs\r14\qc\launcher-cap-green02\pytest\test_storage_cap_rejects_befor0\probe.py' -RunName 'storage-test' -TimeoutSeconds 2; throw 'accepted' }
catch { if ($_.Exception.Message -notmatch 'storage cap') { throw } }
if ($env:TEMP -ne 'unchanged') { throw 'parent environment changed' }
