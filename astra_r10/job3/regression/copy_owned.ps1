$ErrorActionPreference = 'Stop'
$copyProc = [System.Diagnostics.Process]::GetCurrentProcess()
$copyProc.PriorityClass = 'Idle'
$copyProc.ProcessorAffinity = [IntPtr]8
$sourceRoot = 'D:\a10\job3\source\astra_r8\datafilter'
$targetRoot = 'D:\a10\wt\astra_r10\job3\regression\datafilter'
$receiptRoot = 'D:\a10\wt\astra_r10\job3\regression'
if (Test-Path -LiteralPath $targetRoot) { throw 'Refusing an existing regression code copy' }
$archive = Join-Path $receiptRoot 'launcher_before_readonly'
if (Test-Path -LiteralPath $archive) { throw 'Refusing an existing launcher archive' }
New-Item -ItemType Directory -Path $archive | Out-Null
$archiveSources = @(
 'D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1',
 'D:\a10\wt\astra_r10\job3\audit\native-launch-manifest-actual01.json',
 'D:\a10\wt\astra_r10\job3\audit\launch-native-actual01\result.json'
)
$archiveEntries = @()
foreach ($source in $archiveSources) {
 $target = Join-Path $archive (Split-Path $source -Leaf)
 $beforeHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
 [IO.File]::Copy($source, $target, $false)
 if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $beforeHash -or (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $beforeHash) { throw 'Archive identity changed' }
 $archiveEntries += [ordered]@{source=$source;archive=$target;sha256=$beforeHash}
}
[IO.File]::WriteAllText((Join-Path $archive 'ARCHIVE.json'), ([ordered]@{purpose='immutable pre-readonly-extension helper plus completed native audit manifest/receipt';files=$archiveEntries} | ConvertTo-Json -Depth 5), (New-Object System.Text.UTF8Encoding($false)))
$entries = @()
foreach ($file in Get-ChildItem -LiteralPath $sourceRoot -File -Recurse) {
 if ($file.FullName -match '\\__pycache__\\' -or $file.Extension -eq '.pyc') { continue }
 if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Frozen source reparse refused' }
 $relative = $file.FullName.Substring($sourceRoot.Length + 1)
 $target = Join-Path $targetRoot $relative
 $parent = Split-Path $target -Parent
 if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
 [IO.File]::Copy($file.FullName, $target, $false)
 $entries += [ordered]@{relative=$relative;source=$file.FullName;source_sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash;copy_sha256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash}
}
$overlays = @()
foreach ($name in @('convert_forge.py','records.py')) {
 $source = Join-Path 'D:\a10\wt\astra_r10\job3\tool\datafilter' $name
 $target = Join-Path $targetRoot $name
 [IO.File]::Copy($source, $target, $true)
 $overlays += [ordered]@{source=$source;target=$target;sha256=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash}
}
$fullState = 'D:\a10\wt\astra_r10\job3\tool\full_state.py'
$fullStateCopy = Join-Path $receiptRoot 'full_state.py'
[IO.File]::Copy($fullState, $fullStateCopy, $false)
$overlays += [ordered]@{source=$fullState;target=$fullStateCopy;sha256=(Get-FileHash -LiteralPath $fullState -Algorithm SHA256).Hash}
$filter = Join-Path $targetRoot 'filter_positions.py'
$filterText = [IO.File]::ReadAllText($filter)
$oldRoot = "ARTIFACT_ROOT = Path('D:/grok-pc-data/dwqww/astra8_data')"
if (-not $filterText.Contains($oldRoot) -or -not $filterText.Contains('0x4000')) { throw 'Unexpected frozen filter policy text' }
$filterText = $filterText.Replace($oldRoot, "ARTIFACT_ROOT = Path('D:/a10')").Replace('0x4000','0x40').Replace('cannot set BelowNormal priority','cannot set Idle priority')
[IO.File]::WriteAllText($filter, $filterText, (New-Object System.Text.UTF8Encoding($false)))
$conftest = Join-Path $targetRoot 'tests\conftest.py'
$conftestText = [IO.File]::ReadAllText($conftest)
$oldOutput = "Path('D:/grok-pc-data/dwqww/astra8_data')"
if (-not $conftestText.Contains($oldOutput)) { throw 'Unexpected frozen fixture receipt path' }
$conftestText = $conftestText.Replace($oldOutput, "(Path(os.environ['ASTRA_REGRESSION_OUTPUT'])/'runtime_receipts')")
[IO.File]::WriteAllText($conftest, $conftestText, (New-Object System.Text.UTF8Encoding($false)))
$final = @()
foreach ($file in Get-ChildItem -LiteralPath $targetRoot -File -Recurse) {
 $final += [ordered]@{path=$file.FullName;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash}
}
$receipt = Join-Path $receiptRoot 'SOURCE_COPY.json'
if (Test-Path -LiteralPath $receipt) { throw 'Refusing existing source receipt' }
$value = [ordered]@{source_commit='d8982bc0';source_root=$sourceRoot;target_root=$targetRoot;original_files=$entries;reviewed_overlays=$overlays;policy_changes=@('ARTIFACT_ROOT D:/a10','Idle priority0x40','fixture receipt under ASTRA_REGRESSION_OUTPUT/runtime_receipts');final_files=$final}
[IO.File]::WriteAllText($receipt, ($value | ConvertTo-Json -Depth 8), (New-Object System.Text.UTF8Encoding($false)))
