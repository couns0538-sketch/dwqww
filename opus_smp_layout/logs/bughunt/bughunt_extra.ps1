# bughunt_extra.ps1 (opus2 bug hunt, PS 5.1): adversarial UCI cases on the final gate exe, pinned (CPUs 12-15, Idle).
param([string]$Exe = 'D:\forge_jobs_20261107\opus2\out\exe\forge_smpgate_541e8b3d.exe', [string]$OutDir = 'D:\forge_jobs_20261107\opus2\out\bughunt')
$ErrorActionPreference = 'Stop'
. 'D:\forge_jobs_20261107\opus2\repo\opus_smp_layout\tools\o2_uci_lib.ps1'
Set-OspdPlacement 0xF000 'Idle'
$freeGB = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)
$out = New-Object System.Collections.Generic.List[string]
$out.Add("bughunt_extra exe sha256 $(Get-OspdSha256 $Exe); free RAM before $freeGB GB")
if ($freeGB -lt 12) { $out.Add("SKIP big-hash case: free RAM $freeGB GB < 12 GB"); $big = $false } else { $big = $true }
$e = Start-OspdEngine $Exe (Join-Path $OutDir 'bughunt_extra.uci.log')
$null = Initialize-OspdEngine $e @('OwnBook=false')
$fen = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
function Ready { Send-OspdUci $e 'isready'; $null = Wait-OspdUci $e '^readyok' 300 }
# 1 invalid option value must not change the mode: depth-10 nodes stay those of legacy mode on a cold table
Send-OspdUci $e 'setoption name TtLockless value maybe'
$r = Wait-OspdUci $e 'invalid value for option TtLockless' 30; $out.Add("invalid value -> '$($r.Match.Value)'"); Ready
$a = Invoke-OspdSearch $e $fen 'depth 10' -NewGame
Send-OspdUci $e 'setoption name TtLockless value true'; Ready
$b = Invoke-OspdSearch $e $fen 'depth 10' -NewGame
$out.Add(("cold depth 10: after invalid value nodes {0} best {1}; lockless nodes {2} best {3} -> {4}" -f $a.Nodes, $a.Best, $b.Nodes, $b.Best, $(if ($a.Nodes -eq $b.Nodes -and $a.Best -eq $b.Best) { 'identical (OK)' } else { 'DIFFERENT (FAIL)' })))
# 2 odd thread counts in lockless mode, short searches, legal best moves via go perft 1
foreach ($t in 2, 3) {
  Send-OspdUci $e "setoption name Threads value $t"; Ready
  $s = Invoke-OspdSearch $e $fen 'movetime 300' -NewGame
  Send-OspdUci $e ('position fen ' + $fen); Send-OspdUci $e 'go perft 1'; $p = Wait-OspdUci $e '^nodes (\d+)' 60 -Collect
  $legal = @($p.Lines | Where-Object { $_ -match ('^' + [regex]::Escape($s.Best) + ': ') }).Count -eq 1
  $out.Add(("Threads {0} lockless movetime 300: best {1} legal {2}" -f $t, $s.Best, $legal))
}
Send-OspdUci $e 'setoption name Threads value 1'; Ready
# 3 maximum hash with mode toggles (reallocates 2 GB per toggle; peak ~4 GB during the toggle)
if ($big) {
  Send-OspdUci $e 'setoption name Hash value 2048'; Ready
  foreach ($m in 'false', 'true', 'false', 'true') {
    Send-OspdUci $e "setoption name TtLockless value $m"; Ready
    $s = Invoke-OspdSearch $e $fen 'depth 9' -NewGame
    $e.Proc.Refresh()
    $out.Add(("Hash 2048 TtLockless={0}: depth 9 nodes {1} best {2}; working set {3:N0} MiB" -f $m, $s.Nodes, $s.Best, ($e.Proc.WorkingSet64 / 1MB)))
  }
  Send-OspdUci $e 'setoption name Hash value 16'; Ready
}
$e.Proc.Refresh(); $peak = $e.Proc.PeakWorkingSet64
$ok = Stop-OspdEngine $e
$out.Add(("peak working set {0:N0} MiB; exit ok={1} code={2}" -f ($peak / 1MB), $ok, $(if ($ok) { $e.Proc.ExitCode } else { 'n/a' })))
Write-OspdLf (Join-Path $OutDir 'bughunt_extra.txt') $out -Force
$out
