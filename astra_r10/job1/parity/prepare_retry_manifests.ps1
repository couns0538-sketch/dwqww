$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$m=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'build-launch01-manifest.json') -Raw | ConvertFrom-Json
$old=$m.output_directory
$m.output_directory=Join-Path $PSScriptRoot 'build-launch02'
$m.write_paths=@($m.write_paths | Where-Object {$_ -ne $old})+@($m.output_directory)
$m.arguments+=@('--tag','retry02')
$p=Join-Path $PSScriptRoot 'build-launch02-manifest.json'
if (Test-Path -LiteralPath $p) { throw 'New manifest required' }
$m | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $p -Encoding UTF8
$m=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'adapter-green02-manifest.json') -Raw | ConvertFrom-Json
$m.output_directory=Join-Path $PSScriptRoot 'adapter-green03'
$m.write_paths=@($m.output_directory)
$p=Join-Path $PSScriptRoot 'adapter-green03-manifest.json'
if (Test-Path -LiteralPath $p) { throw 'New manifest required' }
$m | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $p -Encoding UTF8
