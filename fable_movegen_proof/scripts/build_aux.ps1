# build_aux.ps1 - build the auxiliary probe (harness\mgprobe.cpp) against ONE frozen engine source tree
# (PowerShell 5.1, ASCII only). Same compiler, sysroot, nine lock switches and flags as the lock's compile line
# (out\build\bn3_on\build.log), -O3, but no LTO, no PGO and no debug info: a test tool, a separate artifact.
#
# What makes the result trustworthy (review 1 of job 3, finding C1):
#   - the candidate switches are NOT a parameter: they come from runs\freeze\INPUTS.json (extra_defs of the tag);
#   - the frozen tree and its manifest are hashed again before the compile;
#   - the harness source is copied into the output folder first and that copy is compiled and hashed;
#   - the preprocessor (-E -dM, same flags) is asked for the EFFECTIVE value of every candidate switch in
#     board.cpp and eval.cpp, and the values are checked against what the tag must have;
#   - the built probe is asked for its identity (`mgprobe id`), which is checked and stored.
# Tag LOCKEQ is the BUNDLE3 tree with no switch (all three default to 0): a different build that must behave
# like the lock, and whose hash must differ from BUN's, which shows that BUN's -D switches took effect.
# With -Coverage the probe is built with clang's source-based coverage (unchanged source, extra compiler flags)
# into aux2\<Tag>_cov: it shows which lines of a patch a corpus executes. It is never used for comparisons.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File build_aux.ps1 -Tag LOCK|LOCKEQ|EVL|PCM|CKL|WNP|KPC|BUN [-Coverage]
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [switch]$Coverage,
    [long]$Mask = 0x78
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'job3_env.ps1')
[void](J3-Pin $Mask)
J3-Guard
# what every tag must end up with: switch -> effective value ('' = the macro must not exist in that tree)
$expect = @{
    'LOCK'   = @{ EVADE_LEGAL = ''; PAWN_CAPMASK = ''; CHECKERS_KL = ''; WITNESS_NOPIN = ''; KING_PAWN_CACHE = '' }
    'LOCKEQ' = @{ EVADE_LEGAL = '0'; PAWN_CAPMASK = '0'; CHECKERS_KL = '0'; WITNESS_NOPIN = ''; KING_PAWN_CACHE = '' }
    'EVL'    = @{ EVADE_LEGAL = '1'; PAWN_CAPMASK = ''; CHECKERS_KL = ''; WITNESS_NOPIN = ''; KING_PAWN_CACHE = '' }
    'PCM'    = @{ EVADE_LEGAL = ''; PAWN_CAPMASK = '1'; CHECKERS_KL = ''; WITNESS_NOPIN = ''; KING_PAWN_CACHE = '' }
    'CKL'    = @{ EVADE_LEGAL = ''; PAWN_CAPMASK = ''; CHECKERS_KL = '1'; WITNESS_NOPIN = ''; KING_PAWN_CACHE = '' }
    'WNP'    = @{ EVADE_LEGAL = ''; PAWN_CAPMASK = ''; CHECKERS_KL = ''; WITNESS_NOPIN = '1'; KING_PAWN_CACHE = '' }
    'KPC'    = @{ EVADE_LEGAL = ''; PAWN_CAPMASK = ''; CHECKERS_KL = ''; WITNESS_NOPIN = ''; KING_PAWN_CACHE = '1' }
    'BUN'    = @{ EVADE_LEGAL = '1'; PAWN_CAPMASK = '1'; CHECKERS_KL = '1'; WITNESS_NOPIN = ''; KING_PAWN_CACHE = '' }
}
if (-not $expect.ContainsKey($Tag)) { throw "unknown tag $Tag" }
$clang = Join-Path $J3_LM 'clang++.exe'
$clangSha = J3-Hash $clang 'SHA256'
if ($clangSha -ne 'd05fee2c3f79b15d998d3c3413c76aabd416ec789edff89c8f698a8be44a3970') { throw 'compiler is not the lock receipt compiler' }
$env:PATH = $J3_LM + ';' + $env:PATH
$frozen = Get-Content -LiteralPath (Join-Path $J3_OUT 'runs\freeze\INPUTS.json') -Raw | ConvertFrom-Json
$entry = $frozen | Where-Object { $_.tag -eq $Tag }
if (-not $entry) { throw "tag $Tag is not in INPUTS.json" }
$treeTag = if ($Tag -eq 'LOCKEQ') { 'BUN' } else { $Tag }        # LOCKEQ is the BUNDLE3 tree
$tree = Join-Path $J3_OUT ("src\" + $treeTag)
if (-not (Test-Path -LiteralPath $tree)) { throw "missing frozen tree $tree" }
# the switches of the build come from the frozen record, never from the command line
$defs = @("$($entry.extra_defs)" -split ',' | Where-Object { $_ })
if ((J3-Hash $entry.manifest_file 'SHA256') -ne $entry.manifest_sha256) { throw "the manifest file of $Tag changed since the freeze" }
$manifest = @{}
foreach ($ln in (Get-Content -LiteralPath $entry.manifest_file)) {
    if ($ln -notmatch '^([0-9a-f]{64})\s+(\S+)$') { continue }
    $want = $Matches[1]; $rel = $Matches[2]
    if ((J3-Hash (Join-Path $tree $rel.Replace('/', '\')) 'SHA256') -ne $want) { throw "frozen tree $treeTag differs from the manifest of $Tag at $rel" }
    $manifest[$rel] = $want
}
if ($manifest.Count -ne 20) { throw "manifest of $Tag has $($manifest.Count) files, expected 20" }
# which files differ from the lock's tree
$lockEntry = $frozen | Where-Object { $_.tag -eq 'LOCK' }
$differs = @()
foreach ($ln in (Get-Content -LiteralPath $lockEntry.manifest_file)) {
    if ($ln -match '^([0-9a-f]{64})\s+(\S+)$' -and $manifest[$Matches[2]] -ne $Matches[1]) { $differs += $Matches[2] }
}
$dirName = if ($Coverage) { $Tag + '_cov' } else { $Tag }
$dir = Join-Path $J3_OUT ("aux2\" + $dirName)
if (Test-Path -LiteralPath $dir) { throw "refusing: $dir exists" }
New-Item -ItemType Directory -Path $dir -Force | Out-Null
# freeze the harness source, then describe the build in a header the probe compiles in
$harness = Join-Path $dir 'mgprobe.cpp'
Copy-Item -LiteralPath (Join-Path $J3_PACK 'harness\mgprobe.cpp') -Destination $harness
$harnessSha = J3-Hash $harness 'SHA256'
$identity = @('// written by build_aux.ps1: what this probe is',
    ('#define MGPROBE_TAG "' + $Tag + '"'),
    ('#define MGPROBE_TREE_MANIFEST "' + $entry.manifest_sha256 + '"'),
    ('#define MGPROBE_DEFS "' + ($defs -join ' ') + '"'),
    ('#define MGPROBE_HARNESS_SHA256 "' + $harnessSha + '"'))
[System.IO.File]::WriteAllLines((Join-Path $dir 'mgprobe_identity.h'), $identity, [System.Text.Encoding]::ASCII)
$common = @('-std=c++20', '-O3', '-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-DFORGE_EXPOSE_TUNABLES=1',
    '-DFORGE_SPD_TT_NOTLS=1', '-DFORGE_SPD_NO_ZERO_MOVELISTS=2', '-DFORGE_SEARCH_SPEED2=1',
    '-DFORGE_SPD_PREFETCH_EARLY=1', '-DFORGE_SPD_SLIDER_PEXT=1', '-DFORGE_SPD_NNUE_ZMM=1') +
    @($defs | ForEach-Object { '-D' + $_ }) +
    @('-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-pthread', ('-I' + (Join-Path $tree 'include')), ('-I' + $dir),
    '--sysroot=C:/msys64/ucrt64', '-stdlib=libstdc++')
if ($Coverage) { $common += @('-fprofile-instr-generate', '-fcoverage-mapping') }
# the effective switch values, asked of the preprocessor with the same flags
$effective = [ordered]@{}
foreach ($unit in 'board', 'eval') {
    $macroFile = Join-Path $dir ($unit + '.macros.txt')
    $pp = Start-Process -FilePath $clang -ArgumentList ($common + @('-E', '-dM', (Join-Path $tree ("src\" + $unit + '.cpp')), '-o', $macroFile)) `
        -NoNewWindow -Wait -PassThru -RedirectStandardOutput (Join-Path $dir 'pp.out') -RedirectStandardError (Join-Path $dir 'pp.err')
    if ($pp.ExitCode -ne 0) { throw "preprocessing $unit.cpp failed" }
    $found = [ordered]@{}
    foreach ($ln in (Get-Content -LiteralPath $macroFile)) {
        if ($ln -match '^#define (FORGE_\w+) (.*)$') { $found[$Matches[1]] = $Matches[2].Trim() }
    }
    $effective[$unit + '.cpp'] = $found
    Remove-Item -LiteralPath $macroFile -Force
}
$problems = @()
foreach ($sw in $expect[$Tag].Keys) {
    $unit = if ($sw -eq 'KING_PAWN_CACHE') { 'eval.cpp' } else { 'board.cpp' }
    $name = 'FORGE_SPD_' + $sw
    $got = if ($effective[$unit].Contains($name)) { "$($effective[$unit][$name])" } else { '' }
    if ($got -ne $expect[$Tag][$sw]) { $problems += "$name in ${unit}: expected '$($expect[$Tag][$sw])', effective '$got'" }
}
if ($problems.Count -ne 0) { throw ("switch check failed for ${Tag}: " + ($problems -join '; ')) }
$exe = Join-Path $dir 'mgprobe.exe'
$argv = $common + @('-rtlib=libgcc', '-fuse-ld=lld', '-static', $harness)
foreach ($u in 'bitboard', 'board', 'eval', 'eval_params', 'nnue', 'search') { $argv += (Join-Path $tree ("src\" + $u + '.cpp')) }
$argv += @('-o', $exe)
$started = J3-Now
$p = Start-Process -FilePath $clang -ArgumentList $argv -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput (Join-Path $dir 'build.out') -RedirectStandardError (Join-Path $dir 'build.err')
$err = Get-Content (Join-Path $dir 'build.err') -ErrorAction SilentlyContinue | Where-Object { $_ -notmatch 'argument unused' }
if ($p.ExitCode -ne 0) { $err | Select-Object -First 40 | ForEach-Object { Write-Output $_ }; throw "probe build failed (exit $($p.ExitCode))" }
if ((J3-Hash $harness 'SHA256') -ne $harnessSha) { throw 'the frozen harness copy changed during the build' }
# ask the probe what it is
$env:LLVM_PROFILE_FILE = Join-Path $dir 'id_%p.profraw'
$idText = & $exe id
$id = $idText | ConvertFrom-Json
if ($id.tag -ne $Tag -or $id.harness_sha256 -ne $harnessSha -or $id.tree_manifest_sha256 -ne $entry.manifest_sha256) { throw 'the probe does not report the identity it was built with' }
if ($id.nnue_available -ne 1 -or $id.nnue_hidden -ne 256) { throw 'the probe has no net or the wrong net size' }
$wantEntry = if ($Tag -eq 'KPC') { 64 } else { 40 }
if ($id.sizeof_pawn_entry -ne $wantEntry) { throw "pawn-cache entry is $($id.sizeof_pawn_entry) bytes, expected $wantEntry for $Tag" }
$receipt = [ordered]@{
    tag = $Tag; coverage_build = [bool]$Coverage; built = $started; finished = (J3-Now)
    harness_source = (Join-Path $J3_PACK 'harness\mgprobe.cpp'); harness_frozen_copy = $harness; harness_sha256 = $harnessSha
    tree = $tree; tree_tag = $treeTag; tree_manifest_sha256 = $entry.manifest_sha256; files_differing_from_lock_tree = $differs
    extra_defs = $defs; extra_defs_source = 'runs\freeze\INPUTS.json'
    effective_switches = $effective; expected_candidate_switches = $expect[$Tag]
    compiler = $clang; compiler_sha256 = $clangSha; argv = $argv
    exe = $exe; exe_md5 = (J3-Hash $exe 'MD5'); exe_sha256 = (J3-Hash $exe 'SHA256'); exe_bytes = (Get-Item -LiteralPath $exe).Length
    probe_id = $id
    relationship = 'auxiliary test binary: mgprobe.cpp plus the six unmodified engine units of this tree; -O3, no LTO, no PGO; not the release executable'
    warnings = @($err | Select-Object -First 20)
}
[System.IO.File]::WriteAllText((Join-Path $dir 'AUX_RECEIPT.json'), ($receipt | ConvertTo-Json -Depth 6), [System.Text.Encoding]::ASCII)
Write-Output ("built $dirName probe sha256 " + $receipt.exe_sha256 + " defs [" + ($defs -join ' ') + "] differs from lock tree in [" + ($differs -join ' ') + "] harness " + $harnessSha.Substring(0, 16))
