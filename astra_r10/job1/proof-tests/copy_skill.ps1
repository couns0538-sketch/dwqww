$ErrorActionPreference = 'Stop'
$self = [Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass = 'Idle'
$self.ProcessorAffinity = [IntPtr]12
$target = 'D:\a10\wt\skills\forge-lock-proof-set'
if (Test-Path -LiteralPath $target) { throw 'Target must be new' }
Copy-Item -LiteralPath 'C:\Users\Administrator\.codex\skills\forge-lock-proof-set' -Destination $target -Recurse
