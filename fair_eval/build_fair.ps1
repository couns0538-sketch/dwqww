# build_fair.ps1 - JOB D (own code, 2026-11-11): one evaluation path = one profile = one exe.
#
#   pwsh -NoProfile -File fair_eval\build_fair.ps1 -Config <id> [-Diag] [-WorkRoot <dir>] [-Jobs <n>]
#
# For the configuration <id> of fair_eval\configs.json this script
#   1. builds an instrumented exe (clang ThinLTO, -fprofile-instr-generate) with the lock's compiler and flags,
#   2. trains it on the lock's frozen benches (bench 11 / 13 / 16) WITH THAT CONFIGURATION'S EVALUATION PATH ON,
#   3. proves from the merged profile which evaluator functions ran (tools\profile_coverage.py),
#   4. rebuilds with -fprofile-instr-use from that profile only, and re-runs the workload on the result.
# The flags are the lock's (forge-combo29\windows_build\build.log) token for token; what differs per configuration
# is the -D list, the net and the setoption lines of the workload.
#
# Profile identity: sha256 over source files, defines, flags, compiler, workload text and net. The work folder is
# <WorkRoot>\<config>[_diag]_<identity 12 hex>, so a profile can only ever be used by the build that recorded it.
# A finished folder (RECEIPT.json present) is reported and left alone; an unfinished one is refused.
# -Diag adds -DFORGE_FAIR_DIAG=1 (commands evalfens / evalbench): a twin for evaluation dumps, never timed.
param(
    [Parameter(Mandatory = $true)][string]$Config,
    [switch]$Diag,
    [string]$WorkRoot = '',
    [int]$Jobs = 0
)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Split-Path -Parent $here
$src = Join-Path $repo 'forge-combo29'
if (-not $WorkRoot) { $WorkRoot = Join-Path $repo '_work\builds' }
if ($Jobs -le 0) { $Jobs = [Environment]::ProcessorCount }
$cfgAll = Get-Content (Join-Path $here 'configs.json') -Raw | ConvertFrom-Json
$cfg = $cfgAll.configs.$Config
if (-not $cfg) { throw "unknown config '$Config'" }
$lm = $cfgAll.compiler_bin
$clang = Join-Path $lm 'clang++.exe'
$profdataTool = Join-Path $lm 'llvm-profdata.exe'
foreach ($t in $clang, $profdataTool) { if (-not (Test-Path $t)) { throw "missing tool $t" } }
$env:PATH = $lm + ';' + $env:PATH   # process-local
function Sha256([string]$path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLower() }
function Sha256Text([string]$text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    -join ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($text)) | ForEach-Object { $_.ToString('x2') })
}

