#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$self = [Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass = [Diagnostics.ProcessPriorityClass]::Idle
$self.ProcessorAffinity = [IntPtr]4
if ([IO.DriveInfo]::new('C:\').AvailableFreeSpace -lt 30GB -or [IO.DriveInfo]::new('D:\').AvailableFreeSpace -lt 50GB) { throw 'R10 disk floor' }
$destination = 'D:\a10\wt\skills\grok-pc-safe-run'
if (Test-Path -LiteralPath $destination) { throw 'Destination already exists' }
Copy-Item -LiteralPath 'C:\Users\Administrator\.codex\skills\grok-pc-safe-run' -Destination $destination -Recurse
Get-FileHash -Algorithm SHA256 -LiteralPath ($destination + '\scripts\Invoke-GrokPcSafeRun.ps1')
