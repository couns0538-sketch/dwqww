# conc7_watch.ps1 (Engine QA executor 2026-10-25, crew vote 8/8 V1+V2, Couns t520u "push CPU to ~90%"). UNPROVEN.
# Runs Idle on CPUs 12-15 (0xF000). Single instance (mutex). Never touches any process except OUR extra datagen tree (cmd PID in -OurPid,
# verified by command line containing selfplay_out_x1_conc7_20261025). No STOP/PAUSE files, deletes nothing.
# Every 30 s:
#  - free RAM < 8 GB                         -> stop OUR extra datagen worker only
#  - GPU hot spot >= 80 C or mem junction >= 88 C or CPU Tctl >= 92 C (2 consecutive fresh HWiNFO samples) -> stop OUR worker
#  - current gate with RUN_INFO concurrency 7 (needs driver r7): first TL/crash -> stop OUR worker; a further TL/crash after that ->
#      set concurrency 7 -> 5 on not-yet-started fresh gates in forge_gates.json (backup + raw re-check + atomic write; running gate untouched;
#      takes effect at the next gate boundary)
#  - first conc-7 gate, at >= 50 finished games: median base_h256_e12 nps (info lines time>=100ms) vs conc-5 baseline (G119 = 1,951,072); < 90% -> ALERT + stop OUR worker
param([int]$OurPid=6240,[double]$BaseNps=1951072)
$Q='C:\Users\Administrator\grok-pc\forge_push\qa_conc7'; $LOG="$Q\conc7_watch.log"; $A='C:\Users\Administrator\grok-pc\forge_push\autorestart'; $D='D:\grok-pc-data\forge_push'
$MANF="$A\forge_gates.json"; $STATE="$A\forge_queue_state.json"; $CSV='C:\Users\Administrator\grok-pc\nnue\tools\hwinfo\gpu_sensors.csv'; $MARK='selfplay_out_x1_conc7_20261025'
$mtx=New-Object Threading.Mutex($false,'Global\forge_conc7_watch'); if(-not $mtx.WaitOne(0)){ exit }
try{ $me=Get-Process -Id $PID; $me.PriorityClass='Idle'; $me.ProcessorAffinity=[IntPtr]0xF000 }catch{}
function L($m){ Add-Content $LOG ("{0} PC | {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),$m) -Encoding utf8 }
function Ours(){ $p=Get-CimInstance Win32_Process -Filter "ProcessId=$OurPid" -ea 0; return ($p -and $p.Name -eq 'cmd.exe' -and $p.CommandLine -like "*$MARK*") }
$script:stopped=$false
function Stop-Ours($why){ if($script:stopped){ return }; if(Ours){ & taskkill.exe /T /F /PID $OurPid 2>&1 | Out-Null; L "STOPPED our extra datagen tree (cmd PID $OurPid): $why" } else { L "would stop our worker ($why) but PID $OurPid is not ours/alive" }; $script:stopped=$true }
function Temps(){ try{ if(((Get-Date)-(Get-Item $CSV).LastWriteTime).TotalSeconds -gt 60){ return $null }
  $h=(Get-Content $CSV -TotalCount 1) -split ','; $ih=(0..($h.Count-1) | ? { $h[$_] -match 'GPU Hot Spot Temperature' })[0]; $ij=(0..($h.Count-1) | ? { $h[$_] -match 'GPU Memory Junction Temperature' })[0]; $ic=(0..($h.Count-1) | ? { $h[$_] -match 'CPU \(Tctl/Tdie\)' })[0]
  $fs=[IO.File]::Open($CSV,'Open','Read','ReadWrite'); $fs.Seek(-30000,'End')|Out-Null; $sr=New-Object IO.StreamReader($fs); $t=$sr.ReadToEnd(); $sr.Close()
  $row=(@($t -split "`r?`n" | ? { $_ -match '^\d\d\.\d\d\.\d{4}' }))[-1] -split ','; return @{hot=[double]($row[$ih] -replace '"','');memj=[double]($row[$ij] -replace '"','');cpu=[double]($row[$ic] -replace '"','')} }catch{ return $null } }
function Head-Nps($f,$who){ try{ $fs=[IO.File]::Open($f,'Open','Read','ReadWrite'); $buf=New-Object byte[] ([math]::Min($fs.Length,40MB)); $n=$fs.Read($buf,0,$buf.Length); $fs.Close(); $t=[Text.Encoding]::UTF8.GetString($buf,0,$n)
  $v=@([regex]::Matches($t,"$who\S* ---> info depth \d+ .*?nps (\d+) .*?time (\d+)") | ? { [int]$_.Groups[2].Value -ge 100 } | % { [double]$_.Groups[1].Value } | Sort-Object); if($v.Count -lt 50){ return $null }; return $v[[int]($v.Count/2)] }catch{ return $null } }
function Revert-Conc5($cur){ $raw=[IO.File]::ReadAllText($MANF); $m=$raw | ConvertFrom-Json; $n=0
  foreach($g in $m.gates){ if(-not $g.confirm_of -and $g.tag -ne $cur -and $g.concurrency -eq 7 -and -not (Test-Path "$D\$($g.tag)\$($g.tag).log")){ $g.concurrency=5; $n++ } }
  if(-not $n){ L "revert: nothing to change"; return }
  $stamp=(Get-Date).ToString('yyyyMMdd_HHmmss'); $bak="$MANF.bak_conc5revert_$stamp"; Copy-Item $MANF $bak
  if([IO.File]::ReadAllText($MANF) -ne $raw){ L "revert: manifest changed while preparing; retry next loop"; return $false }
  $tmp="$MANF.tmp_conc5revert"; [IO.File]::WriteAllText($tmp,($m | ConvertTo-Json -Depth 12),(New-Object Text.UTF8Encoding($true)))
  if(-not (Get-Content $tmp -Raw | ConvertFrom-Json)){ L "revert: tmp did not parse; not applied"; return $false }
  Move-Item $tmp $MANF -Force; L "REVERTED $n not-yet-started fresh gates to concurrency 5 (backup $bak sha $((Get-FileHash $bak).Hash) -> $((Get-FileHash $MANF).Hash)); running gate $cur untouched"; return $true }
L "watch start PID $PID (OurPid $OurPid ours=$(Ours), BaseNps $BaseNps)"
$hotN=0; $tlSeen=@{}; $reverted=$false; $npsDone=$false; $lastHb=Get-Date 0
while($true){
 try{
  $os=Get-CimInstance Win32_OperatingSystem; $free=[math]::Round($os.FreePhysicalMemory/1MB,2)
  if($free -lt 8 -and -not $script:stopped){ Stop-Ours "free RAM $free GB < 8 GB" }
  $tp=Temps
  if($tp){ if($tp.hot -ge 80 -or $tp.memj -ge 88 -or $tp.cpu -ge 92){ $hotN++ } else { $hotN=0 }; if($hotN -ge 2 -and -not $script:stopped){ Stop-Ours "thermal hot=$($tp.hot) memj=$($tp.memj) cpuTctl=$($tp.cpu)" } }
  $st=Get-Content $STATE -Raw -ea 0 | ConvertFrom-Json; $cur=$st.current.tag
  if($cur){ $out="$D\$cur"; $ri=Get-Content "$out\RUN_INFO.json" -Raw -ea 0 | ConvertFrom-Json
   if($ri -and [int]$ri.concurrency -eq 7){
    $gl="$out\$cur.log"; $txt=if(Test-Path $gl){ [IO.File]::ReadAllText($gl) }else{ '' }
    $tl=([regex]::Matches($txt,'(?m)Finished game .*\{.*loses on time')).Count; $cr=([regex]::Matches($txt,'(?m)Finished game .*\{.*(disconnect|stalls|crash|illegal|abandon)')).Count; $bad=$tl+$cr
    $prev=if($tlSeen.ContainsKey($cur)){$tlSeen[$cur]}else{0}
    if($bad -gt $prev){ L "ALERT conc-7 gate $($cur): TL $tl crash $cr"
      if(-not $script:stopped){ Stop-Ours "first TL/crash in conc-7 gate $cur" } elseif(-not $reverted){ $reverted=[bool](Revert-Conc5 $cur) }
      $tlSeen[$cur]=$bad }
    $fin=([regex]::Matches($txt,'(?m)^Finished game')).Count
    if(-not $npsDone -and $fin -ge 50){ $nb=Head-Nps "$out\engine_io.log" 'base_h256_e12'; if($nb){ $r=[math]::Round($nb/$BaseNps,3); $msg="NPS CHECK first conc-7 gate $cur at $fin games: base_h256_e12 median nps $nb vs conc-5 $BaseNps = $r; TL $tl crash $cr -> $(if($r -ge 0.9 -and $bad -eq 0){'PASS'}else{'FAIL'})"; L $msg; $msg | Set-Content "$Q\NPS_CONC7_CHECK.txt" -Encoding utf8; if($r -lt 0.9 -and -not $script:stopped){ Stop-Ours "conc-7 nps ratio $r < 0.90" }; $npsDone=$true } }
   } }
  if(((Get-Date)-$lastHb).TotalMinutes -ge 10){ $cpu=[math]::Round((Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2 -MaxSamples 1).CounterSamples[0].CookedValue,1)
    L "HB cpu $cpu% freeRAM $free GB hot $($tp.hot) memj $($tp.memj) cpuTctl $($tp.cpu) gate $cur ours_alive=$(Ours) stopped=$($script:stopped)"; $lastHb=Get-Date }
 }catch{ L "loop error: $_" }
 Start-Sleep 30 }