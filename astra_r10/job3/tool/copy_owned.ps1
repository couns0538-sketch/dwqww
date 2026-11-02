$ErrorActionPreference = 'Stop'
$sourceRoot = 'D:\a10\job3\source'
$targetRoot = 'D:\a10\wt\astra_r10\job3\tool'
$map = @{
 'datafilter' = @('astra_r8/datafilter/convert_forge.py','astra_r8/datafilter/records.py','astra_r8/datafilter/filter_lichess_rec.py','astra_r8/datafilter/signcheck.py')
 'data' = @('tools/data/forge_pos.py','tools/data/forge_probe.py','tools/data/relabel_positions.py')
}
$entries = @()
foreach ($folder in $map.Keys) {
 New-Item -ItemType Directory -Path (Join-Path $targetRoot $folder) -Force | Out-Null
 foreach ($relative in $map[$folder]) {
  $sourceFile = Join-Path $sourceRoot $relative
  $targetFile = Join-Path (Join-Path $targetRoot $folder) (Split-Path $relative -Leaf)
  if (Test-Path -LiteralPath $targetFile) { throw "Refusing existing $targetFile" }
  Copy-Item -LiteralPath $sourceFile -Destination $targetFile
  $entries += [ordered]@{ source=$relative; destination=($folder+'/'+(Split-Path $relative -Leaf)); sha256=(Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash }
 }
}
[ordered]@{source_commit='d8982bc0';source_root=$sourceRoot;files=$entries} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $targetRoot 'SOURCE_COPY.json') -Encoding UTF8
