# check_consistency.ps1 - do the patch files, the work trees and the builds still describe the same source?
# (PowerShell 5.1, ASCII only; read-only apart from a scratch folder under out\tmp.)
# For every candidate given as Name:tag it checks:
#   1. a fresh copy of the combo29 snapshot + patches\<Name>_after_combo29.patch == out\work\<Name>\b, file by file;
#   2. out\work\<Name>\a == the combo29 snapshot;
#   3. the SOURCE_INPUTS.sha256 written by each build out\build\<tag>_{off,on,v2} == the files of work\<Name>\b now.
# One line per candidate; exit 3 on any mismatch.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File check_consistency.ps1 -Cands KING_PAWN_CACHE:kpc,WITNESS_NOPIN:wit
param(
    [string[]]$Cands = @('KING_PAWN_CACHE:kpc', 'WITNESS_NOPIN:wit', 'EVADE_LEGAL:evd', 'PAWN_CAPMASK:cap', 'CHECKERS_KL:chk'),
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
$Cands = @($Cands | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$base = Join-Path $OUT 'base\combo29_src'
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }
function Tree([string]$root) {
    $h = @{}
    foreach ($f in Get-ChildItem -LiteralPath $root -Recurse -File) { $h[$f.FullName.Substring($root.Length + 1).Replace('\', '/')] = Sha $f.FullName }
    return $h
}
function SameTree($x, $y) {
    if ($x.Count -ne $y.Count) { return $false }
    foreach ($k in $x.Keys) { if (-not $y.ContainsKey($k) -or $y[$k] -ne $x[$k]) { return $false } }
    return $true
}
$baseTree = Tree $base
$bad = 0
foreach ($c in $Cands) {
    $name, $tag = $c -split ':'
    $patch = Join-Path $PACK "patches\${name}_after_combo29.patch"
    $b = Join-Path $OUT "work\$name\b"
    $bTree = Tree $b
    $chk = Join-Path $OUT "tmp\consist_$name"
    if (Test-Path $chk) { Remove-Item -Recurse -Force $chk }
    Copy-Item -Recurse $base $chk
    Get-ChildItem $chk -Recurse -File | ForEach-Object { $_.IsReadOnly = $false }
    Push-Location $chk
    try { & git -c core.autocrlf=false apply --whitespace=nowarn $patch; $ac = $LASTEXITCODE } finally { Pop-Location }
    $applied = ($ac -eq 0) -and (SameTree (Tree $chk) $bTree)
    Remove-Item -Recurse -Force $chk
    $aSame = SameTree (Tree (Join-Path $OUT "work\$name\a")) $baseTree
    $builds = @()
    foreach ($suffix in 'off', 'on', 'v2') {
        $m = Join-Path $OUT "build\${tag}_$suffix\SOURCE_INPUTS.sha256"
        if (-not (Test-Path $m)) { continue }
        $ok = $true; $n = 0
        foreach ($line in [System.IO.File]::ReadAllLines($m)) {
            if ($line -eq '') { continue }
            $sha, $rel = $line -split '  ', 2
            $n++
            if (-not $bTree.ContainsKey($rel) -or $bTree[$rel] -ne $sha) { $ok = $false }
        }
        $builds += ("{0}_{1}:{2}" -f $tag, $suffix, $(if ($ok -and $n -eq 20) { 'same source' } else { 'STALE' }))
        if (-not ($ok -and $n -eq 20)) { $bad++ }
    }
    if (-not $applied -or -not $aSame) { $bad++ }
    Write-Output ("CONSISTENCY {0}: patch md5 {1} sha256 {2}; snapshot+patch = work tree: {3}; work a = snapshot: {4}; builds [{5}]" -f $name,
        (Get-FileHash -Algorithm MD5 -LiteralPath $patch).Hash.ToLower(), (Sha $patch), $(if ($applied) { 'YES' } else { 'NO' }), $(if ($aSame) { 'YES' } else { 'NO' }), ($builds -join ', '))
}
if ($bad -ne 0) { exit 3 }
