# Astra A1: Windows offline data commands

**Windows runtime is UNVERIFIED.** These commands were checked against the five
Python CLIs and the current launcher source, not executed on grok-pc. Use a
PowerShell 7 terminal in the `astra-a1-data` checkout. Run the blocks in order in
one terminal. They do not start training or modify the engine or input shards.

## Paths and explicit spare CPUs

Edit `$Data` if your input location differs. Confirm that the three logical CPU
indices below are spare before running; affinity identifies logical CPUs, not
physical cores. Choose at most three workers, and fewer if fewer CPUs are free.
All substantial jobs below use `run_idle_spare.ps1`: it verifies Idle priority
and affinity on the launching PowerShell process before Python starts. Native
probes explicitly request Idle priority and use one search thread each. Windows
inheritance and runtime behaviour still require qualification on the PC.

```powershell
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'Use PowerShell 7 for these commands.' }
$Python = (Get-Command python.exe -ErrorAction Stop).Source
$Repo = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath $Repo -PathType Container)) {
    throw 'Run this terminal inside the astra-a1-data checkout.'
}
$Data = 'D:\grok-pc-data\selfplay_out' # EDIT if different; input files are read-only.
$SpareCpus = @(12, 13, 14)             # EDIT to the logical CPUs actually free.
$Workers = [Math]::Min(3, $SpareCpus.Count)
if ($Workers -lt 1) { throw 'At least one explicitly spare CPU is required.' }
$Launcher = Join-Path $Repo 'tools\data\run_idle_spare.ps1'
$RunRoot = Join-Path (Split-Path -Parent $Data) ('astra_a1_' + [Guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $RunRoot -ErrorAction Stop

function New-RunPath([string]$Name) {
    Join-Path $RunRoot ($Name + '_' + [Guid]::NewGuid().ToString('N'))
}
function Invoke-DataTool {
    param([string]$Tool, [string[]]$ToolArgs)
    $Script = Join-Path $Repo ('tools\data\' + $Tool)
    $Log = New-RunPath ('log_' + [IO.Path]::GetFileNameWithoutExtension($Tool))
    & $Launcher -Python $Python -Script $Script -CpuList $SpareCpus `
        -LogDirectory $Log -ScriptArguments $ToolArgs
    Write-Host "Original command/output/exit receipt: $Log"
}

$Pos = Join-Path $Data 'forge_selfplay_003.pos'
$Sidecar = Join-Path $Data 'forge_selfplay_003.txt'
foreach ($File in @($Pos, $Sidecar)) {
    if (!(Test-Path -LiteralPath $File -PathType Leaf)) { throw "Missing input: $File" }
}
```

`forge_selfplay_003.pos` and `.txt` are the names in the supplied 10M release;
the same names on your PC do not establish equal content. Compare input hashes
with the experiment receipts. The sidecar must be the original full-FEN text,
in exactly the same record order. FPOS itself omits castling rights, en passant,
clocks and game history. Full-FEN labels preserve current state but cannot
reconstruct earlier repetitions.

Each invocation gets a fresh GUID log directory and each output below gets a
fresh GUID directory. Never reuse an output path; retain failures for review.
These scripts use bounded workers/Hash, but the launcher does not impose a hard
Windows job-object memory cap. Run large jobs sequentially and check free disk:
original query logs, decisions, output shards and the deduplication index are
preserved.

Use an output filesystem that supports ordinary same-volume hard links
(for example NTFS). Atomic no-overwrite publication uses `os.link`; FAT/exFAT
and some network shares do not support that contract. Before the 10M run, run
a small filter pilot in a new folder on the same volume and verify its seal.
Unsupported publication fails closed and retains partials; it is not a
completed dataset.

## Build the standalone probe: GCC 15.2, Zen 5, static

Use MSYS2 **UCRT64** GCC 15.2, CMake and either Ninja or MinGW Makefiles. Change
`$MsysBin` if MSYS2 is elsewhere. This builds a new Release core and standalone
data probe, with all `FORGE_*` CMake options OFF, `-march=znver5 -mtune=znver5`,
`-ffp-contract=off -fno-fast-math`, and static linking. It does not install an exe
over any existing engine. The script records compiler/source/core/probe hashes
and rejects any FMA instruction. Build success alone is not Windows engine
qualification or a speed result.

```powershell
$MsysBin = 'C:\msys64\ucrt64\bin'
$env:PATH = $MsysBin + ';' + $env:PATH
$Cxx = Join-Path $MsysBin 'g++.exe'
$Objdump = Join-Path $MsysBin 'objdump.exe'
$Cmake = (Get-Command cmake.exe -ErrorAction Stop).Source
foreach ($File in @($Cxx, $Objdump)) {
    if (!(Test-Path -LiteralPath $File -PathType Leaf)) { throw "Missing tool: $File" }
}
$GccVersion = (& $Cxx -dumpfullversion -dumpversion).Trim()
if ($LASTEXITCODE -ne 0 -or $GccVersion -notmatch '^15\.2(\.|$)') {
    throw "Expected UCRT64 GCC 15.2; got $GccVersion"
}
$Generator = 'Ninja' # Or exactly 'MinGW Makefiles'; choose an installed generator.
if ($Generator -eq 'Ninja') {
    $null = Get-Command ninja.exe -ErrorAction Stop
} elseif ($Generator -eq 'MinGW Makefiles') {
    $null = Get-Command mingw32-make.exe -ErrorAction Stop
} else { throw 'Select Ninja or MinGW Makefiles.' }

