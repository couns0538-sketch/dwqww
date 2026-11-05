# build_variants.ps1 - build-mode / flag / PGO-workload variants of a Forge source tree (speed job, PowerShell 5.1).
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File build_variants.ps1 -SrcDir <tree> -Tag <name>
#          -Variant <name>[,<name>..] [-Define 'N=V',..] [-NoExpose] [-Twice] [-Extra '<flags>' -Workload v1|wnonet|w12k|wmix]
# Every variant builds from a fresh copy of -SrcDir in F:\ospd\builds\<Tag>_<variant>[_pc1|_pc2]\src_copy (never in the
# source). The LTO+PGO lines are QA's kit v2.3 build_ltopgo.ps1 token for token (same $F, LTO, profile and link
# tokens, objects in the same order, training fed as raw stdin bytes), so lp_v1 of the lock source must give the lock
# exe FD3A5190 byte for byte (the self-test). -Expose is the default because FD3A5190 is the -Expose build.
# Variants:
#   o3        plain lock line (+ -Wl,--no-insert-timestamp so two builds compare)
#   lto       LTO without PGO          pgo       PGO without LTO (workload v1)
#   lp_v1     LTO+PGO, workload v1 (= the lock recipe)
#   lp_z4     -march=znver4            lp_noplt  -fno-plt            lp_nosi   -fno-semantic-interposition
#   lp_af64   -falign-functions=64     lp_ppt    -fprofile-partial-training (use stage)
#   lp_ipapta -fipa-pta                lp_part1  -flto-partition=one lp_nossp  -fno-stack-protector
#   lp_pvw256 / lp_pvw512 -mprefer-vector-width=256 / 512 (g++ 15 default for znver5: none = tuning decides)
#   lp_wnonet workload: UseNNUE=false + bench 11/13/16
#   lp_w12k   workload: v1 + 300 FENs of the 12k set (every 40th) at go depth 10, OwnBook false, ucinewgame each
#   lp_wmix   workload: v1 + 300 game positions (data\game_positions_300.tsv) at go nodes 20000, TT kept per game
#   custom    LTO+PGO with -Extra flags and -Workload
# Checks per exe: g++ exit codes, gcda count = units (PGO), 0 real missing-profile warnings, vfmadd = 0, LTO IR in every
# object (LTO), quick pins bench 11/13/16 with the net (defaults) = lock pins. -Twice builds _pc1 and _pc2 and compares
# the exe sha256 (binding rule for LTO+PGO exes). Placement: CPUs 0-1 (0x3), Idle. Output: SUMMARY.txt per build and
# one line per exe on stdout: 'EXE <variant> <path> sha256 <..> md5 <..> pins OK ...' (only for a build that passed every
# check; a pin DIFF or any other failure prints 'FAIL <variant> : <reason>', writes FAILED + 'RESULT FAIL' and exits 1).
param(
  [Parameter(Mandatory = $true)][string]$SrcDir,
  [Parameter(Mandatory = $true)][string]$Tag,
  [Parameter(Mandatory = $true)][string[]]$Variant,
  [string[]]$Define = @(),
  [switch]$NoExpose,
  [switch]$Twice,
  [string]$Extra = '',
  [string]$Workload = 'v1',
  [string]$Work = 'F:\ospd\builds',
  [int]$TrainTimeoutSec = 3600
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\uci_lib.ps1"
# -File passes a list as ONE comma-joined string: split every list parameter on commas
$Variant = @($Variant | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$Define = @($Define | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$Kit ='C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\kit_v23'
$KitWl = Join-Path $Kit 'workload\frozen_train_cmds.txt'
$Gpp = 'C:\msys64\ucrt64\bin\g++.exe'; $Objdump = 'C:\msys64\ucrt64\bin\objdump.exe'
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
$DataDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'data'

$Table = @{
  o3 = @{ Mode = 'plain'; Extra = ''; Use = ''; Wl = '' }
  lto = @{ Mode = 'lto'; Extra = ''; Use = ''; Wl = '' }
  pgo = @{ Mode = 'pgo'; Extra = ''; Use = ''; Wl = 'v1' }
  lp_v1 = @{ Mode = 'lp'; Extra = ''; Use = ''; Wl = 'v1' }
  lp_z4 = @{ Mode = 'lp'; Extra = 'MARCH=znver4'; Use = ''; Wl = 'v1' }
  lp_noplt = @{ Mode = 'lp'; Extra = '-fno-plt'; Use = ''; Wl = 'v1' }
  lp_nosi = @{ Mode = 'lp'; Extra = '-fno-semantic-interposition'; Use = ''; Wl = 'v1' }
  lp_af64 = @{ Mode = 'lp'; Extra = '-falign-functions=64'; Use = ''; Wl = 'v1' }
  lp_ppt = @{ Mode = 'lp'; Extra = ''; Use = '-fprofile-partial-training'; Wl = 'v1' }
  lp_ipapta = @{ Mode = 'lp'; Extra = '-fipa-pta'; Use = ''; Wl = 'v1' }
  lp_part1 = @{ Mode = 'lp'; Extra = '-flto-partition=one'; Use = ''; Wl = 'v1' }
  lp_nossp = @{ Mode = 'lp'; Extra = '-fno-stack-protector'; Use = ''; Wl = 'v1' }
  lp_pvw256 = @{ Mode = 'lp'; Extra = '-mprefer-vector-width=256'; Use = ''; Wl = 'v1' }
  lp_pvw512 = @{ Mode = 'lp'; Extra = '-mprefer-vector-width=512'; Use = ''; Wl = 'v1' }
  lp_wnonet = @{ Mode = 'lp'; Extra = ''; Use = ''; Wl = 'wnonet' }
  lp_w12k = @{ Mode = 'lp'; Extra = ''; Use = ''; Wl = 'w12k' }
  lp_wmix = @{ Mode = 'lp'; Extra = ''; Use = ''; Wl = 'wmix' }
}

# Say writes straight to stdout, NOT to the PowerShell output stream: Build-One calls it, and anything a function
# writes to the output stream becomes part of its return value (bug of 09:51: the returned build object came back as
# [strings..., object], so -Twice never saw exactly two builds and never printed REPRO).
function Say([string]$Msg) { $line = "$(Get-OspdNow) $Msg"; [Console]::Out.WriteLine($line); if ($script:BuildLog) { Add-OspdLf $script:BuildLog $line } }
function Invoke-Gpp([string]$What, [string]$StageLog, [object[]]$GppArgs) {
  Add-OspdLf $StageLog ("-- $What : g++ " + ($GppArgs -join ' '))
  # native stderr (e.g. the lto-wrapper 'serial compilation' warning) must not become a terminating error (PS 5.1)
  $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  try { $o = @(& $Gpp @GppArgs 2>&1 | ForEach-Object { "$_" }); $rc = $LASTEXITCODE } finally { $ErrorActionPreference = $eap }
  foreach ($l in $o) { Add-OspdLf $StageLog $l }
  if ($rc -ne 0) { throw "g++ failed ($What), exit $rc; see $StageLog" }
}

function Invoke-Training([string]$Exe, [string]$Wl, [string]$Dir) {
  # v1 / wnonet: raw stdin file like the kit; w12k / wmix: UCI driver that waits for bestmove (a 'go' is aborted by the
  # next input line). The instrumented exe must exit normally (quit) so its .gcda files get written.
  $out = Join-Path $Dir 'train_out.txt'
  if ($Wl -eq 'v1' -or $Wl -eq 'wnonet') {
    $file = $KitWl
    if ($Wl -eq 'wnonet') {
      $file = Join-Path $Dir 'train_wnonet.txt'
      Write-OspdLf $file @('uci', 'setoption name UseNNUE value false', 'isready', 'bench 11', 'bench 13', 'bench 16', 'isready', 'quit')
    }
    $p = Start-Process -FilePath $Exe -RedirectStandardInput $file -RedirectStandardOutput $out -RedirectStandardError "$out.stderr.txt" -NoNewWindow -PassThru -WorkingDirectory $Dir
    $null = $p.Handle
    if (-not $p.WaitForExit($TrainTimeoutSec * 1000)) { throw "training timeout ($Exe)" }
    $p.WaitForExit()
    if ($p.ExitCode -ne 0) { throw "training exit $($p.ExitCode)" }
    $n = @(Select-String -Path $out -Pattern 'bench depth').Count
    if ($n -ne 3) { throw "training gave $n bench lines (want 3)" }
    return "workload $Wl file $file sha256 $(Get-OspdSha256 $file)"
  }
  $log = Join-Path $Dir 'train_uci.log'
  $e = Start-OspdEngine $Exe $log
  $null = Initialize-OspdEngine $e @()
  foreach ($d in 11, 13, 16) { $null = Invoke-OspdBench $e $d }
  Send-OspdUci $e 'setoption name OwnBook value false'; Send-OspdUci $e 'isready'; $null = Wait-OspdUci $e '^readyok' 60
  $src = ''
  if ($Wl -eq 'w12k') {
    $src = Join-Path $DataDir 'fens_12k_v2.txt'   # full six-field FENs (the placement-only fens_12k.txt is rejected)
    $fens = @(Get-Content $src | Where-Object { $_.Trim() -and -not $_.StartsWith('#') } | ForEach-Object { ConvertTo-OspdFen $_ })
    for ($i = 0; $i -lt $fens.Count; $i += 40) { $null = Invoke-OspdSearch $e $fens[$i] 'depth 10' -NewGame }
  } elseif ($Wl -eq 'wmix') {
    $src = Join-Path $DataDir 'game_positions_300.tsv'
    $last = ''
    foreach ($row in (Get-Content $src | Where-Object { $_.Trim() -and -not $_.StartsWith('#') })) {
      $f = $row -split "`t"; $ng = ($f[0] -ne $last); $last = $f[0]
      if ($ng) { $null = Invoke-OspdSearch $e $f[2] 'nodes 20000' -NewGame } else { $null = Invoke-OspdSearch $e $f[2] 'nodes 20000' }
    }
  } else { throw "unknown workload $Wl" }
  if (-not (Stop-OspdEngine $e)) { throw 'instrumented exe did not exit after quit' }
  if ($e.Proc.ExitCode -ne 0) { throw "training exit $($e.Proc.ExitCode)" }
  return "workload $Wl (v1 benches + $src md5 $(Get-OspdMd5 $src)) via UCI driver"
}

function Build-One([string]$Name, [hashtable]$Spec, [string]$Dir) {
  New-Item -ItemType Directory -Path $Dir | Out-Null
  $script:BuildLog = Join-Path $Dir 'build_log.txt'
  $summary = New-Object System.Collections.Generic.List[string]
  Copy-Item -Recurse -LiteralPath $SrcDir -Destination (Join-Path $Dir 'src_copy')
  $tree = Join-Path $Dir 'src_copy'
  Get-ChildItem -Recurse -File $tree | ForEach-Object { $_.IsReadOnly = $false }
  Push-Location $tree
  try {
    $units = @(Get-ChildItem src -Filter *.cpp | Sort-Object Name | ForEach-Object { $_.BaseName })
    $march = '-march=znver5'
    $extraTok = @()
    foreach ($t in ($Spec.Extra -split ' ' | Where-Object { $_ })) { if ($t -like 'MARCH=*') { $march = '-march=' + $t.Substring(6) } else { $extraTok += $t } }
    $useTok = @($Spec.Use -split ' ' | Where-Object { $_ })
    $F = @('-std=c++20', '-O3', '-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-ffp-contract=off', '-fno-fast-math', $march, '-pthread', '-Iinclude')
    if (-not $NoExpose) { $F += '-DFORGE_EXPOSE_TUNABLES=1' }
    foreach ($d in $Define) { $F += ('-D' + $d) }
    $F += $extraTok
    $LTO = @('-flto=1', '-fuse-linker-plugin')
    $gver = (& $Gpp --version | Select-Object -First 1)
    Say "variant $Name mode $($Spec.Mode) src $SrcDir defines [$($Define -join ' ')] extra [$($extraTok -join ' ')] use-only [$($useTok -join ' ')] march $march expose $(-not $NoExpose); $gver"
    $summary.Add("variant $Name"); $summary.Add("source $SrcDir"); $summary.Add("compiler $gver")
    $exeName = "forge_${Name}.exe"
    $wlInfo = ''
    if ($Spec.Mode -eq 'plain') {
      $lockFlags = @('-std=c++20', '-O3', '-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-ffp-contract=off', '-fno-fast-math', $march, '-static', '-pthread')
      if (-not $NoExpose) { $lockFlags += '-DFORGE_EXPOSE_TUNABLES=1' }
      foreach ($d in $Define) { $lockFlags += ('-D' + $d) }
      $lockFlags += $extraTok
      $args0 = @($lockFlags) + '-Iinclude' + @($units | ForEach-Object { "src/$_.cpp" }) + '-Wl,--no-insert-timestamp' + '-o' + $exeName
      Invoke-Gpp 'plain' (Join-Path $Dir 'build_plain.log') $args0
      $summary.Add('flags plain: g++ ' + ($args0 -join ' '))
    } elseif ($Spec.Mode -eq 'lto') {
      New-Item -ItemType Directory obj_lto | Out-Null
      foreach ($u in $units) { Invoke-Gpp "lto $u" (Join-Path $Dir 'build_lto.log') (@($F) + $LTO + '-c' + "src/$u.cpp" + '-o' + "obj_lto/$u.o") }
      $link = @($F) + $LTO + '-static' + '-Wl,--no-insert-timestamp' + @((Get-ChildItem obj_lto\*.o).FullName) + '-o' + $exeName
      Invoke-Gpp 'lto link' (Join-Path $Dir 'build_lto.log') $link
      $summary.Add('flags lto: g++ ' + (($F + $LTO) -join ' ') + ' ; link + -static -Wl,--no-insert-timestamp')
    } else {
      $useLto = ($Spec.Mode -eq 'lp')
      $L = @(); if ($useLto) { $L = $LTO }
      $objDir = 'obj_ltopgo'; $P2 = Join-Path $tree 'pgo_profile_lto'
      New-Item -ItemType Directory $P2, $objDir -Force | Out-Null
      $genLog = Join-Path $Dir 'build_gen.log'; $useLog = Join-Path $Dir 'build_use.log'
      foreach ($u in $units) { Invoke-Gpp "gen $u" $genLog (@($F) + $L + "-fprofile-generate=$P2" + '-fprofile-update=single' + '-c' + "src/$u.cpp" + '-o' + "$objDir/$u.o") }
      Invoke-Gpp 'gen link' $genLog (@($F) + $L + "-fprofile-generate=$P2" + '-static' + @((Get-ChildItem "$objDir\*.o").FullName) + '-o' + "forge_instr_$Name.exe")
      $wl = $Spec.Wl
      $wlInfo = Invoke-Training (Join-Path $tree "forge_instr_$Name.exe") $wl $tree
      $trainEnd = Get-Date
      Say "training done: $wlInfo"
      $gc = @(Get-ChildItem $P2 -Filter *.gcda -Recurse).Count
      if ($gc -ne $units.Count) { throw "gcda count $gc != units $($units.Count)" }
      foreach ($u in $units) {
        Invoke-Gpp "use $u" $useLog (@($F) + $L + "-fprofile-use=$P2" + '-fprofile-correction' + '-Wmissing-profile' + $useTok + '-c' + "src/$u.cpp" + '-o' + "$objDir/$u.o")
        if ((Get-Item "$objDir/$u.o").LastWriteTime -le $trainEnd) { throw "$objDir/$u.o not rebuilt after training" }
      }
      $link = @($F) + $L + "-fprofile-use=$P2" + '-fprofile-correction' + '-Wmissing-profile' + $useTok + '-static' + '-Wl,--no-insert-timestamp' + @((Get-ChildItem "$objDir\*.o").FullName) + '-o' + $exeName
      Invoke-Gpp 'use link' $useLog $link
      $useLines = @(Get-Content $useLog | Where-Object { $_ -notlike '-- *' })
      $miss = @($useLines | Where-Object { $_ -match 'warning:' -and $_ -match 'Wmissing-profile|profile count data|coverage mismatch|Wcoverage-mismatch' }).Count
      if ($miss -ne 0) { throw "missing-profile warnings: $miss" }
      if ($useLto) {
        foreach ($u in $units) { $s = @(& $Objdump -h "$objDir/$u.o" | Select-String '\.gnu\.lto_'); if ($s.Count -eq 0) { throw "$u.o has no LTO IR" } }
      }
      $summary.Add("flags $($Spec.Mode): gen/use g++ " + (($F + $L) -join ' ') + " ; use-only [$($useTok -join ' ')] ; use link + -static -Wl,--no-insert-timestamp")
      $summary.Add("training: $wlInfo"); $summary.Add("gcda $gc; missing-profile warnings 0")
    }
    $fma = @(& $Objdump -d $exeName | Select-String 'vfmadd').Count
    if ($fma -ne 0) { throw "vfmadd count $fma (lock rule: 0)" }
    $sha = Get-OspdSha256 $exeName; $md5 = Get-OspdMd5 $exeName
    $e = Start-OspdEngine (Join-Path $tree $exeName) (Join-Path $Dir 'pins_uci.log')
    $null = Initialize-OspdEngine $e @()
    $got = @(); foreach ($d in 11, 13, 16) { $got += (Invoke-OspdBench $e $d).Nodes }
    $null = Stop-OspdEngine $e
    $want = @($script:OspdPinsOn['d11'], $script:OspdPinsOn['d13'], $script:OspdPinsOn['d16'])
    # fail closed (Code Review CR_OPUS_SPEED_TOOLS_637B blocker): a pin table that yields no value, or any pin DIFF,
    # is a FAILED build with a non-zero exit - never 'RESULT PASS'
    if (@($want | Where-Object { -not $_ }).Count -ne 0) { throw "pin table lookup failed (got '$($want -join '/')')" }
    $pins = 'OK'; if (($got -join '/') -ne ($want -join '/')) { $pins = 'DIFF' }
    $summary.Add("exe $tree\$exeName sha256 $sha md5 $md5 vfmadd 0"); $summary.Add("quick pins bench 11/13/16 net on: $($got -join '/') (lock pins $($want -join '/')) $pins")
    if ($pins -ne 'OK') {
      $summary.Add("RESULT FAIL $Name : quick pins DIFF")
      Write-OspdLf (Join-Path $Dir 'SUMMARY.txt') $summary
      throw "quick pins DIFF: bench 11/13/16 net on = $($got -join '/'), lock pins $($want -join '/') (exe kept at $tree\$exeName for analysis, not for use)"
    }
    $summary.Add("RESULT PASS $Name")
    Write-OspdLf (Join-Path $Dir 'SUMMARY.txt') $summary
    return [pscustomobject]@{ Name = $Name; Exe = (Join-Path $tree $exeName); Sha = $sha; Md5 = $md5; Pins = $pins; Got = ($got -join '/') }
  } finally { Pop-Location }
}

$rcAll = 0
try {
  Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
  if (-not (Test-Path (Join-Path $SrcDir 'src'))) { throw "no src\ in $SrcDir" }
  if ($Extra -or ($Variant -contains 'custom')) { $Table['custom'] = @{ Mode = 'lp'; Extra = $Extra; Use = ''; Wl = $Workload } }
  foreach ($v in $Variant) {
    if (-not $Table.ContainsKey($v)) { throw "unknown variant $v" }
    $sides = @(''); if ($Twice) { $sides = @('_pc1', '_pc2') }
    $built = @()
    foreach ($side in $sides) {
      $null = Assert-OspdDisk -PlannedGB 0.15
      $dir = Join-Path $Work ("{0}_{1}{2}" -f $Tag, $v, $side)
      if (Test-Path $dir) { throw "$dir exists; use a new -Tag" }
      try {
        $b = Build-One $v $Table[$v] $dir
        $built += $b
        Write-Output ("EXE {0}{1} {2} sha256 {3} md5 {4} pins {5} {6}" -f $v, $side, $b.Exe, $b.Sha, $b.Md5, $b.Pins, $b.Got)
      } catch {
        Set-Content -Path (Join-Path $dir 'FAILED') -Value "FAILED $(Get-OspdNow): $($_.Exception.Message)"
        Write-Output "FAIL $v$side : $($_.Exception.Message)"
        $rcAll = 1
        break   # with -Twice: no pc2 after a failed pc1
      }
    }
    if ($Twice -and $built.Count -eq 2) {
      if ($built[0].Sha -eq $built[1].Sha) { Write-Output "REPRO $v pc1 = pc2 sha256 $($built[0].Sha)" } else { Write-Output "NOT-REPRODUCIBLE $v pc1 $($built[0].Sha) pc2 $($built[1].Sha)"; $rcAll = 1 }
    }
  }
} catch {
  Write-Output "ERROR: $($_.Exception.Message)"
  $rcAll = 1
}
exit $rcAll
