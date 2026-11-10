# make_manifest.ps1 - MD5/SHA256 manifest and DONE note of the job-3 handoff (PowerShell 5.1, ASCII only).
#
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File make_manifest.ps1            writes MANIFEST.tsv and DONE.md
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File make_manifest.ps1 -Verify    rehashes every listed file
#
# MANIFEST.tsv part 1 lists every file of the pack on the branch (not itself, not DONE.md) with bytes, MD5 and
# SHA256. Part 2 is the inventory of what stays local under out\job3: executables, probes, receipts, ledgers,
# logs, with the same hashes. DONE.md lists every handoff file with its MD5; it does not list itself, and its own
# MD5 goes into the final receipt. Hashes come from System.Security.Cryptography, not from Get-FileHash.
#
# The log of -Verify is itself a handoff file: MANIFEST_VERIFY.log, listed in both lists. A list cannot hold the
# hash of a log that is written only after the list is checked, unless the log's text is known beforehand. So the
# text of a clean verification is fixed: the time stamp of the manifest it verified and the line
# "VERIFY OK: n manifest entries, d DONE entries, 0 problems", with no time of its own. Writing the manifest
# enters the hash of exactly that text and leaves a file that says "not verified yet". -Verify checks every other
# file, writes its real result into the log, and then compares the log it wrote with the listed hash: they agree
# only if the verification found no problem in exactly this manifest. Any problem leaves a log that names it and
# that no longer matches the lists.
param([switch]$Verify)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'job3_env.ps1')
[void](J3-Pin 0x78)
$manifest = Join-Path $J3_PACK 'MANIFEST.tsv'
$done = Join-Path $J3_PACK 'DONE.md'
$vlog = Join-Path $J3_PACK 'MANIFEST_VERIFY.log'
$vlogRel = 'fable_movegen_proof/MANIFEST_VERIFY.log'

