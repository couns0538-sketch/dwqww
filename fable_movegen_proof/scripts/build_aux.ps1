# build_aux.ps1 - build the auxiliary probe (harness\mgprobe.cpp) against ONE frozen engine source tree
# (PowerShell 5.1, ASCII only). Same compiler, sysroot, nine lock switches and flags as the lock's compile line
# (out\build\bn3_on\build.log), -O3, but no LTO, no PGO and no debug info: a test tool, a separate artifact.
# The tree is out\job3\src\<Tag> (copied and hash-checked by freeze_inputs.ps1); it is checked again here.
# Pins itself to 0x78 at Idle; refuses to overwrite; writes only under out\job3\aux\<Tag>.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File build_aux.ps1 -Tag LOCK [-ExtraDefs A=1,B=1]
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [string[]]$ExtraDefs = @(),
    [long]$Mask = 0x78
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'job3_env.ps1')
[void](J3-Pin $Mask)
J3-Guard
$ExtraDefs = @($ExtraDefs | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$clang = Join-Path $J3_LM 'clang++.exe'
$clangSha = J3-Hash $clang 'SHA256'
if ($clangSha -ne 'd05fee2c3f79b15d998d3c3413c76aabd416ec789edff89c8f698a8be44a3970') { throw 'compiler is not the lock receipt compiler' }
$env:PATH = $J3_LM + ';' + $env:PATH
$tree = Join-Path $J3_OUT ("src\" + $Tag)
if (-not (Test-Path -LiteralPath $tree)) { throw "missing frozen tree $tree" }
# the tree must still be what freeze_inputs.ps1 verified
$frozen = Get-Content -LiteralPath (Join-Path $J3_OUT 'runs\freeze\INPUTS.json') -Raw | ConvertFrom-Json
$entry = $frozen | Where-Object { $_.tag -eq $Tag }
if (-not $entry) { throw "tag $Tag is not in INPUTS.json" }
$manifestLines = @()
foreach ($ln in (Get-Content -LiteralPath $entry.manifest_file)) {
    if ($ln -notmatch '^([0-9a-f]{64})\s+(\S+)$') { continue }
    $want = $Matches[1]; $rel = $Matches[2]
    $got = J3-Hash (Join-Path $tree $rel.Replace('/', '\')) 'SHA256'
    if ($got -ne $want) { throw "frozen tree $Tag differs from its manifest at $rel" }
    $manifestLines += "$want  $rel"
}
if ($manifestLines.Count -ne 20) { throw "manifest of $Tag has $($manifestLines.Count) files, expected 20" }
$dir = Join-Path $J3_OUT ("aux\" + $Tag)
if (Test-Path -LiteralPath $dir) { throw "refusing: $dir exists" }
New-Item -ItemType Directory -Path $dir | Out-Null
$harness = Join-Path $J3_PACK 'harness\mgprobe.cpp'
$exe = Join-Path $dir 'mgprobe.exe'
$argv = @('-std=c++20', '-O3', '-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-DFORGE_EXPOSE_TUNABLES=1',
    '-DFORGE_SPD_TT_NOTLS=1', '-DFORGE_SPD_NO_ZERO_MOVELISTS=2', '-DFORGE_SEARCH_SPEED2=1',
    '-DFORGE_SPD_PREFETCH_EARLY=1', '-DFORGE_SPD_SLIDER_PEXT=1', '-DFORGE_SPD_NNUE_ZMM=1') +
    @($ExtraDefs | ForEach-Object { '-D' + $_ }) +
    @('-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-pthread', ('-I' + (Join-Path $tree 'include')),
    '--sysroot=C:/msys64/ucrt64', '-stdlib=libstdc++', '-rtlib=libgcc', '-fuse-ld=lld', '-static', $harness)
foreach ($u in 'bitboard', 'board', 'eval', 'eval_params', 'nnue', 'search') { $argv += (Join-Path $tree ("src\" + $u + '.cpp')) }
$argv += @('-o', $exe)
$started = J3-Now
$p = Start-Process -FilePath $clang -ArgumentList $argv -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput (Join-Path $dir 'build.out') -RedirectStandardError (Join-Path $dir 'build.err')
$err = Get-Content (Join-Path $dir 'build.err') -ErrorAction SilentlyContinue | Where-Object { $_ -notmatch 'argument unused' }
if ($p.ExitCode -ne 0) { $err | Select-Object -First 40 | ForEach-Object { Write-Output $_ }; throw "probe build failed (exit $($p.ExitCode))" }
$receipt = [ordered]@{
    tag = $Tag; built = $started; finished = (J3-Now); harness = $harness; harness_sha256 = (J3-Hash $harness 'SHA256')
    tree = $tree; tree_manifest_sha256 = $entry.manifest_sha256; extra_defs = $ExtraDefs
    compiler = $clang; compiler_sha256 = $clangSha; argv = $argv
    exe = $exe; exe_md5 = (J3-Hash $exe 'MD5'); exe_sha256 = (J3-Hash $exe 'SHA256'); exe_bytes = (Get-Item -LiteralPath $exe).Length
    relationship = 'auxiliary test binary: mgprobe.cpp plus the six unmodified engine units of this tree; -O3, no LTO, no PGO; not the release executable'
    warnings = @($err | Select-Object -First 20)
}
[System.IO.File]::WriteAllText((Join-Path $dir 'AUX_RECEIPT.json'), ($receipt | ConvertTo-Json -Depth 5), [System.Text.Encoding]::ASCII)
Write-Output ("built $Tag probe sha256 " + $receipt.exe_sha256 + " defs [" + ($ExtraDefs -join ' ') + "] harness sha256 " + $receipt.harness_sha256)
