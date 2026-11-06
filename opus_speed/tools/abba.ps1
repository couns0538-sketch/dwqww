# abba.ps1 - ABBA nps protocol of the speed job (PowerShell 5.1).
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File abba.ps1 -A <exeA> -B <exeB> -Out <new dir>
#          [-Core 2] [-Depth 16] [-Rounds 10] [-Cooldown 3] [-Option 'UseNNUE=false'] [-CopyMode Round|None]
#          [-AaCsv <runs.csv of this session's lock-vs-lock run>] [-LabelA lock] [-LabelB cand] [-AllowNodeDiff]
# Per round the order is A B B A; every run is a fresh engine process pinned to ONE logical CPU (-Core, 0-3) at
# BelowNormal (this script pins itself first, so children inherit both from their first instruction), net loaded
# (default options; the uci answer must advertise 'UseNNUE ... default true' unless -Option sets UseNNUE), 'bench
# <Depth>' and the engine's own nodes / ms / nps; -Cooldown seconds between runs. -CopyMode Round (default) runs fresh
# byte copies of A and B in every round (one untimed 'bench 1' warm-up each): an exe and its own byte copy differed by
# 3-5 % on this PC (R12, BH-8), so the per-file effect becomes noise that the interval sees, not a bias.
# Statistics: ratio per round = (nps B1 + nps B2) / (nps A1 + nps A2); median; 95 % two-sided Student-t interval of the
# mean log ratio (exp back); a seeded bootstrap interval of the median as a second line. WIN only if the t-interval's
# low end > 1.000 AND the median >= 1.010. -AaCsv adds the A/A band of the same session. Nodes must be constant per
# exe (always) and equal between A and B (unless -AllowNodeDiff): a bit-exact candidate searches the same tree.
# Outputs in -Out (refused if it exists): runs.csv (round, order, exe, md5, depth, nodes, ms, nps, core, timestamp),
# summary.txt (5 lines + details), uci.log, load.txt, copies\. A named mutex serialises timing runs on the PC.
# Exit: 0 done (WIN or not), 2 node mismatch / missing UseNNUE / bad args, 1 other error.
param(
  [Parameter(Mandatory = $true)][string]$A,
  [Parameter(Mandatory = $true)][string]$B,
  [Parameter(Mandatory = $true)][string]$Out,
  [int]$Core = 2,
  [int]$Depth = 16,
  [int]$Rounds = 10,
  [int]$Cooldown = 3,
  [string[]]$Option = @(),
  [string[]]$OptionB = @(),
  [ValidateSet('Round', 'None')][string]$CopyMode = 'Round',
  [string]$AaCsv = '',
  [string]$LabelA = 'A',
  [string]$LabelB = 'B',
  [switch]$AllowNodeDiff,
  [ValidateSet('Alternate', 'ABBA')][string]$Order = 'Alternate',
  [int]$MutexWaitMin = 240
)
# -Order Alternate (default): odd rounds A B B A, even rounds B A A B, and the arm copied first alternates with it.
# Reason (A/A runs of 2026-11-05): per-slot means differed by up to ~1-2 % between slot positions (in one A/A the
# middle slots - always arm B in plain ABBA - were faster); counterbalancing cancels any slot / copy-order effect over
# every pair of rounds. -Order ABBA keeps the literal A B B A order in every round.
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\uci_lib.ps1"
# -File passes a list as ONE comma-joined string: split every list parameter on commas
$Option = @($Option | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
# -OptionB 'Name=Value,...' (2026-11-06, leftover checks): extra UCI options for arm B only, after -Option (e.g. the same
# gate exe OFF vs ON; needs -AllowNodeDiff when the option changes the tree). Default empty = the old run.
$OptionB = @($OptionB | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
function Get-ArmOptions([string]$Arm) { if ($Arm -eq 'B') { return @($Option + $OptionB) } return @($Option) }

$T975 = @{ 1 = 12.706; 2 = 4.303; 3 = 3.182; 4 = 2.776; 5 = 2.571; 6 = 2.447; 7 = 2.365; 8 = 2.306; 9 = 2.262; 10 = 2.228;
  11 = 2.201; 12 = 2.179; 13 = 2.160; 14 = 2.145; 15 = 2.131; 16 = 2.120; 17 = 2.110; 18 = 2.101; 19 = 2.093; 20 = 2.086;
  21 = 2.080; 22 = 2.074; 23 = 2.069; 24 = 2.064; 25 = 2.060; 26 = 2.056; 27 = 2.052; 28 = 2.048; 29 = 2.045; 30 = 2.042 }
function Get-T975([int]$Df) {
  if ($T975.ContainsKey($Df)) { return $T975[$Df] }
  $z = 1.959964
  return $z + ($z * $z * $z + $z) / (4 * $Df) + (5 * [Math]::Pow($z, 5) + 16 * $z * $z * $z + 3 * $z) / (96 * $Df * $Df)
}
function Get-Median([double[]]$X) {
  $s = [double[]]$X.Clone(); [Array]::Sort($s); $n = $s.Count
  if ($n % 2 -eq 1) { return $s[($n - 1) / 2] } else { return ($s[$n / 2 - 1] + $s[$n / 2]) / 2 }
}
function Get-RatioStats([double[]]$R) {
  $n = $R.Count
  $logs = [double[]]($R | ForEach-Object { [Math]::Log($_) })
  $mean = ($logs | Measure-Object -Average).Average
  $sd = 0.0
  if ($n -gt 1) { $sd = [Math]::Sqrt((($logs | ForEach-Object { ($_ - $mean) * ($_ - $mean) }) | Measure-Object -Sum).Sum / ($n - 1)) }
  $half = 0.0; if ($n -gt 1) { $half = (Get-T975 ($n - 1)) * $sd / [Math]::Sqrt($n) }
  $rng = New-Object System.Random(20261105)
  $meds = New-Object double[] 10000
  for ($i = 0; $i -lt 10000; $i++) {
    $smp = New-Object double[] $n
    for ($j = 0; $j -lt $n; $j++) { $smp[$j] = $R[$rng.Next($n)] }
    $meds[$i] = Get-Median $smp
  }
  [Array]::Sort($meds)
  return [pscustomobject]@{ N = $n; Median = (Get-Median $R); Geo = [Math]::Exp($mean); Lo = [Math]::Exp($mean - $half);
    Hi = [Math]::Exp($mean + $half); SdPct = 100 * $sd; BootLo = $meds[249]; BootHi = $meds[9749] }
}
function Read-RoundRatios([string]$Csv, [string]$Col = 'nps') {
  $rows = Import-Csv $Csv
  if ($rows.Count -gt 0 -and -not ($rows[0].PSObject.Properties.Name -contains $Col)) { return [double[]]@() }
  $byRound = @{}
  foreach ($r in $rows) {
    $arm = ($r.order -split ':')[1]
    if (-not $byRound.ContainsKey($r.round)) { $byRound[$r.round] = @{ A = 0.0; B = 0.0; NA = 0; NB = 0 } }
    if ($arm -eq 'A') { $byRound[$r.round].A += [double]$r.$Col; $byRound[$r.round].NA++ } else { $byRound[$r.round].B += [double]$r.$Col; $byRound[$r.round].NB++ }
  }
  $out = @()
  foreach ($k in ($byRound.Keys | Sort-Object { [int]$_ })) { $v = $byRound[$k]; if ($v.NA -eq 2 -and $v.NB -eq 2) { $out += $v.B / $v.A } }
  return [double[]]$out
}
function Get-CpuLoad([int]$C) {
  $sib = $C -bxor 1
  $paths = @("\Processor($C)\% Processor Time", "\Processor($sib)\% Processor Time", '\Processor(_Total)\% Processor Time')
  try {
    $s = (Get-Counter -Counter $paths -SampleInterval 1 -MaxSamples 2 -ErrorAction Stop).CounterSamples
    $avg = @{}; foreach ($x in $s) { $k = $x.Path; if (-not $avg.ContainsKey($k)) { $avg[$k] = @() }; $avg[$k] += $x.CookedValue }
    $vals = @(); foreach ($p in $paths) { $key = ($avg.Keys | Where-Object { $_ -like ('*' + $p.ToLower()) } | Select-Object -First 1); if ($key) { $vals += ('{0:N0}' -f (($avg[$key] | Measure-Object -Average).Average)) } else { $vals += '?' } }
    return "cpu$C $($vals[0])% sibling cpu$sib $($vals[1])% total $($vals[2])%"
  } catch { return "load sample failed: $($_.Exception.Message)" }
}

try {
  if ($Core -lt 0 -or $Core -gt 3) { throw "-Core must be 0-3 (job rule)" }
  if ($Rounds -lt 10) { throw "-Rounds must be >= 10 (protocol)" }
  foreach ($x in $A, $B) { if (-not (Test-Path -LiteralPath $x)) { throw "missing exe $x" } }
  if ($AaCsv -and -not (Test-Path -LiteralPath $AaCsv)) { throw "missing -AaCsv $AaCsv (checked before the runs, review LOW 5)" }
  if (Test-Path $Out) { throw "$Out exists; use a new folder" }
  $mutex = New-Object System.Threading.Mutex($false, 'Local\ospd_abba_timing')
  $got = $false
  try { $got = $mutex.WaitOne([TimeSpan]::FromMinutes($MutexWaitMin)) } catch [System.Threading.AbandonedMutexException] { $got = $true }
  if (-not $got) { throw "another timing run holds the mutex for > $MutexWaitMin min" }
  Set-OspdPlacement -Mask ([long](1 -shl $Core)) -Priority 'BelowNormal'
  $copies = 0; if ($CopyMode -eq 'Round') { $copies = 2 * $Rounds }
  $diskMsg = Assert-OspdDisk -PlannedGB (0.01 + $copies * ((Get-Item $A).Length + (Get-Item $B).Length) / 2 / 1GB)
  New-Item -ItemType Directory -Path $Out | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $Out 'copies') | Out-Null
  $csv = Join-Path $Out 'runs.csv'; $log = Join-Path $Out 'uci.log'; $loadFile = Join-Path $Out 'load.txt'
  Add-OspdLf $csv 'round,order,exe,md5,depth,nodes,ms,nps,core,timestamp,cpu_ms,cpu_nps'
  $md5A = Get-OspdMd5 $A; $md5B = Get-OspdMd5 $B
  $netOn = -not ($Option | Where-Object { $_ -match '^UseNNUE=' })
  Add-OspdLf $loadFile ("$(Get-OspdNow) start: " + (Get-CpuLoad $Core) + "; $diskMsg")
  $nodes = @{ A = $null; B = $null }
  $ratios = @(); $cpuRatios = @()
  for ($r = 1; $r -le $Rounds; $r++) {
    $exe = @{ A = $A; B = $B }
    $armOrder = @('A', 'B', 'B', 'A'); $copyOrder = @('A', 'B')
    if ($Order -eq 'Alternate' -and ($r % 2 -eq 0)) { $armOrder = @('B', 'A', 'A', 'B'); $copyOrder = @('B', 'A') }
    if ($CopyMode -eq 'Round') {
      foreach ($arm in $copyOrder) {
        $dst = Join-Path $Out ("copies\{0}_r{1:D2}.exe" -f $arm, $r)
        Copy-Item -LiteralPath $exe[$arm] -Destination $dst
        $exe[$arm] = $dst
        $w = Start-OspdEngine $dst $log
        $null = Initialize-OspdEngine $w (Get-ArmOptions $arm)
        $null = Invoke-OspdBench $w 10 120
        $null = Stop-OspdEngine $w
      }
    }
    $sum = @{ A = 0.0; B = 0.0 }; $csum = @{ A = 0.0; B = 0.0 }
    $slot = 0
    foreach ($arm in $armOrder) {
      $slot++
      Start-Sleep -Seconds $Cooldown
      $e = Start-OspdEngine $exe[$arm] $log
      $uciLines = Initialize-OspdEngine $e (Get-ArmOptions $arm)
      if ($netOn -and -not ((Get-OspdUciOptionLine $uciLines 'UseNNUE') -match 'default true')) { $null = Stop-OspdEngine $e; Write-Output "FAIL: $($exe[$arm]) does not advertise UseNNUE default true (net not loaded)"; exit 2 }
      # process CPU time of the bench window (engine idle before and after it): time slices taken by other programs on
      # this CPU do not count here, unlike the engine's own wall-clock nps (both are recorded and evaluated). It removes
      # PREEMPTION only: a busy SMT sibling still slows the run, and Windows counts CPU time in 15.625 ms ticks (about
      # 0.1-0.3 % of a d20 run). The protocol verdict is the wall one; the cpu one is advisory (review LOW 6, SHOULD 4).
      $e.Proc.Refresh(); $c0 = $e.Proc.TotalProcessorTime.TotalMilliseconds
      $res = Invoke-OspdBench $e $Depth
      $e.Proc.Refresh(); $cpuMs = $e.Proc.TotalProcessorTime.TotalMilliseconds - $c0
      $null = Stop-OspdEngine $e
      if ($null -eq $nodes[$arm]) { $nodes[$arm] = $res.Nodes } elseif ($nodes[$arm] -ne $res.Nodes) { Write-Output "FAIL: nodes of $arm changed ($($nodes[$arm]) -> $($res.Nodes))"; exit 2 }
      $md5 = $md5A; if ($arm -eq 'B') { $md5 = $md5B }
      $cpuNps = 0; if ($cpuMs -gt 0) { $cpuNps = [long]($res.Nodes * 1000.0 / $cpuMs) }
      Add-OspdLf $csv ("{0},{1}:{2},{3},{4},{5},{6},{7},{8},{9},{10},{11:F0},{12}" -f $r, $slot, $arm, $exe[$arm], $md5, $Depth, $res.Nodes, $res.Ms, $res.Nps, $Core, (Get-OspdNow), $cpuMs, $cpuNps)
      $sum[$arm] += [double]$res.Nps; $csum[$arm] += [double]$cpuNps
    }
    $ratios += $sum.B / $sum.A
    if ($csum.A -gt 0) { $cpuRatios += $csum.B / $csum.A }
    if (-not $AllowNodeDiff -and $nodes.A -ne $nodes.B) { Write-Output "FAIL: nodes differ A $($nodes.A) vs B $($nodes.B) at bench $Depth (not bit-exact)"; exit 2 }
  }
  Add-OspdLf $loadFile ("$(Get-OspdNow) end: " + (Get-CpuLoad $Core))
  $st = Get-RatioStats ([double[]]$ratios)
  $win = ($st.Lo -gt 1.0) -and ($st.Median -ge 1.010)
  $cst = Get-RatioStats ([double[]]$cpuRatios)
  $cwin = ($cst.Lo -gt 1.0) -and ($cst.Median -ge 1.010)
  $aaLine = 'A/A: none given (-AaCsv)'
  if ($AaCsv) {
    $aa = Get-RatioStats (Read-RoundRatios $AaCsv 'nps')
    $flag = ''; if ($aa.Lo -gt 1.0 -or $aa.Hi -lt 1.0) { $flag = ' (WARNING: excludes 1.000)' }
    $aaLine = ("A/A {0}: wall n={1} median {2:N4} 95% [{3:N4}, {4:N4}] sd {5:N2}%{6}" -f (Split-Path (Split-Path $AaCsv -Parent) -Leaf), $aa.N, $aa.Median, $aa.Lo, $aa.Hi, $aa.SdPct, $flag)
    $aac = Read-RoundRatios $AaCsv 'cpu_nps'
    if ($aac.Count -gt 1) {
      $aa2 = Get-RatioStats $aac
      $flag2 = ''; if ($aa2.Lo -gt 1.0 -or $aa2.Hi -lt 1.0) { $flag2 = ' (WARNING: excludes 1.000)' }
      $aaLine += ("; cpu median {0:N4} 95% [{1:N4}, {2:N4}] sd {3:N2}%{4}" -f $aa2.Median, $aa2.Lo, $aa2.Hi, $aa2.SdPct, $flag2)
    } else { $aaLine += '; cpu: not in that CSV' }
  }
  $verdict = 'NO-WIN'; if ($win) { $verdict = 'WIN' }
  $cverdict = 'NO-WIN'; if ($cwin) { $cverdict = 'WIN' }
  $lines = @(
    ("ABBA {0} (A, md5 {1}) vs {2} (B, md5 {3}); bench d{4}, {5} rounds, order {6}, CPU {7} BelowNormal, net {8}, copies {9}; nodes A {10} B {11} ({12})" -f $LabelA, $md5A, $LabelB, $md5B, $Depth, $Rounds, $(if ($Order -eq 'Alternate') { 'ABBA/BAAB alternating' } else { 'ABBA every round' }), $Core, $(if ($netOn) { 'on' } else { 'off' }), $CopyMode, $nodes.A, $nodes.B, $(if ($nodes.A -eq $nodes.B) { 'equal' } else { 'DIFFERENT' })),
    ("wall (engine nps): B/A median {0:N4} ({1:+0.00;-0.00}%), 95% t-interval [{2:N4}, {3:N4}], sd/round {4:N2}%, bootstrap median CI [{5:N4}, {6:N4}]" -f $st.Median, (100 * ($st.Median - 1)), $st.Lo, $st.Hi, $st.SdPct, $st.BootLo, $st.BootHi),
    ("cpu (nodes / process CPU time of the bench window): B/A median {0:N4} ({1:+0.00;-0.00}%), 95% t-interval [{2:N4}, {3:N4}], sd/round {4:N2}%, bootstrap median CI [{5:N4}, {6:N4}]" -f $cst.Median, (100 * ($cst.Median - 1)), $cst.Lo, $cst.Hi, $cst.SdPct, $cst.BootLo, $cst.BootHi),
    $aaLine,
    ("VERDICT wall {0} / cpu {1} (PROTOCOL verdict = wall, the engine's own bench nps; cpu = advisory: it removes preemption by other programs but not SMT-sibling contention; rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt" -f $verdict, $cverdict)
  )
  $runId = New-OspdRunId
  $lines = @("run $runId") + $lines
  $sumAll = ($lines + @('', 'per-round wall ratios: ' + (($ratios | ForEach-Object { '{0:N4}' -f $_ }) -join ' '), 'per-round cpu ratios: ' + (($cpuRatios | ForEach-Object { '{0:N4}' -f $_ }) -join ' '), "runs.csv md5 $(Get-OspdMd5 $csv)") + (Get-Content $loadFile))
  # Code Review SHOULD 1: every run writes a NEW summary file (run id in the name); nothing is overwritten, and one
  # line per run is appended to F:\ospd\abba\abba_history.log so earlier results stay readable
  Write-OspdLf (Join-Path $Out ("summary_{0}.txt" -f $runId)) $sumAll
  Write-OspdLf (Join-Path $Out 'summary.txt') $sumAll
  Add-OspdLf 'F:\ospd\abba\abba_history.log' ("{0}`t{1}`t{2}" -f $runId, $Out, (($lines | Select-Object -Skip 2) -join ' | '))
  $lines | ForEach-Object { Write-Output $_ }
  exit 0
} catch {
  Write-Output "ERROR: $($_.Exception.Message)"
  exit 1
} finally {
  if ($got) { try { $mutex.ReleaseMutex() } catch {} }
}
