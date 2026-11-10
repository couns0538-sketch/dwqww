# liveness_check.ps1 (opus2, PowerShell 5.1) - is the UCI option TtLockless LIVE in a gate exe, and node-identical?
# A node-identical option cannot be proven live by node counts alone (QA kit: "IDENTICAL to OFF (option not proven live)").
# The option's documented side effect is: a mode change reallocates the table empty (SPEC 3.6). So, Threads 1:
#   session A (option off): go depth D -> a1 (cold); go depth D -> a2 (warm); setoption Clear Hash; go depth D -> a3
#   session B (option on):  go depth D -> b1 (cold); go depth D -> b2 (warm); setoption TtLockless false; go depth D -> b3
# Worker histories survive both 'Clear Hash' and the toggle (only ucinewgame clears them), so a3 is the reference for b3.
# PASS needs: b1 = a1 and b2 = a2 (lockless node-identical cold and warm); a2 != a1 (the warm search really reuses the
# table); a3 != a2 (emptying the table changes the next search: the comparison is sensitive); b3 = a3 (the toggle emptied
# the table exactly as Clear Hash does: the option reached the TT). Nodes, best move and score are compared.
param(
  [Parameter(Mandatory=$true)][string]$Exe,
  [Parameter(Mandatory=$true)][string]$OutDir,
  [int]$Depth = 12,
  [string]$Fen = 'r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8',
  [long]$Mask = 0xF000
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\o2_uci_lib.ps1"
Set-OspdPlacement $Mask 'Idle'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
function Search-Three($Opts, [string]$EmptyCmd, [string]$LogTag) {
  $e = Start-OspdEngine $Exe (Join-Path $OutDir ("liveness_{0}.uci.log" -f $LogTag))
  $null = Initialize-OspdEngine $e (@('OwnBook=false', 'Hash=16') + $Opts)
  $r = @()
  $r += Invoke-OspdSearch $e $Fen "depth $Depth" -NewGame
  $r += Invoke-OspdSearch $e $Fen "depth $Depth"
  Send-OspdUci $e $EmptyCmd; Send-OspdUci $e 'isready'; $null = Wait-OspdUci $e '^readyok' 60
  $r += Invoke-OspdSearch $e $Fen "depth $Depth"
  $null = Stop-OspdEngine $e
  return ,$r
}
$a = Search-Three @() 'setoption name Clear Hash' 'A_legacy_clearhash'
$b = Search-Three @('TtLockless=true') 'setoption name TtLockless value false' 'B_lockless_toggle'
function Row($x) { "nodes {0} best {1} score {2} depth {3}" -f $x.Nodes, $x.Best, $x.Score, $x.Depth }
function Same($x, $y) { ($x.Nodes -eq $y.Nodes) -and ($x.Best -eq $y.Best) -and ($x.Score -eq $y.Score) }
$checks = @(
  @('lockless cold = legacy cold (b1 = a1)', (Same $b[0] $a[0])),
  @('lockless warm = legacy warm (b2 = a2)', (Same $b[1] $a[1])),
  @('warm reuses the table (a2 != a1 nodes)', ($a[1].Nodes -ne $a[0].Nodes)),
  @('emptying the table is visible (a3 != a2 nodes)', ($a[2].Nodes -ne $a[1].Nodes)),
  @('toggle emptied the table like Clear Hash (b3 = a3)', (Same $b[2] $a[2]))
)
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("liveness_check exe=$Exe sha256=$(Get-OspdSha256 $Exe) depth=$Depth fen=$Fen")
$lines.Add("a1 legacy cold             " + (Row $a[0])); $lines.Add("a2 legacy warm             " + (Row $a[1])); $lines.Add("a3 legacy after Clear Hash " + (Row $a[2]))
$lines.Add("b1 lockless cold           " + (Row $b[0])); $lines.Add("b2 lockless warm           " + (Row $b[1])); $lines.Add("b3 after TtLockless->false " + (Row $b[2]))
$bad = 0
foreach ($c in $checks) { $lines.Add(("{0,-45} {1}" -f $c[0], $(if ($c[1]) { 'OK' } else { $bad++; 'FAIL' }))) }
$lines.Add($(if ($bad -eq 0) { 'LIVENESS: PASS (TtLockless is live and node-identical cold and warm)' } else { "LIVENESS: FAIL ($bad)" }))
Write-OspdLf (Join-Path $OutDir 'liveness.txt') $lines -Force
$lines
if ($bad -eq 0) { exit 0 } else { exit 1 }
