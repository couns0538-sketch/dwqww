param([Parameter(Mandatory=$true)][string]$Name)
$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
if ($Name -notmatch '^[a-z0-9_-]+$') { throw 'Invalid receipt name' }
$root='D:\a14'
$out=Join-Path $root ('evidence\r14\health-'+$Name+'.json')
if (Test-Path -LiteralPath $out) { throw 'Receipt exists' }
$drives=@{}
foreach ($drive in @('C','D')) { $drives[$drive]=(Get-PSDrive $drive).Free }
if ($drives.D -lt 50GB -or $drives.C -lt 30GB) { throw 'Disk floor breached' }
# These exact progress logs are read only for the requested workload-health check.
$training='C:\forge_nnue_train\runs\npt_k32h3_l1024_bs16k_e8x152m5_g072_lam10_w4_s38\npt_try1.log'
$gate='F:\forge_push\uhoE3a_evalmatscale12_r6k_vs_AL1lp\uhoE3a_evalmatscale12_r6k_vs_AL1lp.log'
$trainLines=@(Get-Content -LiteralPath $training -Tail 100)
$trainProgress=@($trainLines | Where-Object { $_ -match 'Epoch\s+\d+ \(Train\):\s+\d+%.*it/s' })
$lastTrain=if ($trainProgress.Count) {[string]::Concat('', $trainProgress[-1])} else {$null}
$gateLines=@(Get-Content -LiteralPath $gate)
$completed=@($gateLines | Where-Object {$_ -match '^Finished game \d+ '})
$lastGame=0
foreach ($line in $completed) { if ($line -match '^Finished game (\d+) ') { $lastGame=[Math]::Max($lastGame,[int]$Matches[1]) } }
$memory=Get-CimInstance Win32_OperatingSystem
$ownedBytes=(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Measure-Object -Property Length -Sum).Sum
if ($ownedBytes -ge 5000000000) { throw 'Owned storage cap breached' }
$receipt=@{
 schema=1; time_vienna=((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+' Vienna'); monotonic_ticks=[Diagnostics.Stopwatch]::GetTimestamp(); monotonic_frequency=[Diagnostics.Stopwatch]::Frequency
 free_bytes=$drives; owned_bytes=$ownedBytes; available_memory_bytes=([long]$memory.FreePhysicalMemory*1024)
 training=@{path=$training;last_write_wall=(Get-Item -LiteralPath $training).LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss');progress=$lastTrain}
 gate=@{path=$gate;last_write_wall=(Get-Item -LiteralPath $gate).LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss');completed_games=$completed.Count;maximum_finished_game=$lastGame}
 processes=@(Get-Process | Where-Object {$_.ProcessName -match '^(python|fastchess|forge)'} | Select-Object Id,ProcessName,CPU,PriorityClass)
 interpretation='Observation only; compare successive observations before certifying progress. No process or workload configuration changed.'
}
$utf8=New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($out,($receipt | ConvertTo-Json -Depth 6),$utf8)
$receipt | Select-Object time_vienna,free_bytes,owned_bytes,available_memory_bytes,training,gate | ConvertTo-Json -Depth 5