$BuildOut = New-RunPath 'probe_build'
Invoke-DataTool -Tool 'build_probe.py' -ToolArgs @(
    '--repo', $Repo, '--output', $BuildOut, '--cxx', $Cxx,
    '--cmake', $Cmake, '--objdump', $Objdump, '--generator', $Generator,
    '--march', 'znver5', '--mtune', 'znver5', '--jobs', '1', '--static'
)
$BuildReceipt = Get-Content -Raw -LiteralPath (Join-Path $BuildOut 'build_receipt.json') | ConvertFrom-Json
if ($BuildReceipt.status -ne 'PASS' -or $BuildReceipt.fma_instructions -ne 0) {
    throw 'Build/protocol/FMA qualification failed; retain the build directory.'
}
$Probe = Join-Path $BuildOut 'forge_data_probe.exe'
```

## Verify the entire sidecar, then filter

```powershell
$VerifyOut = New-RunPath 'sidecar_verify'
Invoke-DataTool -Tool 'verify_sidecar.py' -ToolArgs @(
    '--pos', $Pos, '--sidecar', $Sidecar, '--out', $VerifyOut
)
$Verified = Get-Content -Raw -LiteralPath (Join-Path $VerifyOut 'summary.json') | ConvertFrom-Json
if ($Verified.status -ne 'PASS') { throw 'Do not use an unverified sidecar.' }

