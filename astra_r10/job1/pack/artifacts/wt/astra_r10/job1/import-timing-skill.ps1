$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity=[IntPtr]12
$target='D:\a10\wt\skills\abba-nps-timing'
if(Test-Path $target){throw 'skill already imported'}
Copy-Item C:\Users\Administrator\.codex\skills\abba-nps-timing $target -Recurse
Add-Content "$target\SKILL.md" @'

## R10 reviewed native adapter

The branch's astra_r10/job1/timing/ contains the reviewed native Windows adapter,
fixed 10-block A/A then 10-block ABBA protocol, external-wall geometric block
statistics, immutable protocol/input binding and native topology checks. Use its
PROTOCOL.md and actual frozen protocol.json; the template is intentionally not
executable. Root RESULTS.md records focused reviews and native/fixture scope.
Calibration defaults for this R10 task are abs median<=0.5%, IQR<=1 percentage
point, every eligible block within +/-2%. Do not generalize or relax these after
observing results. Original read-only summary helper remains available unchanged.
'@
