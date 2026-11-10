# special_modes.ps1 (opus2 bug hunt, PS 5.1): Threads 1 identity of special search modes (searchmoves, go mate) for
# P, gate TtLockless=false and gate TtLockless=true. Pinned to CPUs 12-15, Idle.
param([string]$OutDir = 'D:\forge_jobs_20261107\opus2\out\bughunt')
$ErrorActionPreference = 'Stop'
. 'D:\forge_jobs_20261107\opus2\repo\opus_smp_layout\tools\o2_uci_lib.ps1'
Set-OspdPlacement 0xF000 'Idle'
$P = 'D:\forge_jobs_20261107\opus2\out\exe\forge_P_4181a589.exe'; $G = 'D:\forge_jobs_20261107\opus2\out\exe\forge_smpgate_541e8b3d.exe'
$cases = @(
  @{ Fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'; Go = 'searchmoves e2e4 d2d4 g1f3 depth 11' },
  @{ Fen = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'; Go = 'searchmoves e2a6 d5e6 depth 10' },
  @{ Fen = 'r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4'; Go = 'mate 2' },
  @{ Fen = '6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1'; Go = 'mate 3' }
)
$rows = @{}
foreach ($cfg in @(@('P', $P, @()), @('Goff', $G, @()), @('Gon', $G, @('TtLockless=true')))) {
  $e = Start-OspdEngine $cfg[1] ''
  $null = Initialize-OspdEngine $e (@('OwnBook=false') + $cfg[2])
  $list = @()
  foreach ($c in $cases) { $r = Invoke-OspdSearch $e $c.Fen $c.Go -NewGame; $list += ("{0} | {1} | depth {2} score {3} nodes {4} best {5}" -f $c.Go, $c.Fen.Substring(0, 20), $r.Depth, $r.Score, $r.Nodes, $r.Best) }
  $null = Stop-OspdEngine $e
  $rows[$cfg[0]] = $list
}
$out = New-Object System.Collections.Generic.List[string]
$bad = 0
for ($i = 0; $i -lt $cases.Count; $i++) {
  $same = ($rows['P'][$i] -eq $rows['Goff'][$i]) -and ($rows['P'][$i] -eq $rows['Gon'][$i]); if (-not $same) { $bad++ }
  $out.Add(("{0} -> {1}" -f $rows['P'][$i], $(if ($same) { 'P = gate OFF = gate ON' } else { "DIFF: Goff [$($rows['Goff'][$i])] Gon [$($rows['Gon'][$i])]" })))
}
$out.Add($(if ($bad -eq 0) { 'SPECIAL MODES: IDENTICAL' } else { "SPECIAL MODES: $bad DIFFERENT" }))
Write-OspdLf (Join-Path $OutDir 'special_modes.txt') $out -Force
$out
