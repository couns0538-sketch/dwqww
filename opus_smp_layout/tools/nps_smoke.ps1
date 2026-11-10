# nps_smoke.ps1 (opus2, PowerShell 5.1) - ADVISORY nps smoke for the SMP pack (opus_smp_layout/BENCH.md). NOT a speed
# verdict, NOT scaling evidence, NOT Elo: CPUs 12-15 are two physical cores (SMT pairs 12/13, 14/15) on a shared PC, so
# Threads 4 is SMT-loaded and Threads 8 would be oversubscribed. QA owns quiet timing (SCALING_PLAN.md).
# Each round starts every config fresh, in alternating order (ABBA / BAAB over the config list), Threads T, Hash 64,
# OwnBook false, then per FEN: ucinewgame + position + 'go nodes N' (or 'go movetime M'); nodes and time come from the
# engine's last info line; round nps = sum nodes / sum time. Reports per-config median, min, max and the ratio of medians.
# Config file lines: name<TAB>exe<TAB>options ('Name=Value;Name2=Value2' or empty).
param(
  [Parameter(Mandatory=$true)][string]$ConfigFile,
  [Parameter(Mandatory=$true)][string]$OutDir,
  [Parameter(Mandatory=$true)][string]$Tag,
  [int]$Threads = 4,
  [ValidateSet('nodes', 'movetime')][string]$Mode = 'nodes',
  [int]$Nodes = 400000,
  [int]$MoveTime = 1500,
  [int]$Rounds = 6,
  [int]$FenCount = 8,
  [string]$Fens = 'D:\forge_jobs_20261107\opus2\out\data\fens_12k_v2.txt',
  [long]$Mask = 0xF000
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\o2_uci_lib.ps1"
Set-OspdPlacement $Mask 'Idle'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$configs = @(Get-Content -LiteralPath $ConfigFile | Where-Object { $_ -and -not $_.StartsWith('#') } | ForEach-Object {
  $p = $_ -split "`t"; [pscustomobject]@{ Name = $p[0]; Exe = $p[1]; Options = $(if ($p.Count -gt 2) { $p[2] } else { '' }); Sha = (Get-OspdSha256 $p[1]) } })
$fenList = @(Get-Content -LiteralPath $Fens | Select-Object -Skip 500 -First $FenCount | ForEach-Object { ConvertTo-OspdFen $_ })
$csv = Join-Path $OutDir "$Tag.runs.csv"
Write-OspdLf $csv @('round,order,config,threads,mode,nodes,ms,nps') -Force
$go = if ($Mode -eq 'nodes') { "go nodes $Nodes" } else { "go movetime $MoveTime" }
$results = @{}
foreach ($c in $configs) { $results[$c.Name] = New-Object System.Collections.Generic.List[double] }
for ($r = 0; $r -lt $Rounds; $r++) {
  $order = if (($r % 2) -eq 0) { $configs } else { @($configs)[($configs.Count - 1)..0] }
  $pos = 0
  foreach ($c in $order) {
    $eng = Start-OspdEngine $c.Exe ''
    $opts = @('OwnBook=false', "Threads=$Threads", 'Hash=64') + @($c.Options -split ';' | Where-Object { $_ })
    $null = Initialize-OspdEngine $eng $opts
    $sumNodes = 0L; $sumMs = 0L
    foreach ($fen in $fenList) {
      Send-OspdUci $eng 'ucinewgame'; Send-OspdUci $eng 'isready'; $null = Wait-OspdUci $eng '^readyok' 120
      Send-OspdUci $eng ("position fen " + $fen); Send-OspdUci $eng $go
      $res = Wait-OspdUci $eng '^bestmove' 600 -Collect
      $last = $null; foreach ($l in $res.Lines) { if ($l -match ' nodes (\d+) .*?time (\d+)' -or $l -match ' time (\d+) .*?nodes (\d+)') { $last = $l } }
      $mn = [regex]::Match($last, ' nodes (\d+)'); $mt = [regex]::Match($last, ' time (\d+)')
      if (-not ($mn.Success -and $mt.Success)) { throw "no nodes/time info line for $($c.Name)" }
      $sumNodes += [long]$mn.Groups[1].Value; $sumMs += [long]$mt.Groups[1].Value
    }
    $null = Stop-OspdEngine $eng
    $nps = if ($sumMs -gt 0) { [double]$sumNodes * 1000.0 / [double]$sumMs } else { 0.0 }
    $results[$c.Name].Add($nps)
    Add-OspdLf $csv ("{0},{1},{2},{3},{4},{5},{6},{7:F0}" -f $r, $pos, $c.Name, $Threads, $Mode, $sumNodes, $sumMs, $nps)
    $pos++
  }
}
function Get-Median($xs) { $s = @($xs | Sort-Object); $n = $s.Count; if ($n -eq 0) { return 0 }; if ($n % 2) { return $s[[int](($n - 1) / 2)] } else { return ($s[$n / 2 - 1] + $s[$n / 2]) / 2 } }
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("nps_smoke $Tag | ADVISORY (shared PC, CPUs 12-15 = 2 physical cores) | threads $Threads | $go | rounds $Rounds | fens $FenCount | start-order alternating")
$base = $null
foreach ($c in $configs) {
  $m = Get-Median $results[$c.Name]; if ($null -eq $base) { $base = $m }
  $mn = ($results[$c.Name] | Measure-Object -Minimum).Minimum; $mx = ($results[$c.Name] | Measure-Object -Maximum).Maximum
  $lines.Add(("{0,-14} sha {1} opts [{2}] median nps {3:F0} min {4:F0} max {5:F0} spread {6:F1}% ratio-to-first {7:F4}" -f $c.Name, $c.Sha.Substring(0, 12), $c.Options, $m, $mn, $mx, (100.0 * ($mx - $mn) / [Math]::Max(1.0, $m)), ($m / [Math]::Max(1.0, $base))))
}
Write-OspdLf (Join-Path $OutDir "$Tag.summary.txt") $lines -Force
$lines