# Full production exclusion requires BOTH complete holdouts. Missing paths stop here.
$Holdouts = @(
    (Join-Path $Data 'forge_selfplay_013.pos'),
    (Join-Path $Data 'forge_selfplay_014.pos')
)
foreach ($File in $Holdouts) {
    if (!(Test-Path -LiteralPath $File -PathType Leaf)) { throw "Missing full holdout: $File" }
}
$FilterOut = New-RunPath 'filter_10m'
$FilterArgs = @(
    '--pos', $Pos, '--sidecar', $Sidecar, '--out', $FilterOut, '--probe', $Probe,
    '--probe-nodes', '1024', '--probe-workers', [string]$Workers,
    '--hash-mb', '1', '--batch-size', '256', '--limit', '10000000',
    '--disagreement-cp', '400', '--draw-disagreement-cp', '800',
    '--near-window', '64', '--near-score-delta', '25', '--holdout'
) + $Holdouts
Invoke-DataTool -Tool 'filter_positions.py' -ToolArgs $FilterArgs
```

The available cloud experiment used only the verified **1.5M-row 013 head**;
014 and authentic game identifiers were absent. To reproduce that limited
experiment, explicitly set `$Holdouts` to the real `forge_selfplay_013_head.txt`
path instead and label the result **partial holdout scope**. Do not silently
omit missing full holdouts. Even both full position holdouts do not prove
game-level separation without authenticated game IDs.

Read `summary.json`, `progress.json` and `manifest.json`, including each supplied
holdout's hash/row count, actual input count and position-overlap check. If the
input is shorter than 10M, do not report a 10M measurement. Removal fractions
are an ordered first-drop waterfall, not independent rule frequencies. A
1024-node search that completes no iteration is counted as `teacher_incomplete`;
other native failures abort. Keep unsealed/failed outputs out of training.

Verify the sealed bytes and accounting with the read-only bundle checker. The
full mode also checks every output record against its FEN and HCE columns; the
launcher stores the receipt outside the sealed output folder.

```powershell
Invoke-DataTool -Tool 'check_data_bundle.py' -ToolArgs @($FilterOut, '--full-records')
```

## Relabel a slice with a configurable deeper budget

Start with 256 rows; use 4096 for the next measurement after checking the pilot.
`65536` nodes is the measured Linux pilot budget, not proof that labels are
better than the original teacher. Adjust `$RelabelNodes` explicitly. Every
request starts cold with one search thread and Hash 1 MB. This scans the
sidecar to validate its total row count, while the earlier verifier checks
every input record.

```powershell
$RelabelCount = 256       # Set 4096 for the next run in a NEW output directory.
$RelabelNodes = 65536     # Fixed nodes per search; configurable.
$RelabelStride = if ($RelabelCount -eq 256) { 39062 } else { 2000 }
# 256/stride39062 reproduces the measured 10M pilot selection; 4096 uses stride2000.
# For any other count/stride, ensure the last selected index is inside the input.
$RelabelOut = New-RunPath ('relabel_' + $RelabelCount)
Invoke-DataTool -Tool 'relabel_positions.py' -ToolArgs @(
    '--pos', $Pos, '--sidecar', $Sidecar, '--sidecar-origin', 'original_full_fen',
    '--out', $RelabelOut, '--probe', $Probe, '--nodes', [string]$RelabelNodes,
    '--workers', [string]$Workers, '--hash-mb', '1', '--start', '0',
    '--count', [string]$RelabelCount, '--stride', [string]$RelabelStride,
    '--batch-size', '128', '--stem', 'forge_relabel'
)
```

Output is a matched `forge_relabel.pos`, `.hce` and `.fen`, plus original search
responses and row provenance. Check `summary.json` status, selected count,
`exact_label_rows`, total pipeline CPU accounting and `positions_per_core_hour`.
No Windows throughput is claimed until those receipts exist. `--allow-reconstructed`
is intentionally absent; do not substitute guessed castling/EP/clocks.

## Standard opening book and separate no-castling FENs

```powershell
$BookOut = New-RunPath 'openings_standard'
Invoke-DataTool -Tool 'generate_openings.py' -ToolArgs @(
    '--probe', $Probe, '--out', $BookOut, '--count', '64', '--seed', '20261030',
    '--nodes', '1024', '--hash-mb', '1', '--min-plies', '6', '--max-plies', '16',
    '--min-abs-cp', '25', '--max-abs-cp', '150', '--max-attempts', '2000', '--format', 'r8'
)
$FenOut = New-RunPath 'openings_960_style'
Invoke-DataTool -Tool 'generate_openings.py' -ToolArgs @(
    '--probe', $Probe, '--out', $FenOut, '--count', '16', '--seed', '20261030',
    '--nodes', '1024', '--hash-mb', '1', '--min-plies', '6', '--max-plies', '16',
    '--min-abs-cp', '25', '--max-abs-cp', '150', '--max-attempts', '2000', '--format', 'fen', '--chess960-style'
)
```

The default checks every selected intermediate position against ±150 cp, then
requires a nonterminal, non-check final position. The commands above explicitly
require a final absolute score of 25–150 cp for unbalanced openings. The earlier
`openings-native` experiment is a separate control with the tool default
`--min-abs-cp 0`: only 43/64 of its standard positions reached 25 cp, so it is
not the unbalanced-book qualification. The separate Linux `openings-unbalanced-25`
book has 64 unique positions with final absolute scores 25–148 cp, evenly split
between White and Black advantages. Fresh native replay verified all 562 legal
plies and 626 selected-position scores/depths/node counts. A second standard generation using the current helper reproduced the book and
settings exactly; metadata changed only in helper-hash fields. An extra min-25
960-style batch was not run. Windows execution remains UNVERIFIED. `SUCCESS.json` and the final manifest are
the seal authority; generation-phase status alone is not a completed run.

R8 v5 commit `5dd3a57d6f286f09b8881671ba8a368f6d34f717` accepts the standard
`openings.moves` through **`--openings <absolute-path>`**, one whitespace-separated
UCI move sequence per line, always from orthodox startpos. Confirm the file
exists, is nonempty and matches its manifest before adding that argument to the
crew's already qualified driver command; that driver silently falls back to
random openings for a missing/empty book. No R8 process is launched here.

The optional FEN export has valid opposite-colour bishops and king-between-rooks
back ranks but **no castling rights**. It is not true Chess960 and unchanged R8
cannot consume it. R8's `--priority idle` controls engine children only; the
unchanged driver sets itself to BelowNormal, so do not describe the whole R8
job as Idle. This runbook neither changes R8 nor the live trainer/GPU jobs.

IDEA_SOURCE: user Astra A1 spare-core/offline-data requirements; this repository's
five Python CLIs and launcher; exact R8 v5 source commit cited above. No external
engine code or tuned values were copied.
