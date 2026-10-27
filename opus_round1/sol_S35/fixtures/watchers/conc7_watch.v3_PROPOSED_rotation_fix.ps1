# conc7_watch.ps1 v2-conc8 (Engine QA executor 2026-10-25 ~13:3x PC clock; crew vote C8 8/8 a/b/c, d N). UNPROVEN.
# v3 PROPOSED by S35 (opus 2026-10-27), NOT deployed: TL/crash dedupe resets when the gate log is rotated or truncated (shorter, or no longer starts with the head seen last tick); a failed read changes nothing.
# v1 (crew 8/8 V1+V2, Couns t520u): conc-7 watch. v2 adds per-gate nps ratio + conc-8 rules. Backup of v1: conc7_watch.ps1.bak_conc8_20261025_132539.
# Runs Idle on CPUs 12-15 (0xF000). Single instance (mutex). Never touches any process except OUR extra datagen tree (cmd PID in -OurPid,
# verified by command line containing selfplay_out_x1_conc7_20261025). NEVER (re)starts the extra datagen worker (it stays off while conc-8 gates run).
# No STOP/PAUSE files, deletes nothing, never touches the running gate or its fastchess.
# Every 30 s:
#  - free RAM < 8 GB, or hot spot >= 80 C / mem junction >= 88 C / CPU Tctl >= 92 C (2 fresh samples) -> stop OUR worker if alive
#  - every gate (concurrency from its RUN_INFO.json): once at >= 50 finished games, median base_h256_e12 nps (info lines time>=100ms,
#    head of engine_io.log) / 1,951,072 -> appended once as "gate,conc,ratio,n" to NPS_RATIO_PER_GATE.csv (n = finished games at measurement)
#  - conc 7: threshold 0.90 (v1 rules: < 0.90 or first TL/crash -> stop OUR worker; a further TL/crash -> not-yet-started conc-7 gates -> 5)
#  - conc 8: threshold 0.85; ratio < 0.85 OR any TL OR any crash -> ALERT in the log and every not-yet-started conc-8 gate -> 7 in
#    forge_gates.json (backup + raw re-check + atomic write); running gate untouched, so it takes effect at the next gate boundary.
param([int]$OurPid=6240,[double]$BaseNps=1951072)
$Q='C:\Users\Administrator\grok-pc\forge_push\qa_conc7'; $LOG="$Q\conc7_watch.log"; $A='C:\Users\Administrator\grok-pc\forge_push\autorestart'; $D='D:\grok-pc-data\forge_push'
$MANF="$A\forge_gates.json"; $STATE="$A\forge_queue_state.json"; $CSV='C:\Users\Administrator\grok-pc\nnue\tools\hwinfo\gpu_sensors.csv'; $MARK='selfplay_out_x1_conc7_20261025'
$RCSV="$Q\NPS_RATIO_PER_GATE.csv"; $THR=@{7=0.90;8=0.85}
$mtx=New-Object Threading.Mutex($false,'Global\forge_conc7_watch'); if(-not $mtx.WaitOne(0)){ exit }
try{ $me=Get-Process -Id $PID; $me.PriorityClass='Idle'; $me.ProcessorAffinity=[IntPtr]0xF000 }catch{}
function L($m){ Add-Content $LOG ("{0} PC | {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),$m) -Encoding utf8 }
function Ours(){ $p=Get-CimInstance Win32_Process -Filter "ProcessId=$OurPid" -ea 0; return ($p -and $p.Name -eq 'cmd.exe' -and $p.CommandLine -like "*$MARK*") }
$script:stopped=-not (Ours)
function Stop-Ours($why){ if($script:stopped){ return }; if(Ours){ & taskkill.exe /T /F /PID $OurPid 2>&1 | Out-Null; L "STOPPED our extra datagen tree (cmd PID $OurPid): $why" } else { L "would stop our worker ($why) but PID $OurPid is not ours/alive" }; $script:stopped=$true }
function Read-Shared($p){ $fs=$null;$sr=$null; try{ $fs=[IO.File]::Open($p,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]'ReadWrite,Delete'); $sr=New-Object IO.StreamReader($fs); return $sr.ReadToEnd() }catch{ return '' }finally{ if($sr){$sr.Close()}; if($fs){$fs.Close()} } }
function Temps(){ try{ if(((Get-Date)-(Get-Item $CSV).LastWriteTime).TotalSeconds -gt 60){ return $null }
  $h=(Get-Content $CSV -TotalCount 1) -split ','; $ih=(0..($h.Count-1) | ? { $h[$_] -match 'GPU Hot Spot Temperature' })[0]; $ij=(0..($h.Count-1) | ? { $h[$_] -match 'GPU Memory Junction Temperature' })[0]; $ic=(0..($h.Count-1) | ? { $h[$_] -match 'CPU \(Tctl/Tdie\)' })[0]
  $fs=[IO.File]::Open($CSV,'Open','Read','ReadWrite'); $fs.Seek(-30000,'End')|Out-Null; $sr=New-Object IO.StreamReader($fs); $t=$sr.ReadToEnd(); $sr.Close()
  $row=(@($t -split "`r?`n" | ? { $_ -match '^\d\d\.\d\d\.\d{4}' }))[-1] -split ','; return @{hot=[double]($row[$ih] -replace '"','');memj=[double]($row[$ij] -replace '"','');cpu=[double]($row[$ic] -replace '"','')} }catch{ return $null } }
function Head-Nps($f,$who){ try{ $fs=[IO.File]::Open($f,'Open','Read','ReadWrite'); $buf=New-Object byte[] ([math]::Min($fs.Length,40MB)); $n=$fs.Read($buf,0,$buf.Length); $fs.Close(); $t=[Text.Encoding]::UTF8.GetString($buf,0,$n)
  $v=@([regex]::Matches($t,"$who\S* ---> info depth \d+ .*?nps (\d+) .*?time (\d+)") | ? { [int]$_.Groups[2].Value -ge 100 } | % { [double]$_.Groups[1].Value } | Sort-Object); if($v.Count -lt 50){ return $null }; return $v[[int]($v.Count/2)] }catch{ return $null } }
function Started($g){ return ((Test-Path "$D\$($g.tag)\RESULT.md") -or (Test-Path "$D\$($g.tag)\$($g.tag).log") -or (Test-Path "$D\$($g.tag)\$($g.tag).pgn")) }
# Lower concurrency $from -> $to on not-yet-started gates (not the running one). $freshOnly: v1 behaviour (skip confirms).
function Revert-Conc($cur,$from,$to,$freshOnly){ $raw=[IO.File]::ReadAllText($MANF); $m=$raw | ConvertFrom-Json; $n=0; $tags=@()
  foreach($g in $m.gates){ if(($freshOnly -and $g.confirm_of) -or $g.tag -eq $cur -or [int]$g.concurrency -ne $from -or (Started $g)){ continue }; $g.concurrency=$to; $n++; $tags+="g$($g.gate)" }
  if(-not $n){ L "revert $from->$($to): nothing to change"; return $true }
  $stamp=(Get-Date).ToString('yyyyMMdd_HHmmss'); $bak="$MANF.bak_conc$($to)revert_$stamp"; Copy-Item $MANF $bak
  if([IO.File]::ReadAllText($MANF) -ne $raw){ L "revert $from->$($to): manifest changed while preparing; retry next loop"; return $false }
  $new=($m | ConvertTo-Json -Depth 12); $chk=$new | ConvertFrom-Json
  if(-not $chk -or @($chk.gates).Count -ne @(($raw|ConvertFrom-Json).gates).Count){ L "revert $from->$($to): new JSON did not parse or gate count changed; not applied"; return $false }
  $tmp="$MANF.tmp_conc$($to)revert"; [IO.File]::WriteAllText($tmp,$new,(New-Object Text.UTF8Encoding($true))); Move-Item $tmp $MANF -Force
  L "REVERTED $n not-yet-started gates concurrency $from -> $to ($($tags -join ' ')); backup $bak sha $((Get-FileHash $bak).Hash) -> $((Get-FileHash $MANF).Hash); running gate $cur untouched (effective at next boundary)"; return $true }
if(-not (Test-Path $RCSV)){ 'gate,conc,ratio,n' | Set-Content $RCSV -Encoding utf8 }
$done=@{}; foreach($r in @(Get-Content $RCSV | Select-Object -Skip 1)){ $done[($r -split ',')[0]]=$true }
L "watch start v2-conc8 PID $PID (OurPid $OurPid ours=$(Ours), BaseNps $BaseNps, thresholds conc7 0.90 conc8 0.85; csv rows already: $($done.Count))"
$hotN=0; $tlSeen=@{}; $segSeen=@{}; $rev5=$false; $rev8=@{}; $lastHb=Get-Date 0; $cur=$null; $tp=$null; $free=$null
while($true){
 try{
  $os=Get-CimInstance Win32_OperatingSystem; $free=[math]::Round($os.FreePhysicalMemory/1MB,2)
  if($free -lt 8 -and -not $script:stopped){ Stop-Ours "free RAM $free GB < 8 GB" }
  $tp=Temps
  if($tp){ if($tp.hot -ge 80 -or $tp.memj -ge 88 -or $tp.cpu -ge 92){ $hotN++ } else { $hotN=0 }; if($hotN -ge 2 -and -not $script:stopped){ Stop-Ours "thermal hot=$($tp.hot) memj=$($tp.memj) cpuTctl=$($tp.cpu)" } }
  $st=Get-Content $STATE -Raw -ea 0 | ConvertFrom-Json; $cur=$st.current.tag
  if($cur){ $out="$D\$cur"; $ri=Get-Content "$out\RUN_INFO.json" -Raw -ea 0 | ConvertFrom-Json
   if($ri){ $conc=[int]$ri.concurrency; $gl="$out\$cur.log"; $txt=if(Test-Path $gl){ Read-Shared $gl }else{ '' }
    $rdFail=(-not $txt) -and (Test-Path $gl) -and ($(try{(Get-Item -LiteralPath $gl -ea Stop).Length}catch{0}) -gt 0); if(-not $rdFail){ $hd=if($txt.Length -gt 512){$txt.Substring(0,512)}else{$txt}; if($segSeen.ContainsKey($cur) -and ($txt.Length -lt $segSeen[$cur].len -or -not $txt.StartsWith($segSeen[$cur].hd,[StringComparison]::Ordinal))){ L "log segment change on gate $($cur) (rotated or truncated: $($segSeen[$cur].len) -> $($txt.Length) chars); TL/crash counter reset"; $tlSeen[$cur]=0 }; $segSeen[$cur]=@{len=$txt.Length;hd=$hd} }
    $tl=([regex]::Matches($txt,'(?m)Finished game .*\{.*loses on time')).Count; $cr=([regex]::Matches($txt,'(?m)Finished game .*\{.*(disconnect|stalls|crash|illegal|abandon)')).Count; $bad=$tl+$cr
    $fin=([regex]::Matches($txt,'(?m)^Finished game')).Count
    $prev=if($tlSeen.ContainsKey($cur)){$tlSeen[$cur]}else{0}
    if($bad -gt $prev){ L "ALERT conc-$conc gate $($cur): TL $tl crash $cr"
      if($conc -eq 7){ if(-not $script:stopped){ Stop-Ours "first TL/crash in conc-7 gate $cur" } elseif(-not $rev5){ $rev5=[bool](Revert-Conc $cur 7 5 $true) } }
      if($conc -eq 8){ Stop-Ours "TL/crash in conc-8 gate $cur"; if(-not $rev8[$cur]){ L "ALERT conc-8 rule: TL/crash on $cur -> not-yet-started conc-8 gates back to 7 at the boundary"; $rev8[$cur]=[bool](Revert-Conc $cur 8 7 $false) } }
      $tlSeen[$cur]=$bad }
    if($conc -eq 8 -and $bad -gt 0 -and $rev8.ContainsKey($cur) -and -not $rev8[$cur]){ $rev8[$cur]=[bool](Revert-Conc $cur 8 7 $false) }
    if(-not $done[$cur] -and $fin -ge 50){ $nb=Head-Nps "$out\engine_io.log" 'base_h256_e12'
     if($nb){ $r=[math]::Round($nb/$BaseNps,3); Add-Content $RCSV ("{0},{1},{2},{3}" -f $cur,$conc,$r.ToString([Globalization.CultureInfo]::InvariantCulture),$fin) -Encoding utf8; $done[$cur]=$true
      $thr=$THR[$conc]; $verdict=if($thr){ if($r -ge $thr -and $bad -eq 0){'PASS'}else{'FAIL'} }else{'INFO (no threshold at this conc)'}
      $msg="NPS CHECK gate $cur conc $conc at $fin games: base_h256_e12 median nps $nb / $BaseNps = $r (threshold $(if($thr){$thr}else{'none'})); TL $tl crash $cr -> $verdict"; L $msg
      if($conc -eq 7){ $msg | Set-Content "$Q\NPS_CONC7_CHECK.txt" -Encoding utf8; if($r -lt 0.90 -and -not $script:stopped){ Stop-Ours "conc-7 nps ratio $r < 0.90" } }
      if($conc -eq 8 -and $r -lt 0.85){ L "ALERT conc-8 rule: nps ratio $r < 0.85 on $cur -> not-yet-started conc-8 gates back to 7 at the boundary"; Stop-Ours "conc-8 nps ratio $r < 0.85"; if(-not $rev8[$cur]){ $rev8[$cur]=[bool](Revert-Conc $cur 8 7 $false) } } } }
   } }
  if(((Get-Date)-$lastHb).TotalMinutes -ge 10){ $cpu=[math]::Round((Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2 -MaxSamples 1).CounterSamples[0].CookedValue,1)
    L "HB cpu $cpu% freeRAM $free GB hot $($tp.hot) memj $($tp.memj) cpuTctl $($tp.cpu) gate $cur conc $($ri.concurrency) games $fin TL $tl crash $cr ours_alive=$(Ours) stopped=$($script:stopped) csv_rows $($done.Count)"; $lastHb=Get-Date }
 }catch{ L "loop error: $_" }
 Start-Sleep 30 }