# build_ltopgo.ps1 v2.3 - PC (grok-pc) mirror of build_ltopgo.sh. QA runs it; Engine Coder never runs anything on the PC.
# Compile/link tokens are QA's build_lto.ps1 (md5 05f39e97a9d2ac5281864e6a958c9d25, the recipe that made 8A4A00C9...), with:
# (1) training input = the FROZEN workload v1 of this kit (no setoption lines, all UCI options at default/OFF), sha256-checked;
# (2) added: lock-style plain build, .gcda sha256 manifest + arcs manifest (names normalised to <BUILD>, LF) + archive,
#     warning/vfmadd/LTO checks, plain-vs-LTO+PGO node identity with lp_check.py.
# v2 (CR_M8_LTOPGO_KIT_20261030 md5 2bb46961): exit-code check after every g++/objdump/engine/python call (M1); manifest names
# normalised (M2); vfmadd > 0 fails; LTO on the link checked; FAILED marker file on any failure; timeout per engine run;
# refuses a source copy holding build leftovers (*.gcda, *.o, *.exe, obj_*/pgo_* dirs).
# v2.1 (QA_M8_AL1_LTOPGO_BUILD_20261030 md5 0ce0d969): gcov-dump is optional (MSYS2 gcc 15.2.0 ships none); without it the
# arcs manifest says 'UNAVAILABLE (no gcov-dump)' and the build continues. Added gcda_manifest_nohdr.txt (sha256 of each .gcda
# without its first 12 bytes = magic/version/stamp). Both gcda manifests are RECORD ONLY. The ONLY binding check is the exe
# sha256: the two clean rebuilds pc1 and pc2 must give the same forge_ltopgo exe sha256. SUMMARY.txt lists all of it.
# v2.2: -Wl,--no-insert-timestamp on the LTO+PGO use link (PE stamp/checksum made pc1 != pc2).
# v2.3 (QA_LTOPGO_CANDS_AL1_PC_20261030 md5 05d7ffcc): optional -Expose switch = the .sh --expose: adds
#   -DFORGE_EXPOSE_TUNABLES=1 to BOTH the plain and LTO+PGO builds so tunables show in the uci list. Only uci.cpp reads it
#   (CMake sets it on the forge target only). Without -Expose every command line is byte-for-byte v2.2.
# Variable names are all distinct ignoring case (PowerShell names are case-insensitive: the old $s/$S bug).
# usage (PowerShell, a CLEAN source copy whose SOURCES list equals the lock's):
#   powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File build_ltopgo.ps1 -SrcDir D:\...\clean_src -Tag al1s198_frozen_pc1 `
#     [-Work D:\forge_push\ltopgo] [-Kit <folder with workload\ and tools\>] [-Affinity 0x3] [-Flto '-flto=1'] `
#     [-CheckOpt 'Name=Value', 'N1=V1;N2=V2'] [-Pins 'd11=312866,...'] [-PerftPins 'startpos=4865609,kiwipete=193690690'] `
#     [-TrainTimeoutSec 3600] [-CheckTimeoutSec 7200] [-Expose]
param(
  [Parameter(Mandatory=$true)][string]$SrcDir,
  [Parameter(Mandatory=$true)][string]$Tag,
  [string]$Work = 'D:\forge_push\ltopgo',
  [string]$Kit = $PSScriptRoot,
  [long]$Affinity = 0x3,
  [string]$Flto = '-flto=1',
  [string[]]$CheckOpt = @(),
  [string]$Pins = '',
  [string]$PerftPins = '',
  [string]$Python = 'python',
  [string]$GcovDump = 'C:\msys64\ucrt64\bin\gcov-dump.exe',
  [int]$TrainTimeoutSec = 3600,
  [int]$CheckTimeoutSec = 7200,
  [switch]$Expose
)
$ErrorActionPreference = 'Continue'
$me = [System.Diagnostics.Process]::GetCurrentProcess(); $me.ProcessorAffinity = [IntPtr]$Affinity; $me.PriorityClass = 'BelowNormal'
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH; $gpp = 'C:\msys64\ucrt64\bin\g++.exe'; $objdumpExe = 'C:\msys64\ucrt64\bin\objdump.exe'
$WlFile = Join-Path $Kit 'workload\frozen_train_cmds.txt'; $FenFile = Join-Path $Kit 'workload\bench_fens.txt'
$Checker = Join-Path $Kit 'tools\lp_check.py'; $ArcsTool = Join-Path $Kit 'tools\gcda_arcs_digest.py'
# ---- preflight (nothing written yet) ----
if ((Get-FileHash $WlFile -Algorithm SHA256).Hash -ne '1D52720A2662153120C394BBA7A0971537DFCAD3C40B0550D37E6A27676ACE30') { throw 'frozen workload sha256 mismatch' }
if ((Get-FileHash $FenFile -Algorithm SHA256).Hash -ne '16F158933265DC5DC05FFD00A181809D345B25D72D3DE8E169804EFED7B1A835') { throw 'bench_fens sha256 mismatch' }
if (Select-String -Path $WlFile -Pattern '^setoption' -Quiet) { throw 'frozen workload must not set options' }
foreach($toolPath in $gpp, $objdumpExe, $Checker, $ArcsTool){ if (-not (Test-Path $toolPath)) { throw "missing tool: $toolPath" } }
$leftovers = @(Get-ChildItem -Recurse -Force $SrcDir | Where-Object { ($_.PSIsContainer -and ($_.Name -like 'obj_*' -or $_.Name -like 'pgo_*')) -or (-not $_.PSIsContainer -and $_.Extension -in '.gcda','.o','.exe') })
if ($leftovers.Count -ne 0) { throw "source copy is not clean ($($leftovers.Count) build leftovers, e.g. $($leftovers[0].FullName)); pass a fresh copy of the source" }
$HaveGcovDump = Test-Path $GcovDump   # optional since v2.1
$OutDir = Join-Path $Work $Tag
if (Test-Path $OutDir) { throw "$OutDir exists; use a new -Tag (never overwrite)" }
New-Item -ItemType Directory $OutDir | Out-Null
$LogFile = Join-Path $OutDir 'build_log.txt'
$SummaryFile = Join-Path $OutDir 'SUMMARY.txt'; $SummaryRows = [System.Collections.Generic.List[string]]::new()
function Say($msg) { $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"; $line; Add-Content $LogFile $line }
function Invoke-Gpp([string]$what, [string]$stageLog, [object[]]$gppArgs) {
  Add-Content $stageLog "-- $what"
  $gppOut = @(& $gpp @gppArgs 2>&1 | ForEach-Object { "$_" }); $gppRc = $LASTEXITCODE
  if ($gppOut.Count) { Add-Content $stageLog $gppOut }
  if ($gppRc -ne 0) { throw "g++ failed ($what), exit $gppRc; see $stageLog" }
}
function Invoke-Timed([string]$exePath, [string[]]$argList, [string]$stdinFile, [string]$stdoutFile, [int]$timeoutSec) {
  $startArgs = @{ FilePath = $exePath; NoNewWindow = $true; PassThru = $true; RedirectStandardOutput = $stdoutFile; RedirectStandardError = "$stdoutFile.stderr.txt" }
  if ($argList.Count) { $startArgs.ArgumentList = ($argList | ForEach-Object { '"' + ($_ -replace '"', '\"') + '"' }) -join ' ' }
  if ($stdinFile) { $startArgs.RedirectStandardInput = $stdinFile }
  $proc = Start-Process @startArgs; $null = $proc.Handle
  if (-not $proc.WaitForExit($timeoutSec * 1000)) { $proc.Kill(); throw "timeout after ${timeoutSec}s: $exePath" }
  $proc.WaitForExit()
  return $proc.ExitCode
}
function Format-GcdaName([string]$rawName) {   # M2: drop the mangled absolute path (holds Work\Tag) -> <BUILD>#obj_ltopgo#<unit>.gcda
  $normName = ($rawName -replace '\\', '/') -replace '^.*[#/]obj_ltopgo[#/]', '<BUILD>#obj_ltopgo#'
  if (-not $normName.StartsWith('<BUILD>#obj_ltopgo#')) { throw "unexpected gcda name: $rawName" }
  return $normName
}
function Write-LfFile([string]$filePath, [string[]]$fileLines) { [System.IO.File]::WriteAllText($filePath, (($fileLines -join "`n") + "`n")) }
try {
  # work in a fresh copy of the candidate source so object/profile paths are ours (source is read only)
  Copy-Item -Recurse $SrcDir (Join-Path $OutDir 'src_copy'); $Tree = Join-Path $OutDir 'src_copy'; Set-Location $Tree
  $F = '-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude'.Split(' ')
  $Units = @(Get-ChildItem src -Filter *.cpp | Sort-Object Name | ForEach-Object { $_.BaseName })   # AL1: bitboard board book eval eval_params nnue search uci
  if ($Expose) { $F = @($F) + '-DFORGE_EXPOSE_TUNABLES=1' }
  $LTO = $Flto,'-fuse-linker-plugin'
  Say "src $SrcDir tag $Tag units $($Units -join ' ') flto $Flto expose $([bool]$Expose)"
  Get-ChildItem -Recurse -File $Tree | Sort-Object FullName | ForEach-Object { "$((Get-FileHash $_.FullName -Algorithm SHA256).Hash)  $($_.FullName.Substring($Tree.Length+1))" } | Set-Content (Join-Path $OutDir 'SOURCES.sha256')
  # 1) plain = the lock's direct g++ line (j1v2/lockref/2_build/build_windows.ps1), same token order
  Say '== plain (lock line)'
  $PlainLog = Join-Path $OutDir 'build_plain.log'; $GenLog = Join-Path $OutDir 'build_gen.log'; $UseLog = Join-Path $OutDir 'build_use.log'
  $lockFlags = '-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread'.Split(' ')
  if ($Expose) { $lockFlags = @($lockFlags) + '-DFORGE_EXPOSE_TUNABLES=1' }
  Invoke-Gpp 'plain' $PlainLog (@($lockFlags) + '-Iinclude' + @($Units | ForEach-Object { "src/$_.cpp" }) + '-o' + "forge_plain_$Tag.exe")
  # 2) LTO+PGO instrumented (QA build_lto.ps1 step (b))
  Say '== LTO+PGO instr'
  $P2 = "$Tree\pgo_profile_lto"; New-Item -ItemType Directory $P2,obj_ltopgo -Force | Out-Null
  if ((Get-ChildItem $P2 -Recurse).Count -ne 0) { throw 'profile dir not empty' }
  foreach($unit in $Units){ Invoke-Gpp "gen $unit" $GenLog (@($F) + $LTO + "-fprofile-generate=$P2" + '-fprofile-update=single' + '-c' + "src/$unit.cpp" + '-o' + "obj_ltopgo/$unit.o") }
  Invoke-Gpp 'gen link' $GenLog (@($F) + $LTO + "-fprofile-generate=$P2" + '-static' + @((Get-ChildItem obj_ltopgo\*.o).FullName) + '-o' + "forge_instr_$Tag.exe")
  # 3) training = FROZEN workload as raw stdin bytes (no setoption: all UCI options at default/OFF), with a timeout
  Say '== train (frozen workload)'
  $TrainOut = Join-Path $OutDir 'train_out.txt'
  $trainRc = Invoke-Timed "$Tree\forge_instr_$Tag.exe" @() $WlFile $TrainOut $TrainTimeoutSec
  if ($trainRc -ne 0) { throw "training exe exit $trainRc" }
  $trainEnd = Get-Date
  $benchLines = @(Get-Content $TrainOut | Select-String 'bench depth'); $benchLines | ForEach-Object { Say "$_" }
  if ($benchLines.Count -ne 3) { throw "training gave $($benchLines.Count) bench lines (want 3)" }
  $gcdaFiles = @(Get-ChildItem $P2 -Filter *.gcda -Recurse); Say "gcda count $($gcdaFiles.Count) (units $($Units.Count))"
  if ($gcdaFiles.Count -ne $Units.Count) { throw 'gcda count != unit count' }
  $manifestRows = @($gcdaFiles | ForEach-Object { [pscustomobject]@{ Norm = (Format-GcdaName $_.FullName.Substring($P2.Length+1)); Hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower() } })
  $normNames = [string[]]($manifestRows | ForEach-Object { $_.Norm }); [Array]::Sort($normNames, [StringComparer]::Ordinal)
  $Manifest = Join-Path $OutDir 'gcda_manifest.txt'
  Write-LfFile $Manifest @($normNames | ForEach-Object { $nm = $_; "$(($manifestRows | Where-Object { $_.Norm -eq $nm }).Hash)  $nm" })
  Compress-Archive -Path $P2 -DestinationPath (Join-Path $OutDir "profile_archive_$Tag.zip")
  Say "gcda_manifest sha256 $((Get-FileHash $Manifest -Algorithm SHA256).Hash) (record only; differs run to run)"
  $nohdrRows = @($gcdaFiles | ForEach-Object { $gcdaBytes = [System.IO.File]::ReadAllBytes($_.FullName); if ($gcdaBytes.Length -lt 12) { throw "short gcda $($_.Name)" }
    $shaAlg = [System.Security.Cryptography.SHA256]::Create(); $hdrHash = ([BitConverter]::ToString($shaAlg.ComputeHash($gcdaBytes, 12, $gcdaBytes.Length - 12)) -replace '-','').ToLower(); $shaAlg.Dispose()
    [pscustomobject]@{ Norm = (Format-GcdaName $_.FullName.Substring($P2.Length+1)); Hash = $hdrHash } })
  $NohdrManifest = Join-Path $OutDir 'gcda_manifest_nohdr.txt'
  Write-LfFile $NohdrManifest @($normNames | ForEach-Object { $nm = $_; "$(($nohdrRows | Where-Object { $_.Norm -eq $nm }).Hash)  $nm" })
  $gcdaSha = (Get-FileHash $Manifest -Algorithm SHA256).Hash; $nohdrSha = (Get-FileHash $NohdrManifest -Algorithm SHA256).Hash
  Say "gcda_manifest_nohdr sha256 $nohdrSha (record only; first 12 header bytes stripped, value-profile counters may still differ)"
  $SummaryRows.Add("expose $([bool]$Expose)")
  $SummaryRows.Add("gcda_manifest sha256 $gcdaSha (record only)"); $SummaryRows.Add("gcda_manifest_nohdr sha256 $nohdrSha (record only)")
  $ArcsManifest = Join-Path $OutDir 'gcda_arcs_manifest.txt'
  if ($HaveGcovDump) {
    $arcsRaw = @(& $Python $ArcsTool $P2 $GcovDump); if ($LASTEXITCODE -ne 0) { throw "gcda_arcs_digest failed, exit $LASTEXITCODE" }
    $arcsRows = @($arcsRaw | Where-Object { $_ -match '^[0-9a-f]{64}  ' } | ForEach-Object { [pscustomobject]@{ Hash = $_.Substring(0, 64); Norm = (Format-GcdaName $_.Substring(66)) } })
    if ($arcsRows.Count -ne $Units.Count) { throw "arcs digest gave $($arcsRows.Count) rows" }
    $arcsNames = [string[]]($arcsRows | ForEach-Object { $_.Norm }); [Array]::Sort($arcsNames, [StringComparer]::Ordinal)
    Write-LfFile $ArcsManifest @($arcsNames | ForEach-Object { $nm = $_; "$(($arcsRows | Where-Object { $_.Norm -eq $nm }).Hash)  $nm" })
    $arcsState = "sha256 $((Get-FileHash $ArcsManifest -Algorithm SHA256).Hash) (record only)"
  } else {
    Write-LfFile $ArcsManifest @('UNAVAILABLE (no gcov-dump)')
    $arcsState = "UNAVAILABLE (no gcov-dump at $GcovDump)"
  }
  Say "gcda_arcs_manifest $arcsState"; $SummaryRows.Add("gcda_arcs_manifest $arcsState")
  # 4) LTO+PGO use (QA build_lto.ps1 step (b) use lines, same object paths)
  Say '== LTO+PGO use'
  foreach($unit in $Units){
    Invoke-Gpp "use $unit" $UseLog (@($F) + $LTO + "-fprofile-use=$P2" + '-fprofile-correction' + '-Wmissing-profile' + '-c' + "src/$unit.cpp" + '-o' + "obj_ltopgo/$unit.o")
    if ((Get-Item "obj_ltopgo/$unit.o").LastWriteTime -le $trainEnd) { throw "obj_ltopgo/$unit.o not rebuilt after training" }
  }
  $linkArgs = @($F) + $LTO + "-fprofile-use=$P2" + '-fprofile-correction' + '-Wmissing-profile' + '-static' + '-Wl,--no-insert-timestamp' + @((Get-ChildItem obj_ltopgo\*.o).FullName) + '-o' + "forge_ltopgo_$Tag.exe"
  Add-Content $UseLog ("-- link command: g++ " + ($linkArgs -join ' '))
  Invoke-Gpp 'use link' $UseLog $linkArgs
  # LTO checks: -flto on the link line, and every object carries LTO IR (.gnu.lto_ sections)
  if (-not ($linkArgs -contains $Flto)) { throw '-flto not on the link line' }
  if (-not ($linkArgs -contains '-Wl,--no-insert-timestamp')) { throw 'v2.2: --no-insert-timestamp not on the use link line' }
  foreach($unit in $Units){
    $ltoSections = @(& $objdumpExe -h "obj_ltopgo/$unit.o" | Select-String '\.gnu\.lto_'); if ($LASTEXITCODE -ne 0) { throw "objdump failed on $unit.o" }
    if ($ltoSections.Count -eq 0) { throw "obj_ltopgo/$unit.o has no LTO IR" }
  }
  $useLines = @(Get-Content $UseLog | Where-Object { $_ -notlike '-- *' })
  $missProf = @($useLines | Where-Object { $_ -match 'warning:' -and $_ -match 'Wmissing-profile|profile count data|coverage mismatch|Wcoverage-mismatch' }).Count
  $warnPlain = @(Get-Content $PlainLog -ErrorAction SilentlyContinue | Where-Object { $_ -match 'warning:' }).Count; $warnUse = @($useLines | Where-Object { $_ -match 'warning:' }).Count
  $fmaTotal = 0
  foreach($exeName in "forge_plain_$Tag.exe","forge_ltopgo_$Tag.exe"){
    $fmaHits = @(& $objdumpExe -d $exeName | Select-String 'vfmadd'); if ($LASTEXITCODE -ne 0) { throw "objdump failed on $exeName" }
    $fmaTotal += $fmaHits.Count
    $exeLine = "$exeName sha256 $((Get-FileHash $exeName -Algorithm SHA256).Hash) md5 $((Get-FileHash $exeName -Algorithm MD5).Hash) vfmadd $($fmaHits.Count)"
    Say $exeLine; $SummaryRows.Insert(0, $exeLine)
  }
  Say "compiler warning lines: plain $warnPlain, ltopgo $warnUse; real missing-profile/coverage warnings: $missProf (must be 0); -flto on link line: yes"
  if ($missProf -ne 0) { throw 'profile not applied everywhere' }
  if ($fmaTotal -ne 0) { throw "vfmadd found ($fmaTotal); the lock has 0 (map hits to functions before any exception)" }
  # 5) node identity plain vs LTO+PGO: OFF (no setoption at all) then each -CheckOpt run
  $Ident = Join-Path $OutDir 'ident'; New-Item -ItemType Directory $Ident | Out-Null
  $allOk = $true
  $runSets = @(@{ Name = 'off'; Opts = @() })
  $k = 0; foreach($optSet in $CheckOpt){ $k++; $runSets += @{ Name = "opt$k"; Opts = $optSet.Split(';') } }
  foreach($runSet in $runSets){
    $optArgs = @(); foreach($kv in $runSet.Opts){ $optArgs += '--opt'; $optArgs += $kv }
    foreach($kind in 'plain','ltopgo'){
      $checkRc = Invoke-Timed $Python (@($Checker, 'run', "$Tree\forge_${kind}_$Tag.exe", "$Ident\$($runSet.Name).$kind.json") + $optArgs + @('--fens', $FenFile)) $null "$Ident\$($runSet.Name).$kind.txt" $CheckTimeoutSec
      if ($checkRc -ne 0) { throw "lp_check run failed ($($runSet.Name) $kind), exit $checkRc" }
    }
    $cmpArgs = @(); if ($runSet.Name -eq 'off') { if ($Pins) { $cmpArgs += '--pins', $Pins }; if ($PerftPins) { $cmpArgs += '--perft-pins', $PerftPins } } else { $cmpArgs += '--off', "$Ident\off.plain.json" }
    $cmp = @(& $Python $Checker compare "$Ident\$($runSet.Name).plain.json" "$Ident\$($runSet.Name).ltopgo.json" @cmpArgs); $cmpRc = $LASTEXITCODE
    $cmp | Set-Content "$Ident\$($runSet.Name).compare.txt"; $cmp | ForEach-Object { Say "$_" }
    if ($cmpRc -ne 0) { $allOk = $false }
  }
  if (-not $allOk) { throw 'node identity MISMATCH' }
  Say "RESULT PASS  exe for GATE_EXE: $Tree\forge_ltopgo_$Tag.exe (binding: its sha256 must equal the other clean rebuild's, pc1 = pc2)"
  $SummaryRows.Add('node identity OFF' + $(if ($CheckOpt.Count) { " + $($CheckOpt.Count) option run(s)" } else { '' }) + ': ALL OK')
  $SummaryRows.Add('BINDING: forge_ltopgo exe sha256 must be equal for pc1 and pc2. gcda manifests and arcs manifest are record only.')
  $SummaryRows.Add("RESULT PASS $Tag"); Write-LfFile $SummaryFile $SummaryRows
} catch {
  $failMsg = "$($_.Exception.Message)"
  Set-Content (Join-Path $OutDir 'FAILED') "FAILED $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): $failMsg -- do not use any exe from this folder"
  Say "RESULT FAIL: $failMsg (FAILED marker written)"
  $SummaryRows.Add("RESULT FAIL $Tag`: $failMsg"); Write-LfFile $SummaryFile $SummaryRows
  exit 1
}
