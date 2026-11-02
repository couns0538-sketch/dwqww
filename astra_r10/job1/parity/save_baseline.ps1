$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess(); $self.PriorityClass='Idle'; $self.ProcessorAffinity=[IntPtr]12
$path=Join-Path $PSScriptRoot 'check_eval_parity_original.py'
if (Test-Path -LiteralPath $path) { throw 'Baseline snapshot already exists' }
Copy-Item -LiteralPath 'D:\a10\wt\skills\eval-exact-simd-port\scripts\check_eval_parity.py' -Destination $path
