# smoke_run.ps1 - crash / time-loss smoke of the SingularNonCut gate exe (option ON) vs trial_w6 with fastchess
# (own code, 2026-11-06, PowerShell 5.1). Not a verdict: W/D/L is information only; the check is 0 crashes /
# disconnects / illegal moves / stalls and the time losses per engine.
# usage (from Git Bash, never the PowerShell tool):
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File smoke_run.ps1 -Out <new dir under D:\opus_singular_noncut\out>
#     [-Mask 0x4] [-Concurrency 1] [-Rounds 100] [-Srand 20261106] [-Tc 10+0.1] [-Start 1]
# Placement: sets Idle + -Mask on itself first and reads both back (fastchess and both engines inherit them); fails
# closed. Masks inside CPUs 0-3 are always allowed; CPUs 4-6 only before the owner's window end (2026-11-06 02:27 PC
# clock), and only if the run cannot overrun it by the -MaxMinutes estimate. Settings = the crew gate's
# (tc 10+0.1 timemargin=1000, Hash 16, OwnBook false, 8moves_v3 order=random, -games 2 -repeat, -recover) except
# Threads 1 (one CPU per game). Output: <Out>\fastchess.out.txt, smoke.pgn, engine_io.log, SUMMARY.txt.
param(
  [Parameter(Mandatory = $true)][string]$Out,
  [string]$Mask = '0x4',
  [int]$Concurrency = 1,
  [int]$Rounds = 100,
  [int]$Srand = 20261106,
  [string]$Tc = '10+0.1',
  [int]$MaxMinutes = 0,
  [string]$Cand = 'D:\opus_singular_noncut\pack\forge_singular_noncut_gate_5f6be7c5.exe',
  [string]$CandSha = '5f6be7c55ba318790c26690b0a96edec678aab786334247a8e7a630c5610d117',
  [string]$Base = 'C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe',
  [string]$BaseSha = '4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0',
  [string]$Book = 'C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn',
  [string]$Fastchess = 'C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe'
)
$ErrorActionPreference = 'Stop'
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture
$WindowEnd = [datetime]'2026-11-06 02:27:00'
function Now { Get-Date -Format 'yyyy-MM-dd HH:mm:ss' }
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }
function Line([string]$s) { [Console]::Out.WriteLine($s); if ($script:Sum) { [System.IO.File]::AppendAllText($script:Sum, $s + "`n") } }
$script:Sum = ''
try {
  $m = [Convert]::ToInt64(($Mask -replace '^0x', ''), 16)
  if ($m -le 0) { throw "bad mask $Mask" }
  $inLow = (($m -band (-bnot 0xF)) -eq 0)
  $inWin = (($m -band (-bnot 0x7F)) -eq 0)
  if (-not $inLow) {
    if (-not $inWin) { throw "mask $Mask uses CPUs beyond 0-6" }
    if ((Get-Date) -ge $WindowEnd) { throw "mask $Mask uses CPUs 4-6 after the window end $WindowEnd" }
    if ($MaxMinutes -le 0) { throw "a CPU 4-6 mask needs -MaxMinutes (run time estimate)" }
    if ((Get-Date).AddMinutes($MaxMinutes) -gt $WindowEnd) { throw "estimate $MaxMinutes min would overrun the window end $WindowEnd" }
  }
  $nCpu = 0; for ($i = 0; $i -lt 7; $i++) { if ($m -band (1L -shl $i)) { $nCpu++ } }
  if ($Concurrency -lt 1 -or $Concurrency -gt $nCpu) { throw "concurrency $Concurrency > $nCpu CPUs in $Mask" }
  if (-not $Out.StartsWith('D:\opus_singular_noncut\out\')) { throw "output must be under D:\opus_singular_noncut\out\" }
  if (Test-Path $Out) { throw "$Out exists; use a new folder" }
  $dFree = (Get-PSDrive D).Free / 1GB
  if ($dFree -lt 50.3) { throw ("D: has {0:N1} GB free (< 50.3)" -f $dFree) }
  foreach ($x in $Cand, $Base, $Book, $Fastchess) { if (-not (Test-Path -LiteralPath $x)) { throw "missing $x" } }
  if ((Sha $Cand) -ne $CandSha) { throw "cand sha256 mismatch" }
  if ((Sha $Base) -ne $BaseSha) { throw "base sha256 mismatch" }
  $me = [System.Diagnostics.Process]::GetCurrentProcess()
  $me.PriorityClass = 'Idle'
  $me.ProcessorAffinity = [IntPtr]$m
  $me.Refresh()
  if ([long]$me.ProcessorAffinity -ne $m) { throw "affinity not applied" }
  if ("$($me.PriorityClass)" -ne 'Idle') { throw "priority not applied" }
  New-Item -ItemType Directory -Path $Out | Out-Null
  $script:Sum = Join-Path $Out 'SUMMARY.txt'
  Line "smoke_run start $(Now): mask $Mask ($nCpu CPUs) Idle, concurrency $Concurrency, rounds $Rounds (games $(2 * $Rounds)), tc $Tc, srand $Srand"
  Line "cand $Cand sha256 $CandSha option SingularNonCut=1; base $Base sha256 $BaseSha; book $Book order=random"
  $pgn = Join-Path $Out 'smoke.pgn'; $elog = Join-Path $Out 'engine_io.log'
  $fargs = @(
    '-engine', "cmd=$Cand", 'name=snc_on', 'option.SingularNonCut=1',
    '-engine', "cmd=$Base", 'name=trial_w6',
    '-each', "tc=$Tc", 'timemargin=1000', 'proto=uci', 'option.Threads=1', 'option.Hash=16', 'option.OwnBook=false',
    '-openings', "file=$Book", 'format=pgn', 'order=random',
    '-srand', "$Srand", '-games', '2', '-repeat', '-rounds', "$Rounds", '-concurrency', "$Concurrency", '-recover',
    '-pgnout', "file=$pgn", 'timeleft=true',
    '-log', "file=$elog", 'level=warn', 'engine=true', 'append=false')
  Line ("fastchess " + ($fargs -join ' '))
  $fo = Join-Path $Out 'fastchess.out.txt'
  $p = Start-Process -FilePath $Fastchess -ArgumentList $fargs -RedirectStandardOutput $fo -RedirectStandardError "$fo.stderr.txt" -NoNewWindow -PassThru -WorkingDirectory $Out
  $null = $p.Handle
  $p.WaitForExit()
  Line "fastchess exit $($p.ExitCode) at $(Now)"
  $txt = @(Get-Content $fo)
  $fin = @($txt | Where-Object { $_ -match '^Finished game' })
  # fastchess names the colour ('{White loses on time}'); '(A vs B)' = A has White
  $timeCand = @($fin | Where-Object { ($_ -match '\(snc_on vs trial_w6\)' -and $_ -match 'White loses on time') -or ($_ -match '\(trial_w6 vs snc_on\)' -and $_ -match 'Black loses on time') }).Count
  $timeBase = @($fin | Where-Object { ($_ -match '\(trial_w6 vs snc_on\)' -and $_ -match 'White loses on time') -or ($_ -match '\(snc_on vs trial_w6\)' -and $_ -match 'Black loses on time') }).Count
  $timeAll = @($fin | Where-Object { $_ -match 'loses on time' }).Count
  if ($timeAll -ne ($timeCand + $timeBase)) { Line "time-loss lines $timeAll do not split into the two engines ($timeCand + $timeBase): read fastchess.out.txt" }
  $bad = @($txt | Where-Object { $_ -match '(?i)disconnect|illegal|crash|stall|timeout|error|warning|responsive' })
  Line "finished games $($fin.Count) of $(2 * $Rounds); time losses snc_on $timeCand, trial_w6 $timeBase; disconnect / illegal / crash / stall / error lines $($bad.Count)"
  foreach ($b in ($bad | Select-Object -First 20)) { Line "  $b" }
  foreach ($r in ($txt | Where-Object { $_ -match '^(Results of|Elo:|LOS:|Games:|Ptnml|Points:|Draw)' } | Select-Object -Last 8)) { Line "  $r" }
  if ($p.ExitCode -ne 0 -or $fin.Count -ne (2 * $Rounds) -or $bad.Count -ne 0) { Line 'SMOKE CHECK: NOT CLEAN (see above)'; exit 3 }
  Line 'SMOKE CHECK: CLEAN (no crash / disconnect / illegal move / stall line; time losses listed above; W/D/L not a verdict)'
  exit 0
} catch {
  Line "smoke_run ERROR: $($_.Exception.Message)"
  exit 1
}
