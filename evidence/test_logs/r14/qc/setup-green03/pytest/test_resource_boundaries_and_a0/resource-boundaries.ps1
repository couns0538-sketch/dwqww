$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
. 'D:\a14\tools\Setup-R14Runtime.ps1' -Fixture -FixtureScript 'D:\a14\evidence\test_logs\r14\qc\setup-green03\pytest\test_resource_boundaries_and_a0\probe.py'
$script:dFree=50GB;$script:cFree=30GB;$script:owned=0
function Get-PSDrive([string]$Name) { if ($Name -eq 'D') { return @{Free=$script:dFree} }; return @{Free=$script:cFree} }
function Get-R14OwnedBytes { return $script:owned }
$results=@{}
try { Assert-R14Resources; $results['exact_floors']='PASS' } catch { $results['exact_floors']=$_.Exception.Message }
try { Assert-R14Resources 1; $results['d_reserve']='BAD' } catch { $results['d_reserve']=$_.Exception.Message }
$script:dFree=80GB;$script:cFree=30GB-1
try { Assert-R14Resources; $results['c_floor']='BAD' } catch { $results['c_floor']=$_.Exception.Message }
$script:cFree=30GB;$script:owned=4999999999
try { Assert-R14Resources 1; $results['owned_cap']='BAD' } catch { $results['owned_cap']=$_.Exception.Message }
$results | ConvertTo-Json | Set-Content -LiteralPath 'D:\a14\evidence\test_logs\r14\qc\setup-green03\pytest\test_resource_boundaries_and_a0\boundaries.json' -Encoding utf8
