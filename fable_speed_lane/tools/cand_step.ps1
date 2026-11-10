# cand_step.ps1 - routine steps for one candidate, each printing one short result line (PowerShell 5.1, ASCII).
#   -Stage patch : write patches\<Name>_after_combo29.patch from work\<Name>\{a,b} and prove it re-creates b
#   -Stage build : lock-recipe builds <Tag>_off (switch 0) and <Tag>_on (-D<Def>=1); skipped when present
#   -Stage off   : byte ranges of the switch-0 exe against the lock exe
#   -Stage pins  : the 12 pins on the switch-1 exe
#   -Stage abba  : INDICATIVE A/B, lock exe vs switch-1 exe, -Blocks blocks, net -Net
#   -Stage prim  : harness on the switch-1 tree over -Fens FENs (0 = all), transcript compared with the base
# Everything runs pinned to -Mask (default CPU 3) at Idle and writes under out\.
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][string]$Def,
    [Parameter(Mandatory = $true)][ValidateSet('patch', 'build', 'off', 'pins', 'abba', 'prim')][string]$Stage,
    [int]$Blocks = 10,
    [int]$Depth = 20,
    [ValidateSet('on', 'off')][string]$Net = 'on',
    [int]$Fens = 0,
    [string]$Src = '',
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
$work = Join-Path $OUT "work\$Name"
if ($Src -eq '') { $Src = Join-Path $work 'b' }
$idDir = Join-Path $OUT "id\$Name"
New-Item -ItemType Directory -Force $idDir | Out-Null
$lock = Join-Path $OUT 'base\combo29_lock_E1284F7F.exe'
# -Def may name several switches (the bundle): "A,B" or "A=1,B=1"; a bare name means =1
$onDefs = (@($Def -split ',' | Where-Object { $_ }) | ForEach-Object { if ($_ -match '=') { $_ } else { "$_=1" } }) -join ','
$offExe = Join-Path $OUT "build\${Tag}_off\m2use\forge_m2use.exe"
$onExe = Join-Path $OUT "build\${Tag}_on\m2use\forge_m2use.exe"
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }
function RunPinned([string]$exe, [string]$argLine, [string]$outFile) {
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PIN, '-Exe', $exe, '-Mask', $Mask, '-ArgLine', $argLine, '-OutFile', $outFile)
    & powershell.exe @a | Out-Null
    return $LASTEXITCODE
}

