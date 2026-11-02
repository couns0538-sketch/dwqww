$ErrorActionPreference = 'Stop'
$prepareProc = [Diagnostics.Process]::GetCurrentProcess()
$prepareProc.PriorityClass = 'Idle'
$prepareProc.ProcessorAffinity = [IntPtr]8
$original = 'D:\a10\wt\astra_r10\job1\safety-tests\Test-R10Safety.ps1'
$copy = 'D:\a10\wt\astra_r10\job3\regression\Test-OriginalSafety.ps1'
if (Test-Path -LiteralPath $copy) { throw 'Refusing an existing copied baseline fixture' }
$body = [IO.File]::ReadAllText($original)
$oldRoot = 'D:\a10\wt\astra_r10\job1\safety-tests\*'
$newRoot = 'D:\a10\wt\astra_r10\job3\regression\*'
if (-not $body.Contains($oldRoot)) { throw 'Original safety fixture layout changed' }
$body = $body.Replace($oldRoot,$newRoot)
[IO.File]::WriteAllText($copy,$body,(New-Object System.Text.UTF8Encoding($false)))
$receipt = [ordered]@{source=$original;source_sha256=(Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash;copy=$copy;copy_sha256=(Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash;change='Only allowed new evidence directory moved from job1 to job3; all19 original assertions unchanged'}
[IO.File]::WriteAllText('D:\a10\wt\astra_r10\job3\regression\BASELINE_TEST_COPY.json',($receipt | ConvertTo-Json),(New-Object System.Text.UTF8Encoding($false)))
