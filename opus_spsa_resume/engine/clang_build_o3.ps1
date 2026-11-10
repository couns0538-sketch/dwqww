# opus3 derivation of QA's recipe 1fd87517 (gate0415\detached1735_all31\adapter\clang_build.ps1): only the CPU mask guard
# (0xF000 = CPUs 12-15) and the optional -ExtraDefines parameter differ; see RECIPE_INTERDIFF.patch.
# CRFIX v2: FRONTEND instrumentation PGO, not IR-PGO. Changed recipe; requires native review.
# c_t2_build.ps1 - job C: re-verify the OSS scout's T2 build (opus_oss_scout/tools/t2_build.ps1 at 715b8acf) on
# this job's own D: copy of trial_w6. Same compiler (llvm-mingw 20261104, clang 23.1.5) and the same flags token for
# originally as the scout's m2gen / m2use with -LibStdCxx (MSYS2 ucrt64 GCC 15.2 libstdc++ / libgcc / CRT), the six lock
# switches through -D (the source keeps them at 0), ThinLTO + IR PGO trained on QA's frozen workload v1 (bench
# 11 / 13 / 16 only, sha256 1d52720a...). Placement: CPUs 0-1 (0x3), Idle, set on itself first (children inherit).
# Refuses to overwrite its output folder. Writes only below -OutRoot (D:).
#   powershell -NoProfile -ExecutionPolicy Bypass -File c_t2_build.ps1 -Tag <new name> [-Src <tree>]
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [string]$Src = 'D:\sdk_jobs\sdk_longjob_20261106\src_w6',
    [string]$OutRoot = 'D:\sdk_jobs\sdk_longjob_20261106\c_t2',
    [string]$Workload = 'D:\sdk_jobs\sdk_longjob_20261106\kit_v23\workload\frozen_train_cmds.txt',
    [long]$Mask = 0xF000,
    [string]$ExtraDefines = ''   # opus3: 'NAME=VALUE;NAME=VALUE' appended as -D defines; empty = the original tokens
)
$ErrorActionPreference = 'Stop'
if ($Mask -le 0 -or ($Mask -band (-bnot 0xF000)) -ne 0) { throw 'mask must lie inside 0xF000 (CPUs 12-15; opus3 job rule)' }
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

$root = Join-Path $OutRoot $Tag
if (Test-Path $root) { throw "refusing: $root exists" }
New-Item -ItemType Directory -Path $root | Out-Null
$log = Join-Path $root 'build.log'
# Fail closed: receipt begins HOLD and becomes PASS only at the final statement.
$receiptPath = Join-Path $root 'RUN_RECEIPT.json'
$receipt = [ordered]@{status='HOLD'; label='clang23 ThinLTO + frontend instrumentation PGO';
    timezone='Europe/Vienna'; started_utc=[DateTime]::UtcNow.ToString('o');
    recipe_sha256=(Get-FileHash $PSCommandPath -Algorithm SHA256).Hash.ToLower(); compiler=$clang; compiler_sha256=(Get-FileHash $clang -Algorithm SHA256).Hash.ToLower();
    profdata_tool=$profdataTool; profdata_tool_sha256=(Get-FileHash $profdataTool -Algorithm SHA256).Hash.ToLower();
    workload_sha256=$wlSha; thinlto_jobs=1; source_manifest_sha256=$null;
    raw_profile_sha256=$null; merged_profile_sha256=$null; exe_sha256=$null;
    flags=$null; source=$null; training_nodes=$null; completed_utc=$null }
