# abba_queue.ps1 - run abba.ps1 for a list of candidate exes against the lock, one after another (speed job, PS 5.1).
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File abba_queue.ps1 -List <list.tsv> -AaCsv <A/A runs.csv>
#          [-Depth 20] [-Rounds 10] [-OutRoot F:\ospd\abba] [-Results <results.tsv>]
# list.tsv: one 'name<TAB>exe path' per line ('#' comments). The list is re-read before every entry, so entries can be
# appended while the queue runs; an entry is done when F:\ospd\abba\<name>_d<D>\summary.txt exists. An exe whose sha256
# equals the lock's is not timed (identical file: ratio 1 by definition) and is recorded as IDENTICAL-EXE.
# results.tsv (append): time, name, sha256 prefix, depth, rounds, median, t-interval, sd, verdict, out dir.
param(
  [Parameter(Mandatory = $true)][string]$List,
  [Parameter(Mandatory = $true)][string]$AaCsv,
  [int]$Depth = 20,
  [int]$Rounds = 10,
  [string]$OutRoot = 'F:\ospd\abba',
  [string]$Results = 'F:\ospd\abba\results.tsv'
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\uci_lib.ps1"
if (-not (Test-Path $Results)) { Add-OspdLf $Results "time`tname`tsha8`tdepth`trounds`twall_median`twall_lo`twall_hi`twall_sd`tcpu_median`tcpu_lo`tcpu_hi`tcpu_sd`tverdict_wall`tverdict_cpu`tout" }
$lockSha = $script:OspdLockSha.ToLower()
while ($true) {
  $todo = $null
  foreach ($row in (Get-Content $List)) {
    if (-not $row.Trim() -or $row.StartsWith('#')) { continue }
    $f = $row -split "`t"; if ($f.Count -lt 2) { continue }
    $dir = Join-Path $OutRoot ("{0}_d{1}" -f $f[0], $Depth)
    if (-not (Test-Path (Join-Path $dir 'summary.txt')) -and -not (Test-Path (Join-Path $dir 'IDENTICAL.txt')) -and -not (Test-Path (Join-Path $dir 'ERROR.txt'))) { $todo = @{ Name = $f[0]; Exe = $f[1]; Dir = $dir }; break }
  }
  if ($null -eq $todo) { Write-Output "$(Get-OspdNow) queue empty"; break }
  $sha = Get-OspdSha256 $todo.Exe
  if ($sha -eq $lockSha) {
    New-Item -ItemType Directory -Force -Path $todo.Dir | Out-Null
    Write-OspdLf (Join-Path $todo.Dir 'IDENTICAL.txt') @("$($todo.Exe) sha256 $sha = live lock trial_w6: identical file, not timed")
    Add-OspdLf $Results ("{0}`t{1}`t{2}`t{3}`t0`t1`t1`t1`t0`t1`t1`t1`t0`tIDENTICAL-EXE`tIDENTICAL-EXE`t{4}" -f (Get-OspdNow), $todo.Name, $sha.Substring(0, 8), $Depth, $todo.Dir)
    Write-Output "$(Get-OspdNow) $($todo.Name): identical to the lock exe"
    continue
  }
  Write-Output "$(Get-OspdNow) $($todo.Name): ABBA d$Depth x $Rounds vs lock"
  $o = @(& "$PSScriptRoot\abba.ps1" -A $script:OspdLockExe -B $todo.Exe -Out $todo.Dir -Depth $Depth -Rounds $Rounds -AaCsv $AaCsv -LabelA 'live lock trial_w6' -LabelB $todo.Name)
  $rc = $LASTEXITCODE
  Set-OspdPlacement -Mask 0x3 -Priority 'Idle'   # abba pinned this process to the timing CPU (review LOW 7)
  $o | ForEach-Object { Write-Output "  $_" }
  if ($rc -ne 0) {
    New-Item -ItemType Directory -Force -Path $todo.Dir | Out-Null
    Write-OspdLf (Join-Path $todo.Dir 'ERROR.txt') (@("abba rc $rc") + $o)
    Add-OspdLf $Results ("{0}`t{1}`t{2}`t{3}`t{4}`t`t`t`t`t`t`t`t`tERROR rc {5}`tERROR`t{6}" -f (Get-OspdNow), $todo.Name, $sha.Substring(0, 8), $Depth, $Rounds, $rc, $todo.Dir)
    continue
  }
  $rx = 'B/A median ([0-9.]+) .*95% t-interval \[([0-9.]+), ([0-9.]+)\], sd/round ([0-9.]+)%'
  $mw = [regex]::Match((@($o | Where-Object { $_ -like 'wall*' }) -join ' '), $rx)
  $mc = [regex]::Match((@($o | Where-Object { $_ -like 'cpu*' }) -join ' '), $rx)
  $vm = [regex]::Match((@($o | Where-Object { $_ -like 'VERDICT*' }) -join ' '), 'VERDICT wall (\S+) / cpu (\S+)')
  Add-OspdLf $Results ("{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}`t{7}`t{8}`t{9}`t{10}`t{11}`t{12}`t{13}`t{14}`t{15}" -f (Get-OspdNow), $todo.Name, $sha.Substring(0, 8), $Depth, $Rounds, $mw.Groups[1].Value, $mw.Groups[2].Value, $mw.Groups[3].Value, $mw.Groups[4].Value, $mc.Groups[1].Value, $mc.Groups[2].Value, $mc.Groups[3].Value, $mc.Groups[4].Value, $vm.Groups[1].Value, $vm.Groups[2].Value, $todo.Dir)
}
exit 0