# ---- net
$netPath = ''; $netSha = ''
if ($cfg.net) {
    $net = $cfgAll.nets.($cfg.net)
    $netPath = Join-Path $repo ('_work\nets\' + $net.file)
    if (-not (Test-Path $netPath)) { throw "net file missing: $netPath" }
    $netSha = Sha256 $netPath
    if (-not $net.sha256) { throw "configs.json has no sha256 for net '$($cfg.net)'" }
    if ($netSha -ne $net.sha256) { throw "net $($cfg.net) sha256 $netSha, expected $($net.sha256)" }
}

# ---- flags (the lock's) and defines
$defs = @($cfgAll.lock_defines) + @($cfg.defines)
if ($Diag) { $defs += '-DFORGE_FAIR_DIAG=1' }
$inc = '-I' + (Join-Path $src 'include')
$common = @('-std=c++20', '-O3') + $defs + @('-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-pthread',
    '-g', '-gcodeview', $inc, "--sysroot=$($cfgAll.sysroot)", '-stdlib=libstdc++', '-rtlib=libgcc', '-unwindlib=libgcc')
# The lock's eight units; a unit listed in configs.json "optional_units" is compiled only for a configuration that
# names it in "extra_units" (it is empty behind its switch otherwise, and stays out of the lock-equivalent builds).
$units = @(Get-ChildItem (Join-Path $src 'src') -Filter *.cpp | Sort-Object Name |
    Where-Object { (@($cfgAll.optional_units) -notcontains $_.Name) -or (@($cfg.extra_units) -contains $_.Name) })

# ---- workload text (LF): the frozen v1 commands with this configuration's setoption lines before the benches
$setopts = @($cfg.train_setoptions | ForEach-Object { $_.Replace('{NET}', $netPath) })
$lines = @('uci', 'isready') + $setopts + @($cfgAll.train_benches | ForEach-Object { "bench $_" }) + @('isready', 'quit')
$workloadText = ($lines -join "`n") + "`n"
$workloadSha = Sha256Text $workloadText
if ($setopts.Count -eq 0 -and $workloadSha -ne $cfgAll.frozen_v1_sha256) { throw "workload without options is not the frozen v1 ($workloadSha)" }

# ---- identity
$manifest = @(Get-ChildItem (Join-Path $src 'src'), (Join-Path $src 'include\forge') -File | Sort-Object FullName |
    ForEach-Object { (Sha256 $_.FullName) + '  ' + $_.FullName.Substring($src.Length + 1).Replace('\', '/') })
$manifestSha = Sha256Text ($manifest -join "`n")
$compilerSha = Sha256 $clang
$idText = @($manifestSha, ($defs -join ' '), (($common | Where-Object { $_ -ne $inc }) -join ' '), $compilerSha,
    (Sha256 $profdataTool), $workloadSha, $netSha) -join '|'
$identity = Sha256Text $idText
$tag = $Config + $(if ($Diag) { '_diag' } else { '' })
$root = Join-Path $WorkRoot ($tag + '_' + $identity.Substring(0, 12))
if (Test-Path (Join-Path $root 'RECEIPT.json')) { Write-Output "ALREADY BUILT $root"; exit 0 }
if (Test-Path $root) { throw "refusing: $root exists without a receipt (unfinished build). Remove it or use another -WorkRoot." }
New-Item -ItemType Directory -Path $root -Force | Out-Null
$log = Join-Path $root 'build.log'
function Log([string]$s) { [System.IO.File]::AppendAllText($log, $s + "`n"); [Console]::Out.WriteLine($s) }
$ver = (& $clang --version | Select-Object -First 1)
$t00 = Get-Date
Log "build_fair config=$tag identity=$identity start $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') jobs=$Jobs; $ver"
Log "defines: $($defs -join ' ')"
[System.IO.File]::WriteAllText((Join-Path $root 'workload.txt'), $workloadText)
[System.IO.File]::WriteAllText((Join-Path $root 'source_manifest.sha256'), ($manifest -join "`n") + "`n")

function Start-Tool([string]$exe, [string[]]$argv, [string]$outBase) {
    [System.IO.File]::AppendAllText($log, "CMD: `"$exe`" " + ($argv -join ' ') + "`n")
    Start-Process -FilePath $exe -ArgumentList $argv -NoNewWindow -PassThru `
        -RedirectStandardOutput "$outBase.out" -RedirectStandardError "$outBase.err"
}
function Finish-Tool($proc, [string]$outBase, [string]$what) {
    $null = $proc.Handle
    $proc.WaitForExit()
    foreach ($f in "$outBase.out", "$outBase.err") {
        $t = Get-Content $f -Raw -ErrorAction SilentlyContinue
        if ($t) { [System.IO.File]::AppendAllText($log, $t) }
        Remove-Item $f -ErrorAction SilentlyContinue
    }
    if ($proc.ExitCode -ne 0) { throw "$what failed with exit $($proc.ExitCode); see $log" }
}
function Build-Stage([string]$stage, [string[]]$extra) {
    $dir = Join-Path $root $stage
    New-Item -ItemType Directory -Path $dir, (Join-Path $dir 'obj') | Out-Null
    $objs = @(); $running = @()
    foreach ($u in $units) {
        $o = Join-Path $dir ('obj\' + $u.BaseName + '.o')
        $objs += $o
        while (@($running | Where-Object { -not $_.p.HasExited }).Count -ge $Jobs) { Start-Sleep -Milliseconds 50 }
        $base = Join-Path $dir ('cc_' + $u.BaseName)
        $running += @{ p = (Start-Tool $clang ($common + @('-flto=thin') + $extra + @('-c', $u.FullName, '-o', $o)) $base); b = $base; n = $u.Name }
    }
    foreach ($r in $running) { Finish-Tool $r.p $r.b "compile $($r.n) ($stage)" }
    $exe = Join-Path $dir "forge_$stage.exe"
    $base = Join-Path $dir 'link'
    $p = Start-Tool $clang ($common + @('-flto=thin') + $extra + @('-fuse-ld=lld', '-static') + $objs +
        @('-o', $exe, "-Wl,--pdb=$(Join-Path $dir "forge_$stage.pdb")", '-Wl,--no-insert-timestamp', '-Wl,--thinlto-jobs=1')) $base
    Finish-Tool $p $base "link ($stage)"
    Log ("built $exe sha256 " + (Sha256 $exe))
    return $exe
}
function Run-Workload([string]$exe, [string]$outFile) {
    $dir = Split-Path $exe -Parent
    $p = Start-Process -FilePath $exe -RedirectStandardInput (Join-Path $root 'workload.txt') -RedirectStandardOutput $outFile `
        -RedirectStandardError "$outFile.err" -NoNewWindow -PassThru -WorkingDirectory $dir
    $null = $p.Handle
    if (-not $p.WaitForExit(3600000)) { throw 'workload timeout' }
    $p.WaitForExit()
    if ($p.ExitCode -ne 0) { throw "workload exit $($p.ExitCode) for $exe" }
    $nodes = @(Select-String -Path $outFile -Pattern 'bench depth (\d+) nodes (\d+)' | ForEach-Object { [long]$_.Matches[0].Groups[2].Value })
    if ($nodes.Count -ne @($cfgAll.train_benches).Count) { throw "workload gave $($nodes.Count) bench lines" }
    if ($setopts.Count -gt 0 -and $cfg.net -and -not (Select-String -Path $outFile -Pattern 'info string EvalFile\w+ loaded' -Quiet)) { throw 'the net file was not loaded during the workload' }
    if (Select-String -Path $outFile -Pattern 'ERROR|invalid value' -Quiet) { throw "the workload output reports an error, see $outFile" }
    return $nodes
}

# 1) instrumented build
$gen = Build-Stage 'gen' @('-fprofile-instr-generate')
$genDir = Split-Path $gen -Parent
# 2) training with this configuration's evaluation path
$env:LLVM_PROFILE_FILE = (Join-Path $genDir 'prof_%p.profraw')
$trainNodes = Run-Workload $gen (Join-Path $genDir 'workload.out')
Remove-Item Env:\LLVM_PROFILE_FILE
Log ("training nodes: " + ($trainNodes -join ' / '))
$expect = @($cfg.expect_nodes)
if ($expect.Count -gt 0 -and (($trainNodes -join ',') -ne ($expect -join ','))) { throw "training nodes differ from the expected $($expect -join ' / ')" }
$raws = @(Get-ChildItem $genDir -Filter 'prof_*.profraw')
if ($raws.Count -ne 1) { throw "expected one profraw, found $($raws.Count)" }
$profdata = Join-Path $genDir 'profile.profdata'
$p = Start-Tool $profdataTool @('merge', '-o', $profdata, $raws[0].FullName) (Join-Path $genDir 'merge')
Finish-Tool $p (Join-Path $genDir 'merge') 'llvm-profdata merge'
$profSha = Sha256 $profdata
Log "profdata sha256 $profSha"
# 3) coverage proof from the profile
$covJson = Join-Path $root 'coverage.json'
$covArgs = @((Join-Path $here 'tools\profile_coverage.py'), '--profdata', $profdata, '--tool-dir', $lm, '--out', $covJson)
if (@($cfg.must_run).Count) { $covArgs += '--must-run'; $covArgs += @($cfg.must_run) }
if (@($cfg.must_be_zero).Count) { $covArgs += '--must-be-zero'; $covArgs += @($cfg.must_be_zero) }
$covArgs += @('--report', 'Worker::static_evaluate\(', 'Evaluator::evaluate_runtime\(')
$covOut = & python @covArgs 2>&1
$covRc = $LASTEXITCODE
$covOut | ForEach-Object { Log "coverage: $_" }
if ($covRc -ne 0) { throw "profile coverage check failed (exit $covRc): the intended evaluator did not run, or a forbidden one did" }
# 4) optimised build from this profile only (the lock's use-stage flags)
$use = Build-Stage 'use' @("-fprofile-instr-use=$profdata", '-Werror=profile-instr-unprofiled', '-Werror=profile-instr-out-of-date')
$useNodes = Run-Workload $use (Join-Path (Split-Path $use -Parent) 'workload.out')
Log ("final exe nodes on the training workload: " + ($useNodes -join ' / '))
if (($useNodes -join ',') -ne ($trainNodes -join ',')) { throw 'final exe nodes differ from the instrumented exe' }
$final = Join-Path $root "forge_fair_$tag.exe"
Copy-Item -LiteralPath $use -Destination $final
$receipt = [ordered]@{
    config = $tag; path = $cfg.path; identity = $identity; built = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    seconds = [Math]::Round(((Get-Date) - $t00).TotalSeconds, 1)
    source_commit = (& git -C $repo rev-parse HEAD); source_dirty = [bool](& git -C $repo status --porcelain -- forge-combo29)
    source_manifest_sha256 = $manifestSha
    compiler = $clang; compiler_version = "$ver"; compiler_sha256 = $compilerSha
    defines = $defs; common_flags = ($common | Where-Object { $_ -ne $inc })
    stage_flags = [ordered]@{ gen = '-flto=thin -fprofile-instr-generate'; use = '-flto=thin -fprofile-instr-use=<this profile> -Werror=profile-instr-unprofiled -Werror=profile-instr-out-of-date'; link = '-fuse-ld=lld -static -Wl,--no-insert-timestamp -Wl,--thinlto-jobs=1' }
    net = $cfg.net; net_path = $netPath; net_sha256 = $netSha
    workload_sha256 = $workloadSha; workload = $lines
    training_nodes = $trainNodes; final_exe_nodes = $useNodes
    profdata_sha256 = $profSha; coverage = (Get-Content $covJson -Raw | ConvertFrom-Json)
    exe = $final; exe_bytes = (Get-Item $final).Length; exe_sha256 = (Sha256 $final)
    exe_md5 = (Get-FileHash -Algorithm MD5 -LiteralPath $final).Hash.ToLower()
    run_setoptions = @($cfg.run_setoptions | ForEach-Object { $_.Replace('{NET}', $netPath) })
}
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'RECEIPT.json') -Encoding utf8
Log "RESULT $final md5 $($receipt.exe_md5) in $($receipt.seconds) s"
