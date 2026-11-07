# t2_build.ps1 - OSS scout trial T2: build the trial_w6 source (lock d4f4312 + trial_w6.patch, six speed switches ON
# through -D, the same values as F:\ospd\packs\trial_w6\src_kit) with g++ (reference) and with LLVM 18 clang (MSVC
# target, lld-link). Runs in the caller's priority / affinity (the session: Idle, CPUs 2-3). One compiler process at a
# time. Refuses to overwrite an output folder.
#   pwsh -NoProfile -File t2_build.ps1 -Variant g0|c0|c1|c2gen|c2use|c3gen|c3use [-Profdata <file>]
#   g0     g++ 15.2 plain: the kit's flags (-O3 ... -march=znver5 -static), no LTO / PGO - source identity reference
#   c0     clang++ -O3 -march=znver4, static CRT, PDB
#   c1     c0 + ThinLTO (-flto=thin, lld-link)
#   c2gen  c1 + -fprofile-instr-generate (instrumented)      c2use  c1 + -fprofile-instr-use=<Profdata>
#   c3gen  c2use + -fcs-profile-generate (context-sensitive)  c3use  c1 + -fprofile-instr-use=<merged Profdata>
param(
    [Parameter(Mandatory = $true)][string]$Variant,
    [string]$Src = 'C:\opus_5h\oss_scout\build\t2\src_w6',
    [string]$OutRoot = 'C:\opus_5h\oss_scout\build\t2',
    [string]$Profdata = '',
    [string]$Tag = '',
    [switch]$LibStdCxx
)
$ErrorActionPreference = 'Stop'
$name = if ($Tag) { "$Variant`_$Tag" } else { $Variant }
$out = Join-Path $OutRoot $name
if (Test-Path $out) { throw "refusing: $out exists" }
New-Item -ItemType Directory -Path $out | Out-Null
$log = Join-Path $out 'build.log'
function Log([string]$s) { Add-Content -Path $log -Value $s -Encoding utf8; Write-Output $s }

$defs = @('-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-DFORGE_EXPOSE_TUNABLES=1',
    '-DFORGE_SPD_TT_NOTLS=1', '-DFORGE_SPD_NO_ZERO_MOVELISTS=2', '-DFORGE_SEARCH_SPEED2=1',
    '-DFORGE_SPD_PREFETCH_EARLY=1', '-DFORGE_SPD_SLIDER_PEXT=1', '-DFORGE_SPD_NNUE_ZMM=1')
$units = @(Get-ChildItem (Join-Path $Src 'src') -Filter *.cpp | Sort-Object Name | ForEach-Object { $_.FullName })
$inc = '-I' + (Join-Path $Src 'include')
Log ("t2_build variant=$Variant tag=$Tag start " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " units=" + $units.Count)

