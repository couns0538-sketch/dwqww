# uci_lifecycle_stress.ps1 (opus2, PowerShell 5.1) - exe-level SMP lifecycle stress (opus_smp_layout/SPEC.md section 6).
# One engine session, random but seeded actions, each waiting for the engine's real answer (no sleeps as a substitute for
# synchronisation; short sleeps only to let a search run before stop / ponderhit):
#   go movetime | go nodes | go depth | go infinite -> stop | go ponder -> ponderhit | go ponder -> stop |
#   isready while searching (latency) | setoption Threads (from -ThreadSet) | Hash 1/16/64 | Clear Hash | ucinewgame
# Checks: every bestmove (and ponder move) is legal by the engine's own 'go perft 1' on the same position, no
# 'info string' error/invalid line, isready answers while searching, quit -> exit within 30 s with code 0.
# Records peak working set. Runs pinned (CPUs 12-15, Idle) and never ends a process: a hang is reported and left.
param(
  [Parameter(Mandatory=$true)][string]$Exe,
  [Parameter(Mandatory=$true)][string]$Tag,
  [Parameter(Mandatory=$true)][string]$OutDir,
  [string]$Options = '',                 # e.g. 'TtLockless=true'
  [string]$ThreadSet = '1,4,8',
  [int]$Cycles = 300,
  [int]$Seed = 20261109,
  [string]$Fens = 'D:\forge_jobs_20261107\opus2\out\data\fens_12k_v2.txt',
  [long]$Mask = 0xF000
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\o2_uci_lib.ps1"
Set-OspdPlacement $Mask 'Idle'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$null = Assert-OspdDisk 0.05
$threadsList = @($ThreadSet -split ',' | Where-Object { $_ } | ForEach-Object { [int]$_ })
$rng = New-Object System.Random($Seed)
$fenPool = @(Get-Content -LiteralPath $Fens | Select-Object -First 3000 | ForEach-Object { ConvertTo-OspdFen $_ })
$log = Join-Path $OutDir "$Tag.uci.log"
$summary = Join-Path $OutDir "$Tag.summary.txt"
$fail = New-Object System.Collections.Generic.List[string]
$count = @{}
function Note([string]$k) { if ($count.ContainsKey($k)) { $count[$k]++ } else { $count[$k] = 1 } }

function Get-LegalSet($Eng, [string]$PositionCmd) {
  Send-OspdUci $Eng $PositionCmd
  Send-OspdUci $Eng 'go perft 1'
  $r = Wait-OspdUci $Eng '^nodes (\d+)' 120 -Collect
  $set = @{}
  foreach ($l in $r.Lines) { if ($l -match '^([a-h][1-8][a-h][1-8][qrbn]?): \d+$') { $set[$Matches[1]] = $true } }
  return $set
}
function Assert-Bestmove($Eng, [string]$Fen, [string[]]$Lines, [string]$What) {
  $bm = $null; $pm = $null
  foreach ($l in $Lines) {
    if ($l.StartsWith('info string') -and ($l -match '(?i)error|invalid|exception')) { $fail.Add("$What : engine said '$l'") }
    if ($l -match '^bestmove (\S+)(?: ponder (\S+))?') { $bm = $Matches[1]; if ($Matches.Count -gt 2) { $pm = $Matches[2] } }
  }
  if (-not $bm) { $fail.Add("$What : no bestmove"); return }
  $legal = Get-LegalSet $Eng ("position fen " + $Fen)
  if ($legal.Count -eq 0) { if ($bm -ne '(none)' -and $bm -ne '0000') { $fail.Add("$What : bestmove $bm in a position without legal moves") }; return }
  if (-not $legal.ContainsKey($bm)) { $fail.Add("$What : ILLEGAL bestmove $bm (fen $Fen)"); return }
  Note 'legal_bestmove'
  if ($pm) {
    $legal2 = Get-LegalSet $Eng ("position fen " + $Fen + " moves " + $bm)
    if (-not $legal2.ContainsKey($pm)) { $fail.Add("$What : ILLEGAL ponder move $pm after $bm (fen $Fen)") } else { Note 'legal_pondermove' }
  }
}

$eng = Start-OspdEngine $Exe $log
$opts = @('OwnBook=false') + @($Options -split ';' | Where-Object { $_ })
$null = Initialize-OspdEngine $eng $opts
$maxReadyMs = 0.0; $curThreads = 1
$t0 = Get-Date
try {
  for ($i = 0; $i -lt $Cycles; $i++) {
    $fen = $fenPool[$rng.Next($fenPool.Count)]
    $a = $rng.Next(100)
    if ($a -lt 8) {
      $th = $threadsList[$rng.Next($threadsList.Count)]; $curThreads = $th
      Send-OspdUci $eng "setoption name Threads value $th"; Send-OspdUci $eng 'isready'; $null = Wait-OspdUci $eng '^readyok' 120; Note "threads_$th"
    } elseif ($a -lt 14) {
      $h = @(1, 16, 64)[$rng.Next(3)]
      Send-OspdUci $eng "setoption name Hash value $h"; Send-OspdUci $eng 'isready'; $null = Wait-OspdUci $eng '^readyok' 120; Note "hash_$h"
    } elseif ($a -lt 18) {
      Send-OspdUci $eng 'setoption name Clear Hash'; Send-OspdUci $eng 'isready'; $null = Wait-OspdUci $eng '^readyok' 120; Note 'clear_hash'
    } elseif ($a -lt 22) {
      Send-OspdUci $eng 'ucinewgame'; Send-OspdUci $eng 'isready'; $null = Wait-OspdUci $eng '^readyok' 120; Note 'ucinewgame'
    } else {
      Send-OspdUci $eng ("position fen " + $fen)
      $b = $rng.Next(100)
      if ($b -lt 25) {
        Send-OspdUci $eng ("go movetime " + (30 + $rng.Next(120))); $r = Wait-OspdUci $eng '^bestmove' 120 -Collect; Assert-Bestmove $eng $fen $r.Lines "cycle $i movetime T$curThreads"; Note 'go_movetime'
      } elseif ($b -lt 45) {
        Send-OspdUci $eng ("go nodes " + (5000 + $rng.Next(60000))); $r = Wait-OspdUci $eng '^bestmove' 600 -Collect; Assert-Bestmove $eng $fen $r.Lines "cycle $i nodes T$curThreads"; Note 'go_nodes'
      } elseif ($b -lt 55) {
        Send-OspdUci $eng ("go depth " + (4 + $rng.Next(5))); $r = Wait-OspdUci $eng '^bestmove' 600 -Collect; Assert-Bestmove $eng $fen $r.Lines "cycle $i depth T$curThreads"; Note 'go_depth'
      } elseif ($b -lt 72) {
        Send-OspdUci $eng 'go infinite'; Start-Sleep -Milliseconds (20 + $rng.Next(80))
        if ($rng.Next(2) -eq 0) {
          $sw = [System.Diagnostics.Stopwatch]::StartNew(); Send-OspdUci $eng 'isready'
          $rr = Wait-OspdUci $eng '^readyok' 30 -Collect; $ms = $sw.Elapsed.TotalMilliseconds; if ($ms -gt $maxReadyMs) { $maxReadyMs = $ms }
          foreach ($x in $rr.Lines) { if ($x.StartsWith('bestmove')) { $fail.Add("cycle $i : bestmove before stop during go infinite") } }
          Note 'isready_while_searching'
        }
        Send-OspdUci $eng 'stop'; $r = Wait-OspdUci $eng '^bestmove' 60 -Collect; Assert-Bestmove $eng $fen $r.Lines "cycle $i infinite+stop T$curThreads"; Note 'go_infinite_stop'
      } elseif ($b -lt 88) {
        Send-OspdUci $eng ("go ponder movetime " + (40 + $rng.Next(100))); Start-Sleep -Milliseconds (15 + $rng.Next(60))
        Send-OspdUci $eng 'ponderhit'; $r = Wait-OspdUci $eng '^bestmove' 120 -Collect; Assert-Bestmove $eng $fen $r.Lines "cycle $i ponder+ponderhit T$curThreads"; Note 'go_ponder_ponderhit'
      } else {
        Send-OspdUci $eng 'go ponder'; Start-Sleep -Milliseconds (15 + $rng.Next(60))
        Send-OspdUci $eng 'stop'; $r = Wait-OspdUci $eng '^bestmove' 60 -Collect; Assert-Bestmove $eng $fen $r.Lines "cycle $i ponder+stop T$curThreads"; Note 'go_ponder_stop'
      }
    }
  }
} catch {
  $fail.Add("EXCEPTION: $($_.Exception.Message)")
}
$peak = 0
try { $eng.Proc.Refresh(); $peak = $eng.Proc.PeakWorkingSet64 } catch {}
$exitOk = Stop-OspdEngine $eng
$code = $null; if ($exitOk) { $code = $eng.Proc.ExitCode; if ($code -ne 0) { $fail.Add("exit code $code") } } else { $fail.Add("engine did not exit within 30 s after quit (left running, pid $($eng.Proc.Id))") }
$secs = ((Get-Date) - $t0).TotalSeconds
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("uci_lifecycle_stress tag=$Tag exe=$Exe sha256=$(Get-OspdSha256 $Exe) options=[$($opts -join ';')] threads={$ThreadSet} cycles=$Cycles seed=$Seed")
$lines.Add(("wall {0:N1} s | peak working set {1:N1} MiB | max isready latency while searching {2:N1} ms | exit ok={3} code={4}" -f $secs, ($peak / 1MB), $maxReadyMs, $exitOk, $code))
foreach ($k in ($count.Keys | Sort-Object)) { $lines.Add("  $k = $($count[$k])") }
foreach ($f in $fail) { $lines.Add("FAIL $f") }
$lines.Add($(if ($fail.Count -eq 0) { "STRESS: PASS" } else { "STRESS: FAIL ($($fail.Count))" }))
Write-OspdLf $summary $lines -Force
$lines
if ($fail.Count -eq 0) { exit 0 } else { exit 1 }
