# spd_build.ps1 - the combo29 lock recipe for one source tree (PowerShell 5.1, ASCII only).
#
# Compiler, flags and their order are taken token for token from the lock's own build log
# (D:\forge-qa\pack_combo29_20261108\pc_payload\build\build.log): llvm-mingw 20261104 clang 23.1.5, MSYS2 ucrt64
# libstdc++ sysroot, the six lock switches through -D, ThinLTO + frontend-instrumentation PGO trained on QA's frozen
# workload (bench 11 / 13 / 16, sha256 1d52720a...), -g -gcodeview with a PDB, --no-insert-timestamp, --thinlto-jobs=1.
# Only the paths differ, plus -ExtraDefs (appended right after the six lock switches, as QA's c_t2_build_extradefs.ps1
# does) and -LinkExtra (appended to the link line; empty for every normal build).
# Placement: this script pins itself to mask 0x78 (or a subset) at Idle first; every child inherits both.
# Refuses to overwrite its output folder. Writes only below -OutRoot (D:). Reads the compiler and sysroot on C:.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File spd_build.ps1 -Tag <new name> -Src <tree>
#                  [-ExtraDefs FORGE_SPD_X=1,FORGE_SPD_Y=1] [-OutRoot <dir>] [-Mask 0x78] [-GenOnly]
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][string]$Src,
    [string]$OutRoot = 'D:\forge_jobs_20261109\fable2\out\build',
    [string]$Workload = 'D:\forge_jobs_20261109\fable2\out\base\frozen_train_cmds.txt',
    [string[]]$ExtraDefs = @(),
    [string[]]$LinkExtra = @(),
    [long]$Mask = 0x78,
    [double]$MinFreeGiB = 30.3,
    [switch]$GenOnly
)
$ErrorActionPreference = 'Stop'
$Lane = 0x78
if ($Mask -le 0 -or ($Mask -band (-bnot $Lane)) -ne 0) { throw 'mask must lie inside 0x78 (CPUs 3-6)' }
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask; $me.Refresh()
if ([long]$me.ProcessorAffinity -ne $Mask -or "$($me.PriorityClass)" -ne 'Idle') { throw 'placement not applied' }
# -File passes a list as ONE comma-joined string: split every list parameter on commas
$ExtraDefs = @($ExtraDefs | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$LinkExtra = @($LinkExtra | ForEach-Object { $_ -split ';' } | Where-Object { $_ })

$JobRoot = 'D:\forge_jobs_20261109\fable2'
$env:TEMP = Join-Path $JobRoot 'out\tmp'; $env:TMP = $env:TEMP
$lm = 'C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin'   # read only
$clang = Join-Path $lm 'clang++.exe'
$profdataTool = Join-Path $lm 'llvm-profdata.exe'
if (-not (Test-Path $clang) -or -not (Test-Path $profdataTool)) { throw "llvm-mingw not found at $lm" }
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }
$clangSha = Sha $clang
if ($clangSha -ne 'd05fee2c3f79b15d998d3c3413c76aabd416ec789edff89c8f698a8be44a3970') { throw "compiler sha256 $clangSha is not the lock receipt's" }
$pdSha = Sha $profdataTool
if ($pdSha -ne '55bfe8da39b548fb8b03736218c669aaec5234a14d964d4da323d7d4103b5e32') { throw "llvm-profdata sha256 $pdSha is not the lock receipt's" }
$env:PATH = $lm + ';' + $env:PATH   # process-local
$wlSha = Sha $Workload
if ($wlSha -ne '1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30') { throw "workload sha256 $wlSha" }
if ((Get-PSDrive D).Free / 1GB -lt $MinFreeGiB) { throw ('D: below {0} GiB free' -f $MinFreeGiB) }
$Src = (Resolve-Path -LiteralPath $Src).Path.TrimEnd('\')
$root = Join-Path $OutRoot $Tag
if (Test-Path $root) { throw "refusing: $root exists" }
New-Item -ItemType Directory -Path $root | Out-Null
$log = Join-Path $root 'build.log'
function NowV { [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'W. Europe Standard Time').ToString('yyyy-MM-dd HH:mm:ss') + ' Vienna' }
function Log([string]$s) { [System.IO.File]::AppendAllText($log, $s + "`n"); [Console]::Out.WriteLine($s) }

# Source manifest in QA's format (sha256, two spaces, forward-slash path, LF, ordinal order): the untouched combo29
# snapshot gives a manifest whose own sha256 is 3389cfe3... (RUN_RECEIPT.source_manifest_sha256 of the lock).
$files = @(Get-ChildItem -LiteralPath (Join-Path $Src 'include') -Recurse -File) + @(Get-ChildItem -LiteralPath (Join-Path $Src 'src') -Recurse -File)
$rels = New-Object 'System.Collections.Generic.List[string]'
foreach ($f in $files) { $rels.Add($f.FullName.Substring($Src.Length + 1).Replace('\', '/')) }
$relArr = $rels.ToArray(); [Array]::Sort($relArr, [StringComparer]::Ordinal)
$sb = New-Object System.Text.StringBuilder
foreach ($r in $relArr) { [void]$sb.Append((Sha (Join-Path $Src $r.Replace('/', '\'))) + '  ' + $r + "`n") }
$manifestPath = Join-Path $root 'SOURCE_INPUTS.sha256'
[System.IO.File]::WriteAllText($manifestPath, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
$manifestSha = Sha $manifestPath

function Run([string]$exe, [string[]]$argv, [string]$dir) {
    Log ("CMD: `"$exe`" " + ($argv -join ' '))
    $t0 = Get-Date
    $p = Start-Process -FilePath $exe -ArgumentList $argv -NoNewWindow -Wait -PassThru `
        -RedirectStandardOutput (Join-Path $dir 'stdout.tmp') -RedirectStandardError (Join-Path $dir 'stderr.tmp')
    foreach ($f in 'stdout.tmp', 'stderr.tmp') {
        $t = Get-Content (Join-Path $dir $f) -Raw -ErrorAction SilentlyContinue
        if ($t) { [System.IO.File]::AppendAllText($log, $t) }
    }
    Log ("exit " + $p.ExitCode + " in " + [Math]::Round(((Get-Date) - $t0).TotalSeconds, 1) + " s")
    if ($p.ExitCode -ne 0) { throw "$exe failed with exit $($p.ExitCode); see $log" }
}

$defs = @('-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-DFORGE_EXPOSE_TUNABLES=1',
    '-DFORGE_SPD_TT_NOTLS=1', '-DFORGE_SPD_NO_ZERO_MOVELISTS=2', '-DFORGE_SEARCH_SPEED2=1',
    '-DFORGE_SPD_PREFETCH_EARLY=1', '-DFORGE_SPD_SLIDER_PEXT=1', '-DFORGE_SPD_NNUE_ZMM=1') + @($ExtraDefs | ForEach-Object { '-D' + $_ })
$units = @(Get-ChildItem (Join-Path $Src 'src') -Filter *.cpp | Sort-Object Name | ForEach-Object { $_.FullName })
$want = 'bitboard', 'board', 'book', 'eval', 'eval_params', 'nnue', 'search', 'uci'
$got = @($units | ForEach-Object { [IO.Path]::GetFileNameWithoutExtension($_) })
if (($got -join ',') -ne ($want -join ',')) { throw "unit list or order differs from the lock: $($got -join ',')" }
$inc = '-I' + (Join-Path $Src 'include')
$common = @('-std=c++20', '-O3') + $defs + @('-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-pthread',
    '-g', '-gcodeview', $inc, '--sysroot=C:/msys64/ucrt64', '-stdlib=libstdc++', '-rtlib=libgcc', '-unwindlib=libgcc')
$ver = (& $clang --version | Select-Object -First 1)
Log ("spd_build tag=$Tag src=$Src start " + (NowV) + " units=" + $units.Count + "; $ver; mask 0x$('{0:X}' -f $Mask) Idle")
Log ("extra defs: [" + ($ExtraDefs -join ' ') + "]; link extra: [" + ($LinkExtra -join ' ') + "]; source manifest sha256 $manifestSha")

function Build-Stage([string]$stage, [string[]]$extra) {
    $dir = Join-Path $root $stage
    New-Item -ItemType Directory -Path $dir, (Join-Path $dir 'obj') | Out-Null
    $objs = @()
    foreach ($u in $units) {
        $o = Join-Path $dir ('obj\' + [IO.Path]::GetFileNameWithoutExtension($u) + '.o')
        Run $clang ($common + @('-flto=thin') + $extra + @('-c', $u, '-o', $o)) $dir
        $objs += $o
    }
    $exe = Join-Path $dir "forge_$stage.exe"
    Run $clang ($common + @('-flto=thin') + $extra + @('-fuse-ld=lld', '-static') + $objs + @('-o', $exe, "-Wl,--pdb=$(Join-Path $dir "forge_$stage.pdb")", '-Wl,--no-insert-timestamp', '-Wl,--thinlto-jobs=1') + $LinkExtra) $dir
    Log ("built $exe sha256 " + (Sha $exe))
    return $exe
}

# 1) instrumented ThinLTO build
$gen = Build-Stage 'm2gen' @('-fprofile-instr-generate')
# 2) training on the frozen workload, raw stdin bytes
$genDir = Split-Path $gen -Parent
Copy-Item -LiteralPath $Workload -Destination (Join-Path $genDir 'frozen_train_cmds.txt')
$env:LLVM_PROFILE_FILE = (Join-Path $genDir 'm2_%p.profraw')
# Redirection through cmd.exe: the workload file reaches the engine's stdin byte for byte. (Start-Process
# -RedirectStandardInput handed the engine an empty stdin when this script ran under a console-less host:
# 0 bench lines, seen 2026-11-10 08:13 Vienna.)
$trainCmd = Join-Path $genDir 'train.cmd'
[System.IO.File]::WriteAllText($trainCmd, "@echo off`r`n`"$gen`" < `"$(Join-Path $genDir 'frozen_train_cmds.txt')`" > `"$(Join-Path $genDir 'workload.out')`" 2> `"$(Join-Path $genDir 'workload.err')`"`r`nexit /b %ERRORLEVEL%`r`n", [System.Text.Encoding]::ASCII)
Push-Location $genDir
try { & $env:ComSpec /d /c $trainCmd; $trainExit = $LASTEXITCODE } finally { Pop-Location }
Remove-Item Env:\LLVM_PROFILE_FILE
if ($trainExit -ne 0) { throw "training exit $trainExit" }
$benches = @(Select-String -Path (Join-Path $genDir 'workload.out') -Pattern 'bench depth (\d+) nodes (\d+)')
$trainNodes = @($benches | ForEach-Object { $_.Matches[0].Groups[2].Value })
Log ("training: " + (($benches | ForEach-Object { $_.Matches[0].Value }) -join '; '))
if ($benches.Count -ne 3) { throw "training gave $($benches.Count) bench lines" }
if (($trainNodes -join ',') -ne '312866,862329,3024920') { throw "training nodes $($trainNodes -join ',') are not the lock pins (search changed?)" }
$raws = @(Get-ChildItem $genDir -Filter 'm2_*.profraw')
if ($raws.Count -ne 1) { throw "expected one profraw, found $($raws.Count)" }
$profdata = Join-Path $genDir 'm2.profdata'
Run $profdataTool @('merge', '-o', $profdata, $raws[0].FullName) $genDir
$rawSha = Sha $raws[0].FullName
$mergedSha = Sha $profdata
Log ("profraw sha256 $rawSha; profdata sha256 $mergedSha")
$useExe = $null
if (-not $GenOnly) {
    # 3) the optimised build
    $useExe = Build-Stage 'm2use' @("-fprofile-instr-use=$profdata", '-Werror=profile-instr-unprofiled', '-Werror=profile-instr-out-of-date')
    Log ("RESULT exe $useExe")
}
$receipt = [ordered]@{
    tag = $Tag; src = $Src; started = $null; finished = (NowV)
    recipe = 'combo29 lock build.log command lines; paths differ'
    compiler = $clang; compiler_sha256 = $clangSha; compiler_version = "$ver"
    profdata_tool_sha256 = $pdSha; workload_sha256 = $wlSha
    extra_defs = @($ExtraDefs); link_extra = @($LinkExtra)
    source_manifest_sha256 = $manifestSha
    training_nodes = @($trainNodes)
    raw_profile_sha256 = $rawSha; merged_profile_sha256 = $mergedSha
    gen_exe = $gen; gen_exe_sha256 = (Sha $gen)
    exe = $useExe; exe_sha256 = $(if ($useExe) { Sha $useExe } else { $null })
    exe_md5 = $(if ($useExe) { (Get-FileHash -Algorithm MD5 -LiteralPath $useExe).Hash.ToLower() } else { $null })
    mask = ('0x{0:X}' -f $Mask); priority = 'Idle'
}
($receipt | ConvertTo-Json -Depth 4) | Set-Content -Encoding ASCII (Join-Path $root 'RUN_RECEIPT.json')
Log ("end " + (NowV))