function Rel([string]$full, [string]$root) { return $full.Substring($root.Length).TrimStart('\').Replace('\', '/') }
function CleanText([string]$stamp, [int]$n, [int]$d) {
    return ("make_manifest.ps1 -Verify of the manifest written {0}`nVERIFY OK: {1} manifest entries, {2} DONE entries, 0 problems`n" -f $stamp, $n, $d)
}
function HashText([string]$text, [string]$alg) {
    if ($alg -eq 'MD5') { $h = [System.Security.Cryptography.MD5]::Create() } else { $h = [System.Security.Cryptography.SHA256]::Create() }
    try { $b = $h.ComputeHash([System.Text.Encoding]::ASCII.GetBytes($text)) } finally { $h.Dispose() }
    return ([System.BitConverter]::ToString($b) -replace '-', '').ToLower()
}

if ($Verify) {
    $bad = 0; $n = 0; $out = @(); $want = @{}
    $lines = Get-Content -LiteralPath $manifest
    $stamp = $(if ($lines[0] -match 'Written ([0-9: -]+ Vienna)') { $Matches[1] } else { 'unknown' })
    foreach ($ln in $lines) {
        $c = $ln -split "`t"
        if ($c.Count -lt 5 -or $c[0] -notin 'branch', 'local') { continue }
        $n++
        if ($c[0] -eq 'branch' -and $c[1] -eq $vlogRel) { $want['md5'] = $c[3]; $want['sha256'] = $c[4]; continue }      # this run's own log: compared after it is written
        $root = if ($c[0] -eq 'branch') { $J3_REPO } else { $J3_OUT }
        $p = Join-Path $root $c[1].Replace('/', '\')
        if (-not (Test-Path -LiteralPath $p)) { $bad++; $out += "MISSING $($c[0]) $($c[1])"; continue }
        if ((J3-Hash $p 'SHA256') -ne $c[4] -or (J3-Hash $p 'MD5') -ne $c[3]) { $bad++; $out += "CHANGED $($c[0]) $($c[1])" }
    }
    $dn = 0
    foreach ($ln in (Get-Content -LiteralPath $done)) {
        if ($ln -match '^\| `([^`]+)` \| `([0-9a-f]{32})` \|') {
            $dn++
            if ($Matches[1] -eq $vlogRel) { $want['done_md5'] = $Matches[2]; continue }
            $p = Join-Path $J3_REPO $Matches[1].Replace('/', '\')
            if (-not (Test-Path -LiteralPath $p) -or (J3-Hash $p 'MD5') -ne $Matches[2]) { $bad++; $out += "DONE.md: CHANGED OR MISSING $($Matches[1])" }
        }
    }
    if ($bad -eq 0) { $text = CleanText $stamp $n $dn }
    else { $text = ("make_manifest.ps1 -Verify of the manifest written {0}`n{1}`nVERIFY FAILED: {2} manifest entries, {3} DONE entries, {4} problems`n" -f $stamp, ($out -join "`n"), $n, $dn, $bad) }
    [System.IO.File]::WriteAllText($vlog, $text, [System.Text.Encoding]::ASCII)
    # the log just written against the hash the two lists hold for it
    if (-not $want.ContainsKey('md5') -or -not $want.ContainsKey('done_md5') -or (J3-Hash $vlog 'SHA256') -ne $want['sha256'] -or (J3-Hash $vlog 'MD5') -ne $want['md5'] -or (J3-Hash $vlog 'MD5') -ne $want['done_md5']) {
        $bad++
        Write-Output $text.TrimEnd()
        Write-Output "CHANGED branch $vlogRel (the log of this verification is not the log the lists expect: see the lines above)"
        exit 3
    }
    Write-Output $text.TrimEnd()
    exit 0
}

$stamp = J3-Now
# until -Verify has run, the log says so; the lists get the hash of the text a clean verification writes
[System.IO.File]::WriteAllText($vlog, "not verified yet: run make_manifest.ps1 -Verify`n", [System.Text.Encoding]::ASCII)
$branchFiles = Get-ChildItem -LiteralPath $J3_PACK -Recurse -File | Where-Object { $_.FullName -ne $manifest -and $_.FullName -ne $done } | Sort-Object FullName
# what stays local: executables, frozen source copies, probes, receipts, ledgers, logs, seed files, failure evidence
# (not tmp and not pycache: they hold nothing that a result depends on)
$local = @()
foreach ($sub in 'bin', 'src', 'aux', 'aux2', 'runs', 'logs', 'fail', 'corpus') {
    $d = Join-Path $J3_OUT $sub
    if (Test-Path -LiteralPath $d) { $local += Get-ChildItem -LiteralPath $d -Recurse -File }
}
$handoff = Get-ChildItem -LiteralPath $J3_PACK -Recurse -File | Where-Object { $_.FullName -ne $done } | Sort-Object FullName
if (-not (Test-Path -LiteralPath $manifest)) { $handoffCount = $handoff.Count + 1 } else { $handoffCount = $handoff.Count }      # MANIFEST.tsv is a handoff file
$clean = CleanText $stamp ($branchFiles.Count + $local.Count) $handoffCount

$rows = @("# MANIFEST of job 3 (move-generator proof). Written $stamp. Columns: where, path, bytes, md5, sha256.",
          "# 'branch' paths are relative to the repo root (branch fable52-movegen-proof-20261110); 'local' paths are relative to $J3_OUT and are not on the branch.",
          "# This file and DONE.md are not listed here; DONE.md lists this file. MANIFEST_VERIFY.log is listed with the hash of the log a clean -Verify of this manifest writes.")
foreach ($f in $branchFiles) {
    if ($f.FullName -eq $vlog) { $rows += ("branch`t{0}`t{1}`t{2}`t{3}" -f $vlogRel, $clean.Length, (HashText $clean 'MD5'), (HashText $clean 'SHA256')); continue }
    $rows += ("branch`t{0}`t{1}`t{2}`t{3}" -f (Rel $f.FullName $J3_REPO), $f.Length, (J3-Hash $f.FullName 'MD5'), (J3-Hash $f.FullName 'SHA256'))
}
foreach ($f in ($local | Sort-Object FullName)) {
    $rows += ("local`t{0}`t{1}`t{2}`t{3}" -f (Rel $f.FullName $J3_OUT), $f.Length, (J3-Hash $f.FullName 'MD5'), (J3-Hash $f.FullName 'SHA256'))
}
[System.IO.File]::WriteAllLines($manifest, $rows, [System.Text.Encoding]::ASCII)

$d = @('# DONE: handoff files of job 3', '',
       "Written $stamp. Every file of the pack ``fable_movegen_proof/`` on branch ``fable52-movegen-proof-20261110`` with its MD5.",
       'This note does not list itself; its own MD5 is in the final receipt of the job. `MANIFEST.tsv` adds SHA256 and the inventory of the artifacts that stay local under `out\job3`.',
       '`VERIFY_EVIDENCE.log` is the output of `scripts/verify_evidence.ps1`; `MANIFEST_VERIFY.log` is the output of `scripts/make_manifest.ps1 -Verify` on this manifest (its MD5 here is that of a clean verification; see the head of the script).', '',
       '| File | MD5 |', '|---|---|')
$handoff = Get-ChildItem -LiteralPath $J3_PACK -Recurse -File | Where-Object { $_.FullName -ne $done } | Sort-Object FullName
foreach ($f in $handoff) {
    if ($f.FullName -eq $vlog) { $d += ('| `{0}` | `{1}` |' -f $vlogRel, (HashText $clean 'MD5')); continue }
    $d += ('| `{0}` | `{1}` |' -f (Rel $f.FullName $J3_REPO), (J3-Hash $f.FullName 'MD5'))
}
[System.IO.File]::WriteAllLines($done, $d, [System.Text.Encoding]::ASCII)
if ($handoff.Count -ne $handoffCount) { throw "make_manifest: $($handoff.Count) handoff files, $handoffCount were expected when the log text was fixed" }
Write-Output ("MANIFEST.tsv: {0} branch files, {1} local files; DONE.md: {2} files" -f $branchFiles.Count, $local.Count, $handoff.Count)
Write-Output ("MANIFEST.tsv md5 {0}; DONE.md md5 {1}; not verified yet: run -Verify" -f (J3-Hash $manifest 'MD5'), (J3-Hash $done 'MD5'))
