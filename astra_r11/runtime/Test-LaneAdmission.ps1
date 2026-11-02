$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'lane_admission.ps1')
$rows=@(
 [pscustomobject]@{pid=100;name='own';command='self';mask=12},
 [pscustomobject]@{pid=101;name='wide';command='worker';mask=65535},
 [pscustomobject]@{pid=102;name='narrow12';command='worker';mask=12},
 [pscustomobject]@{pid=103;name='narrow15';command='worker';mask=15},
 [pscustomobject]@{pid=104;name='gateOther';command='worker';mask=65520},
 [pscustomobject]@{pid=105;name='timing';command='run_tmfit';mask=65535}
)
$found=@(Get-R11LaneConflicts $rows @(100) 65535)
if(($found.pid -join ',') -ne '102,103,105'){throw 'Lane predicate failed pinned12/15/timing admission'}
Write-Output 'PASS: unrelated masks12/15 and timing refused; own/normal/all-other-CPU accepted'
