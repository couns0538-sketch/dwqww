#requires -Version 5.1
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]4
if ([IO.DriveInfo]::new('C:\').AvailableFreeSpace -lt 30GB -or [IO.DriveInfo]::new('D:\').AvailableFreeSpace -lt 50GB) {throw 'R10 floor'}
$target='D:\a10\wt\skills\gate-handover-pack'
if (Test-Path -LiteralPath $target) {throw 'Preserve existing target'}
Copy-Item -LiteralPath 'C:\Users\Administrator\.codex\skills\gate-handover-pack' -Destination $target -Recurse
