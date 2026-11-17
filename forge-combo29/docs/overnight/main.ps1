$ErrorActionPreference='Stop'
$o='C:\Users\Administrator\grok-pc\forge_push\overnight_timing_20261108';$ad="$o\adapter"
$py='C:\Users\Administrator\grok-pc\nnue\pythons\cpython-3.10-windows-x86_64-none\python.exe'
$ref='C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe'
$fens='C:\Users\Administrator\grok-pc\sdk_longjob_20261106_copy\data\fens_12k_v2.txt'
$w='D:\grok_sdk_speed_20261107\detached1735_all31'
function Log($m){$t=[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow,'W. Europe Standard Time').ToString('yyyy-MM-dd HH:mm:ss');"$t Vienna $m"|Add-Content "$o\MAIN.log"}
function Stage($file,$params,$mask,$stem){
 $p=Start-Process powershell.exe -ArgumentList (@('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$file)+$params) -WindowStyle Hidden -RedirectStandardOutput "$stem.out.log" -RedirectStandardError "$stem.err.log" -PassThru
 $null=$p.Handle  # FIX Nov8: cache handle so ExitCode is not $null (PS5.1 bug that silently failed all 308 stages Nov7)
 $p.PriorityClass='Idle';$p.ProcessorAffinity=[IntPtr]$mask;return $p}
function Save($recs){$recs|ConvertTo-Json -Depth 8|Set-Content "$o\RESULTS.json"}
$rf=@{}  # Resume marker check first
try{
Log 'START main'
$prev=gc 'C:\Users\Administrator\grok-pc\forge_push\sdk_speedonly_20261107\gate0415\detached1735_all31\RESULTS.json' -raw|ConvertFrom-Json
$names=@{1='KING';2='BADCAP';4='SEE';8='EQ32';16='CLANG'}
$recs=@();foreach($m in 1..31){$f=($names.Keys|sort|?{$m -band $_}|%{$names[$_]}) -join '+'
 $p=$prev|?{$_.bits -eq $m -and $_.exe}|select -first 1
 if($p){$recs+=[pscustomobject]@{name=$p.name;bits=$m;features=$f;exe=$p.exe;sha256=(Get-FileHash $p.exe -A SHA256).Hash;on='PASS_PRIOR';off='PASS_PRIOR';stage='READY';summary=$null;error=$null}}
 else{$e=if($m -band 16){"$w\clang\all31_m$m\m2use\forge_m2use.exe"}else{"$w\gcc\all31_m${m}_lp_v1\src_copy\forge_lp_v1.exe"}
  if(Test-Path $e){$recs+=[pscustomobject]@{name="combo$m";bits=$m;features=$f;exe=$e;sha256=(Get-FileHash $e -A SHA256).Hash;on='TODO';off='TODO';stage='CHECK';summary=$null;error=$null}}
  else{$recs+=[pscustomobject]@{name="combo$m";bits=$m;features=$f;exe=$null;sha256=$null;on='NA';off='NA';stage='NO_EXE';summary=$null;error='exe missing'}}}}
Save $recs
# Phase A: 12k bit-exact on/off, 6 parallel slots off cores 4-7
$jobs=New-Object Collections.Queue;foreach($r in $recs|?{$_.stage -eq 'CHECK'}){foreach($md in 'on','off'){$jobs.Enqueue(@($r,$md))}}
$slots=@(0,1,8,9,12,13);$run=@{}
while($jobs.Count -gt 0 -or $run.Count -gt 0){
 foreach($s in $slots){
  if($run.ContainsKey($s)){$j=$run[$s];if($j.p.HasExited){$r=$j.r;$md=$j.md;$log="$o\checks2\$($r.name)_$md\bitexact.log";$t=if(Test-Path $log){[IO.File]::ReadAllText($log)}else{''}
    $ok=($j.p.ExitCode -eq 0 -and $t -match '12000 / 12000 identical' -and $t -match 'VERDICT BIT-EXACT')
    $r.$md=if($ok){'PASS12000'}else{"FAIL exit=$($j.p.ExitCode)"};Log "$($r.name) $md $($r.$md)";$run.Remove($s);Save $recs}}
  if(-not $run.ContainsKey($s) -and $jobs.Count -gt 0){$x=$jobs.Dequeue();$r=$x[0];$md=$x[1]
   $opts=if($md -eq 'on'){'UseNNUE=true,Threads=1,Hash=16'}else{'UseNNUE=false,Threads=1,Hash=16'}
   New-Item -ItemType Directory -Force "$o\checks2"|Out-Null
   $mask=(1 -shl $s) -bor (1 -shl ($s+2))
   $p=Stage "$ad\bitexact_combo.ps1" @('-Cand',$r.exe,'-Ref',$ref,'-Out',"$o\checks2\$($r.name)_$md",'-Fens',$fens,'-FenDepth','13','-SkipSan','-FenOptions',$opts,'-CoreBase',"$s") $mask "$o\checks2\$($r.name)_$md"
   $run[$s]=@{p=$p;r=$r;md=$md};Log "check start $($r.name) $md slot $s"}}
 Start-Sleep 10}
foreach($r in $recs|?{$_.stage -eq 'CHECK'}){$r.stage=if($r.on -eq 'PASS12000' -and $r.off -eq 'PASS12000'){'READY'}else{'NOT_BITEXACT'}};Save $recs
# Phase B: calibration, max 3 attempts
New-Item -ItemType Directory -Force "$o\timing"|Out-Null
$cal=$false;foreach($i in 1..3){$p=Stage "$ad\abba.ps1" @('-Cand',$ref,'-Tag',"cal_$i",'-Calibration','-OutputRoot',"$o\timing",'-Blocks','10') 0xF0 "$o\timing\cal_$i";$p.WaitForExit()
 Log "cal_$i abba exit=$($p.ExitCode)";if($p.ExitCode -eq 0){& $py -I -B "$ad\summarize.py" "$o\timing\abba_cal_$i"|Out-File "$o\timing\cal_$i.summary.txt";Log "cal_$i summarize exit=$LASTEXITCODE";if($LASTEXITCODE -eq 0){$cal=$true;break}}}
if(-not $cal){Log 'CALIBRATION FAILED 3x - stopping timing, see timing\cal_*';throw 'CAL_FAILED_3X'}
foreach($r in $recs|?{$_.stage -eq 'READY'}){$tag="b$($r.bits)";$p=Stage "$ad\abba.ps1" @('-Cand',$r.exe,'-Tag',$tag,'-OutputRoot',"$o\timing",'-Blocks','10') 0xF0 "$o\timing\$tag";$p.WaitForExit()
 if($p.ExitCode -ne 0){$r.stage='ABBA_ERROR';$r.error="exit $($p.ExitCode)";Log "$($r.name) abba exit $($p.ExitCode)";Save $recs;continue}
 $j=& $py -I -B "$ad\summarize.py" "$o\timing\abba_$tag";if($LASTEXITCODE -ne 0){$r.stage='SUMMARY_ERROR'}else{$r.summary=($j|ConvertFrom-Json);$r.stage='TIMED'};Log "$($r.name) $($r.stage) $($r.summary.delta_pct)";Save $recs}
$rk=$recs|?{$_.summary}|sort {$_.summary.ratio} -desc
$md=@('# Overnight all-31 ABBA vs trial_w6 (NPS only, T1, core 4, 10 blocks, 1 outlier dropped)','','|Rank|Build|Features|Median delta %|CI95 %|Win|','|---|---|---|---:|---|---|')
$k=0;foreach($r in $rk){$k++;$md+="|$k|$($r.name)|$($r.features)|$('{0:N3}' -f $r.summary.delta_pct)|$('{0:N3}' -f $r.summary.ci95_pct[0])..$('{0:N3}' -f $r.summary.ci95_pct[1])|$($r.summary.win)|"}
foreach($r in $recs|?{-not $_.summary}){$md+="|-|$($r.name)|$($r.features)|-|-|$($r.stage) $($r.error)|"}
$md|Set-Content "$o\RANKED.md"
$best=$rk|select -first 1;if($best -and $best.summary.win){[pscustomobject]@{build=$best.name;exe=$best.exe;sha256=$best.sha256;delta_pct=$best.summary.delta_pct;ci95=$best.summary.ci95_pct;note='bit-exact 12k on/off; QA publishes lock'}|ConvertTo-Json|Set-Content "$o\LOCK_CANDIDATE.json"}
$status='COMPLETE'
}catch{$status="ERROR: $($_.Exception.Message)";Log $status}
finally{
 # Phase C: always restart everything
 try{& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$o\pause_resume.ps1" -Resume}catch{Log "resume err $_"}
 foreach($t in (Import-Csv "$o\PAUSED_TASKS.csv")){try{Enable-ScheduledTask -TaskName $t.TaskName|Out-Null}catch{Log "enable $($t.TaskName) err"}}
 foreach($t in 'Forge-Boot-Kick','Forge-AutoRestart-Watchdog','Forge-NNUE-Supervisor','Forge-Resource-Guard','GrokPC-Watchdog','Forge-7Day-WorkloadWatchdog'){try{Start-ScheduledTask -TaskName $t}catch{Log "start $t err"}}
 Log 'tasks re-enabled and kicked';Start-Sleep 300
 $v=Get-CimInstance Win32_Process|?{$_.ExecutablePath -like 'C:\Users\Administrator\grok-pc\*' -and $_.Name -match 'fastchess|forge|python'}|%{$pr=Get-Process -Id $_.ProcessId -ea 0;[pscustomobject]@{pid=$_.ProcessId;name=$_.Name;cpu=$pr.CPU}}
 $v|ConvertTo-Json|Set-Content "$o\RESUME_VERIFY.json"
 [pscustomobject]@{status=$status;finished=(Get-Date -f s);ranked="$o\RANKED.md";lock_candidate=(Test-Path "$o\LOCK_CANDIDATE.json");resumed_procs=@($v).Count}|ConvertTo-Json|Set-Content "$o\DONE.json";Log "DONE $status"}

