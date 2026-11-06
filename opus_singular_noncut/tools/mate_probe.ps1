# mate_probe.ps1 - the crew's mate probe (opus_r13/tools/data/mate_probe.epd: 20 KRK / KQK + 2 mate-in-1) on the gate exe,
# SingularNonCut 0 vs 1 (own code, 2026-11-06, PowerShell 5.1; run from Git Bash).
# usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File mate_probe.ps1 -Epd <file> -Out <new dir> [-Nodes 3000000]
# Per FEN: ucinewgame, OwnBook false, Hash 16, go nodes N; records depth / score / nodes / bestmove of the last info line.
# Placement: CPUs 0-1 Idle (Set-OspdPlacement, fail closed). Report = counts (mate found OFF / ON, same result), no verdict.
param(
  [Parameter(Mandatory = $true)][string]$Epd,
  [Parameter(Mandatory = $true)][string]$Out,
  [long]$Nodes = 3000000,
  [string]$Exe = 'D:\opus_singular_noncut\pack\forge_singular_noncut_gate_5f6be7c5.exe'
)
$ErrorActionPreference = 'Stop'
. 'F:\ospd\wt\opus_speed\tools\uci_lib.ps1'
Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
if (Test-Path $Out) { throw "$Out exists" }
New-Item -ItemType Directory -Path $Out | Out-Null
$fens = @(Get-Content $Epd | Where-Object { $_.Trim() } | ForEach-Object { ConvertTo-OspdFen (($_ -split ';')[0].Trim()) })
$rows = @("i`tside`tdepth`tscore`tnodes`tbestmove`tfen")
$res = @{}
foreach ($on in 0, 1) {
  $e = Start-OspdEngine $Exe (Join-Path $Out "uci_on$on.log")
  $null = Initialize-OspdEngine $e @("SingularNonCut=$on", 'OwnBook=false', 'Hash=16')
  for ($i = 0; $i -lt $fens.Count; $i++) {
    $r = Invoke-OspdSearch $e $fens[$i] "nodes $Nodes" -NewGame
    $res["$on/$i"] = $r
    $rows += ("{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}" -f $i, $on, $r.Depth, $r.Score, $r.Nodes, $r.Best, $fens[$i])
  }
  $null = Stop-OspdEngine $e
}
Write-OspdLf (Join-Path $Out 'mate_probe.tsv') $rows
$m0 = 0; $m1 = 0; $same = 0; $diff = @()
for ($i = 0; $i -lt $fens.Count; $i++) {
  $a = $res["0/$i"]; $b = $res["1/$i"]
  if ($a.Score -like 'mate *') { $m0++ }
  if ($b.Score -like 'mate *') { $m1++ }
  if ($a.Score -eq $b.Score -and $a.Best -eq $b.Best) { $same++ } else { $diff += ("  fen {0}: OFF {1} {2} / ON {3} {4}" -f $i, $a.Score, $a.Best, $b.Score, $b.Best) }
}
$sum = @("mate_probe $(Get-OspdNow): exe $Exe sha256 $(Get-OspdSha256 $Exe); epd $Epd md5 $(Get-OspdMd5 $Epd); go nodes $Nodes",
  "positions $($fens.Count): mate score found OFF $m0, ON $m1; same score + bestmove $same") + $diff
Write-OspdLf (Join-Path $Out 'SUMMARY.txt') $sum
$sum | ForEach-Object { [Console]::Out.WriteLine($_) }
