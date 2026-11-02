$ErrorActionPreference = 'Stop'
$self = [Diagnostics.Process]::GetCurrentProcess(); $self.PriorityClass='Idle'; $self.ProcessorAffinity=[IntPtr]12
$target='D:\a10\wt\skills\eval-exact-simd-port'
if (Test-Path -LiteralPath $target) { throw 'Target exists' }
Copy-Item -LiteralPath 'C:\Users\Administrator\.codex\skills\eval-exact-simd-port' -Destination $target -Recurse
