# build.ps1 - the combo29 lock recipe for one source tree (PowerShell 5.1, ASCII only).
#
# Compiler, flags and their order follow the lock's own build log
# (D:\forge-qa\pack_combo29_20261108\pc_payload\build\build.log) as carried by my job-3 script spd_build.ps1:
# llvm-mingw 20261104 clang 23.1.5, MSYS2 ucrt64 libstdc++ sysroot, the lock switches through -D, ThinLTO plus
# frontend-instrumentation PGO trained on the frozen workload (bench 11 / 13 / 16), -g -gcodeview with a PDB,
# --no-insert-timestamp, --thinlto-jobs=1. Differences from the lock run: paths; the 8 unit compiles of a stage run
# side by side (same command per unit); -ExtraDefs are appended after the lock switches.
# Placement: this script pins itself to -Mask (inside 0x707F) at BelowNormal first; every child inherits both.
# Refuses to overwrite its output folder. Writes only below -OutRoot. Deletes nothing.
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][string]$Src,
    [string]$OutRoot = 'D:\forge_jobs_20261110\fable4cpu\out\build',
    [string]$Workload = 'D:\forge_jobs_20261110\fable4cpu\out\base\frozen_train_cmds.txt',
    [string[]]$ExtraDefs = @(),
    [long]$Mask = 0x707F,
    [int]$Jobs = 8,
    [double]$MinFreeGiB = 31.1,
    [switch]$GenOnly
)
$ErrorActionPreference = 'Stop'
$env:PSModulePath = "$env:ProgramFiles\WindowsPowerShell\Modules;$env:WINDIR\system32\WindowsPowerShell\v1.0\Modules"
$Lane = 0x707F
if ($Mask -le 0 -or ($Mask -band (-bnot $Lane)) -ne 0) { throw 'mask must lie inside 0x707F' }
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
$me.ProcessorAffinity = [IntPtr]$Mask
$me.Refresh()
if ([long]$me.ProcessorAffinity -ne $Mask) { throw 'affinity not applied' }
$ExtraDefs = @($ExtraDefs | ForEach-Object { $_ -split ',' } | Where-Object { $_ })

