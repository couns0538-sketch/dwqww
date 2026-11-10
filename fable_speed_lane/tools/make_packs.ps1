# make_packs.ps1 - D:-only rebuild packs for QA, laid out like the Engine Coder PCPACK (PowerShell 5.1, ASCII only).
# One folder per item under out\packs\<NAME>\ :
#   <name>_src.zip          the 20 source files (include\ + src\) with the patch applied
#   SOURCE_INPUTS.sha256    per-file sha256 of that tree (QA's format; equals the manifest of this job's builds)
#   <NAME>_after_combo29.patch, frozen_train_cmds.txt (the lock workload, unchanged), BUILD_RECIPE.txt,
#   PCPACK_HANDOFF.md, exe\forge_<tag>_{off,on}.exe with their RUN_RECEIPT json, MD5SUMS.txt, SHA256SUMS.txt
# Nothing here is committed to the branch (engine source and net stay on D:). Refuses to overwrite a pack.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File make_packs.ps1 [-Only BUNDLE4]
param(
    [string[]]$Only = @(),
    [string]$PackRoot = '',
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$Only = @($Only | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$items = @(
    @{ N = 'BUNDLE4'; G = 'bn4'; D = 'FORGE_SPD_WITNESS_NOPIN=1,FORGE_SPD_EVADE_LEGAL=1,FORGE_SPD_PAWN_CAPMASK=1,FORGE_SPD_CHECKERS_KL=1'; S = 'the four new candidates in one tree' },
    @{ N = 'BUNDLE3'; G = 'bn3'; D = 'FORGE_SPD_EVADE_LEGAL=1,FORGE_SPD_PAWN_CAPMASK=1,FORGE_SPD_CHECKERS_KL=1'; S = 'three of the new candidates in one tree (no WITNESS_NOPIN)' },
    @{ N = 'WITNESS_NOPIN'; G = 'wit'; D = 'FORGE_SPD_WITNESS_NOPIN=1'; S = 'new candidate (LISTED-UNBUILT)' },
    @{ N = 'EVADE_LEGAL'; G = 'evd'; D = 'FORGE_SPD_EVADE_LEGAL=1'; S = 'new candidate (LISTED-UNBUILT)' },
    @{ N = 'PAWN_CAPMASK'; G = 'cap'; D = 'FORGE_SPD_PAWN_CAPMASK=1'; S = 'new candidate (UNLISTED)' },
    @{ N = 'CHECKERS_KL'; G = 'chk'; D = 'FORGE_SPD_CHECKERS_KL=1'; S = 'new candidate (LISTED-UNBUILT)' },
    @{ N = 'KING_PAWN_CACHE'; G = 'kpc'; D = 'FORGE_SPD_KING_PAWN_CACHE=1'; S = 'EXTRA, NOT NEW: mechanism built before (commit 928f1ff7, 2026-10-13); see DUPCHECK.md' },
    @{ N = 'BUNDLE'; G = 'bun'; D = 'FORGE_SPD_WITNESS_NOPIN=1,FORGE_SPD_EVADE_LEGAL=1,FORGE_SPD_PAWN_CAPMASK=1,FORGE_SPD_CHECKERS_KL=1,FORGE_SPD_KING_PAWN_CACHE=1'; S = 'EXTRA: BUNDLE4 plus the not-new KING_PAWN_CACHE' }
)
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }
function Md5([string]$p) { (Get-FileHash -Algorithm MD5 -LiteralPath $p).Hash.ToLower() }
function WriteLf([string]$path, [string[]]$lines) { [System.IO.File]::WriteAllText($path, (($lines -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding($false))) }
$lockSha = 'e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e'
$workload = Join-Path $OUT 'base\frozen_train_cmds.txt'
if ((Sha $workload) -ne '1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30') { throw 'workload is not the lock workload' }
foreach ($it in $items) {
    if ($Only.Count -gt 0 -and $Only -notcontains $it.N) { continue }
    $name = $it.N; $tag = $it.G
    $tree = Join-Path $OUT "work\$name\b"
    $dst = Join-Path $(if ($PackRoot) { $PackRoot } else { Join-Path $OUT 'packs' }) $name
    if (Test-Path $dst) { throw "refusing: $dst exists" }
    $onRoot = Join-Path $OUT "build\${tag}_on"; $offRoot = Join-Path $OUT "build\${tag}_off"
    foreach ($need in (Join-Path $onRoot 'm2use\forge_m2use.exe'), (Join-Path $offRoot 'm2use\forge_m2use.exe'), (Join-Path $onRoot 'SOURCE_INPUTS.sha256')) {
        if (-not (Test-Path $need)) { throw "missing $need" }
    }
    # the tree being packed must be the tree the ON exe was built from
    $rels = @()
    foreach ($line in [System.IO.File]::ReadAllLines((Join-Path $onRoot 'SOURCE_INPUTS.sha256'))) {
        if ($line -eq '') { continue }
        $sha, $rel = $line -split '  ', 2
        if ((Sha (Join-Path $tree $rel.Replace('/', '\'))) -ne $sha) { throw "$name work tree differs from the source of ${tag}_on at $rel" }
        $rels += $rel
    }
    if ($rels.Count -ne 20) { throw "$name source manifest has $($rels.Count) files, not 20" }
    New-Item -ItemType Directory -Force (Join-Path $dst 'exe') | Out-Null
    $zipName = $name.ToLower() + '_src.zip'
    $zip = [System.IO.Compression.ZipFile]::Open((Join-Path $dst $zipName), [System.IO.Compression.ZipArchiveMode]::Create)
    try { foreach ($rel in $rels) { [void][System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, (Join-Path $tree $rel.Replace('/', '\')), $rel, [System.IO.Compression.CompressionLevel]::Optimal) } } finally { $zip.Dispose() }
    Copy-Item (Join-Path $onRoot 'SOURCE_INPUTS.sha256') (Join-Path $dst 'SOURCE_INPUTS.sha256')
    $patch = Join-Path $PACK "patches\${name}_after_combo29.patch"
    Copy-Item $patch $dst
    Copy-Item $workload (Join-Path $dst 'frozen_train_cmds.txt')
    Copy-Item (Join-Path $onRoot 'm2use\forge_m2use.exe') (Join-Path $dst "exe\forge_${tag}_on.exe")
    Copy-Item (Join-Path $offRoot 'm2use\forge_m2use.exe') (Join-Path $dst "exe\forge_${tag}_off.exe")
    Copy-Item (Join-Path $onRoot 'RUN_RECEIPT.json') (Join-Path $dst "exe\RUN_RECEIPT_${tag}_on.json")
    Copy-Item (Join-Path $offRoot 'RUN_RECEIPT.json') (Join-Path $dst "exe\RUN_RECEIPT_${tag}_off.json")
    $defs = @($it.D -split ',')
    $dTokens = ($defs | ForEach-Object { "'-D" + $_ + "'" }) -join ','
    $changed = @(Get-Content $patch | Where-Object { $_ -match '^\+\+\+ b/' } | ForEach-Object { $_.Substring(6) })
    WriteLf (Join-Path $dst 'BUILD_RECIPE.txt') @(
        "FORGE $name - combo29 clang ThinLTO+PGO build recipe (fable2 speed lane, $(NowVienna))",
        '',
        'Base lock',
        "  CURRENT_LOCK combo29, exe sha256 $lockSha",
        '  recipe: the lock build.log command lines; PGO workload frozen_train_cmds.txt',
        '  (sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30), unchanged in this pack',
        '',
        'What this pack adds',
        "  $zipName = combo29 include/+src/ with ${name}_after_combo29.patch applied (20 files);",
        "  changed against the lock snapshot: $($changed -join ', ')",
        "  patch md5 $(Md5 $patch)",
        '  every added line sits behind a switch that defaults to 0; with all switches at 0 the build equals the lock',
        '  in every code and data byte (only the embedded PDB hash and path differ).',
        '',
        'Switches for the ON build (appended after the six lock switches)',
        ('  ' + (($defs | ForEach-Object { '-D' + $_ }) -join ' ')),
        '',
        'PC build with QA''s own script (D: only, Idle, refuses to overwrite)',
        "  unzip $zipName into Src\  (must contain include\ and src\)",
        '  powershell -NoProfile -ExecutionPolicy Bypass -File D:\forge_qa\quiet_abba_e4_c2_20261109\c_t2_build_extradefs.ps1 `',
        "    -Tag $tag -Src <Src> -OutRoot <build folder> -Workload <this pack>\frozen_train_cmds.txt ``",
        "    -ExtraDefs $dTokens",
        "  Output: <build folder>\$tag\m2use\forge_m2use.exe",
        '  A rebuild will not match any other exe byte for byte (embedded PDB paths). Binding checks: the pins below.',
        '',
        'Expected pins (Threads 1, Hash 16, OwnBook false) - identical to the lock, because the patch is node-identical',
        '  net-on  312866/862329/3024920/12389307/34048354',
        '  net-off 375354/907205/2448617/13573040/24506465',
        '  perft5  4865609 (startpos), 193690690 (kiwipete)',
        '',
        'This job''s own builds of the same tree (lock recipe, CPU 3, Idle), for reference only',
        "  exe\forge_${tag}_on.exe   sha256 $(Sha (Join-Path $dst "exe\forge_${tag}_on.exe"))",
        "  exe\forge_${tag}_off.exe  sha256 $(Sha (Join-Path $dst "exe\forge_${tag}_off.exe"))  (all switches 0)"
    )
    WriteLf (Join-Path $dst 'PCPACK_HANDOFF.md') @(
        'PCPACK_HANDOFF',
        'From: fable2 speed lane (Claude Fable 5.2) -> To: Engine QA',
        "Item: $name - $($it.S)",
        "Written: $(NowVienna)",
        '',
        '## Role',
        'PC rebuild kit so QA can build this item ON with the lock recipe and time it in the quiet ABBA.',
        'No games, no queue edit, no lock change by this job. No speed claim: this job''s timings are INDICATIVE only.',
        '',
        '## Contents',
        '| file | role |',
        '|---|---|',
        "| $zipName | combo29 include/ + src/ with the patch applied (20 files) |",
        '| SOURCE_INPUTS.sha256 | per-file sha256 of that tree |',
        "| ${name}_after_combo29.patch | the patch against the combo29 snapshot (-p1) |",
        '| frozen_train_cmds.txt | lock PGO workload, unchanged |',
        '| BUILD_RECIPE.txt | build command with QA''s own script, switches, expected pins |',
        "| exe\forge_${tag}_on.exe, exe\forge_${tag}_off.exe | this job's builds (switches 1 / all 0), with their receipts |",
        '| MD5SUMS.txt, SHA256SUMS.txt | this pack |',
        '',
        '## Evidence (branch fable52-speed-lane-20261109, folder fable_speed_lane)',
        'BENCH.md section 2 (identity ladder: switch-0 byte compare, 12 pins, harness over 12,000 FENs, cold depth 13 net on',
        'and net off against the lock rows, warm session, Threads 2-4 soak, perft set) and section 3 (INDICATIVE timing;',
        'read 3.1 and 3.2, not the superseded 3.3).',
        'DUPCHECK.md for the novelty status. STATUS.md for what is BLOCKED or unresolved.',
        '',
        '## PC next (QA)',
        '1. Copy this folder to a new QA folder on D:; unzip the source.',
        '2. Build with BUILD_RECIPE.txt; check the pins and perft 5 on the new exe.',
        '3. Quiet ABBA against the lock E1284F7F with QA''s adapter unchanged (QA_ABBA_PROTOCOL.md). Read its first',
        '   section before trusting one run of two fixed exe files: lock against a copy of the lock is the check.'
    )
    $sumFiles = @(Get-ChildItem $dst -Recurse -File | Where-Object { $_.Name -notin 'MD5SUMS.txt', 'SHA256SUMS.txt' } | Sort-Object FullName)
    WriteLf (Join-Path $dst 'MD5SUMS.txt') @($sumFiles | ForEach-Object { (Md5 $_.FullName) + '  ' + $_.FullName.Substring($dst.Length + 1).Replace('\', '/') })
    WriteLf (Join-Path $dst 'SHA256SUMS.txt') @($sumFiles | ForEach-Object { (Sha $_.FullName) + '  ' + $_.FullName.Substring($dst.Length + 1).Replace('\', '/') })
    # proof: the zip extracts to the manifest
    $chk = Join-Path $OUT "tmp\packcheck_$name"
    if (Test-Path $chk) { Remove-Item -Recurse -Force $chk }
    [System.IO.Compression.ZipFile]::ExtractToDirectory((Join-Path $dst $zipName), $chk)
    $bad = 0
    foreach ($line in [System.IO.File]::ReadAllLines((Join-Path $dst 'SOURCE_INPUTS.sha256'))) { if ($line -ne '') { $sha, $rel = $line -split '  ', 2; if ((Sha (Join-Path $chk $rel.Replace('/', '\'))) -ne $sha) { $bad++ } } }
    Remove-Item -Recurse -Force $chk
    $size = [math]::Round(((Get-ChildItem $dst -Recurse -File | Measure-Object Length -Sum).Sum) / 1MB, 2)
    Write-Output ("PACK {0}: {1} files, {2} MiB, zip re-extracts to the manifest: {3}; {4}" -f $name, ($sumFiles.Count + 2), $size, $(if ($bad -eq 0) { 'YES' } else { "NO ($bad)" }), $dst)
    if ($bad -ne 0) { exit 3 }
}
