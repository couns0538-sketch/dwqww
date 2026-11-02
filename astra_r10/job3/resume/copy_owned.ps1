$ErrorActionPreference = 'Stop'
$copyProc = [System.Diagnostics.Process]::GetCurrentProcess()
$copyProc.PriorityClass = 'Idle'
$copyProc.ProcessorAffinity = [IntPtr]8
$sourceRoot = 'D:\a10\job3\source'
$targetRoot = 'D:\a10\wt\astra_r10\job3\resume'
$map = @{
 'data2' = @('tools/data2/convert_dataset.py','tools/data2/bullet_records.py','tools/data2/external_tool_policy.py')
 'data' = @('tools/data/forge_pos.py','tools/data/forge_probe.py','tools/data/filter_positions.py')
}
$entries = @()
foreach ($folder in $map.Keys) {
 New-Item -ItemType Directory -Path (Join-Path $targetRoot $folder) -Force | Out-Null
 foreach ($relative in $map[$folder]) {
  $sourceFile = Join-Path $sourceRoot $relative
  $targetFile = Join-Path (Join-Path $targetRoot $folder) (Split-Path $relative -Leaf)
  if (Test-Path -LiteralPath $targetFile) { throw "Refusing existing $targetFile" }
  [System.IO.File]::Copy($sourceFile, $targetFile, $false)
  $entries += [ordered]@{ source=$relative; destination=($folder+'/'+(Split-Path $relative -Leaf)); sha256=(Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash }
 }
}
$receipt = Join-Path $targetRoot 'SOURCE_COPY.json'
if (Test-Path -LiteralPath $receipt) { throw 'Refusing existing source receipt' }
[System.IO.File]::WriteAllText($receipt, ([ordered]@{source_commit='d8982bc0';source_root=$sourceRoot;files=$entries} | ConvertTo-Json -Depth 5), (New-Object System.Text.UTF8Encoding($false)))
