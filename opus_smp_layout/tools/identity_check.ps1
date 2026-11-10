# identity_check.ps1 (opus2, PowerShell 5.1) - node-identity evidence for one exe + UCI option set, inside the job envelope.
# Own code on top of o2_uci_lib.ps1 (whose driver is the speed job's uci_lib.ps1). Modes (one per run):
#   pins : L1 bench d11/13/16/20/22 net on and net off (UseNNUE false) + L2 perft 5 startpos / kiwipete vs the lock pins
#   cold : L3 per FEN 'ucinewgame' + 'position fen' + 'go depth D' -> rows "i<TAB>depth<TAB>score<TAB>nodes<TAB>bestmove"
#          (fails closed on an 'invalid' FEN line; refuses a degenerate set: fewer than n/10 distinct rows)
#   warm : L3b one session with the table kept warm (no ucinewgame): 'bench 1' + 'go perft 1' first, then per FEN
#          'position fen' + 'go nodes N', and every 25 FENs one change from the cycle Hash 1, Hash 64, Clear Hash,
#          UseNNUE false, UseNNUE true, Hash 16 (the speed job's warm_identity cycle); 'bench 13' last. The transcript
#          after the handshake is normalised (nps/time fields removed) so two exes can be compared byte for byte.
# Output: <OutDir>\<Tag>.<mode>.tsv|txt plus <same>.sha256; the comparison is a plain byte compare of two such files.
# The process pins itself to CPUs 12-15 (or -Mask, a subset) at Idle before starting the engine (fail closed).
param(
  [Parameter(Mandatory=$true)][string]$Exe,
  [Parameter(Mandatory=$true)][string]$Tag,
  [Parameter(Mandatory=$true)][ValidateSet('pins', 'cold', 'warm')][string]$Mode,
  [Parameter(Mandatory=$true)][string]$OutDir,
  [string]$Options = '',              # 'Name=Value;Name2=Value2' applied after uci (OwnBook=false is always applied)
  [string]$Fens = 'D:\forge_jobs_20261107\opus2\out\data\fens_12k_v2.txt',
  [int]$First = 0, [int]$Count = 12000, [int]$Depth = 13,
  [int]$WarmNodes = 20000,
  [long]$Mask = 0xF000
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\o2_uci_lib.ps1"
Set-OspdPlacement $Mask 'Idle'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$null = Assert-OspdDisk 0.05
$opts = @('OwnBook=false') + @($Options -split ';' | Where-Object { $_ })
$base = Join-Path $OutDir ("{0}.{1}" -f $Tag, $Mode)
$log = "$base.uci.log"
$head = @("# identity_check $Mode tag=$Tag exe=$Exe sha256=$(Get-OspdSha256 $Exe) options=[$($opts -join ';')] start=$(Get-OspdNow) (PC clock)")
$eng = Start-OspdEngine $Exe $log
$uciLines = Initialize-OspdEngine $eng $opts
$rows = New-Object System.Collections.Generic.List[string]
$verdict = 'DONE'
try {
  switch ($Mode) {
    'pins' {
      $bad = 0
      foreach ($net in @('true', 'false')) {
        Send-OspdUci $eng "setoption name UseNNUE value $net"; Send-OspdUci $eng 'isready'; $null = Wait-OspdUci $eng '^readyok' 60
        $pins = if ($net -eq 'true') { $script:OspdPinsOn } else { $script:OspdPinsOff }
        foreach ($d in $script:OspdDepths) {
          $b = Invoke-OspdBench $eng $d
          $want = $pins["d$d"]; $ok = ($b.Nodes -eq $want); if (-not $ok) { $bad++ }
          $rows.Add(("bench net {0} d{1} nodes {2} pin {3} {4}" -f $net, $d, $b.Nodes, $want, $(if ($ok) { 'OK' } else { 'FAIL' })))
        }
      }
      Send-OspdUci $eng 'setoption name UseNNUE value true'
      foreach ($p in $script:OspdPerftPins.Keys) {
        $pos = if ($p -eq 'startpos') { 'startpos' } else { $script:OspdKiwi }
        $n = Invoke-OspdPerft $eng $pos 5; $want = $script:OspdPerftPins[$p]; $ok = ($n -eq $want); if (-not $ok) { $bad++ }
        $rows.Add(("perft5 {0} {1} pin {2} {3}" -f $p, $n, $want, $(if ($ok) { 'OK' } else { 'FAIL' })))
      }
      $verdict = if ($bad -eq 0) { 'PINS: ALL OK' } else { "PINS: $bad FAIL" }
      $rows.Add($verdict)
    }
    'cold' {
      $lines = @(Get-Content -LiteralPath $Fens | Select-Object -Skip $First -First $Count)
      $i = $First
      foreach ($l in $lines) {
        $r = Invoke-OspdSearch $eng (ConvertTo-OspdFen $l) ("depth $Depth") -NewGame
        $rows.Add(("{0}`t{1}`t{2}`t{3}`t{4}" -f $i, $r.Depth, $r.Score, $r.Nodes, $r.Best)); $i++
      }
      $distinct = @($rows | ForEach-Object { ($_ -split "`t", 2)[1] } | Sort-Object -Unique).Count
      if ($rows.Count -ge 100 -and $distinct -lt ($rows.Count / 10)) { throw "degenerate result set: $distinct distinct rows of $($rows.Count)" }
      $verdict = "COLD: $($rows.Count) rows, $distinct distinct"
    }
    'warm' {
      $cycle = @('setoption name Hash value 1', 'setoption name Hash value 64', 'setoption name Clear Hash',
                 'setoption name UseNNUE value false', 'setoption name UseNNUE value true', 'setoption name Hash value 16')
      $norm = { param($s) (($s -replace ' nps \d+', '') -replace ' time \d+', '') }
      $b1 = Invoke-OspdBench $eng 1; $rows.Add("bench 1 nodes $($b1.Nodes)")
      Send-OspdUci $eng 'position startpos'; Send-OspdUci $eng 'go perft 1'
      $r = Wait-OspdUci $eng '^nodes (\d+)' 120 -Collect; foreach ($x in $r.Lines) { $rows.Add((& $norm $x)) }
      $lines = @(Get-Content -LiteralPath $Fens | Select-Object -Skip $First -First $Count)
      $k = 0; $c = 0
      foreach ($l in $lines) {
        $fen = ConvertTo-OspdFen $l
        Send-OspdUci $eng ("position fen " + $fen)
        Send-OspdUci $eng ("go nodes $WarmNodes")
        $r = Wait-OspdUci $eng '^bestmove (\S+)' 3600 -Collect
        foreach ($x in $r.Lines) {
          if ($x.StartsWith('info string') -and $x -match 'invalid') { throw "engine rejected FEN $k : $x" }
          $rows.Add((& $norm $x))
        }
        $k++
        if (($k % 25) -eq 0) {
          $cmd = $cycle[$c % $cycle.Count]; $c++
          $rows.Add("> $cmd"); Send-OspdUci $eng $cmd; Send-OspdUci $eng 'isready'; $null = Wait-OspdUci $eng '^readyok' 120
        }
      }
      Send-OspdUci $eng 'setoption name UseNNUE value true'
      $b13 = Invoke-OspdBench $eng 13; $rows.Add("bench 13 nodes $($b13.Nodes)")
      if ($b13.Nodes -ne $script:OspdPinsOn['d13']) { throw "bench 13 after the warm run = $($b13.Nodes), pin $($script:OspdPinsOn['d13'])" }
      $verdict = "WARM: $k FENs, $c state changes, $($rows.Count) normalised lines"
    }
  }
} catch {
  $verdict = "ERROR: $($_.Exception.Message)"
}
$ok = Stop-OspdEngine $eng
$rows.Add("# engine exit ok=$ok")
$ext = if ($Mode -eq 'cold') { 'tsv' } else { 'txt' }
$outFile = "$base.$ext"
Write-OspdLf $outFile ($head + $rows) -Force
# The sha256 covers the result lines only (header has paths/time): compare files from different exes by this hash.
$body = @($rows | Where-Object { -not $_.StartsWith('# ') })
$bodyFile = "$base.body.$ext"
Write-OspdLf $bodyFile $body -Force
Write-OspdLf "$base.sha256" @("$(Get-OspdSha256 $bodyFile)  $([System.IO.Path]::GetFileName($bodyFile))") -Force
# The engine's exit state is not part of the hashed body (fable bug hunt NIT-6): print it and fail on it here.
Write-Output "$verdict | engine exit ok=$ok | body sha256 $(Get-OspdSha256 $bodyFile) | $outFile"
if ($verdict.StartsWith('ERROR') -or $verdict -match 'FAIL' -or -not $ok) { exit 1 } else { exit 0 }
