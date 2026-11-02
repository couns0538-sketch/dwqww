$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$base=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'adapter-green01-manifest.json') -Raw | ConvertFrom-Json
foreach ($tag in @('adapter-red02','adapter-green02')) {
  $base.output_directory=Join-Path $PSScriptRoot $tag
  $base.write_paths=@($base.output_directory)
  $base.read_paths=@($base.read_paths | Where-Object {$_ -ne 'D:\a10\wt\astra_r9\evidence\c1-source.json'})+@('D:\a10\wt\astra_r9\evidence\c1-source.json')
  $path=Join-Path $PSScriptRoot ($tag+'-manifest.json')
  if (Test-Path -LiteralPath $path) { throw 'New manifest required' }
  $base | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $path -Encoding UTF8
}
