# rc_measure.ps1 (opus2, PS 5.1) - D3 gate measurement on the instrumented scratch exe (rc.exe; never shipped).
param(
  [string]$Exe = 'D:\forge_jobs_20261107\opus2\out\scratch\rc\rc.exe',
  [string]$Fens = 'D:\forge_jobs_20261107\opus2\out\data\fens_12k_v2.txt',
  [string]$OutDir = 'D:\forge_jobs_20261107\opus2\out\cache_gate',
  [int]$NFen = 300, [int]$NFenT4 = 20
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\o2_uci_lib.ps1"
Set-OspdPlacement 0xF000 'Idle'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$log = Join-Path $OutDir ("rc_uci_{0}.log" -f (New-OspdRunId))
$sum = Join-Path $OutDir 'rc_summary.txt'
function Get-Rc($Eng) {
  Send-OspdUci $Eng 'rcdump'
  $m = (Wait-OspdUci $Eng '^info string RC refresh (\d+) update (\d+) eval (\d+) tree_refresh (\d+) root_refresh (\d+) back((?: \d+){10})$' 60).Match
  return [pscustomobject]@{ Refresh = [long]$m.Groups[1].Value; Update = [long]$m.Groups[2].Value; Eval = [long]$m.Groups[3].Value
    Tree = [long]$m.Groups[4].Value; Root = [long]$m.Groups[5].Value; Back = @($m.Groups[6].Value.Trim() -split ' ' | ForEach-Object { [long]$_ }) }
}
function Format-Delta([string]$Name, $A, $B, [long]$Searches) {
  $back = @(); for ($i = 0; $i -lt 10; $i++) { $back += ($B.Back[$i] - $A.Back[$i]) }
  "{0}: searches {1} | refresh {2} (root {3}, in-tree {4}) | lazy update calls {5} | evals {6} | walk-back histogram back=0..8,9+ : {7}" -f $Name, $Searches,
    ($B.Refresh - $A.Refresh), ($B.Root - $A.Root), ($B.Tree - $A.Tree), ($B.Update - $A.Update), ($B.Eval - $A.Eval), ($back -join ' ')
}
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("rc_measure exe $Exe sha256 $(Get-OspdSha256 $Exe); fens $Fens md5 $(Get-OspdMd5 $Fens); start $(Get-OspdNow) (PC clock)")
$eng = Start-OspdEngine $Exe $log
$null = Initialize-OspdEngine $eng @('OwnBook=false')
$r0 = Get-Rc $eng
$b = Invoke-OspdBench $eng 16
$r1 = Get-Rc $eng
$lines.Add((Format-Delta ("bench 16 (nodes {0})" -f $b.Nodes) $r0 $r1 -1))
$fenList = @(Get-Content -LiteralPath $Fens | Select-Object -First $NFen)
foreach ($f in $fenList) { $null = Invoke-OspdSearch $eng (ConvertTo-OspdFen $f) 'depth 13' -NewGame }
$r2 = Get-Rc $eng
$lines.Add((Format-Delta "go depth 13, $NFen FENs, Threads 1, ucinewgame each" $r1 $r2 $NFen))
Send-OspdUci $eng 'setoption name Threads value 4'; Send-OspdUci $eng 'isready'; $null = Wait-OspdUci $eng '^readyok' 60
foreach ($f in ($fenList | Select-Object -First $NFenT4)) { $null = Invoke-OspdSearch $eng (ConvertTo-OspdFen $f) 'movetime 500' -NewGame }
$r3 = Get-Rc $eng
$lines.Add((Format-Delta "go movetime 500, $NFenT4 FENs, Threads 4" $r2 $r3 $NFenT4))
$ok = Stop-OspdEngine $eng
$lines.Add("engine exit ok=$ok; end $(Get-OspdNow) (PC clock)")
Write-OspdLf $sum $lines -Force
$lines
