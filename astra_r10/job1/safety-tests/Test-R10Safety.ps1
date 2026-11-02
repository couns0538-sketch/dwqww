#requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$Launcher,
      [Parameter(Mandatory=$true)][string]$Evidence)
$ErrorActionPreference = 'Stop'
$self = [Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass = [Diagnostics.ProcessPriorityClass]::Idle
$self.ProcessorAffinity = [IntPtr]4
if ($Evidence -notlike 'D:\a10\wt\astra_r10\job1\safety-tests\*' -or (Test-Path -LiteralPath $Evidence)) { throw 'New owned evidence directory required' }
if ([IO.DriveInfo]::new('C:\').AvailableFreeSpace -lt 30GB -or [IO.DriveInfo]::new('D:\').AvailableFreeSpace -lt 50GB) { throw 'R10 disk floor' }
$null = New-Item -ItemType Directory -Path $Evidence
$env:TEMP = $Evidence; $env:TMP = $Evidence; $env:TMPDIR = $Evidence
. $Launcher
$roots = @('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
$rows = New-Object System.Collections.Generic.List[object]
function Check([string]$Name,[scriptblock]$Body) {
    try { & $Body; $rows.Add([pscustomobject]@{name=$Name;status='PASS';detail=''}) }
    catch { $rows.Add([pscustomobject]@{name=$Name;status='FAIL';detail=$_.Exception.Message}) }
}
function Refuses([scriptblock]$Body,[string]$Reason) {
    $errorText = $null
    try { & $Body | Out-Null } catch { $errorText = $_.Exception.Message }
    if (-not $errorText -or $errorText -notmatch $Reason) { throw "Expected refusal /$Reason/; received '$errorText'" }
}
$fixture = Join-Path $Evidence 'fixture.exe'
[IO.File]::WriteAllText($fixture,'preflight fixture only; never executed')
$j = [pscustomobject]@{schema=1;executable=$fixture;executable_sha256=(Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash;arguments=@('--threads','1');working_directory=$Evidence;output_directory=(Join-Path $Evidence 'unused-output');read_paths=@($fixture);write_paths=@((Join-Path $Evidence 'unused-output'));logical_cpus=@(2);worker_threads=1;minimum_free_mib=51200;required_bytes=4096}
Check 'full C D F protected-roots list accepted' { $null = Test-SafeJob $j $roots }
Check 'runtime C path refused with full roots' { Refuses { Assert-DPath 'C:\outside.exe' $roots } 'Absolute D:' }
Check 'runtime F path refused without touching F' { Refuses { Assert-DPath 'F:\outside.exe' $roots } 'Absolute D:' }
Check 'protected D descendant refused' { Refuses { Assert-DPath 'D:\forge_nnue_train\example.bin' $roots } 'Protected production root' }
Check 'protected D ancestor refused' { Refuses { Assert-DPath 'D:\grok-pc-data\forge_push' $roots } 'Protected production root' }
Check 'protected sibling prefix allowed' { $null = Assert-DPath (Join-Path $Evidence 'sibling') @(($Evidence+'-blocked'),'F:\') }
Check 'dot traversal refused' { Refuses { Assert-DPath 'D:\a10\..\outside' $roots } 'Dot path' }
Check 'alternate stream refused' { Refuses { Assert-DPath 'D:\a10\sample:stream' $roots } 'alternate data streams' }
Check 'relative protected root refused' { Refuses { Assert-DPath $Evidence @('F:') } 'Protected roots' }
Check 'write outside R10 root refused' {
    $original = $j.write_paths
    try { $j.write_paths = @($j.output_directory,'D:\a10-other\forbidden'); Refuses { Test-SafeJob $j @('D:\protected') } 'write root' }
    finally { $j.write_paths = $original }
}
Check 'working directory outside R10 refused' {
    $original = $j.working_directory
    try { $j.working_directory = 'D:\'; Refuses { Test-SafeJob $j @('D:\protected') } 'write root|D: root' }
    finally { $j.working_directory = $original }
}
Check 'old 32GiB floor refused' { Refuses { Assert-SafeDisk 32768 0 } '51200' }
Check 'storage exact boundaries accepted' { Assert-R10StorageBudget -CFreeBytes 32212254720 -DFreeBytes 53687091200 -WorkspaceBytes 15000000000 -RequiredBytes 0 -MinimumMiB 51200 }
Check 'C floor breach refused' { Refuses { Assert-R10StorageBudget -CFreeBytes 32212254719 -DFreeBytes 53687091200 -WorkspaceBytes 0 -RequiredBytes 0 -MinimumMiB 51200 } 'C:.*floor' }
Check 'D floor plus reservation refused' { Refuses { Assert-R10StorageBudget -CFreeBytes 32212254720 -DFreeBytes 53687091200 -WorkspaceBytes 0 -RequiredBytes 1 -MinimumMiB 51200 } 'D:.*reserve' }
Check 'workspace cap plus reservation refused' { Refuses { Assert-R10StorageBudget -CFreeBytes 32212254720 -DFreeBytes 63687091200 -WorkspaceBytes 14999999999 -RequiredBytes 2 -MinimumMiB 51200 } 'workspace.*cap' }
Check 'negative reservation refused' { Refuses { Assert-R10StorageBudget -CFreeBytes 32212254720 -DFreeBytes 63687091200 -WorkspaceBytes 0 -RequiredBytes -1 -MinimumMiB 51200 } 'nonnegative' }
Check 'fresh workspace count includes hidden files and subdirectories' {
    $countRoot=Join-Path $Evidence 'count-fixture';$null=New-Item -ItemType Directory -Path ($countRoot+'\nested')
    [IO.File]::WriteAllBytes(($countRoot+'\one'),[byte[]](1,2,3))
    [IO.File]::WriteAllBytes(($countRoot+'\nested\two'),[byte[]](1,2))
    (Get-Item -LiteralPath ($countRoot+'\one')).Attributes=[IO.FileAttributes]::Hidden
    if ((Get-R10WorkspaceBytes $countRoot) -ne 5) { throw 'Wrong byte count' }
}
Check 'reparse workspace and runtime ancestors refused' {
    $target=Join-Path $Evidence 'reparse-target';$junction=Join-Path $Evidence 'reparse-junction'
    $null=New-Item -ItemType Directory -Path $target
    $null=New-Item -ItemType Junction -Path $junction -Target $target
    try {
        Refuses { Get-R10WorkspaceBytes $Evidence } 'Reparse'
        Refuses { Assert-DPath ($junction+'\child') $roots } 'Reparse'
    } finally {
        # Delete only this newly created junction, never its target or contents.
        [IO.Directory]::Delete($junction)
    }
}
$report = [ordered]@{scope='PowerShell 5.1 preflight regression; fixture executable never launched';launcher=$Launcher;launcher_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $Launcher).Hash;priority=[string]$self.PriorityClass;affinity=$self.ProcessorAffinity.ToInt64();utc=[DateTime]::UtcNow.ToString('o');checks=@($rows.ToArray())}
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $Evidence 'results.json') -Encoding UTF8
$rows | Format-Table -AutoSize | Out-String -Width 240 | Set-Content -LiteralPath (Join-Path $Evidence 'results.txt') -Encoding UTF8
$rows | Format-Table -AutoSize
if (@($rows | Where-Object status -eq 'FAIL').Count) { exit 1 }
exit 0