function Save-Receipt { $receipt | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $receiptPath }
Save-Receipt
trap { $receipt.status='HOLD'; Save-Receipt; throw $_ }
# Snapshot only compile inputs; never compile the caller's mutable source twice.
$inputSnapshot = Join-Path $root 'source_snapshot'
New-Item -ItemType Directory -Path $inputSnapshot | Out-Null
foreach ($part in 'include','src') {
    Copy-Item -Recurse -LiteralPath (Join-Path $Src $part) -Destination (Join-Path $inputSnapshot $part)
}
$Src = $inputSnapshot
function Source-Manifest {
    $rows = @(Get-ChildItem -LiteralPath $Src -Recurse -File | Sort-Object FullName | ForEach-Object {
        $rel = $_.FullName.Substring($Src.Length).TrimStart('\').Replace('\','/')
        (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower() + '  ' + $rel
    })
    return ($rows -join "`n")
}
$boundManifest = Source-Manifest
$sourceManifestPath = Join-Path $root 'SOURCE_INPUTS.sha256'
[IO.File]::WriteAllText($sourceManifestPath, $boundManifest + "`n", (New-Object Text.UTF8Encoding($false)))
$receipt.source_manifest_sha256=(Get-FileHash $sourceManifestPath -Algorithm SHA256).Hash.ToLower()
$receipt.source=$Src
Save-Receipt
function Assert-Binding {
    if ((Get-FileHash $PSCommandPath -Algorithm SHA256).Hash.ToLower() -ne $receipt.recipe_sha256) { throw 'HOLD: recipe changed' }
    if ((Source-Manifest) -cne $boundManifest) { throw 'HOLD: source inputs changed' }
    if ((Get-FileHash $Workload -Algorithm SHA256).Hash.ToLower() -ne $wlSha) { throw 'HOLD: workload changed' }
    if ((Get-FileHash $clang -Algorithm SHA256).Hash.ToLower() -ne $receipt.compiler_sha256) { throw 'HOLD: compiler changed' }
    if ((Get-FileHash $profdataTool -Algorithm SHA256).Hash.ToLower() -ne $receipt.profdata_tool_sha256) { throw 'HOLD: profdata tool changed' }
}
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
    $diagnostics = Get-Content (Join-Path $dir 'stderr.tmp') -Raw -ErrorAction SilentlyContinue
    if ($diagnostics -match '(?i)(profile[^\r\n]*(mismatch|out.of.date|unprofiled|missing|not found)|no profile data)') {
        throw 'HOLD: profile diagnostic; see raw build log'
    }
    Log ("exit " + $p.ExitCode + " in " + [Math]::Round(((Get-Date) - $t0).TotalSeconds, 1) + " s")
    if ($p.ExitCode -ne 0) { throw "$exe failed with exit $($p.ExitCode); see $log" }
}

$defs = @('-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-DFORGE_EXPOSE_TUNABLES=1',
    '-DFORGE_SPD_TT_NOTLS=1', '-DFORGE_SPD_NO_ZERO_MOVELISTS=2', '-DFORGE_SEARCH_SPEED2=1',
    '-DFORGE_SPD_PREFETCH_EARLY=1', '-DFORGE_SPD_SLIDER_PEXT=1', '-DFORGE_SPD_NNUE_ZMM=1') + @($ExtraDefines -split ';' | Where-Object { $_ } | ForEach-Object { '-D' + $_ })
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
    Run $clang ($common + @('-flto=thin') + $extra + @('-fuse-ld=lld', '-static') + $objs + @('-o', $exe, "-Wl,--pdb=$(Join-Path $dir "forge_$stage.pdb")", '-Wl,--no-insert-timestamp', '-Wl,--thinlto-jobs=1')) $dir
    Log ("built $exe sha256 " + (Get-FileHash $exe -Algorithm SHA256).Hash.ToLower())
    return $exe
}

