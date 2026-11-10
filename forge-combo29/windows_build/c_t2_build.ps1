# c_t2_build.ps1 - job C: re-verify the OSS scout's T2 build (opus_oss_scout/tools/t2_build.ps1 at 715b8acf) on
# this job's own D: copy of trial_w6. Same compiler (llvm-mingw 20261104, clang 23.1.5) and the same flags token for
# token as the scout's m2gen / m2use with -LibStdCxx (MSYS2 ucrt64 GCC 15.2 libstdc++ / libgcc / CRT), the six lock
# switches through -D (the source keeps them at 0), ThinLTO + IR PGO trained on QA's frozen workload v1 (bench
# 11 / 13 / 16 only, sha256 1d52720a...). Placement: CPUs 0-1 (0x3), Idle, set on itself first (children inherit).
# Refuses to overwrite its output folder. Writes only below -OutRoot (D:).
#   powershell -NoProfile -ExecutionPolicy Bypass -File c_t2_build.ps1 -Tag <new name> [-Src <tree>]
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [string]$Src = 'D:\sdk_jobs\sdk_longjob_20261106\src_w6',
    [string]$OutRoot = 'D:\sdk_jobs\sdk_longjob_20261106\c_t2',
    [string]$Workload = 'D:\sdk_jobs\sdk_longjob_20261106\kit_v23\workload\frozen_train_cmds.txt',
    [long]$Mask = 0x3
)
$ErrorActionPreference = 'Stop'
if ($Mask -le 0 -or ($Mask -band (-bnot 0xF)) -ne 0) { throw 'mask must lie inside 0xF (CPUs 0-3)' }
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask; $me.Refresh()
if ([long]$me.ProcessorAffinity -ne $Mask -or "$($me.PriorityClass)" -ne 'Idle') { throw 'placement not applied' }
$lm = 'C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin'   # read only
$clang = Join-Path $lm 'clang++.exe'
$profdataTool = Join-Path $lm 'llvm-profdata.exe'
if (-not (Test-Path $clang) -or -not (Test-Path $profdataTool)) { throw "llvm-mingw not found at $lm" }
$env:PATH = $lm + ';' + $env:PATH   # process-local
$wlSha = (Get-FileHash -Algorithm SHA256 $Workload).Hash.ToLower()
if ($wlSha -ne '1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30') { throw "workload sha256 $wlSha" }
foreach ($d in 'C', 'D') { if ((Get-PSDrive $d).Free / 1GB -lt 31) { throw "$d`: below 31 GB free" } }
$root = Join-Path $OutRoot $Tag
if (Test-Path $root) { throw "refusing: $root exists" }
New-Item -ItemType Directory -Path $root | Out-Null
$log = Join-Path $root 'build.log'
function Log([string]$s) { [System.IO.File]::AppendAllText($log, $s + "`n"); [Console]::Out.WriteLine($s) }

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
    '-DFORGE_SPD_PREFETCH_EARLY=1', '-DFORGE_SPD_SLIDER_PEXT=1', '-DFORGE_SPD_NNUE_ZMM=1')
$units = @(Get-ChildItem (Join-Path $Src 'src') -Filter *.cpp | Sort-Object Name | ForEach-Object { $_.FullName })
$inc = '-I' + (Join-Path $Src 'include')
$common = @('-std=c++20', '-O3') + $defs + @('-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-pthread',
    '-g', '-gcodeview', $inc, '--sysroot=C:/msys64/ucrt64', '-stdlib=libstdc++', '-rtlib=libgcc', '-unwindlib=libgcc')
$ver = (& $clang --version | Select-Object -First 1)
Log ("c_t2_build tag=$Tag src=$Src start " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " units=" + $units.Count + "; $ver")

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
    Run $clang ($common + @('-flto=thin') + $extra + @('-fuse-ld=lld', '-static') + $objs + @('-o', $exe, "-Wl,--pdb=$(Join-Path $dir "forge_$stage.pdb")", '-Wl,--no-insert-timestamp')) $dir
    Log ("built $exe sha256 " + (Get-FileHash $exe -Algorithm SHA256).Hash.ToLower())
    return $exe
}

# 1) instrumented ThinLTO build
$gen = Build-Stage 'm2gen' @('-fprofile-instr-generate')
# 2) training on the frozen workload, raw stdin bytes (as the kit and the scout do)
$genDir = Split-Path $gen -Parent
Copy-Item -LiteralPath $Workload -Destination (Join-Path $genDir 'frozen_train_cmds.txt')
$env:LLVM_PROFILE_FILE = (Join-Path $genDir 'm2_%p.profraw')
$p = Start-Process -FilePath $gen -RedirectStandardInput (Join-Path $genDir 'frozen_train_cmds.txt') `
    -RedirectStandardOutput (Join-Path $genDir 'workload.out') -RedirectStandardError (Join-Path $genDir 'workload.err') -NoNewWindow -PassThru -WorkingDirectory $genDir
$null = $p.Handle
if (-not $p.WaitForExit(3600000)) { throw 'training timeout' }
$p.WaitForExit()
Remove-Item Env:\LLVM_PROFILE_FILE
if ($p.ExitCode -ne 0) { throw "training exit $($p.ExitCode)" }
$benches = @(Select-String -Path (Join-Path $genDir 'workload.out') -Pattern 'bench depth (\d+) nodes (\d+)')
Log ("training: " + (($benches | ForEach-Object { $_.Matches[0].Value }) -join '; '))
if ($benches.Count -ne 3) { throw "training gave $($benches.Count) bench lines" }
$raws = @(Get-ChildItem $genDir -Filter 'm2_*.profraw')
if ($raws.Count -ne 1) { throw "expected one profraw, found $($raws.Count)" }
$profdata = Join-Path $genDir 'm2.profdata'
Run $profdataTool @('merge', '-o', $profdata, $raws[0].FullName) $genDir
Log ("profdata sha256 " + (Get-FileHash $profdata -Algorithm SHA256).Hash.ToLower())
# 3) the optimised build
$use = Build-Stage 'm2use' @("-fprofile-instr-use=$profdata", '-Wno-profile-instr-unprofiled', '-Wno-profile-instr-out-of-date')
Log ("RESULT exe $use")
Log ("end " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
