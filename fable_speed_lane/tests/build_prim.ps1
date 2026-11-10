# build_prim.ps1 - build tests\prim_dump.cpp against one engine source tree (PowerShell 5.1, ASCII only).
# Same compiler and sysroot as the lock, the six lock switches, -O2, no LTO, no PGO (a test tool, not a timing exe).
# Pins itself to mask 0x78 (or a subset) at Idle; refuses to overwrite; writes only under -OutRoot (D:).
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File build_prim.ps1 -Tag <new> -Src <tree> [-ExtraDefs A=1,B=1]
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][string]$Src,
    [string]$OutRoot = 'D:\forge_jobs_20261109\fable2\out\build',
    [string[]]$ExtraDefs = @(),
    [long]$Mask = 0x78
)
$ErrorActionPreference = 'Stop'
if ($Mask -le 0 -or ($Mask -band (-bnot 0x78)) -ne 0) { throw 'mask must lie inside 0x78 (CPUs 3-6)' }
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask; $me.Refresh()
if ([long]$me.ProcessorAffinity -ne $Mask -or "$($me.PriorityClass)" -ne 'Idle') { throw 'placement not applied' }
$ExtraDefs = @($ExtraDefs | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$env:TEMP = 'D:\forge_jobs_20261109\fable2\out\tmp'; $env:TMP = $env:TEMP
$lm = 'C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin'   # read only
$clang = Join-Path $lm 'clang++.exe'
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $clang).Hash.ToLower() -ne 'd05fee2c3f79b15d998d3c3413c76aabd416ec789edff89c8f698a8be44a3970') { throw 'compiler is not the lock receipt compiler' }
$env:PATH = $lm + ';' + $env:PATH
if ((Get-PSDrive D).Free / 1GB -lt 30.3) { throw 'D: below 30.3 GiB free' }
$Src = (Resolve-Path -LiteralPath $Src).Path.TrimEnd('\')
$dir = Join-Path $OutRoot ("prim_" + $Tag)
if (Test-Path $dir) { throw "refusing: $dir exists" }
New-Item -ItemType Directory -Path $dir | Out-Null
$harness = Join-Path $PSScriptRoot 'prim_dump.cpp'
$exe = Join-Path $dir 'prim_dump.exe'
$argv = @('-std=c++20', '-O2', '-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-DFORGE_EXPOSE_TUNABLES=1',
    '-DFORGE_SPD_TT_NOTLS=1', '-DFORGE_SPD_NO_ZERO_MOVELISTS=2', '-DFORGE_SEARCH_SPEED2=1',
    '-DFORGE_SPD_PREFETCH_EARLY=1', '-DFORGE_SPD_SLIDER_PEXT=1', '-DFORGE_SPD_NNUE_ZMM=1') +
    @($ExtraDefs | ForEach-Object { '-D' + $_ }) +
    @('-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-pthread', ('-I' + (Join-Path $Src 'include')),
    '--sysroot=C:/msys64/ucrt64', '-stdlib=libstdc++', '-rtlib=libgcc', '-fuse-ld=lld', '-static', $harness)
foreach ($u in 'bitboard', 'board', 'eval', 'eval_params', 'nnue', 'search') { $argv += (Join-Path $Src ("src\" + $u + '.cpp')) }
$argv += @('-o', $exe)
$p = Start-Process -FilePath $clang -ArgumentList $argv -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput (Join-Path $dir 'build.out') -RedirectStandardError (Join-Path $dir 'build.err')
$err = Get-Content (Join-Path $dir 'build.err') -ErrorAction SilentlyContinue | Where-Object { $_ -notmatch 'argument unused' }
if ($p.ExitCode -ne 0) { $err | Select-Object -First 40 | ForEach-Object { Write-Output $_ }; throw "harness build failed (exit $($p.ExitCode))" }
Write-Output ("built $exe sha256 " + (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash.ToLower() + " defs [" + ($ExtraDefs -join ' ') + "]")