# 1) instrumented ThinLTO build
Assert-Binding
$receipt.flags = [ordered]@{common=$common; compile=@('-flto=thin'); link=@('-fuse-ld=lld','-static','-Wl,--no-insert-timestamp','-Wl,--thinlto-jobs=1'); gen=@('-fprofile-instr-generate'); use_diagnostics=@('-Werror=profile-instr-unprofiled','-Werror=profile-instr-out-of-date')}
Save-Receipt
$gen = Build-Stage 'm2gen' @('-fprofile-instr-generate')
# 2) training on the frozen workload, raw stdin bytes (as the kit and the scout do)
Assert-Binding
$genDir = Split-Path $gen -Parent
Copy-Item -LiteralPath $Workload -Destination (Join-Path $genDir 'frozen_train_cmds.txt')
$env:LLVM_PROFILE_FILE = (Join-Path $genDir 'm2_%p.profraw')
# opus3: raw stdin bytes through cmd.exe redirection (cmd opens the file and hands the engine the raw handle).
# Start-Process -RedirectStandardInput and .NET Process.StandardInput re-encode the input when Windows PowerShell 5.1
# runs without a console: the stdin writer emits a UTF-8 BOM, so the engine's first line became "\xEF\xBB\xBFuci" and
# 'uci' was silently ignored (observed: training output had no uciok; profile short by the uci loop counts).
$wlPath = Join-Path $genDir 'frozen_train_cmds.txt'
$cmdArgs = '/d /s /c ""' + $gen + '" < "' + $wlPath + '" > "' + (Join-Path $genDir 'workload.out') + '" 2> "' + (Join-Path $genDir 'workload.err') + '""'
$psi = New-Object System.Diagnostics.ProcessStartInfo 'cmd.exe', $cmdArgs
$psi.UseShellExecute = $false; $psi.WorkingDirectory = $genDir
$p = [System.Diagnostics.Process]::Start($psi)
if (-not $p.WaitForExit(3600000)) { throw 'training timeout' }
$p.WaitForExit()
Remove-Item Env:\LLVM_PROFILE_FILE
if ($p.ExitCode -ne 0) { throw "training exit $($p.ExitCode)" }
$benches = @(Select-String -Path (Join-Path $genDir 'workload.out') -Pattern 'bench depth (\d+) nodes (\d+)')
Log ("training: " + (($benches | ForEach-Object { $_.Matches[0].Value }) -join '; '))
if ($benches.Count -ne 3) { throw "training gave $($benches.Count) bench lines" }
$wantNodes=@('312866','862329','3024920'); $wantDepth=@('11','13','16')
for ($i=0; $i -lt 3; $i++) {
    if ($benches[$i].Matches[0].Groups[1].Value -ne $wantDepth[$i] -or $benches[$i].Matches[0].Groups[2].Value -ne $wantNodes[$i]) { throw 'HOLD: training pins mismatch' }
}
$receipt.training_nodes=$wantNodes
$raws = @(Get-ChildItem $genDir -Filter 'm2_*.profraw')
if ($raws.Count -ne 1) { throw "expected one profraw, found $($raws.Count)" }
if ($raws[0].Length -le 0) { throw 'HOLD: empty raw profile' }
$receipt.raw_profile_sha256=(Get-FileHash $raws[0].FullName -Algorithm SHA256).Hash.ToLower()
Save-Receipt
$profdata = Join-Path $genDir 'm2.profdata' 
Run $profdataTool @('merge', '-o', $profdata, $raws[0].FullName) $genDir
Log ("profdata sha256 " + (Get-FileHash $profdata -Algorithm SHA256).Hash.ToLower())
if ((Get-Item $profdata).Length -le 0) { throw 'HOLD: empty merged profile' }
$receipt.merged_profile_sha256=(Get-FileHash $profdata -Algorithm SHA256).Hash.ToLower()
$receipt.flags['use']=@("-fprofile-instr-use=$profdata", '-Werror=profile-instr-unprofiled', '-Werror=profile-instr-out-of-date')
Save-Receipt
Assert-Binding
# 3) the optimised build
$use = Build-Stage 'm2use' @("-fprofile-instr-use=$profdata", '-Werror=profile-instr-unprofiled', '-Werror=profile-instr-out-of-date')
Assert-Binding
if ((Get-FileHash $profdata -Algorithm SHA256).Hash.ToLower() -ne $receipt.merged_profile_sha256) { throw 'HOLD: profile changed' }
$receipt.exe_sha256=(Get-FileHash $use -Algorithm SHA256).Hash.ToLower()
$receipt.completed_utc=[DateTime]::UtcNow.ToString('o')
$receipt.status='BUILD_PASS_NATIVE_BENCH_PENDING'
Save-Receipt
Log ("RESULT exe $use")
Log ("end " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
