# freeze_inputs.ps1 - job 3, step "freeze and preflight" (PowerShell 5.1, ASCII only).
#
# Verifies every input by hash BEFORE anything is run, copies the executables and the source trees into
# out\job3 (bin\<TAG>, src\<TAG>), verifies the copies, and writes runs\freeze\INPUTS.json and INPUTS.txt.
# A supplied-executable MD5 mismatch is an input-identity blocker: that tag is marked BLOCKED and not copied.
# Reads only; writes only under out\job3. Refuses to overwrite an existing copy that differs.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File freeze_inputs.ps1
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'job3_env.ps1')
[void](J3-Pin 0x78)
J3-Guard

$QA = $J3_QA; $J2 = $J3_JOB2
# tag, release exe, expected md5 ('' = none given, recorded only), expected sha256 ('' = none), source tree,
# its SOURCE_INPUTS.sha256, receipt, extra defines of the build, what the tag is.
$inputs = @(
    @{ tag = 'LOCK';   exe = "$J2\base\combo29_lock_E1284F7F.exe"; md5 = 'c0051c99695f48bf93272d96fe7548c3'; sha = 'e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e'; tree = "$J2\base\combo29_src"; man = "$J2\base\SOURCE_INPUTS.sha256"; receipt = ''; defs = ''; what = 'reference lock combo29 (copy named in job-2 STATUS.md)' },
    @{ tag = 'LOCKEQ'; exe = "$J2\build\bn3_off\m2use\forge_m2use.exe"; md5 = ''; sha = '74bb3cfa3121bc2e260406b24409fbb2c0eeb760fa3bc413d524bdcf04ab9f9b'; tree = ''; man = "$J2\build\bn3_off\SOURCE_INPUTS.sha256"; receipt = "$J2\build\bn3_off\RUN_RECEIPT.json"; defs = ''; what = 'lock-equivalent: BUNDLE3 tree, all switches 0 (pin-equivalent, not byte-identical)' },
    @{ tag = 'EVL';    exe = "$QA\build_v3\EVL\m2use\forge_m2use.exe"; md5 = '35781e5cac204370584ff4cb1f5ee93e'; sha = 'b89df40fce1726e316e7fb8e3348866401bd86a406aa689e9967f4a487c30237'; tree = "$QA\build_v3\EVL\source_snapshot"; man = "$QA\build_v3\EVL\SOURCE_INPUTS.sha256"; receipt = "$QA\build_v3\EVL\RUN_RECEIPT.json"; defs = ''; what = 'EVADE_LEGAL, QA build_v3' },
    @{ tag = 'PCM';    exe = "$QA\build_v3\PCM\m2use\forge_m2use.exe"; md5 = '2cd6d44845e343f8b206b60f876c2165'; sha = 'a60aa7cff6163b172dc4e0c88afffa41516c70b8722ce600817ff39c5feb482e'; tree = "$QA\build_v3\PCM\source_snapshot"; man = "$QA\build_v3\PCM\SOURCE_INPUTS.sha256"; receipt = "$QA\build_v3\PCM\RUN_RECEIPT.json"; defs = ''; what = 'PAWN_CAPMASK v2, QA build_v3' },
    @{ tag = 'CKL';    exe = "$QA\build_v3\CKL\m2use\forge_m2use.exe"; md5 = '8a159aed19f0d1ff0a9ee468e279794f'; sha = 'c643808f19905387cc5b6328f2c464d63208579998777257b179762b33869dbd'; tree = "$QA\build_v3\CKL\source_snapshot"; man = "$QA\build_v3\CKL\SOURCE_INPUTS.sha256"; receipt = "$QA\build_v3\CKL\RUN_RECEIPT.json"; defs = ''; what = 'CHECKERS_KL v3 mode 1, QA build_v3' },
    @{ tag = 'WNP';    exe = "$QA\build_v3\WNP\m2use\forge_m2use.exe"; md5 = '1bf0291be0b2936c394c9a908f7432fe'; sha = '5c8f0ec88a73dc7c1049d47a7a69724f2079834a6c4cd47df61f8308287b478b'; tree = "$QA\build_v3\WNP\source_snapshot"; man = "$QA\build_v3\WNP\SOURCE_INPUTS.sha256"; receipt = "$QA\build_v3\WNP\RUN_RECEIPT.json"; defs = ''; what = 'WITNESS_NOPIN, QA build_v3' },
    @{ tag = 'KPC';    exe = "$QA\build_v3\KPC\m2use\forge_m2use.exe"; md5 = '55e1fe1230b5d19bd5382636a86f9c90'; sha = '67eea5dc9d0deb59c2248c6488ab70c6aa5e22a01d247d2497f2454a8083d4aa'; tree = "$QA\build_v3\KPC\source_snapshot"; man = "$QA\build_v3\KPC\SOURCE_INPUTS.sha256"; receipt = "$QA\build_v3\KPC\RUN_RECEIPT.json"; defs = ''; what = 'KING_PAWN_CACHE v2, QA build_v3 (claim: eval identity)' },
    @{ tag = 'BUN';    exe = "$J2\build\bn3_on\m2use\forge_m2use.exe"; md5 = ''; sha = 'db12981c4c840be4e9a93f04e88f12b1d7e90beb11f73070d0df9c316cc17d3c'; tree = "$J2\work\BUNDLE3\b"; man = "$J2\build\bn3_on\SOURCE_INPUTS.sha256"; receipt = "$J2\build\bn3_on\RUN_RECEIPT.json"; defs = 'FORGE_SPD_EVADE_LEGAL=1,FORGE_SPD_PAWN_CAPMASK=1,FORGE_SPD_CHECKERS_KL=1'; what = 'BUNDLE3 = EVL + PCM v2 + CKL v3 mode 1, job-2 build bn3_on, patch md5 ba2fcf2e78a0e2c85964a1e6e258d150 (pin-equivalent, not byte-identical)' }
)
$switchRx = '^\s*#\s*define\s+(FORGE_SPD_(WITNESS_NOPIN|EVADE_LEGAL|PAWN_CAPMASK|CHECKERS_KL|KING_PAWN_CACHE))\s+(\S+)'
$report = @()
$lines = @("freeze_inputs.ps1 at $(J3-Now); D: free $(J3-Free) GiB")
foreach ($i in $inputs) {
    $tag = $i.tag
    $r = [ordered]@{ tag = $tag; what = $i.what; status = 'OK'; notes = @(); exe_source = $i.exe; expected_md5 = $i.md5; expected_sha256 = $i.sha }
    if (-not (Test-Path -LiteralPath $i.exe)) { $r.status = 'BLOCKED'; $r.notes += 'release exe missing'; $report += $r; continue }
    $r.exe_bytes = (Get-Item -LiteralPath $i.exe).Length
    $r.exe_md5 = J3-Hash $i.exe 'MD5'
    $r.exe_sha256 = J3-Hash $i.exe 'SHA256'
    if ($i.md5 -ne '' -and $r.exe_md5 -ne $i.md5) { $r.status = 'BLOCKED'; $r.notes += "MD5 mismatch: expected $($i.md5), found $($r.exe_md5)" }
    if ($i.sha -ne '' -and $r.exe_sha256 -ne $i.sha) { $r.status = 'BLOCKED'; $r.notes += "SHA256 mismatch against the recorded value $($i.sha)" }
    if ($r.status -eq 'OK') {
        $dstDir = Join-Path $J3_OUT ("bin\" + $tag)
        New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
        $dst = Join-Path $dstDir 'engine.exe'
        if (Test-Path -LiteralPath $dst) {
            if ((J3-Hash $dst 'SHA256') -ne $r.exe_sha256) { throw "refusing: $dst exists and differs from the verified input" }
        } else { Copy-Item -LiteralPath $i.exe -Destination $dst }
        if ((J3-Hash $dst 'SHA256') -ne $r.exe_sha256 -or (J3-Hash $dst 'MD5') -ne $r.exe_md5) { throw "copy of $tag does not hash like its source" }
        $r.exe_copy = $dst
        if ($tag -eq 'LOCK') {
            # second byte-for-byte copy: the positive control of the harness self-test
            $cdir = Join-Path $J3_OUT 'bin\LOCKCOPY'; New-Item -ItemType Directory -Force -Path $cdir | Out-Null
            $c = Join-Path $cdir 'engine.exe'
            if (-not (Test-Path -LiteralPath $c)) { Copy-Item -LiteralPath $i.exe -Destination $c }
            if ((J3-Hash $c 'SHA256') -ne $r.exe_sha256) { throw 'LOCKCOPY does not hash like the lock' }
            $r.lockcopy = $c
        }
    }
    # source manifest of the build, and the tree it was built from
    $r.manifest_file = $i.man
    $r.manifest_sha256 = J3-Hash $i.man 'SHA256'
    if ($i.receipt -ne '') {
        $rc = Get-Content -LiteralPath $i.receipt -Raw | ConvertFrom-Json
        $r.receipt = $i.receipt
        $r.receipt_source_manifest_sha256 = "$($rc.source_manifest_sha256)"
        $r.receipt_exe_sha256 = "$($rc.exe_sha256)"
        if ($rc.PSObject.Properties.Name -contains 'extra_defs') { $r.receipt_extra_defs = @($rc.extra_defs) }
        if ($rc.PSObject.Properties.Name -contains 'recipe') { $r.receipt_recipe = "$($rc.recipe)" }
        if ($rc.PSObject.Properties.Name -contains 'recipe_sha256') { $r.receipt_recipe_sha256 = "$($rc.recipe_sha256)" }
        if ($rc.PSObject.Properties.Name -contains 'compiler_sha256') { $r.receipt_compiler_sha256 = "$($rc.compiler_sha256)" }
        if ("$($rc.exe_sha256)" -ne '' -and "$($rc.exe_sha256)".ToLower() -ne $r.exe_sha256) { $r.status = 'BLOCKED'; $r.notes += 'exe sha256 differs from its RUN_RECEIPT' }
    }
    $r.extra_defs = $i.defs
    if ($i.tree -ne '') {
        $bad = 0; $n = 0; $files = @()
        foreach ($ln in (Get-Content -LiteralPath $i.man)) {
            if ($ln -notmatch '^([0-9a-f]{64})\s+(\S+)$') { continue }
            $want = $Matches[1]; $rel = $Matches[2].Replace('/', '\'); $n++
            $srcFile = Join-Path $i.tree $rel
            $got = if (Test-Path -LiteralPath $srcFile) { J3-Hash $srcFile 'SHA256' } else { 'MISSING' }
            if ($got -ne $want) { $bad++; $r.notes += "source file $rel : manifest $want, tree $got" }
            $dstFile = Join-Path (Join-Path $J3_OUT ("src\" + $tag)) $rel
            if ($got -eq $want) {
                New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dstFile) | Out-Null
                if (-not (Test-Path -LiteralPath $dstFile)) { Copy-Item -LiteralPath $srcFile -Destination $dstFile }
                if ((J3-Hash $dstFile 'SHA256') -ne $want) { throw "copy of $tag $rel does not hash like the manifest" }
            }
            $files += [ordered]@{ file = $Matches[2]; sha256 = $want }
        }
        $r.tree_source = $i.tree; $r.tree_copy = (Join-Path $J3_OUT ("src\" + $tag)); $r.tree_files = $n; $r.tree_mismatches = $bad
        if ($n -ne 20 -or $bad -ne 0) { $r.status = 'BLOCKED'; $r.notes += "source tree: $n files in the manifest, $bad mismatches" }
        $r.nnue_weights_sha256 = (($files | Where-Object { $_.file -eq 'src/nnue_weights.inc' }) | Select-Object -First 1).sha256
        # the meaning of ON: every candidate switch definition as the tree has it
        $sw = @()
        foreach ($rel in 'src\board.cpp', 'src\eval.cpp', 'include\forge\eval.hpp', 'include\forge\board.hpp') {
            $f = Join-Path $i.tree $rel; $k = 0
            foreach ($ln in (Get-Content -LiteralPath $f)) { $k++; if ($ln -match $switchRx) { $sw += ('{0}:{1}: #define {2} {3}' -f $rel, $k, $Matches[1], $Matches[3]) } }
        }
        $r.switch_defaults_in_tree = $sw
    }
    $report += $r
    $lines += ('{0,-7} {1,-8} md5 {2} sha256 {3} manifest {4} defs [{5}] {6}' -f $tag, $r.status, $r.exe_md5, $r.exe_sha256, $r.manifest_sha256, $i.defs, ($r.notes -join '; '))
}
$dir = Join-Path $J3_OUT 'runs\freeze'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
[System.IO.File]::WriteAllText((Join-Path $dir 'INPUTS.json'), ($report | ConvertTo-Json -Depth 6), [System.Text.Encoding]::ASCII)
# other frozen inputs
$fens = "$J2\base\fens_12k_v2.txt"
$lines += ('fens_12k_v2.txt md5 {0} sha256 {1} bytes {2}' -f (J3-Hash $fens 'MD5'), (J3-Hash $fens 'SHA256'), (Get-Item -LiteralPath $fens).Length)
$clang = Join-Path $J3_LM 'clang++.exe'
$lines += ('clang++.exe sha256 {0}' -f (J3-Hash $clang 'SHA256'))
$lines += ('python.exe sha256 {0}' -f (J3-Hash $J3_PY 'SHA256'))
$blocked = @($report | Where-Object { $_.status -ne 'OK' }).Count
$lines += ("FREEZE {0}: {1} tags, {2} blocked" -f $(if ($blocked -eq 0) { 'OK' } else { 'HAS BLOCKED INPUTS' }), $report.Count, $blocked)
[System.IO.File]::WriteAllLines((Join-Path $dir 'INPUTS.txt'), $lines, [System.Text.Encoding]::ASCII)
$lines | ForEach-Object { Write-Output $_ }
foreach ($r in $report) { if ($r.switch_defaults_in_tree) { Write-Output ("ON " + $r.tag + ": " + ($r.switch_defaults_in_tree -join ' | ')) } }
if ($blocked -ne 0) { exit 3 }
exit 0
