# make_manifest.ps1 - MD5/SHA256 manifest and DONE note of the job-3 handoff (PowerShell 5.1, ASCII only).
#
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File make_manifest.ps1            writes MANIFEST.tsv and DONE.md
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File make_manifest.ps1 -Verify    rehashes every listed file
#
# MANIFEST.tsv part 1 lists every file of the pack on the branch (not itself, not DONE.md) with bytes, MD5 and
# SHA256. Part 2 is the inventory of what stays local under out\job3: executables, probes, receipts, ledgers,
# logs, with the same hashes. DONE.md lists every handoff file with its MD5; it does not list itself, and its own
# MD5 goes into the final receipt. Hashes come from System.Security.Cryptography, not from Get-FileHash.
param([switch]$Verify)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'job3_env.ps1')
[void](J3-Pin 0x78)
$manifest = Join-Path $J3_PACK 'MANIFEST.tsv'
$done = Join-Path $J3_PACK 'DONE.md'

function Rel([string]$full, [string]$root) { return $full.Substring($root.Length).TrimStart('\').Replace('\', '/') }

if ($Verify) {
    $bad = 0; $n = 0
    foreach ($ln in (Get-Content -LiteralPath $manifest)) {
        $c = $ln -split "`t"
        if ($c.Count -lt 5 -or $c[0] -notin 'branch', 'local') { continue }
        $root = if ($c[0] -eq 'branch') { $J3_REPO } else { $J3_OUT }
        $p = Join-Path $root $c[1].Replace('/', '\')
        $n++
        if (-not (Test-Path -LiteralPath $p)) { $bad++; Write-Output "MISSING $($c[0]) $($c[1])"; continue }
        if ((J3-Hash $p 'SHA256') -ne $c[4] -or (J3-Hash $p 'MD5') -ne $c[3]) { $bad++; Write-Output "CHANGED $($c[0]) $($c[1])" }
    }
    $dn = 0
    foreach ($ln in (Get-Content -LiteralPath $done)) {
        if ($ln -match '^\| `([^`]+)` \| `([0-9a-f]{32})` \|') {
            $dn++
            $p = Join-Path $J3_REPO $Matches[1].Replace('/', '\')
            if (-not (Test-Path -LiteralPath $p) -or (J3-Hash $p 'MD5') -ne $Matches[2]) { $bad++; Write-Output "DONE.md: CHANGED OR MISSING $($Matches[1])" }
        }
    }
    Write-Output ("VERIFY {0}: {1} manifest entries, {2} DONE entries, {3} problems" -f $(if ($bad -eq 0) { 'OK' } else { 'FAILED' }), $n, $dn, $bad)
    if ($bad -ne 0) { exit 3 }
    exit 0
}

$rows = @("# MANIFEST of job 3 (move-generator proof). Written $(J3-Now). Columns: where, path, bytes, md5, sha256.",
          "# 'branch' paths are relative to the repo root (branch fable52-movegen-proof-20261110); 'local' paths are relative to $J3_OUT and are not on the branch.",
          "# This file and DONE.md are not listed here; DONE.md lists this file.")
$branchFiles = Get-ChildItem -LiteralPath $J3_PACK -Recurse -File | Where-Object { $_.FullName -ne $manifest -and $_.FullName -ne $done } | Sort-Object FullName
foreach ($f in $branchFiles) {
    $rows += ("branch`t{0}`t{1}`t{2}`t{3}" -f (Rel $f.FullName $J3_REPO), $f.Length, (J3-Hash $f.FullName 'MD5'), (J3-Hash $f.FullName 'SHA256'))
}
# what stays local: binaries, receipts, ledgers, logs, failure evidence (not tmp, not pycache, not frozen source copies:
# the source trees are identified by their manifests in runs\freeze\INPUTS.json)
$local = @()
foreach ($sub in 'bin', 'aux', 'runs', 'logs', 'fail', 'corpus') {
    $d = Join-Path $J3_OUT $sub
    if (Test-Path -LiteralPath $d) { $local += Get-ChildItem -LiteralPath $d -Recurse -File }
}
foreach ($f in ($local | Sort-Object FullName)) {
    $rows += ("local`t{0}`t{1}`t{2}`t{3}" -f (Rel $f.FullName $J3_OUT), $f.Length, (J3-Hash $f.FullName 'MD5'), (J3-Hash $f.FullName 'SHA256'))
}
[System.IO.File]::WriteAllLines($manifest, $rows, [System.Text.Encoding]::ASCII)

$d = @('# DONE: handoff files of job 3', '',
       "Written $(J3-Now). Every file of the pack ``fable_movegen_proof/`` on branch ``fable52-movegen-proof-20261110`` with its MD5.",
       'This note does not list itself; its own MD5 is in the final receipt of the job. `MANIFEST.tsv` adds SHA256 and the inventory of the artifacts that stay local under `out\job3`.', '',
       '| File | MD5 |', '|---|---|')
$handoff = Get-ChildItem -LiteralPath $J3_PACK -Recurse -File | Where-Object { $_.FullName -ne $done } | Sort-Object FullName
foreach ($f in $handoff) { $d += ('| `{0}` | `{1}` |' -f (Rel $f.FullName $J3_REPO), (J3-Hash $f.FullName 'MD5')) }
[System.IO.File]::WriteAllLines($done, $d, [System.Text.Encoding]::ASCII)
Write-Output ("MANIFEST.tsv: {0} branch files, {1} local files; DONE.md: {2} files" -f $branchFiles.Count, $local.Count, $handoff.Count)
Write-Output ("MANIFEST.tsv md5 {0}; DONE.md md5 {1}" -f (J3-Hash $manifest 'MD5'), (J3-Hash $done 'MD5'))
