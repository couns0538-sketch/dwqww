$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$m=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'adapter-green02-manifest.json') -Raw | ConvertFrom-Json
$m.output_directory=Join-Path $PSScriptRoot 'probe-launch01'
$m.arguments=@('-B',(Join-Path $PSScriptRoot 'probe_compiler_path.py'),'--threads','1','--out','D:\a10\parity-compiler-probe01')
$m.write_paths=@($m.output_directory,'D:\a10\parity-compiler-probe01')
$p=Join-Path $PSScriptRoot 'probe-launch01-manifest.json'
if (Test-Path -LiteralPath $p) { throw 'New manifest required' }
$m | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $p -Encoding UTF8
