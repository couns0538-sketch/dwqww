#requires -Version 5.1
# Original R10 preflight tests. No runtime executable/import/training is started.
param([Parameter(Mandatory=$true)][string]$Launcher,
      [Parameter(Mandatory=$true)][string]$Evidence)
$ErrorActionPreference = 'Stop'
$self = [Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass = 'Idle'
$self.ProcessorAffinity = [IntPtr]4
if ($Evidence -notlike 'D:\a10\wt\astra_r10\job3\regression\*' -or (Test-Path -LiteralPath $Evidence)) { throw 'New owned evidence directory required' }
if ([IO.DriveInfo]::new('C:\').AvailableFreeSpace -lt 30GB -or [IO.DriveInfo]::new('D:\').AvailableFreeSpace -lt 50GB) { throw 'R10 disk floor' }
$null = New-Item -ItemType Directory -Path $Evidence
$env:TEMP=$Evidence; $env:TMP=$Evidence; $env:TMPDIR=$Evidence
. $Launcher
$roots = @('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
$runtime='D:\grok-pc-data\npt\nnue-pytorch-amd'
$enabled=@($runtime)
$rows = New-Object System.Collections.Generic.List[object]
function Check([string]$Name,[scriptblock]$Body) {
    try { & $Body; $rows.Add([pscustomobject]@{name=$Name;status='PASS';detail=''}) }
    catch { $rows.Add([pscustomobject]@{name=$Name;status='FAIL';detail=$_.Exception.Message}) }
}
function Refuses([scriptblock]$Body,[string]$Reason) {
    $errorText=$null
    try { & $Body | Out-Null } catch { $errorText=$_.Exception.Message }
    if (-not $errorText -or $errorText -notmatch $Reason) { throw "Expected refusal /$Reason/; received '$errorText'" }
}
Check 'default remains protected' { Refuses { Assert-ReadPath ($runtime+'\train.py') $roots } 'Protected production' }
Check 'explicit exact runtime source read allowed' { $null=Assert-ReadPath ($runtime+'\train.py') $roots $enabled }
Check 'explicit runtime root read allowed' { $null=Assert-ReadPath $runtime $roots $enabled }
Check 'DLL read allowed only through read validator' { $null=Assert-ReadPath ($runtime+'\build\libtraining_data_loader.dll') $roots $enabled }
Check 'strict path validator still rejects opted-in runtime' { Refuses { Assert-DPath ($runtime+'\train.py') $roots } 'Protected production' }
Check 'protected write still rejected' { Refuses { Assert-R10WritePath ($runtime+'\new.py') $roots } 'Protected production' }
Check 'parent of runtime refused' { Refuses { Assert-ReadPath 'D:\grok-pc-data\npt' $roots $enabled } 'Protected production' }
Check 'ancestor outside exact runtime refused' { Refuses { Assert-ReadPath 'D:\grok-pc-data' $roots $enabled } 'Protected production' }
Check 'sibling prefix not opted in' { Refuses { Assert-ReadPath ($runtime+'-other\train.py') $roots $enabled } 'Protected production' }
Check 'wrong runtime exception rejected' { Refuses { Assert-ReadPath 'D:\a10\test' $roots @('D:\grok-pc-data\npt') } 'not explicitly authorized' }
Check 'F runtime exception rejected lexically' { Refuses { Assert-ReadPath 'D:\a10\test' $roots @('F:\runtime') } 'Absolute D:' }
Check 'F read refused before filesystem access' { Refuses { Assert-ReadPath 'F:\any.file' $roots $enabled } 'Absolute D:' }
Check 'required protected root cannot be omitted' { Refuses { Assert-ReadPath $runtime @('F:\') $enabled } 'complete protected NPT root' }
Check 'nested protected runtime path overrides read exception' { Refuses { Assert-ReadPath ($runtime+'\trainer\engine.py') @($roots+@($runtime+'\trainer')) $enabled } 'Protected production' }
Check 'extra protected ancestor overrides read exception' { Refuses { Assert-ReadPath ($runtime+'\train.py') @($roots+@('D:\grok-pc-data')) $enabled } 'Protected production' }
foreach ($leaf in @('queue_state.json','queue.txt','forge_queue_state.json','forge_gates.json','CURRENT_LOCK.json','STOP','PAUSE.txt')) {
    $currentLeaf=$leaf
    Check ('control/queue leaf refused: '+$leaf) { Refuses { Assert-ReadPath ($runtime+'\'+$currentLeaf) $roots $enabled } 'queue/lock/control' }
}
Check 'dot traversal still refused' { Refuses { Assert-ReadPath ($runtime+'\..\trainer') $roots $enabled } 'Dot path' }
Check 'ADS still refused' { Refuses { Assert-ReadPath ($runtime+'\train.py:stream') $roots $enabled } 'alternate data streams' }
$fixture=Join-Path $Evidence 'fixture.exe'; [IO.File]::WriteAllText($fixture,'preflight fixture; NEVER EXECUTED')
$j=[pscustomobject]@{schema=1;executable=$fixture;executable_sha256=(Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash;arguments=@('--threads','1');working_directory=$Evidence;output_directory=(Join-Path $Evidence 'unused-output');read_paths=@($fixture,$runtime);write_paths=@((Join-Path $Evidence 'unused-output'));logical_cpus=@(2);worker_threads=1;minimum_free_mib=51200;required_bytes=4096}
Check 'manifest with declared runtime read accepted only opt-in' { $null=Test-SafeJob $j $roots $enabled; Refuses { Test-SafeJob $j $roots } 'Protected production' }
Check 'manifest runtime write refused despite opt-in' {
    $old=$j.write_paths
    try { $j.write_paths=@($j.output_directory,($runtime+'\out')); Refuses { Test-SafeJob $j $roots $enabled } 'Protected production' }
    finally { $j.write_paths=$old }
}
Check 'runtime command path remains forbidden' {
    $old=$j.arguments
    try { $j.arguments=@('--threads','1',($runtime+'\train.py')); Refuses { Test-SafeJob $j $roots $enabled } 'Protected production' }
    finally { $j.arguments=$old }
}
Check 'reparse below ordinary D root still refused with opt-in' {
    $target=Join-Path $Evidence 'target';$junction=Join-Path $Evidence 'junction'
    $null=New-Item -ItemType Directory -Path $target
    $null=New-Item -ItemType Junction -Path $junction -Target $target
    try { Refuses { Assert-ReadPath ($junction+'\child') $roots $enabled } 'Reparse' }
    finally { [IO.Directory]::Delete($junction) }
}
Check 'authorized runtime always invokes reparse guard' {
    $original=(Get-Item Function:\Assert-NoReparsePath).ScriptBlock
    try {
        Set-Item Function:\Assert-NoReparsePath { param([string]$Full) throw 'Reparse fixture: runtime guard reached' }
        Refuses { Assert-ReadPath ($runtime+'\train.py') $roots $enabled } 'Reparse fixture'
    } finally { Set-Item Function:\Assert-NoReparsePath $original }
}
$report=[ordered]@{scope='PS5.1 read-only-runtime policy preflight; no external runtime import/execution';launcher=$Launcher;launcher_sha256=(Get-FileHash -LiteralPath $Launcher -Algorithm SHA256).Hash;priority=[string]$self.PriorityClass;affinity=$self.ProcessorAffinity.ToInt64();utc=[DateTime]::UtcNow.ToString('o');checks=@($rows.ToArray())}
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $Evidence 'results.json') -Encoding UTF8
$rows | Format-Table -AutoSize
if (@($rows | Where-Object status -eq 'FAIL').Count) { exit 1 }
exit 0