function Run([string]$exe, [string[]]$argv) {
    Log ("CMD: `"$exe`" " + ($argv -join ' '))
    $t0 = Get-Date
    $p = Start-Process -FilePath $exe -ArgumentList $argv -NoNewWindow -Wait -PassThru `
        -RedirectStandardOutput (Join-Path $out 'stdout.tmp') -RedirectStandardError (Join-Path $out 'stderr.tmp')
    foreach ($f in 'stdout.tmp', 'stderr.tmp') {
        $t = Get-Content (Join-Path $out $f) -Raw -ErrorAction SilentlyContinue
        if ($t) { Add-Content -Path $log -Value $t -Encoding utf8 }
    }
    $sec = [Math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
    Log ("exit " + $p.ExitCode + " in " + $sec + " s")
    if ($p.ExitCode -ne 0) { throw "$exe failed with exit $($p.ExitCode); see $log" }
}

if ($Variant -match '^m') {
    # llvm-mingw 20261104 (clang 23.1.5, x86_64-w64-windows-gnu, UCRT, libc++): the MinGW ABI of the lock's g++.
    # The installed LLVM 18 cannot use the VS 18 STL (STL1000: "expected Clang 20 or newer"), see RESULT.md.
    $lm = 'C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin'
    $env:PATH = $lm + ';' + $env:PATH   # process-local
    $clang = Join-Path $lm 'clang++.exe'
    $common = @('-std=c++20', '-O3') + $defs + @('-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-pthread',
        '-g', '-gcodeview', $inc)
    if ($LibStdCxx) {
        # Use the MSYS2 ucrt64 GCC 15.2 runtime (libstdc++, libgcc, mingw-w64 CRT) like the lock's g++ build, so that
        # library code (std::sort tie order, std::log) is the same as in the lock.
        $common += @('--sysroot=C:/msys64/ucrt64', '-stdlib=libstdc++', '-rtlib=libgcc', '-unwindlib=libgcc')
    }
    $lto = @(); $prof = @()
    switch ($Variant) {
        'm0' { }
        'm1' { $lto = @('-flto=thin') }
        'm2gen' { $lto = @('-flto=thin'); $prof = @('-fprofile-instr-generate') }
        'm2use' { if (-not (Test-Path $Profdata)) { throw 'm2use needs -Profdata' }; $lto = @('-flto=thin'); $prof = @("-fprofile-instr-use=$Profdata", '-Wno-profile-instr-unprofiled', '-Wno-profile-instr-out-of-date') }
        'm3gen' { if (-not (Test-Path $Profdata)) { throw 'm3gen needs -Profdata' }; $lto = @('-flto=thin'); $prof = @("-fprofile-instr-use=$Profdata", '-fcs-profile-generate', '-Wno-profile-instr-unprofiled') }
        'm3use' { if (-not (Test-Path $Profdata)) { throw 'm3use needs -Profdata' }; $lto = @('-flto=thin'); $prof = @("-fprofile-instr-use=$Profdata", '-Wno-profile-instr-unprofiled', '-Wno-profile-instr-out-of-date') }
        default { throw "unknown variant $Variant" }
    }
    $objDir = Join-Path $out 'obj'
    New-Item -ItemType Directory -Path $objDir | Out-Null
    $objs = @()
    foreach ($u in $units) {
        $o = Join-Path $objDir (([IO.Path]::GetFileNameWithoutExtension($u)) + '.o')
        Run $clang ($common + $lto + $prof + @('-c', $u, '-o', $o))
        $objs += $o
    }
    $exeOut = Join-Path $out "forge_$name.exe"
    $pdb = Join-Path $out "forge_$name.pdb"
    Run $clang ($common + $lto + $prof + @('-fuse-ld=lld', '-static') + $objs + @('-o', $exeOut, "-Wl,--pdb=$pdb", '-Wl,--no-insert-timestamp'))
} elseif ($Variant -eq 'g0') {
    $gpp = 'C:\msys64\ucrt64\bin\g++.exe'
    $env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH   # process-local: cc1plus / as / ld helpers
    $exeOut = Join-Path $out 'forge_g0.exe'
    $argv = @('-std=c++20', '-O3') + $defs + @('-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-static', '-pthread', $inc) +
        $units + @('-Wl,--no-insert-timestamp', '-o', $exeOut)
    Run $gpp $argv
} else {
    # MSVC environment (INCLUDE / LIB / PATH) for this process only
    $vc = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
    $envDump = & cmd.exe /d /c "`"$vc`" >nul 2>&1 && set"
    foreach ($line in $envDump) {
        $i = $line.IndexOf('=')
        if ($i -gt 0) { [Environment]::SetEnvironmentVariable($line.Substring(0, $i), $line.Substring($i + 1), 'Process') }
    }
    if (-not $env:INCLUDE) { throw 'vcvars64 did not set INCLUDE' }
    $clang = 'C:\Program Files\LLVM\bin\clang++.exe'
    $common = @('-std=c++20', '-O3') + $defs + @('-ffp-contract=off', '-fno-fast-math', '-march=znver4', '-fms-runtime-lib=static',
        '-g', '-gcodeview', '-Wno-unused-command-line-argument', $inc)
    $lto = @()
    $prof = @()
    switch ($Variant) {
        'c0' { }
        'c1' { $lto = @('-flto=thin') }
        'c2gen' { $lto = @('-flto=thin'); $prof = @('-fprofile-instr-generate') }
        'c2use' { if (-not (Test-Path $Profdata)) { throw 'c2use needs -Profdata' }; $lto = @('-flto=thin'); $prof = @("-fprofile-instr-use=$Profdata", '-Wno-profile-instr-unprofiled', '-Wno-profile-instr-out-of-date') }
        'c3gen' { if (-not (Test-Path $Profdata)) { throw 'c3gen needs -Profdata' }; $lto = @('-flto=thin'); $prof = @("-fprofile-instr-use=$Profdata", '-fcs-profile-generate', '-Wno-profile-instr-unprofiled') }
        'c3use' { if (-not (Test-Path $Profdata)) { throw 'c3use needs -Profdata' }; $lto = @('-flto=thin'); $prof = @("-fprofile-instr-use=$Profdata", '-Wno-profile-instr-unprofiled', '-Wno-profile-instr-out-of-date') }
        default { throw "unknown variant $Variant" }
    }
    $objDir = Join-Path $out 'obj'
    New-Item -ItemType Directory -Path $objDir | Out-Null
    $objs = @()
    foreach ($u in $units) {
        $o = Join-Path $objDir (([IO.Path]::GetFileNameWithoutExtension($u)) + '.o')
        Run $clang ($common + $lto + $prof + @('-c', $u, '-o', $o))
        $objs += $o
    }
    $exeOut = Join-Path $out "forge_$name.exe"
    Run $clang ($common + $lto + $prof + @('-fuse-ld=lld') + $objs + @('-o', $exeOut, '-Wl,/DEBUG:FULL', '-Wl,/OPT:REF', '-Wl,/OPT:ICF', '-Wl,/Brepro'))
}
$h = (Get-FileHash $exeOut -Algorithm SHA256).Hash
Log ("built $exeOut sha256 $h size " + (Get-Item $exeOut).Length)
Log ("end " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
