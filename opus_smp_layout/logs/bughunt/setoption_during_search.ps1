# setoption_during_search.ps1 (opus2 bug hunt, PS 5.1): setoption (TtLockless / Hash / Clear Hash) sent WHILE a search
# runs. UCI must stop and join the search (stop_search) before touching the table. Every bestmove must be legal, the
# engine must stay responsive (isready) and quit cleanly. Pinned to CPUs 12-15, Idle.
param([string]$Exe = 'D:\forge_jobs_20261107\opus2\out\exe\forge_smpgate_541e8b3d.exe', [string]$OutDir = 'D:\forge_jobs_20261107\opus2\out\bughunt')
$ErrorActionPreference = 'Stop'
. 'D:\forge_jobs_20261107\opus2\repo\opus_smp_layout\tools\o2_uci_lib.ps1'
Set-OspdPlacement 0xF000 'Idle'
$out = New-Object System.Collections.Generic.List[string]
$out.Add("setoption_during_search exe sha256 $(Get-OspdSha256 $Exe)")
$e = Start-OspdEngine $Exe (Join-Path $OutDir 'setoption_during_search.uci.log')
$null = Initialize-OspdEngine $e @('OwnBook=false')
$fens = @('r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8', 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1')
$bad = 0
function Legal([string]$fen, [string]$mv) {
  Send-OspdUci $e ('position fen ' + $fen); Send-OspdUci $e 'go perft 1'; $p = Wait-OspdUci $e '^nodes (\d+)' 60 -Collect
  return (@($p.Lines | Where-Object { $_ -match ('^' + [regex]::Escape($mv) + ': ') }).Count -eq 1)
}
$cases = @(
  @{ T = 1; Cmd = 'setoption name TtLockless value true' }, @{ T = 1; Cmd = 'setoption name Hash value 64' },
  @{ T = 4; Cmd = 'setoption name TtLockless value false' }, @{ T = 4; Cmd = 'setoption name Clear Hash' },
  @{ T = 4; Cmd = 'setoption name TtLockless value true' }, @{ T = 4; Cmd = 'setoption name Hash value 16' },
  @{ T = 8; Cmd = 'setoption name TtLockless value false' }, @{ T = 8; Cmd = 'ucinewgame' }
)
$i = 0
foreach ($c in $cases) {
  $fen = $fens[$i % 2]; $i++
  Send-OspdUci $e "setoption name Threads value $($c.T)"; Send-OspdUci $e 'isready'; $null = Wait-OspdUci $e '^readyok' 60
  Send-OspdUci $e ('position fen ' + $fen); Send-OspdUci $e 'go infinite'
  Start-Sleep -Milliseconds 150
  Send-OspdUci $e $c.Cmd                       # arrives while the search runs: UCI stops + joins it first
  $r = Wait-OspdUci $e '^bestmove (\S+)' 60 -Collect
  $mv = $r.Match.Groups[1].Value
  Send-OspdUci $e 'isready'; $null = Wait-OspdUci $e '^readyok' 60
  $ok = Legal $fen $mv
  # and a normal search right after, in whatever mode the table is now
  $s = Invoke-OspdSearch $e $fen 'depth 8'
  $ok2 = Legal $fen $s.Best
  if (-not ($ok -and $ok2)) { $bad++ }
  $out.Add(("Threads {0} go infinite + '{1}': bestmove {2} legal {3}; next go depth 8 best {4} legal {5}" -f $c.T, $c.Cmd, $mv, $ok, $s.Best, $ok2))
}
$okExit = Stop-OspdEngine $e
$out.Add(("exit ok={0} code={1}; {2}" -f $okExit, $(if ($okExit) { $e.Proc.ExitCode } else { 'n/a' }), $(if ($bad -eq 0 -and $okExit -and $e.Proc.ExitCode -eq 0) { 'SETOPTION-DURING-SEARCH: PASS' } else { "SETOPTION-DURING-SEARCH: FAIL ($bad)" })))
Write-OspdLf (Join-Path $OutDir 'setoption_during_search.txt') $out -Force
$out