$JobRoot = 'D:\forge_jobs_20261110\fable4cpu'
$env:TEMP = Join-Path $JobRoot 'tmp'; $env:TMP = $env:TEMP
$lm = 'C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin'   # read only
$clang = Join-Path $lm 'clang++.exe'
$profdataTool = Join-Path $lm 'llvm-profdata.exe'
function Sha([string]$p) { $a = [System.Security.Cryptography.SHA256]::Create(); $s = [System.IO.File]::OpenRead($p); try { ([BitConverter]::ToString($a.ComputeHash($s))).Replace('-', '').ToLower() } finally { $s.Dispose(); $a.Dispose() } }
function Md5([string]$p) { $a = [System.Security.Cryptography.MD5]::Create(); $s = [System.IO.File]::OpenRead($p); try { ([BitConverter]::ToString($a.ComputeHash($s))).Replace('-', '').ToLower() } finally { $s.Dispose(); $a.Dispose() } }
$clangSha = Sha $clang
if ($clangSha -ne 'd05fee2c3f79b15d998d3c3413c76aabd416ec789edff89c8f698a8be44a3970') { throw "compiler sha256 $clangSha is not the lock receipt's" }
$pdSha = Sha $profdataTool
if ($pdSha -ne '55bfe8da39b548fb8b03736218c669aaec5234a14d964d4da323d7d4103b5e32') { throw "llvm-profdata sha256 $pdSha is not the lock receipt's" }
$env:PATH = $lm + ';' + $env:PATH   # process-local
$wlSha = Sha $Workload
if ($wlSha -ne '1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30') { throw "workload sha256 $wlSha" }
$freeGiB = (New-Object System.IO.DriveInfo('D')).AvailableFreeSpace / 1GB
if ($freeGiB -lt $MinFreeGiB) { throw ('NOT STARTED (disk guard): D: has {0:N2} GiB free, under {1:N1}' -f $freeGiB, $MinFreeGiB) }
$Src = (Resolve-Path -LiteralPath $Src).Path.TrimEnd('\')
$root = Join-Path $OutRoot $Tag
if (Test-Path $root) { throw "refusing: $root exists" }
New-Item -ItemType Directory -Path $root | Out-Null
$log = Join-Path $root 'build.log'
# Vienna time: the PC's UTC clock runs 25159.3 s ahead of github.com's Date header (measured at the clone).
function NowV { ([DateTime]::UtcNow.AddSeconds(-25159.3).AddHours(1)).ToString('yyyy-MM-dd HH:mm:ss') + ' Vienna' }
function Log([string]$s) { [System.IO.File]::AppendAllText($log, $s + "`n"); [Console]::Out.WriteLine($s) }

# Source manifest in QA's format; the untouched combo29 source gives the lock receipt's source_manifest_sha256.
$files = @(Get-ChildItem -LiteralPath (Join-Path $Src 'include') -Recurse -File) + @(Get-ChildItem -LiteralPath (Join-Path $Src 'src') -Recurse -File)
$rels = New-Object 'System.Collections.Generic.List[string]'
foreach ($f in $files) { $rels.Add($f.FullName.Substring($Src.Length + 1).Replace('\', '/')) }
$relArr = $rels.ToArray(); [Array]::Sort($relArr, [StringComparer]::Ordinal)
$sb = New-Object System.Text.StringBuilder
foreach ($r in $relArr) { [void]$sb.Append((Sha (Join-Path $Src $r.Replace('/', '\'))) + '  ' + $r + "`n") }
$manifestPath = Join-Path $root 'SOURCE_INPUTS.sha256'
[System.IO.File]::WriteAllText($manifestPath, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
$manifestSha = Sha $manifestPath

# Run a set of commands, at most $maxPar at a time; output of each goes to its own file and then into the log.
function Run-Set([object[]]$set, [int]$maxPar, [string]$dir) {
    $queue = New-Object System.Collections.Queue
    foreach ($j in $set) { $queue.Enqueue($j) }
    $running = New-Object System.Collections.ArrayList
    $failed = @()
    while ($queue.Count -gt 0 -or $running.Count -gt 0) {
        while ($queue.Count -gt 0 -and $running.Count -lt $maxPar) {
            $j = $queue.Dequeue()
            $outf = Join-Path $dir ($j.name + '.out.txt')
            $psi = New-Object System.Diagnostics.ProcessStartInfo
            $psi.FileName = $env:ComSpec
            $psi.Arguments = '/d /s /c ""' + $j.exe + '" ' + ($j.argv -join ' ') + ' > "' + $outf + '" 2>&1"'
            $psi.UseShellExecute = $false
            $psi.CreateNoWindow = $true
            $psi.WorkingDirectory = $dir
            $p = [System.Diagnostics.Process]::Start($psi)
            $aff = 'n/a'
            try { $aff = ('0x{0:X}' -f [int64]$p.ProcessorAffinity) } catch { }
            [void]$running.Add(@{ p = $p; j = $j; out = $outf; t0 = [DateTime]::UtcNow; aff = $aff })
        }
        Start-Sleep -Milliseconds 50
        foreach ($r in @($running)) {
            if ($r.p.HasExited) {
                $r.p.WaitForExit()
                $secs = [Math]::Round(([DateTime]::UtcNow - $r.t0).TotalSeconds, 1)
                Log ('CMD: "' + $r.j.exe + '" ' + ($r.j.argv -join ' '))
                $t = ''
                try { $t = [System.IO.File]::ReadAllText($r.out) } catch { }
                if ($t) { [System.IO.File]::AppendAllText($log, $t) }
                Log ('exit ' + $r.p.ExitCode + ' in ' + $secs + ' s; child affinity ' + $r.aff)
                if ($r.p.ExitCode -ne 0) { $failed += $r.j.name }
                $running.Remove($r)
            }
        }
    }
    if ($failed.Count -gt 0) { throw ('failed: ' + ($failed -join ', ') + "; see $log") }
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
Log ("build tag=$Tag src=$Src start " + (NowV) + " units=" + $units.Count + "; $ver; " + ('mask 0x{0:X} BelowNormal; jobs {1}' -f $Mask, $Jobs))
Log ("script build.ps1 sha256 " + (Sha $PSCommandPath) + "; compiler sha256 $clangSha")
Log ("extra defs: [" + ($ExtraDefs -join ' ') + "]; source manifest sha256 $manifestSha; D: free " + ('{0:N2}' -f $freeGiB) + ' GiB')

function Build-Stage([string]$stage, [string[]]$extra) {
    $dir = Join-Path $root $stage
    New-Item -ItemType Directory -Path $dir, (Join-Path $dir 'obj') | Out-Null
    $objs = @()
    $set = @()
    foreach ($u in $units) {
        $name = [IO.Path]::GetFileNameWithoutExtension($u)
        $o = Join-Path $dir ('obj\' + $name + '.o')
        $set += @{ name = ('cc_' + $name); exe = $clang; argv = ($common + @('-flto=thin') + $extra + @('-c', $u, '-o', $o)) }
        $objs += $o
    }
    Run-Set $set $Jobs $dir
    $exe = Join-Path $dir "forge_$stage.exe"
    $link = @{ name = 'link'; exe = $clang; argv = ($common + @('-flto=thin') + $extra + @('-fuse-ld=lld', '-static') + $objs + @('-o', $exe, "-Wl,--pdb=$(Join-Path $dir "forge_$stage.pdb")", '-Wl,--no-insert-timestamp', '-Wl,--thinlto-jobs=1')) }
    Run-Set @($link) 1 $dir
    Log ("built $exe sha256 " + (Sha $exe))
    return $exe
}

# 1) instrumented ThinLTO build
$gen = Build-Stage 'm2gen' @('-fprofile-instr-generate')
# 2) training on the frozen workload; cmd.exe redirection hands the file to the engine's stdin byte for byte
$genDir = Split-Path $gen -Parent
Copy-Item -LiteralPath $Workload -Destination (Join-Path $genDir 'frozen_train_cmds.txt')
$env:LLVM_PROFILE_FILE = (Join-Path $genDir 'm2_%p.profraw')
$trainCmd = Join-Path $genDir 'train.cmd'
[System.IO.File]::WriteAllText($trainCmd, "@echo off`r`n`"$gen`" < `"$(Join-Path $genDir 'frozen_train_cmds.txt')`" > `"$(Join-Path $genDir 'workload.out')`" 2> `"$(Join-Path $genDir 'workload.err')`"`r`nexit /b %ERRORLEVEL%`r`n", [System.Text.Encoding]::ASCII)
Push-Location $genDir
try { & $env:ComSpec /d /c $trainCmd; $trainExit = $LASTEXITCODE } finally { Pop-Location }
$env:LLVM_PROFILE_FILE = $null
if ($trainExit -ne 0) { throw "training exit $trainExit" }
$benches = @(Select-String -Path (Join-Path $genDir 'workload.out') -Pattern 'bench depth (\d+) nodes (\d+)')
$trainNodes = @($benches | ForEach-Object { $_.Matches[0].Groups[2].Value })
Log ("training: " + (($benches | ForEach-Object { $_.Matches[0].Value }) -join '; '))
if ($benches.Count -ne 3) { throw "training gave $($benches.Count) bench lines" }
if (($trainNodes -join ',') -ne '312866,862329,3024920') { throw "training nodes $($trainNodes -join ',') are not the lock pins (search changed?)" }
$raws = @(Get-ChildItem $genDir -Filter 'm2_*.profraw')
if ($raws.Count -ne 1) { throw "expected one profraw, found $($raws.Count)" }
$profdata = Join-Path $genDir 'm2.profdata'
Run-Set @(@{ name = 'profdata'; exe = $profdataTool; argv = @('merge', '-o', $profdata, $raws[0].FullName) }) 1 $genDir
$rawSha = Sha $raws[0].FullName
$mergedSha = Sha $profdata
Log ("profraw sha256 $rawSha; profdata sha256 $mergedSha")
$useExe = $null
if (-not $GenOnly) {
    # 3) the optimised build
    $useExe = Build-Stage 'm2use' @("-fprofile-instr-use=$profdata", '-Werror=profile-instr-unprofiled', '-Werror=profile-instr-out-of-date')
    Log ("RESULT exe $useExe md5 " + (Md5 $useExe) + " sha256 " + (Sha $useExe))
}
$receipt = [ordered]@{
    tag = $Tag; src = $Src; finished = (NowV)
    recipe = 'combo29 lock build.log command lines; paths differ; unit compiles side by side'
    script_sha256 = (Sha $PSCommandPath)
    compiler = $clang; compiler_sha256 = $clangSha; compiler_version = "$ver"
    profdata_tool_sha256 = $pdSha; workload_sha256 = $wlSha
    extra_defs = @($ExtraDefs)
    source_manifest_sha256 = $manifestSha
    training_nodes = @($trainNodes)
    raw_profile_sha256 = $rawSha; merged_profile_sha256 = $mergedSha
    gen_exe = $gen; gen_exe_sha256 = (Sha $gen)
    exe = $useExe
    exe_sha256 = $(if ($useExe) { Sha $useExe } else { $null })
    exe_md5 = $(if ($useExe) { Md5 $useExe } else { $null })
    mask = ('0x{0:X}' -f $Mask); priority = 'BelowNormal'; jobs = $Jobs
}
($receipt | ConvertTo-Json -Depth 4) | Set-Content -Encoding ASCII (Join-Path $root 'RUN_RECEIPT.json')
$sz = (Get-ChildItem -LiteralPath $root -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
Log (("end " + (NowV) + '; build folder {0:N1} MiB' -f $sz))