switch ($Stage) {
    'patch' {
        $patch = Join-Path $PACK "patches\${Name}_after_combo29.patch"
        New-Item -ItemType Directory -Force (Split-Path $patch -Parent) | Out-Null
        Push-Location $work
        try {
            # --no-prefix: the folder names a and b are the prefixes, so the patch reads "--- a/src/x.cpp" (-p1)
            $txt = & git -c core.autocrlf=false -c core.safecrlf=false diff --no-index --no-prefix --no-color -U3 a b
            $code = $LASTEXITCODE
        } finally { Pop-Location }
        if ($code -ne 1) { throw "git diff exit $code (1 = differences expected)" }
        $body = (@($txt | Where-Object { $_ -notmatch '^(diff --git|index [0-9a-f]+\.\.)' }) -join "`n") + "`n"
        [System.IO.File]::WriteAllText($patch, $body, (New-Object System.Text.UTF8Encoding($false)))
        # proof: a fresh copy of the base + the patch = the work tree, file by file
        $chk = Join-Path $OUT "tmp\patchcheck_$Name"
        if (Test-Path $chk) { Remove-Item -Recurse -Force $chk }
        Copy-Item -Recurse (Join-Path $OUT 'base\combo29_src') $chk
        Get-ChildItem $chk -Recurse -File | ForEach-Object { $_.IsReadOnly = $false }
        Push-Location $chk
        try { & git -c core.autocrlf=false apply --whitespace=nowarn $patch; $ac = $LASTEXITCODE } finally { Pop-Location }
        if ($ac -ne 0) { throw 'git apply failed on a fresh copy of the base' }
        $bad = 0; $changed = @()
        foreach ($f in Get-ChildItem $Src -Recurse -File) {
            $rel = $f.FullName.Substring($Src.Length + 1)
            if ((Sha $f.FullName) -ne (Sha (Join-Path $chk $rel))) { $bad++ }
            if ((Sha $f.FullName) -ne (Sha (Join-Path $OUT "base\combo29_src\$rel"))) { $changed += $rel.Replace('\', '/') }
        }
        Remove-Item -Recurse -Force $chk
        $adds = @($txt | Where-Object { $_ -match '^\+[^+]' -or $_ -eq '+' }).Count
        $dels = @($txt | Where-Object { $_ -match '^-[^-]' -or $_ -eq '-' }).Count
        Write-Output ("PATCH {0}: md5 {1}, +{2} -{3} lines, files [{4}], base+patch = work tree: {5}" -f (Split-Path $patch -Leaf),
            (Get-FileHash -Algorithm MD5 -LiteralPath $patch).Hash.ToLower(), $adds, $dels, ($changed -join ' '), $(if ($bad -eq 0) { 'YES' } else { "NO ($bad files differ)" }))
        if ($bad -ne 0) { exit 3 }
    }
    'build' {
        foreach ($v in @(@("${Tag}_off", ''), @("${Tag}_on", $onDefs))) {
            $root = Join-Path $OUT "build\$($v[0])"
            if (Test-Path (Join-Path $root 'RUN_RECEIPT.json')) { Write-Output "BUILD $($v[0]): present"; continue }
            $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $T 'spd_build.ps1'), '-Tag', $v[0], '-Src', $Src, '-Mask', $Mask)
            if ($v[1] -ne '') { $a += @('-ExtraDefs', $v[1]) }
            $t0 = Get-Date
            & powershell.exe @a | Out-Null
            if ($LASTEXITCODE -ne 0) { Write-Output "BUILD $($v[0]): FAILED, see $root\build.log"; exit 3 }
            $r = Get-Content (Join-Path $root 'RUN_RECEIPT.json') -Raw | ConvertFrom-Json
            Write-Output ("BUILD {0}: ok in {1} s, training nodes {2}, exe sha256 {3} md5 {4}" -f $v[0], [int]((Get-Date) - $t0).TotalSeconds,
                ($r.training_nodes -join '/'), $r.exe_sha256, $r.exe_md5)
        }
    }
    'off' {
        $rc = RunPinned $PY "-I -B `"$T\bytecmp.py`" `"$lock`" `"$offExe`" --json `"$idDir\bytecmp_lock_vs_off.json`"" "$idDir\bytecmp_lock_vs_off.txt"
        $cmp = Get-Content "$idDir\bytecmp_lock_vs_off.json" -Raw | ConvertFrom-Json
        Write-Output ("OFF {0}: {1}; debug-record bytes {2}, other bytes {3}; ranges {4}" -f $Name, $cmp.verdict, $cmp.differing_bytes_debug,
            $cmp.differing_bytes_other, (($cmp.ranges | ForEach-Object { "$($_.from)-$($_.to)" }) -join ','))
        if ($rc -ne 0) { exit 3 }
    }
    'pins' {
        $rc = RunPinned $PY "-I -B `"$T\spd_uci.py`" pins --exe `"$onExe`" --out `"$idDir\pins_on.json`"" "$idDir\pins_on.txt"
        Write-Output ("PINS {0} ON: {1} (exit {2})" -f $Name, (Get-Content "$idDir\pins_on.txt" -Tail 1), $rc)
        if ($rc -ne 0) { exit 3 }
    }
    'abba' {
        $o = Join-Path $OUT ("id\$Name\abba_" + $Net + '_' + (Get-Date -Format 'HHmmss'))
        $rc = RunPinned $PY "-I -B `"$T\spd_uci.py`" abba --a `"$lock`" --b `"$onExe`" --out `"$o`" --blocks $Blocks --depth $Depth --net $Net" "$o.txt"
        Get-Content "$o.txt" | Where-Object { $_ -match '^ABBA INDICATIVE|^ERROR|mismatch|!=' } | ForEach-Object { Write-Output ("{0} {1}" -f $Name, $_) }
        if ($rc -ne 0) { Write-Output "ABBA exit $rc"; exit 3 }
    }
    'prim' {
        $ptag = "${Tag}_on"
        $pexe = Join-Path $OUT "build\prim_$ptag\prim_dump.exe"
        if (-not (Test-Path $pexe)) {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PACK 'tests\build_prim.ps1') -Tag $ptag -Src $Src -ExtraDefs $onDefs -Mask $Mask | Out-Null
            if ($LASTEXITCODE -ne 0) { Write-Output "PRIM build failed for $ptag"; exit 3 }
        }
        $n = $(if ($Fens -gt 0) { "$Fens" } else { 'all' })
        $baseOut = Join-Path $OUT "id\prim\base_$n.tsv"
        $argTail = $(if ($Fens -gt 0) { " 0 $Fens" } else { '' })
        if (-not (Test-Path $baseOut)) {
            $rc = RunPinned (Join-Path $OUT 'build\prim_base\prim_dump.exe') "`"$OUT\base\fens_12k_v2.txt`" `"$baseOut`"$argTail" "$baseOut.log"
            if ($rc -ne 0) { Write-Output "PRIM base run failed (exit $rc)"; exit 3 }
        }
        $candOut = "$idDir\prim_on_$n.tsv"
        $rc = RunPinned $pexe "`"$OUT\base\fens_12k_v2.txt`" `"$candOut`"$argTail" "$candOut.log"
        $same = ((Sha $candOut) -eq (Sha $baseOut))
        Write-Output ("PRIM {0} ON ({1} FENs): {2}; transcript sha256 {3}; equal to base: {4}" -f $Name, $n, (Get-Content "$candOut.log" -Tail 1), (Sha $candOut), $same)
        if ($rc -ne 0 -or -not $same) { exit 3 }
    }
}
