# Build and run tools/etc_probe (PowerShell 5.1 compatible, ASCII only).
# Everything runs through tools/pin.ps1: CPU 3-6, Idle, TEMP/TMP on D:.
#
# Inputs, all read-only:
#   - the lock source snapshot of the Engine QA pack (bitboard.cpp, board.cpp, eval.cpp, eval_params.cpp, headers)
#   - the compiler QA used for the lock (llvm-mingw clang 23, hash checked below)
# Outputs: only under D:\forge_jobs_20261109\fable52\out\etc_build and the TSV named by -OutTsv.
param(
    [string]$OutTsv = 'D:\forge_jobs_20261109\fable52\repo\fable_search_gap\data\etc_probe_results.tsv',
    [int]$HashMb = 16,
    [switch]$BuildOnly
)
$ErrorActionPreference = 'Stop'
$J = 'D:\forge_jobs_20261109\fable52'
$Tools = Join-Path $J 'repo\fable_search_gap\tools'
$Here = Join-Path $Tools 'etc_probe'
$Build = Join-Path $J 'out\etc_build'
$Snap = 'D:\forge-qa\pack_combo29_20261108\pc_payload\source_snapshot'
$Cxx = 'C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin\clang++.exe'
$CxxSha = 'd05fee2c3f79b15d998d3c3413c76aabd416ec789edff89c8f698a8be44a3970'

if (-not (Test-Path -LiteralPath $Build)) { New-Item -ItemType Directory -Force $Build | Out-Null }
if ((Get-FileHash -LiteralPath $Cxx -Algorithm SHA256).Hash.ToLower() -ne $CxxSha) { Write-Output 'compiler hash differs from the QA receipt'; exit 10 }
if ((Get-FileHash -LiteralPath "$Snap\src\search.cpp" -Algorithm MD5).Hash.ToLower() -ne 'b9f9aab051b548ebd50389c9ca9d5352') { Write-Output 'source snapshot is not the combo29 lock source'; exit 11 }
$free = [math]::Round((Get-PSDrive D).Free / 1GB, 2)
if ($free -lt 31) { Write-Output "D: free $free GiB is below 31 GiB: no build"; exit 12 }

$Exe = Join-Path $Build 'etc_probe.exe'
$flags = '-std=c++20 -O2 -DNDEBUG -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 ' +
         '-DFORGE_SPD_SLIDER_PEXT=1 -ffp-contract=off -fno-fast-math -march=znver5 -pthread ' +
         '--sysroot=C:/msys64/ucrt64 -stdlib=libstdc++ -rtlib=libgcc -fuse-ld=lld -static'
$srcs = "$Here\etc_probe.cpp $Snap\src\bitboard.cpp $Snap\src\board.cpp $Snap\src\eval.cpp $Snap\src\eval_params.cpp"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$Tools\pin.ps1" -Exe $Cxx `
    -ArgLine "$flags -I$Snap\include $srcs -o $Exe" -OutFile "$Build\build.log"
if ($LASTEXITCODE -ne 0) { Write-Output "build failed, see $Build\build.log"; Get-Content "$Build\build.log" | Select-Object -First 40; exit 13 }
Write-Output ('built ' + $Exe + ' sha256 ' + (Get-FileHash -LiteralPath $Exe -Algorithm SHA256).Hash.ToLower())
if ($BuildOnly) { exit 0 }

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$Tools\pin.ps1" -Exe $Exe `
    -ArgLine "$Here\positions.epd $OutTsv $HashMb" -OutFile "$Build\run.log" -WorkDir $Build
Write-Output "run exit $LASTEXITCODE; console log $Build\run.log"
exit $LASTEXITCODE
