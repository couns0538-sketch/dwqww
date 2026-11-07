# mate_probe.ps1 - mate probe of one gate exe, option OFF (its defaults) vs ON (own code, 2026-11-06, PowerShell 5.1;
# run from Git Bash). Generalised from opus_singular_noncut/tools/mate_probe.ps1: the exe, the ON options, the go limit,
# the CPU mask and a FEN subset are parameters.
# usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File mate_probe.ps1 -Exe <gate exe> -OnOptions 'A=1,B=2'
#          -Epd <file> -Out <new dir> [-Go 'nodes 3000000'] [-Mask 0x3] [-Index '3,7']
# Per FEN: ucinewgame, OwnBook false, Hash 16, go <Go>; records depth / score / nodes / bestmove of the last info line.
# Flags per FEN: LOST = OFF has a mate score, ON has none; LONGER = both mate and |N_on| > |N_off| (N = the UCI mate
# number); GAINED / SHORTER are listed too. Report = counts + flags, no verdict.
param(
  [Parameter(Mandatory = $true)][string]$Exe,
  [Parameter(Mandatory = $true)][string[]]$OnOptions,
  [Parameter(Mandatory = $true)][string]$Epd,
  [Parameter(Mandatory = $true)][string]$Out,
  [string]$Go = 'nodes 3000000',
  [long]$Mask = 0x3,
  [string[]]$Index = @()
)
$ErrorActionPreference = 'Stop'
$lib = Join-Path $PSScriptRoot 'uci_lib.ps1'; if (-not (Test-Path $lib)) { $lib = 'F:\ospd\wt\opus_speed\tools\uci_lib.ps1' }
. $lib
# -File passes a list as ONE comma-joined string: split on commas
$OnOptions = @($OnOptions | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$Index = @($Index | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
Set-OspdPlacement -Mask $Mask -Priority 'Idle'
if (Test-Path $Out) { throw "$Out exists" }
New-Item -ItemType Directory -Path $Out | Out-Null
$fens = @(Get-Content $Epd | Where-Object { $_.Trim() -and -not $_.StartsWith('#') } | ForEach-Object { ConvertTo-OspdFen (($_ -split ';')[0].Trim()) })
$idx = @(0..($fens.Count - 1)); if ($Index.Count -gt 0) { $idx = @($Index | ForEach-Object { [int]$_ }) }
$rows = @("i`tside`tdepth`tscore`tnodes`tbestmove`tfen")
$res = @{}
foreach ($on in 0, 1) {
  $e = Start-OspdEngine $Exe (Join-Path $Out "uci_on$on.log")
  $opts = @('OwnBook=false', 'Hash=16'); if ($on -eq 1) { $opts += $OnOptions }
  $null = Initialize-OspdEngine $e $opts
  foreach ($i in $idx) {
    $r = Invoke-OspdSearch $e $fens[$i] $Go -NewGame
    $res["$on/$i"] = $r
    $rows += ("{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}" -f $i, $on, $r.Depth, $r.Score, $r.Nodes, $r.Best, $fens[$i])
  }
  $null = Stop-OspdEngine $e
}
Write-OspdLf (Join-Path $Out 'mate_probe.tsv') $rows
function Get-MateN([string]$s) { if ($s -match '^mate (-?\d+)$') { return [int]$matches[1] } else { return $null } }
$m0 = 0; $m1 = 0; $same = 0; $lost = 0; $longer = 0; $lines = @()
foreach ($i in $idx) {
  $a = $res["0/$i"]; $b = $res["1/$i"]; $na = Get-MateN $a.Score; $nb = Get-MateN $b.Score
  if ($null -ne $na) { $m0++ }
  if ($null -ne $nb) { $m1++ }
  if ($a.Score -eq $b.Score -and $a.Best -eq $b.Best) { $same++ }
  $flag = ''
  if ($null -ne $na -and $null -eq $nb) { $flag = 'LOST'; $lost++ }
  elseif ($null -eq $na -and $null -ne $nb) { $flag = 'GAINED' }
  elseif ($null -ne $na -and $null -ne $nb) {
    if ([Math]::Abs($nb) -gt [Math]::Abs($na)) { $flag = 'LONGER'; $longer++ } elseif ([Math]::Abs($nb) -lt [Math]::Abs($na)) { $flag = 'SHORTER' }
    if ([Math]::Sign($na) -ne [Math]::Sign($nb)) { $flag = 'SIGN'; $lost++ }
  }
  $lines += ("  fen {0,2}: OFF {1,-9} {2,-6} d{3} / ON {4,-9} {5,-6} d{6}  {7}" -f $i, $a.Score, $a.Best, $a.Depth, $b.Score, $b.Best, $b.Depth, $flag)
}
$sum = @("mate_probe $(Get-OspdNow): exe $Exe sha256 $(Get-OspdSha256 $Exe); ON options $($OnOptions -join ', '); epd $Epd md5 $(Get-OspdMd5 $Epd); go $Go; mask 0x$('{0:X}' -f $Mask)",
  "positions $($idx.Count): mate score found OFF $m0, ON $m1; same score + bestmove $same; LOST (or sign flip) by ON $lost; LONGER by ON $longer") + $lines
Write-OspdLf (Join-Path $Out 'SUMMARY.txt') $sum
$sum | ForEach-Object { [Console]::Out.WriteLine($_) }
