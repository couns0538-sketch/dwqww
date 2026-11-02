$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$m=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'prepare-launch01-manifest.json') -Raw | ConvertFrom-Json
$oldOut=$m.output_directory
$m.output_directory=Join-Path $PSScriptRoot 'prepare-launch02'
$m.write_paths=@($m.write_paths | Where-Object {$_ -ne $oldOut})+@($m.output_directory)
$sourceManifest='D:\a10\wt\astra_r9\evidence\c1-source.json'
$m.read_paths+=@($sourceManifest)
$m.arguments+=@('--source-manifest',$sourceManifest)
$path=Join-Path $PSScriptRoot 'prepare-launch02-manifest.json'
if (Test-Path -LiteralPath $path) { throw 'New manifest required' }
$m | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $path -Encoding UTF8
