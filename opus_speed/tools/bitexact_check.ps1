# bitexact_check.ps1 - bit-exact proof of the speed job (PowerShell 5.1). Prints PASS / FAIL per line, stops at the
# first FAIL (so a node-changing candidate never reaches the ABBA).
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File bitexact_check.ps1 -Cand <exe> -Out <new dir>
#          [-Ref <exe, default lock FD3A5190>] [-Quick] [-FenCount N] [-Fens <file>] [-FenDepth 13]
#          [-SanSrc <source dir> [-Define 'N=V',..] [-SanNdebug]] [-SkipSan] [-NoStop]
# Levels (Threads 1, depth / node limits only, never time):
#   L1 bench d11/13/16/20/22 with the net (defaults) and with UseNNUE=false: cand = ref (and ref = lock pins if ref is
#      the lock);
#   L2 perft 5 startpos + kiwipete: cand = ref = pins;
#   L3 per FEN (12k set, md5 078b6c2e; -Quick = the first 2,000): ucinewgame, position, go depth 13 with OwnBook=false;
#      depth, score, nodes of the last 'info depth' line and the bestmove must match; 2 engines on CPUs 0 and 1 with a
#      fixed chunking (same for ref and cand); ref results cached in F:\ospd\ref\<sha8 of ref>\ by sha256 + set + depth;
#   L4 clang (MSVC target) ASan + UBSan build of -SanSrc (+ -Define), bench 16 with the net: nodes = pin 3024920 and
#      no sanitizer report (falls back to separate ASan and UBSan-trap builds if the combined link fails).
# Exit 0 = BIT-EXACT (all levels run passed), 3 = NOT BIT-EXACT, 1 = error. Placement: CPUs 0-1 (0x3), Idle.
param(
  [Parameter(Mandatory = $true)][string]$Cand,
  [Parameter(Mandatory = $true)][string]$Out,
  [string]$Ref = '',
  [switch]$Quick,
  [int]$FenCount = 0,
  [string]$Fens = 'F:\ospd\wt\opus_speed\data\fens_12k.txt',
  [int]$FenDepth = 13,
  [string]$SanSrc = '',
  [string[]]$Define = @(),
  [switch]$SanNdebug,
  [switch]$SkipSan,
  [switch]$NoStop
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\uci_lib.ps1"
if (-not $Ref) { $Ref = $script:OspdLockExe }
$script:Fail = 0
$script:LogFile = ''
function Say([string]$Msg) { Write-Output $Msg; if ($script:LogFile) { Add-OspdLf $script:LogFile $Msg } }
function Verdict-Line([string]$Level, [string]$What, $RefVal, $CandVal, $Pin = $null) {
  $ok = ("$RefVal" -eq "$CandVal")
  if ($null -ne $Pin) { $ok = $ok -and ("$CandVal" -eq "$Pin") }
  $pinTxt = ''; if ($null -ne $Pin) { $pinTxt = " pin $Pin" }
  $state = 'PASS'; if (-not $ok) { $state = 'FAIL'; $script:Fail++ }
  # no return value: Say writes to the output stream, and a caller's '$null =' would swallow it
  Say ("{0} {1,-28} ref {2,-12} cand {3,-12}{4}  {5}" -f $Level, $What, $RefVal, $CandVal, $pinTxt, $state)
}
function Stop-IfFailed([string]$Level) {
  if ($script:Fail -gt 0 -and -not $NoStop) { Say "VERDICT NOT BIT-EXACT (first failure at $Level; later levels not run)"; exit 3 }
}

function Get-L1L2([string]$Exe, [string]$CacheDir) {
  # bench signature (net on + off) and perft; cached as JSON for any exe (keyed by sha256).
  $sha = Get-OspdSha256 $Exe
  $cache = Join-Path $CacheDir ("sig_{0}.json" -f $sha.Substring(0, 16))
  if (Test-Path $cache) { return (Get-Content $cache -Raw | ConvertFrom-Json) }
  $res = [ordered]@{ sha256 = $sha; exe = $Exe; on = [ordered]@{}; off = [ordered]@{}; perft = [ordered]@{} }
  $log = Join-Path $CacheDir ("sig_{0}.uci.log" -f $sha.Substring(0, 16))
  $e = Start-OspdEngine $Exe $log
  $null = Initialize-OspdEngine $e @()
  foreach ($d in $script:OspdDepths) { $res.on["d$d"] = (Invoke-OspdBench $e $d).Nodes }
  $res.perft['startpos'] = Invoke-OspdPerft $e 'startpos' 5
  $res.perft['kiwipete'] = Invoke-OspdPerft $e $script:OspdKiwi 5
  $null = Stop-OspdEngine $e
  $e = Start-OspdEngine $Exe $log
  $null = Initialize-OspdEngine $e @('UseNNUE=false')
  foreach ($d in $script:OspdDepths) { $res.off["d$d"] = (Invoke-OspdBench $e $d).Nodes }
  $null = Stop-OspdEngine $e
  ($res | ConvertTo-Json -Depth 4) | Set-Content -Encoding ASCII $cache
  return (Get-Content $cache -Raw | ConvertFrom-Json)
}

function Invoke-FenSet([string]$Exe, [string[]]$FenList, [int]$Depth, [string]$OutTsv, [string]$Log) {
  # Two engines (CPU 0 and CPU 1), chunk 0 = first half, chunk 1 = second half, event-driven reads.
  $n = $FenList.Count; $half = [int][Math]::Ceiling($n / 2)
  $chunks = @(@{ From = 0; To = [Math]::Min($half, $n) }, @{ From = $half; To = $n })
  $engs = @()
  for ($c = 0; $c -lt 2; $c++) {
    if ($chunks[$c].From -ge $chunks[$c].To) { continue }
    $e = Start-OspdEngine $Exe ("{0}.c{1}" -f $Log, $c) ([long](1 -shl $c))
    $null = Initialize-OspdEngine $e @('OwnBook=false')
    $engs += [pscustomobject]@{ Eng = $e; Next = $chunks[$c].From; To = $chunks[$c].To; State = 'idle'; Cur = -1; Info = $null }
  }
  $rows = New-Object 'string[]' $n
  $t0 = Get-Date
  while ($true) {
    foreach ($s in $engs) {
      if ($s.State -eq 'idle' -and $s.Next -lt $s.To) {
        $s.Cur = $s.Next; $s.Next++; $s.Info = $null
        $s.Eng.In.WriteLine('ucinewgame'); $s.Eng.In.WriteLine('isready'); $s.State = 'ready'
      }
    }
    $active = @($engs | Where-Object { $_.State -ne 'idle' })
    if ($active.Count -eq 0) { break }
    foreach ($s in $active) { if ($null -eq $s.Eng.Pending) { $s.Eng.Pending = $s.Eng.Out.ReadLineAsync() } }
    $tasks = [System.Threading.Tasks.Task[]]@($active | ForEach-Object { $_.Eng.Pending })
    $k = [System.Threading.Tasks.Task]::WaitAny($tasks, 1800000)
    if ($k -lt 0) { throw "FEN search timeout (30 min without output)" }
    $s = $active[$k]; $line = $s.Eng.Pending.Result; $s.Eng.Pending = $null
    if ($null -eq $line) { throw "engine exited during FEN $($s.Cur)" }
    if ($s.State -eq 'ready') {
      if ($line -eq 'readyok') { $s.Eng.In.WriteLine('position fen ' + $FenList[$s.Cur]); $s.Eng.In.WriteLine("go depth $Depth"); $s.State = 'search' }
    } elseif ($s.State -eq 'search') {
      if ($line.StartsWith('info depth ')) { $s.Info = $line }
      elseif ($line.StartsWith('bestmove ')) {
        $best = ($line -split ' ')[1]; $dd = ''; $sc = ''; $nn = ''
        if ($s.Info) {
          $mm = [regex]::Match($s.Info, '^info depth (\d+) .*? score (cp -?\d+|mate -?\d+)(?: (?:lowerbound|upperbound))? nodes (\d+)')
          if ($mm.Success) { $dd = $mm.Groups[1].Value; $sc = $mm.Groups[2].Value; $nn = $mm.Groups[3].Value }
        }
        $rows[$s.Cur] = "{0}`t{1}`t{2}`t{3}`t{4}" -f $s.Cur, $dd, $sc, $nn, $best
        $s.State = 'idle'
      }
    }
  }
  foreach ($s in $engs) { $null = Stop-OspdEngine $s.Eng }
  Write-OspdLf $OutTsv $rows
  return ((Get-Date) - $t0).TotalSeconds
}

function Get-VcEnv {
  $vcv = Get-ChildItem 'C:\Program Files (x86)\Microsoft Visual Studio\*\BuildTools\VC\Auxiliary\Build\vcvars64.bat', 'C:\Program Files\Microsoft Visual Studio\*\*\VC\Auxiliary\Build\vcvars64.bat' -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $vcv) { throw 'vcvars64.bat not found' }
  $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  try { $lines = & cmd.exe /d /c "call `"$($vcv.FullName)`" >nul 2>&1 && set" } finally { $ErrorActionPreference = $eap }
  foreach ($l in $lines) { $i = $l.IndexOf('='); if ($i -gt 0) { Set-Item -Path ("env:" + $l.Substring(0, $i)) -Value $l.Substring($i + 1) } }
  return $vcv.FullName
}

function Invoke-SanBuild([string]$Src, [string]$OutExe, [string[]]$Sanitize, [string]$BuildLog) {
  $clang = 'C:\Program Files\LLVM\bin\clang++.exe'
  $units = @(Get-ChildItem (Join-Path $Src 'src') -Filter *.cpp | Sort-Object Name | ForEach-Object { 'src/' + $_.Name })
  $args1 = @('-std=c++20', '-O1', '-g', '-gcodeview', '-fno-omit-frame-pointer', '-march=znver4', '-ffp-contract=off', '-DFORGE_NNUE_HIDDEN=256',
    '-DFORGE_EXPOSE_TUNABLES=1', '-Iinclude') + $Sanitize
  if ($SanNdebug) { $args1 += '-DNDEBUG' }
  foreach ($d in $Define) { $args1 += ('-D' + $d) }
  $args1 += $units; $args1 += @('-o', $OutExe)
  Add-OspdLf $BuildLog ("-- $(Get-OspdNow) clang++ " + ($args1 -join ' '))
  Push-Location $Src
  $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  try { $o = @(& $clang @args1 2>&1 | ForEach-Object { "$_" }); $rc = $LASTEXITCODE } finally { Pop-Location; $ErrorActionPreference = $eap }
  if ($o.Count) { foreach ($l in $o) { Add-OspdLf $BuildLog $l } }
  Add-OspdLf $BuildLog "-- exit $rc"
  return $rc
}

function Invoke-SanBench([string]$Exe, [string]$Dir, [string]$Tag) {
  $in = Join-Path $Dir "$Tag.in.txt"; $outF = Join-Path $Dir "$Tag.out.txt"; $errF = Join-Path $Dir "$Tag.err.txt"
  Write-OspdLf $in @('uci', 'isready', 'bench 16', 'isready', 'quit')
  $rtDir = (Get-ChildItem 'C:\Program Files\LLVM\lib\clang\*\lib\windows' -Directory | Select-Object -First 1).FullName
  $env:PATH = $rtDir + ';' + $env:PATH
  $env:ASAN_OPTIONS = 'halt_on_error=1:detect_leaks=0'
  $env:UBSAN_OPTIONS = 'halt_on_error=1:print_stacktrace=1'
  $p = Start-Process -FilePath $Exe -RedirectStandardInput $in -RedirectStandardOutput $outF -RedirectStandardError $errF -NoNewWindow -PassThru -WorkingDirectory $Dir
  $null = $p.Handle
  if (-not $p.WaitForExit(1800000)) { throw "sanitizer bench did not finish in 30 min ($Exe)" }
  $p.WaitForExit()
  $nodes = ''
  $m = Select-String -Path $outF -Pattern 'bench depth 16 nodes (\d+)' | Select-Object -First 1
  if ($m) { $nodes = $m.Matches[0].Groups[1].Value }
  $rep = @(Select-String -Path $errF, $outF -Pattern 'AddressSanitizer|runtime error|UndefinedBehaviorSanitizer|SUMMARY:' -ErrorAction SilentlyContinue)
  return [pscustomobject]@{ Exit = $p.ExitCode; Nodes = $nodes; Reports = $rep.Count; ErrFile = $errF }
}

try {
  Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
  if (Test-Path $Out) { throw "$Out exists; use a new folder" }
  foreach ($x in $Cand, $Ref, $Fens) { if (-not (Test-Path -LiteralPath $x)) { throw "missing $x" } }
  $diskMsg = Assert-OspdDisk -PlannedGB 0.3
  New-Item -ItemType Directory -Path $Out | Out-Null
  $script:LogFile = Join-Path $Out 'bitexact.log'
  $refSha = Get-OspdSha256 $Ref; $candSha = Get-OspdSha256 $Cand
  $cacheDir = Join-Path 'F:\ospd\ref' $refSha.Substring(0, 8); New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
  $candCache = Join-Path $Out 'cand'; New-Item -ItemType Directory -Path $candCache | Out-Null
  $refIsLock = ($refSha -eq $script:OspdLockSha.ToLower())
  Say "bitexact_check $(Get-OspdNow): ref $Ref (sha256 $refSha$(if ($refIsLock) { ', = lock FD3A5190' }))"
  Say "                cand $Cand (sha256 $candSha, md5 $(Get-OspdMd5 $Cand)); $diskMsg"

  # L1 + L2
  $r = Get-L1L2 $Ref $cacheDir; $c = Get-L1L2 $Cand $candCache
  foreach ($d in $script:OspdDepths) { $pin = $null; if ($refIsLock) { $pin = $script:OspdPinsOn["d$d"] }; Verdict-Line 'L1' "bench d$d net on" $r.on."d$d" $c.on."d$d" $pin }
  foreach ($d in $script:OspdDepths) { $pin = $null; if ($refIsLock) { $pin = $script:OspdPinsOff["d$d"] }; Verdict-Line 'L1' "bench d$d net off" $r.off."d$d" $c.off."d$d" $pin }
  Stop-IfFailed 'L1'
  foreach ($k in $script:OspdPerftPins.Keys) { Verdict-Line 'L2' "perft 5 $k" $r.perft.$k $c.perft.$k $script:OspdPerftPins[$k] }
  Stop-IfFailed 'L2'

  # L3
  $allFens = @(Get-Content $Fens | Where-Object { $_.Trim() })
  $n = $allFens.Count
  if ($Quick) { $n = [Math]::Min(2000, $n) }
  if ($FenCount -gt 0) { $n = [Math]::Min($FenCount, $allFens.Count) }
  $fenList = [string[]]$allFens[0..($n - 1)]
  $fmd5 = Get-OspdMd5 $Fens
  $refTsv = Join-Path $cacheDir ("fens_{0}_n{1}_d{2}_ob0.tsv" -f $fmd5.Substring(0, 8), $n, $FenDepth)
  if (-not (Test-Path $refTsv)) {
    $part = $refTsv + '.part'
    $sec = Invoke-FenSet $Ref $fenList $FenDepth $part (Join-Path $cacheDir 'fens.uci.log')
    Move-Item -LiteralPath $part -Destination $refTsv
    Say ("L3 ref FEN set computed in {0:N0} s -> {1}" -f $sec, $refTsv)
  } else { Say "L3 ref FEN set from cache $refTsv" }
  $candTsv = Join-Path $Out ("fens_n{0}_d{1}.tsv" -f $n, $FenDepth)
  $sec = Invoke-FenSet $Cand $fenList $FenDepth $candTsv (Join-Path $Out 'fens.uci.log')
  $ra = Get-Content $refTsv; $ca = Get-Content $candTsv
  $same = 0; $diffs = @()
  for ($i = 0; $i -lt $n; $i++) { if ($ra[$i] -eq $ca[$i] -and $ra[$i] -match "`t\d+`t") { $same++ } else { if ($diffs.Count -lt 10) { $diffs += "  FEN $i ref [$($ra[$i])] cand [$($ca[$i])]" } } }
  $state = 'PASS'; if ($same -ne $n) { $state = 'FAIL'; $script:Fail++ }
  Say ("L3 FENs {0} (md5 {1}) go depth {2}: {3} / {4} identical (depth, score, nodes, bestmove), cand {5:N0} s  {6}" -f (Split-Path $Fens -Leaf), $fmd5.Substring(0, 8), $FenDepth, $same, $n, $sec, $state)
  foreach ($d in $diffs) { Say $d }
  Stop-IfFailed 'L3'

  # L4
  if ($SkipSan -or -not $SanSrc) {
    Say "L4 sanitizer build: NOT RUN ($(if ($SkipSan) { '-SkipSan' } else { 'no -SanSrc' }))"
    $l4 = 'not run'
  } else {
    $vc = Get-VcEnv
    $sanDir = Join-Path $Out 'san'; New-Item -ItemType Directory -Path $sanDir | Out-Null
    $blog = Join-Path $sanDir 'build.log'
    Add-OspdLf $blog "vcvars: $vc"
    $exeAU = Join-Path $sanDir 'forge_asan_ubsan.exe'
    $rc = Invoke-SanBuild $SanSrc $exeAU @('-fsanitize=address,undefined', '-fno-sanitize-recover=undefined', '-fms-runtime-lib=dll') $blog
    $runs = @()
    if ($rc -eq 0) { $runs += @{ Tag = 'asan_ubsan'; Exe = $exeAU } }
    else {
      Say "L4 combined ASan+UBSan build failed (exit $rc, see $blog); trying separate builds"
      $exeA = Join-Path $sanDir 'forge_asan.exe'; $exeU = Join-Path $sanDir 'forge_ubsan_trap.exe'
      $rcA = Invoke-SanBuild $SanSrc $exeA @('-fsanitize=address', '-fms-runtime-lib=dll') $blog
      $rcU = Invoke-SanBuild $SanSrc $exeU @('-fsanitize=undefined', '-fsanitize-trap=undefined') $blog
      if ($rcA -ne 0 -or $rcU -ne 0) { throw "sanitizer builds failed (asan $rcA, ubsan $rcU); see $blog" }
      $runs += @{ Tag = 'asan'; Exe = $exeA }; $runs += @{ Tag = 'ubsan_trap'; Exe = $exeU }
    }
    foreach ($run in $runs) {
      $sb = Invoke-SanBench $run.Exe $sanDir $run.Tag
      $ok = ($sb.Exit -eq 0 -and $sb.Reports -eq 0 -and "$($sb.Nodes)" -eq "$($c.on.d16)")
      $state = 'PASS'; if (-not $ok) { $state = 'FAIL'; $script:Fail++ }
      Say ("L4 {0,-11} bench 16 nodes {1} (cand plain {2}), exit {3}, sanitizer reports {4}  {5}" -f $run.Tag, $sb.Nodes, $c.on.d16, $sb.Exit, $sb.Reports, $state)
    }
    $l4 = 'run'
    Stop-IfFailed 'L4'
  }
  if ($script:Fail -gt 0) { Say "VERDICT NOT BIT-EXACT ($($script:Fail) failing lines)"; exit 3 }
  $scope = 'L1-L3'; if ($l4 -eq 'run') { $scope = 'L1-L4' }
  Say ("VERDICT BIT-EXACT ({0}; L3 on {1} FENs{2})" -f $scope, $n, $(if ($n -lt $allFens.Count) { ' = quick subset' } else { '' }))
  exit 0
} catch {
  Write-Output "ERROR: $($_.Exception.Message)"
  if ($script:LogFile) { Add-OspdLf $script:LogFile "ERROR: $($_.Exception.Message)" }
  exit 1
}
