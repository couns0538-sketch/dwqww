#requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$Launcher,[Parameter(Mandatory=$true)][string]$Evidence)
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]4
if($Evidence -notlike 'D:\a10\wt\astra_r10\job3\regression\*' -or (Test-Path -LiteralPath $Evidence)){throw 'Fresh owned evidence required'}
if([IO.DriveInfo]::new('C:\').AvailableFreeSpace -lt 30GB -or [IO.DriveInfo]::new('D:\').AvailableFreeSpace -lt 50GB){throw 'Disk floor'}
$null=New-Item -ItemType Directory -Path $Evidence
$env:TEMP=$Evidence;$env:TMP=$Evidence;$env:TMPDIR=$Evidence
. $Launcher
$roots=@('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
$msvc='C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.51.36231'
$inc='C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0'
$lib='C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0'
$allowed=@($msvc,$inc,$lib);$npt=@('D:\grok-pc-data\npt\nnue-pytorch-amd')
$cl=$msvc+'\bin\Hostx64\x64\cl.exe'
$rows=New-Object System.Collections.Generic.List[object]
function Check([string]$Name,[scriptblock]$Body){try{& $Body;$rows.Add([pscustomobject]@{name=$Name;status='PASS';detail=''})}catch{$rows.Add([pscustomobject]@{name=$Name;status='FAIL';detail=$_.Exception.Message})}}
function Refuses([scriptblock]$Body,[string]$Reason){$message=$null;try{& $Body|Out-Null}catch{$message=$_.Exception.Message};if(-not $message -or $message -notmatch $Reason){throw "Expected /$Reason/, got '$message'"}}
Check 'default C compiler read refused' {Refuses {Assert-ReadPath $cl $roots} 'Absolute D:'}
Check 'compiler read only with exact opt-in' {$null=Assert-ReadPath $cl $roots @() $allowed}
Check 'header and library reads allowed' {$null=Assert-ReadPath ($inc+'\ucrt\stdio.h') $roots @() $allowed;$null=Assert-ReadPath ($lib+'\um\x64\kernel32.lib') $roots @() $allowed}
Check 'broad C root refused' {Refuses {Assert-ReadPath $cl $roots @() @('C:\')} 'not explicitly authorized'}
Check 'broad ProgramFiles root refused' {Refuses {Assert-ReadPath $cl $roots @() @('C:\Program Files (x86)')} 'not explicitly authorized'}
Check 'unapproved SDK version refused' {Refuses {Assert-ReadPath $cl $roots @() @($inc.Replace('26100','22000'))} 'not explicitly authorized'}
Check 'LLVM not authorized' {Refuses {Assert-ReadPath 'C:\Program Files\LLVM\bin\clang-cl.exe' $roots @() $allowed} 'outside exact authorized'}
Check 'F root refused lexically' {Refuses {Assert-ReadPath $cl $roots @() @('F:\tool')} 'Only exact authorized C:'}
Check 'F read still refused' {Refuses {Assert-ReadPath 'F:\anything' $roots $npt $allowed} 'Absolute D:'}
Check 'parent and sibling prefix refused' {Refuses {Assert-ReadPath ([IO.Path]::GetDirectoryName($msvc)) $roots @() $allowed} 'outside exact authorized';Refuses {Assert-ReadPath ($msvc+'-other\cl.exe') $roots @() $allowed} 'outside exact authorized'}
Check 'duplicate opt-in refused' {Refuses {Assert-ReadPath $cl $roots @() @($msvc,$msvc)} 'Unique exact'}
Check 'ADS refused before access' {Refuses {Assert-ReadPath ($cl+':stream') $roots @() $allowed} 'without wildcard, stream'}
Check 'dot traversal refused before access' {Refuses {Assert-ReadPath ($msvc+'\..\other') $roots @() $allowed} 'dot components'}
Check 'nested protected path still wins' {Refuses {Assert-ReadPath $cl @($roots+@($msvc+'\bin')) @() $allowed} 'Protected production'}
Check 'protected ancestor still wins' {Refuses {Assert-ReadPath $cl @($roots+@('C:\Program Files (x86)')) @() $allowed} 'Protected production'}
Check 'strict write validator unchanged' {Refuses {Assert-R10WritePath ($msvc+'\out.txt') $roots} 'Absolute D:'}
Check 'NPT opt-in remains independent' {$null=Assert-ReadPath ($npt[0]+'\train.py') $roots $npt $allowed;Refuses {Assert-ReadPath ($npt[0]+'\train.py') $roots @() $allowed} 'Protected production'}
foreach($leaf in @('queue_state.json','forge_queue_state.json','CURRENT_LOCK.json','STOP','PAUSE')){ $current=$leaf;Check ('control refused '+$leaf) {Refuses {Assert-ReadPath ($msvc+'\'+$current) $roots @() $allowed} 'queue/lock/control'}}
Check 'authorized C read invokes reparse guard' {
 $original=(Get-Item Function:\Assert-NoReparsePath).ScriptBlock
 try{Set-Item Function:\Assert-NoReparsePath {param([string]$Full)throw 'Reparse fixture reached'};Refuses {Assert-ReadPath $cl $roots @() $allowed} 'Reparse fixture'}finally{Set-Item Function:\Assert-NoReparsePath $original}
}
$fixture=Join-Path $Evidence 'fixture.exe';[IO.File]::WriteAllText($fixture,'never executed')
$j=[pscustomobject]@{schema=1;executable=$fixture;executable_sha256=(Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash;arguments=@('--threads','1');working_directory=$Evidence;output_directory=(Join-Path $Evidence 'unused');read_paths=@($fixture,$msvc,$inc,$lib);write_paths=@((Join-Path $Evidence 'unused'));logical_cpus=@(2);worker_threads=1;minimum_free_mib=51200;required_bytes=4096}
Check 'manifest declared read accepted only opt-in' {$null=Test-SafeJob $j $roots @() $allowed;Refuses {Test-SafeJob $j $roots} 'Absolute D:'}
Check 'C executable remains forbidden' {$old=$j.executable;try{$j.executable=$cl;Refuses {Test-SafeJob $j $roots @() $allowed} 'Absolute D:'}finally{$j.executable=$old}}
Check 'C cwd remains forbidden' {$old=$j.working_directory;try{$j.working_directory=$msvc;Refuses {Test-SafeJob $j $roots @() $allowed} 'Absolute D:'}finally{$j.working_directory=$old}}
Check 'C write remains forbidden' {$old=$j.write_paths;try{$j.write_paths=@($j.output_directory,($msvc+'\out'));Refuses {Test-SafeJob $j $roots @() $allowed} 'Absolute D:'}finally{$j.write_paths=$old}}
Check 'C command path remains forbidden' {$old=$j.arguments;try{$j.arguments=@('--threads','1',$cl);Refuses {Test-SafeJob $j $roots @() $allowed} 'Absolute D:'}finally{$j.arguments=$old}}
$report=[ordered]@{scope='toolchain read policy fixtures only; no compiler or external runtime executed';launcher_sha256=(Get-FileHash -LiteralPath $Launcher -Algorithm SHA256).Hash;utc=[DateTime]::UtcNow.ToString('o');priority=[string]$self.PriorityClass;affinity=$self.ProcessorAffinity.ToInt64();checks=@($rows.ToArray())}
$report|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $Evidence 'results.json') -Encoding UTF8
$rows|Format-Table -AutoSize
if(@($rows|Where-Object status -eq 'FAIL').Count){exit 1}
exit 0
