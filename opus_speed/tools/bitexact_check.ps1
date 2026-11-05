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
  [string]$Fens = 'F:\ospd\wt\opus_speed\data\fens_12k_v2.txt',
  [int]$FenDepth = 13,
  [string]$SanSrc = '',
  [string[]]$Define = @(),
  [switch]$SanNdebug,
  [switch]$SkipSan,
  [switch]$NoStop,
  [switch]$OnlyL4
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\uci_lib.ps1"
# -File passes a list as ONE comma-joined string: split every list parameter on commas
$Define = @($Define | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
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
      # the lock answers a bad FEN with 'info string invalid FEN: ...' and keeps the old position: fail, never compare
      if ($line.StartsWith('info string') -and $line -match 'invalid') { throw "engine rejected FEN $($s.Cur): $line" }
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

function Invoke-Native([string]$Tool, [object[]]$ToolArgs, [string]$Cwd, [string]$BuildLog) {
  Add-OspdLf $BuildLog ("-- $(Get-OspdNow) $Tool " + ($ToolArgs -join ' '))
  Push-Location $Cwd
  $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  try { $o = @(& $Tool @ToolArgs 2>&1 | ForEach-Object { "$_" }); $rc = $LASTEXITCODE } finally { Pop-Location; $ErrorActionPreference = $eap }
  foreach ($l in $o) { Add-OspdLf $BuildLog $l }
  Add-OspdLf $BuildLog "-- exit $rc"
  return $rc
}

function New-MsvcPortCopy([string]$Src, [string]$Dst) {
  # MSVC has no unsigned __int128, so the source's own fallback would index the TT by key % count (a different TT
  # index = a different search). The sanitizer-only copy gets ONE extra branch giving the identical index via
  # __umulh (high 64 bits of key * count, = the __int128 path). Nothing else changes; bench nodes = pin proves it.
  Copy-Item -Recurse -LiteralPath $Src -Destination $Dst
  Get-ChildItem -Recurse -File $Dst | ForEach-Object { $_.IsReadOnly = $false }
  $h = Join-Path $Dst 'include\forge\search.hpp'
  $t = [System.IO.File]::ReadAllText($h)
  $anchor = "#else`n        return clusters_[static_cast<std::size_t>(key % cluster_count_)];"
  $nl = "`n"; if ($t.Contains("`r`n")) { $anchor = $anchor.Replace("`n", "`r`n"); $nl = "`r`n" }
  $cnt = ([regex]::Matches($t, [regex]::Escape($anchor))).Count
  if ($cnt -ne 1) { return "anchor found $cnt times" }
  $t = $t.Replace($anchor, "#elif defined(_MSC_VER)$nl        return clusters_[static_cast<std::size_t>(__umulh(key, static_cast<std::uint64_t>(cluster_count_)))];$nl$anchor")
  [System.IO.File]::WriteAllText($h, ("#ifdef _MSC_VER$nl#include <intrin.h>$nl#endif$nl" + $t), (New-Object System.Text.UTF8Encoding($false)))
  return 'ok'
}

function Invoke-SanBench([string]$Exe, [string]$Dir, [string]$Tag) {
  $in = Join-Path $Dir "$Tag.in.txt"; $outF = Join-Path $Dir "$Tag.out.txt"; $errF = Join-Path $Dir "$Tag.err.txt"
  Write-OspdLf $in @('uci', 'isready', 'bench 16', 'isready', 'quit')
  # the MSVC ASan runtime DLL is on the PATH that vcvars64 set (VC\Tools\MSVC\<ver>\bin\Hostx64\x64)
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

  if ($OnlyL4) {
    # sanitizer level alone (re-tests): compare against the lock pin, skip L1-L3
    $c = [pscustomobject]@{ on = [pscustomobject]@{ d16 = $script:OspdPinsOn['d16'] } }
    Say 'L1-L3 skipped (-OnlyL4); L4 nodes are compared with the lock pin d16'
  } else {
  # L1 + L2
  $r = Get-L1L2 $Ref $cacheDir; $c = Get-L1L2 $Cand $candCache
  foreach ($d in $script:OspdDepths) { $pin = $null; if ($refIsLock) { $pin = $script:OspdPinsOn["d$d"] }; Verdict-Line 'L1' "bench d$d net on" $r.on."d$d" $c.on."d$d" $pin }
  foreach ($d in $script:OspdDepths) { $pin = $null; if ($refIsLock) { $pin = $script:OspdPinsOff["d$d"] }; Verdict-Line 'L1' "bench d$d net off" $r.off."d$d" $c.off."d$d" $pin }
  Stop-IfFailed 'L1'
  foreach ($k in $script:OspdPerftPins.Keys) { Verdict-Line 'L2' "perft 5 $k" $r.perft.$k $c.perft.$k $script:OspdPerftPins[$k] }
  Stop-IfFailed 'L2'

  # L3
  $rawFens = @(Get-Content $Fens | Where-Object { $_.Trim() -and -not $_.StartsWith('#') })
  $allFens = @($rawFens | ForEach-Object { ConvertTo-OspdFen $_ })   # Code Review SHOULD 2: six fields, side to move added
  $normalized = @(for ($i = 0; $i -lt $rawFens.Count; $i++) { if ($rawFens[$i].Trim() -ne $allFens[$i]) { $i } }).Count
  $n = $allFens.Count
  if ($Quick) { $n = [Math]::Min(2000, $n) }
  if ($FenCount -gt 0) { $n = [Math]::Min($FenCount, $allFens.Count) }
  $fenList = [string[]]$allFens[0..($n - 1)]
  $fmd5 = Get-OspdMd5 $Fens
  $refTsv = Join-Path $cacheDir ("fens_{0}_n{1}_d{2}_ob0.tsv" -f $fmd5.Substring(0, 8), $n, $FenDepth)
  # one computation per reference file: concurrent checks (several packs at once) wait for the first one instead of
  # each computing the same reference (seen 10:00: three quick checks computed the n=2000 reference in parallel)
  $refMutex = New-Object System.Threading.Mutex($false, ('Local\ospd_ref_' + (Split-Path $refTsv -Leaf)))
  $haveRef = $false
  try { $haveRef = $refMutex.WaitOne([TimeSpan]::FromMinutes(120)) } catch [System.Threading.AbandonedMutexException] { $haveRef = $true }
  if (-not $haveRef) { throw "waited 120 min for another process computing $refTsv" }
  try {
    if (-not (Test-Path $refTsv)) {
      $part = $refTsv + ".part$PID"
      $sec = Invoke-FenSet $Ref $fenList $FenDepth $part (Join-Path $cacheDir 'fens.uci.log')
      if (Test-Path $refTsv) {
        # written meanwhile by a process without the mutex (older code): the two must agree byte for byte
        if ((Get-OspdSha256 $part) -ne (Get-OspdSha256 $refTsv)) { throw "reference $refTsv differs from this run's $part (non-deterministic reference?)" }
        Say ("L3 ref FEN set computed in {0:N0} s; equals the cached copy written meanwhile" -f $sec)
      } else {
        Move-Item -LiteralPath $part -Destination $refTsv
        Say ("L3 ref FEN set computed in {0:N0} s -> {1}" -f $sec, $refTsv)
      }
    } else { Say "L3 ref FEN set from cache $refTsv" }
  } finally { $refMutex.ReleaseMutex() }
  $candTsv = Join-Path $Out ("fens_n{0}_d{1}.tsv" -f $n, $FenDepth)
  $sec = Invoke-FenSet $Cand $fenList $FenDepth $candTsv (Join-Path $Out 'fens.uci.log')
  $ra = Get-Content $refTsv; $ca = Get-Content $candTsv
  # degenerate-set guard (bug of 09:2x: placement-only FENs were rejected and every row searched the same position)
  $distinct = @($ra | ForEach-Object { ($_ -split "`t", 2)[1] } | Sort-Object -Unique).Count
  if ($n -ge 100 -and $distinct -lt [int]($n / 10)) { throw "L3 reference is degenerate: only $distinct distinct results for $n FENs" }
  $same = 0; $diffs = @()
  for ($i = 0; $i -lt $n; $i++) { if ($ra[$i] -eq $ca[$i] -and $ra[$i] -match "`t\d+`t") { $same++ } else { if ($diffs.Count -lt 10) { $diffs += "  FEN $i ref [$($ra[$i])] cand [$($ca[$i])]" } } }
  $state = 'PASS'; if ($same -ne $n) { $state = 'FAIL'; $script:Fail++ }
  Say ("L3 FENs {0} (md5 {1}; {7} lines completed to six fields) go depth {2}: {3} / {4} identical (depth, score, nodes, bestmove; {8} distinct ref results), cand {5:N0} s  {6}" -f (Split-Path $Fens -Leaf), $fmd5.Substring(0, 8), $FenDepth, $same, $n, $sec, $state, $normalized, $distinct)
  foreach ($d in $diffs) { Say $d }
  Stop-IfFailed 'L3'
  }

  # L4
  if ($SkipSan -or -not $SanSrc) {
    Say "L4 sanitizer build: NOT RUN ($(if ($SkipSan) { '-SkipSan' } else { 'no -SanSrc' }))"
    $l4 = 'not run'
  } else {
    $vc = Get-VcEnv
    $sanDir = Join-Path $Out 'san'; New-Item -ItemType Directory -Path $sanDir | Out-Null
    $blog = Join-Path $sanDir 'build.log'
    Add-OspdLf $blog "vcvars: $vc"
    # The PC has no ASan for g++ (MinGW) and its LLVM 18 does not accept the installed MSVC STL (needs clang 20+), so:
    # ASan = MSVC cl /fsanitize=address on a port copy (one TT-index line, see New-MsvcPortCopy); UBSan = the lock's
    # g++ with -fsanitize=undefined in trap mode (no runtime library needed) on the unchanged source.
    $runs = @()
    $port = Join-Path $sanDir 'src_msvc'
    $pc = New-MsvcPortCopy $SanSrc $port
    $exeA = Join-Path $sanDir 'forge_asan_msvc.exe'
    if ($pc -ne 'ok') { Say "L4 asan: port copy failed ($pc) -> ASan NOT RUN"; $script:Fail++ }
    else {
      $units = @(Get-ChildItem (Join-Path $port 'src') -Filter *.cpp | Sort-Object Name | ForEach-Object { 'src\' + $_.Name })
      $clArgs = @('/nologo', '/std:c++20', '/EHsc', '/O2', '/Zi', '/fsanitize=address', '/arch:AVX512', '/DFORGE_NNUE_HIDDEN=256', '/DFORGE_EXPOSE_TUNABLES=1', '/Iinclude', ('/Fd' + (Join-Path $sanDir 'asan.pdb')), ('/Fo' + $sanDir + '\'))
      if ($SanNdebug) { $clArgs += '/DNDEBUG' }
      foreach ($d in $Define) { $clArgs += ('/D' + $d) }
      # /STACK: Worker::clear() assigns a ~1.4 MB ContinuationHistory temporary on the stack; MSVC's default 1 MB stack
      # overflows (seen 09:26 under ASan), MinGW's default is 2 MB. 64 MB here only for the sanitizer harness.
      $clArgs += $units; $clArgs += @(('/Fe' + $exeA), '/link', '/INCREMENTAL:NO', '/STACK:67108864')
      $rcA = Invoke-Native 'cl.exe' $clArgs $port $blog
      if ($rcA -ne 0) { Say "L4 asan: MSVC build failed (exit $rcA, see $blog)"; $script:Fail++ } else { $runs += @{ Tag = 'asan_msvc'; Exe = $exeA } }
    }
    $exeU = Join-Path $sanDir 'forge_ubsan_trap.exe'
    $units2 = @(Get-ChildItem (Join-Path $SanSrc 'src') -Filter *.cpp | Sort-Object Name | ForEach-Object { 'src/' + $_.Name })
    $gArgs = @('-std=c++20', '-O1', '-DFORGE_NNUE_HIDDEN=256', '-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-static', '-pthread',
      '-DFORGE_EXPOSE_TUNABLES=1', '-fsanitize=undefined', '-fsanitize-trap=all', '-fno-sanitize-recover=all', '-Iinclude')
    if ($SanNdebug) { $gArgs += '-DNDEBUG' }
    foreach ($d in $Define) { $gArgs += ('-D' + $d) }
    $gArgs += $units2; $gArgs += @('-o', $exeU)
    $env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
    $rcU = Invoke-Native 'C:\msys64\ucrt64\bin\g++.exe' $gArgs $SanSrc $blog
    if ($rcU -ne 0) { Say "L4 ubsan: g++ build failed (exit $rcU, see $blog)"; $script:Fail++ } else { $runs += @{ Tag = 'ubsan_trap'; Exe = $exeU } }
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
