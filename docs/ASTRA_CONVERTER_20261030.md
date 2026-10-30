# Astra FEN conversion — 2026-10-30

Branch: `astra-fen-convert-20261030`. Base: `110f0c4a819756b79a77d88a5ef525b6dafd925b`.
This is offline tooling. Engine source, search, live trainers and gates are unchanged.

## QA correction and training status

**NOT CLEARED FOR TRAINING:** complete private holdouts 013 and 014 are unavailable
in this environment. Neither the old synthetic overlap test nor the new audit's
fixtures certify those real files. Before any training use, run the independent
clearance command below and require PASS with zero overlapping keys. No command
was run on grok-pc for this correction.

Earlier MIT-only binpack wording was wrong. Full notices at the pinned commit
explicitly identify modified nodchip/Stockfish GPLv3 code in `nodchip.h:46-47`;
`binpack.h` includes it and `chess.h` cites Cfish. Treat the compiled
`forge_binpack_adapter` as **GPL-3.0 external tooling**, with dependencies and
executable outside every repository. The repository retains our original wrapper
and tests, not upstream headers or compiled binaries. This tool is optional and
**OFF by default**. Default conversion uses only bulletformat plus its verified
sidecar. Historical raw logs are preserved; their MIT-only descriptions are
superseded by this correction and `qa_licence_fix/notice_verification.json`.

## Verified results

| Check | Result | Original evidence |
|---|---|---|
| First 1,000,000 original shard 003 rows, lossless FEN/score/result sidecar | PASS, 0 mismatches against original text | `roundtrip_1m_original_compare.json` |
| Official MIT bulletformat loader and parser on all 1M records | PASS, 0 mismatches | `bullet_loader_1m/` |
| External GPL-3.0 binpack reader on all 1M records | PASS, byte-identical decoded text | `binpack_final/roundtrip_1m.json` |
| Castling and en passant in that slice | 216,652 castling rows; 35,547 EP rows preserved | Same original 1M receipts |
| Synthetic overlap using 1,000 real sample rows as their own holdout | PASS: 1,000 removed, 0 remain | `fake_holdout_1000*`, `fake_holdout_original/` |
| Prior-training dedup on 1,024 real rows, first 1,000 supplied as prior kept | PASS: 1,000 duplicates removed, 24 retained, 0 holdout removals | `prior_real1024*` |
| Native Forge filtering, 1,024 original rows | PASS: 977 kept; 46 best-move captures and 1 result disagreement dropped | `native_1024*`, `native_1024_original/` |
| Both filtered output formats | PASS: 977 records checked; native binpack decode matches exact sidecar | `native_1024_verify.*` |
| Converter and adapter unit regressions | 45 PASS, normal and optimized Python | `unit_prior_training_accounting*` |
| Native adapter ASan/UBSan with leak detection | 13 PASS; no diagnostics in native run | `binpack_final/tests_san_native.*` |
| GPU bullet training / a complete training epoch / exported trained-net parity | UNVERIFIED here | No GPU trainer run claimed |
| Full private 013/014 position exclusion | UNVERIFIED here; command supplied for the PC | Those inputs were not uploaded |
| Windows runtime | UNVERIFIED | Commands and source reviewed, not run on grok-pc |

All evidence paths above are relative to `validation/astra-converter-20261030/`.
The original sandbox LeakSanitizer/ptrace failure and earlier compiler logs are
retained separately; a later native sanitizer pass does not erase those attempts.

The 1M test is **format qualification only**: filters and deduplication were
explicitly disabled to compare the identical source slice. It is not a training
approval. No Elo, training gain or speed claim is made.

## Representations and semantics

`tools/data2/convert_dataset.py` writes immutable chunks with:

- `rows.bullet`: standard 32-byte bulletformat `ChessBoard` records.
- `rows.txt`: the inseparable original six-field FEN, STM centipawn score and
  White-relative result, in the original retained order.
- `provenance.tsv`: original input row and optional authenticated game ID.
- `rows.binpack`, a small move sidecar and adapter logs only when an external
  `--binpack-tool` and `--accept-gpl3` are explicitly provided and the tool
  resolves outside every Git repository. No duplicate full-FEN adapter input is kept.

**Standard bulletformat alone loses original STM, castling, EP and clocks.**
Exact FEN recovery is a property of the record plus its verified sidecar, not the
32-byte file alone. The official loader/parser test independently verifies every
piece, king index, normalized score and result. Forge labels are STM-relative;
the official bullet text parser expects White-relative scores, so that comparison
explicitly flips the input score for Black before the parser normalizes it back.

Binpack preserves the six fields in the tested slice. It encodes signed STM
results; decode restores White result. Its representable clocks are bounded:
halfmove 0..255, packed ply 1..16383. Out-of-range state is rejected, never clamped.
For filtered production rows the actual Forge probe best move is passed to the
binpack adapter. The 1M format test explicitly selects a legal **transport move**
because source rows do not carry best moves. This fallback is not a teacher move,
a quiet-root claim, or suitable evidence for training filters.

The standalone adapter decoder accepts its own standard independent-record
binpack chunks. It deliberately rejects continuation-compressed files from other
producers; it is not a general arbitrary-binpack validator.

## Filtering, holdouts and accepted split policy

Production conversion requires the native Forge probe and an explicit source
`--shard-id` in 001..039. The tool rejects 013 and 014 as training shards. The user
explicitly accepted **whole-shard 013/014 exclusion as the game-level split policy**
because rows are unordered and authentic game IDs are unavailable. No IDs are
invented. Optional real game-ID sidecars enable additional exclusion if available.
The policy declaration is recorded; it does not prove unseen cross-shard game IDs.

First-drop order is: supplied holdout game, supplied holdout position, duplicate,
score cap, result disagreement, root in check, terminal, insufficient teacher
budget, best-move capture, best-move promotion. Zero counts are reported too.
Counts are a waterfall, not independent marginal filter prevalence. Exact dedup
and holdout keys are board plus side to move, matching the crew's specified policy;
castling, EP and clocks remain in retained labels but are omitted from that key.

Default cap is 3,000 cp; decisive disagreement threshold is 400 cp; draw threshold
is 800 cp. The probe uses one thread, Hash 1 MB and a configurable fixed node
budget (default 1,024). No completed iteration is an explicit exclusion; malformed
responses or other native failures abort. These are recorded initial settings,
not empirically optimal training choices.

The separate `holdout-dedup` command accepts `.pos` or full `FEN | score | result`
files. Use both complete private shards on the PC. QA already found **281** A1
retained rows overlapping complete 013/014; the cloud's original 013-head test is
not a substitute for removing them. Filtered 003 must **replace** raw 003 in an
isolated ablation, never be appended on top of a training set already containing
003. The tool processes one source shard per invocation. For cross-shard training
deduplication, pass every earlier retained `rows.txt` chunk (or retained FPOS file)
with repeatable `--dedup-against`. These immutable inputs seed the dedup index;
hits count as `duplicate`, not holdout. Their hashes and path bindings receive the
same identity checks as source/holdout inputs. The receipt records indexed rows
and unique prior keys. This makes a correct sequential pipeline possible, but
index construction is repeated and **indexes are retained by default**, including
on resume. Run explicit `verify --prune-indexes` after each completed shard if
you want to reclaim them; without that opt-in cumulative index storage grows. Full 305M runtime
remains unmeasured. Omitting earlier outputs does not certify
zero cross-shard duplicates.

## Build and Linux commands

Default conversion needs **no binpack fetch or build**. Optional external tooling
must be explicitly opted into and built outside every repository:

```bash
python3 tools/data2/fetch_binpack_dependency.py --accept-gpl3 --out /new/external/binpack-gpl3
c++ -std=c++20 -O2 -Wall -Wextra -I/new/external/binpack-gpl3 \
  tools/data2/forge_binpack_adapter.cpp -o /new/external/forge_binpack_adapter
FORGE_BINPACK_ADAPTER=/new/external/forge_binpack_adapter \
  python3 -m unittest discover -s tests/data2 -v
```

Production filtering to bulletformat + sidecar, one new output directory:

```bash
python3 tools/data2/convert_dataset.py convert \
  --input /data/forge_selfplay_003.txt --pos /data/forge_selfplay_003.pos \
  --shard-id 003 --out /new/filtered003 --min-free-mb 20000 \
  --probe /path/forge_data_probe --nodes 1024 \
  --holdout /private/forge_selfplay_013.pos \
  --holdout /private/forge_selfplay_014.pos
python3 tools/data2/convert_dataset.py verify --out /new/filtered003
```

For A1's existing output use `--input forge_filtered.fen --pos forge_filtered.pos
--sidecar-format fen`. The tool verifies every selected FEN against its POS record.
The default production mode reruns the configured native quiet-root check. Do not
rerun the original 10M A1 job merely to rebuild these artifacts.

Separate private holdout exclusion on text data:

```bash
python3 tools/data2/convert_dataset.py holdout-dedup \
  --input /data/forge_selfplay_003.txt --shard-id 003 \
  --holdout /private/forge_selfplay_013.pos \
  --holdout /private/forge_selfplay_014.pos --out /new/dedup003 --min-free-mb 20000
python3 tools/data2/convert_dataset.py verify --out /new/dedup003
```

Sequential cross-shard use: keep a stable order of the 37 training shard IDs,
exclude 013/014 entirely, and use filtered 003 in place of raw 003. Verify each
completed output before using every retained chunk to seed the next shard. For
example, after verified shard 001 output:

```bash
python3 tools/data2/convert_dataset.py convert \
  --input /data/forge_selfplay_002.txt --pos /data/forge_selfplay_002.pos \
  --shard-id 002 --out /new/filtered002 --min-free-mb 20000 \
  --probe /path/forge_data_probe --nodes 1024 \
  --holdout /private/forge_selfplay_013.pos \
  --holdout /private/forge_selfplay_014.pos \
  --dedup-against /verified/filtered001/data_CHUNK_A/rows.txt \
  --dedup-against /verified/filtered001/data_CHUNK_B/rows.txt
```

Use **all** actual prior retained chunks, not these example names. For shard 003
include both prior 001 and 002 retained outputs, then continue cumulatively.
Chunks are listed by the verified `chunk_*.json` receipts; never include an
unsealed tail. `--dedup-against` conflicts with `--no-dedupe` and fails closed.
Holdout position keys still have precedence and their counts remain distinct.
No prior shard file is modified, and a changed prior file prevents resume.

`holdout-dedup` performs exclusion/deduplication only; it does not silently claim
root filtering. To request a format-only binpack test, explicitly supply
`--no-filters --no-dedupe --allow-transport-moves`. The standalone reproducible 1M
binpack test is:

```bash
python3 tools/data2/run_1m_roundtrip.py \
  --input /data/forge_selfplay_003.txt \
  --adapter /new/bin/forge_binpack_adapter \
  --adapter-source tools/data2/forge_binpack_adapter.cpp --out /new/roundtrip1m
```

The Rust loader test is `tools/data2/bullet_loader_check` (pinned MIT dependency):

```bash
cargo build --release --manifest-path tools/data2/bullet_loader_check/Cargo.toml
/path/to/forge_bullet_loader_check /chunk/rows.bullet /chunk/rows.txt
```

## PC execution at Idle priority

Windows execution remains UNVERIFIED. Save this block as a script and invoke it
with `powershell.exe -NoProfile -NonInteractive -File ... -Cpu <spareCPU> -Python
<absoluteVenvPython> -Probe <newProbeExe>`. All required values are mandatory
parameters; there is no `Read-Host` prompt. Supply a verified spare CPU and paths.
Use a new output folder, leave the live trainer/gates untouched, and do not rerun
the sealed A1 10M job. The default does not fetch, build or invoke binpack.

```powershell
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][ValidateRange(0,62)][int]$Cpu,
  [Parameter(Mandatory=$true)][string]$Python,
  [Parameter(Mandatory=$true)][string]$Probe,
  [Parameter(Mandatory=$true)][string]$Repo
)
$ErrorActionPreference = 'Stop'
$PosDir = 'D:\grok-pc-data\forge_push\nnue_data\pos'
$TxtDir = 'D:\grok-pc-data\selfplay_out'
$Run = Join-Path 'D:\grok-pc-data' ('astra_convert_' + [Guid]::NewGuid().ToString('N'))
$ConverterArgs = @('convert', '--input', (Join-Path $TxtDir 'forge_selfplay_003.txt'),
  '--pos', (Join-Path $PosDir 'forge_selfplay_003.pos'), '--shard-id', '003',
  '--out', $Run, '--probe', $Probe, '--nodes', '1024', '--min-free-mb', '20000',
  '--holdout', (Join-Path $PosDir 'forge_selfplay_013.pos'),
  '--holdout', (Join-Path $PosDir 'forge_selfplay_014.pos'))
& (Join-Path $Repo 'tools\data\run_idle_spare.ps1') `
  -Python $Python -Script (Join-Path $Repo 'tools\data2\convert_dataset.py') `
  -CpuList @($Cpu) -LogDirectory ($Run + '_logs') -ScriptArguments $ConverterArgs
```

Add **all** previous retained chunks via `--dedup-against` for cumulative runs.
Verify with the same launcher, a fresh log directory, and arguments
`@('verify', '--out', $Run)`. Only an explicit external binpack opt-in adds
`--binpack-tool EXTERNAL_EXE --accept-gpl3` to both conversion and verification.
Both its original path and resolved target are checked; a repository-local alias
or a target inside a repository is refused before execution.

### Required real-holdout clearance before training

The separate audit verifies the sealed output independently, indexes its unique
board+STM keys, and reads **both full** FPOS holdouts. It requires expected hashes
and row counts from the crew's trusted full-shard manifest, not a small sample's
self-reported identity. Use the same Idle launcher on the PC with these script
arguments (replace variables with the trusted values):

```powershell
$AuditArgs = @('--out', $Run,
  '--holdout-013', (Join-Path $PosDir 'forge_selfplay_013.pos'),
  '--holdout-014', (Join-Path $PosDir 'forge_selfplay_014.pos'),
  '--holdout-013-sha256', $Trusted013Sha256, '--holdout-013-rows', $Trusted013Rows,
  '--holdout-014-sha256', $Trusted014Sha256, '--holdout-014-rows', $Trusted014Rows,
  '--min-free-mb', '20000', '--work-dir', 'D:\grok-pc-data',
  '--report', ($Run + '_real_013_014_clearance.json'))
& (Join-Path $Repo 'tools\data\run_idle_spare.ps1') `
  -Python $Python -Script (Join-Path $Repo 'tools\data2\audit_holdout_clearance.py') `
  -CpuList @($Cpu) -LogDirectory ($Run + '_holdout_logs') -ScriptArguments $AuditArgs
```

Any missing/mismatched full-shard identity, output corruption or positive overlap
is a failed clearance. **Training stays blocked until a real PASS receipt is
produced.** No such real 013/014 receipt is claimed in this cloud review.

## Restart and evidence contract

Every input, tool and native executable is hashed. Actual reads use the initially
resolved paths; original symlink bindings are checked again before completion.
Chunks and final receipts are published by atomic exclusive hard links after data
fsync. Source data, sealed outputs and original logs are never overwritten or
deleted. Conversion and resume never prune indexes automatically. The explicit
`verify --prune-indexes` command removes only owned, reconstructible indexes
after verification. Filesystems must support same-volume hard links. Resume uses the
same command with `--resume`, verifies the same source/tool hashes and every
sealed chunk, rebuilds dedup state from those chunks, and retains unsealed tails.
A changed tool cannot silently resume an older protocol; frozen 1M tool bytes are
included in the evidence.

The default free-space reserve is **20,000 MiB**, plus a preflight index/output
budget. Index loading, recovery and row processing also check remaining space.
These guards are not quotas: other processes can consume disk between checks.
Only one Idle conversion should run at a time. Completed indexes are disposable
but retained unless cleanup is explicitly requested; receipts, input hashes and
output verification are retained in either case. See the measured
budget addendum below for sample sizes and conservative projections.

The final review found and repaired: incomplete COMPLETE-accounting validation,
unhashed data-role paths, optional skipping of a requested missing binpack,
input-symlink retargeting, an unclosed holdout reader, and missing fsync of native
chunk outputs. Regression logs preserve the before/after review evidence.

## Output identities and sources

1M native binpack: 34,000,264 bytes,
SHA256 `db200a129194456ffbdc101e2154a5d5fd920c175fea12b69e878c38a28c9396`.
Original and decoded first-1M text SHA256:
`f8fb8e78cfc643bbc3a79f0384aafc848bb679e01a9e5b71ca97fd91966766be`.
Large original run outputs remain in the execution workspace; commands, frozen
protocol, original logs, input/output hashes and small native proof bundles are
published on the isolated branch. No large output release is claimed.

IDEA_SOURCE: user crew contract and accepted shard policy; same-project A1 reader
and native probe; MIT bulletformat wire layout at
`eddd9a2d77dbc1391d68f23ba524657e91bd9a73`; external GPL-3.0 binpack API and full
notice review at `ec2ead9feeb5677b828536fc53000d1379a1d207`. New wrappers and
conversion code are original. Do not describe the compiled binpack closure as
MIT-only. No upstream header or compiled adapter is vendored or linked to Forge.


## QA disk measurements and recovery

Measurements below are box-only, with binpack **OFF**. The bounded fixtures used
`--min-free-mb 0` because this cloud scratch volume has less than 20 GiB free;
production defaults remain **20,000 MiB**. This override is not the PC recipe.
**The measurements below used the previous automatic cleanup policy.** With
the current policy those index bytes remain until `verify --prune-indexes`;
unchanged raw logs describe their original runs. Original commands, source
hashes, before-prune bytes and logs are in
`validation/astra-converter-20261030/qa_fix_disk/`.

| Measured slice | Retained rows | Live index before verification | Index after explicit cleanup / historical cleanup | Retained files/logs |
|---|---:|---:|---:|---:|
| First 50,000 real rows, with interruption/resume | 49,999 | 2,203,648 B | 0 B | 5,140,974 B |
| Next 50,000, seeded from all prior retained chunks | 49,994 | 4,362,240 B (99,993 cumulative keys) | 0 B | 5,166,932 B |
| Native filtered 1,024-row pilot | 977 | Disposable | 0 B | 181,536 B |

The native pilot removed 46 capture-root rows and 1 result disagreement. It kept
71,439 bytes of original compressed request/response/process logs (69.765 bytes
per input row). A real native bestmove was also streamed through the optional
external adapter in a separate one-row test: exact decode passed, no duplicated
full-FEN input remained, and the verified index was pruned.

**10M-row shard projections, not full-shard measurements:** transport-only bytes
at the 100k sample rate are about 1.03 GB per shard; native logs at the pilot rate
add about 0.70 GB. Actual filtering, FEN lengths and compression change these
figures. The second index measured 43.63 bytes per cumulative unique key, about
0.44 GB per 10M keys; its size grows with prior retained keys plus holdout keys,
and stays on disk by default. Explicitly cleaning each verified shard prevents
retaining those cumulative indexes 37 times. Existing source files and earlier retained outputs are separate
persistent storage, not deleted to reclaim scratch.

Preflight deliberately budgets **64 bytes per possible index key**, a 1 MiB
index margin, full source text, original UTF-8 game-ID file bytes if any, output
records/provenance, and **2,048 bytes per input row for native logs**. The last
allowance is 20.48 GB for 10M inputs and is intentionally much larger than this
pilot's 0.70 GB projection; it is not a measured requirement or a hard quota for
arbitrary external stderr. The printed `disk_preflight` JSON gives the exact
estimate for each shard's actual arguments, on top of the 20,000 MiB reserve.
The native log allowance, largest cumulative index and new shard output coexist;
do not plan using output size alone. Guards recheck every 1,024 rows while
loading holdouts/prior/recovered keys and while processing new rows.

Only explicit `verify --prune-indexes` removes disposable indexes carrying a
matching config-bound `INDEX_OWNER.json` marker, under the converter's exclusive
output lock, **after sealed hashes and row parity verify**. Logs, source data,
unsealed tails and receipts remain. Resume retains earlier indexes and builds a
fresh one; no recovery trusts the retained database contents. Journal recovery is disabled solely for this
reconstructible scratch database. Old unmarked indexes are not automatically
removed. Completed old output can still be verified; unfinished old-code
checkpoints require their original frozen tool.

For an interrupted cleanup after COMPLETE, run:

```bash
python3 tools/data2/convert_dataset.py verify --out /verified/output --prune-indexes
```

Plain `verify` stays read-only. Passing `--prune-indexes` explicitly takes the
output lock and verifies before cleanup. The full private-holdout clearance audit
has its own output-key index (96 bytes per row plus 16 MiB preflight margin),
streaming checks, and opt-in `--prune-indexes` cleanup after validated completion.
Its default also retains the owned database and reports its path and size; failed
identity checks retain it even if pruning was requested. It requires additional
scratch during that stage.

QA validation: **86/86 data2 tests passed** with the explicitly selected external
adapter; the default suite skips the 13 optional adapter tests. This includes
21 new holdout-audit cases. Nine additional independent disk/ownership/resume
checks passed. No source or engine search/evaluation/network was changed by
these tooling fixes, and no new bench, speed or Elo result is asserted.


Final follow-up: the complete data2 suite is now **93/93 PASS**, including seven
CRLF transport regressions. Optional decoder verification accepts only a terminal
CRLF-to-LF normalization; fields, other whitespace, extra rows and missing final
newlines still fail exact comparison. The new clearance CLI also processed
49,999 real-derived output rows with two 1,000-row fake-holdout cases: it found
1,000 overlapping keys in the positive control, and zero in the nonoverlap case.
These holdouts came from shard003 and do **not** certify private013/014.
Original reports/receipts are in `qa_final_review/real_slice_audit/`.

The unchanged A1 suite passed 130 discovery cases with one explicit native-suite
skip; that separate native suite passed9/9 with its original probe. Initial
attempts failed because sparse checkout omitted tests/source/two helper scripts;
restoring the exact tracked bytes resolved those setup failures. Their original
logs remain preserved. No A1 code or expected value was changed.


## Policy refinement: explicit cleanup and GPL acknowledgement

Current defaults retain indexes. To opt into cleanup after verification:

```bash
python3 tools/data2/convert_dataset.py verify --out /verified/output --prune-indexes
```

For optional external binpack verification, both flags are required:

```bash
python3 tools/data2/convert_dataset.py verify --out /verified/output \
  --binpack-tool /external/forge_binpack_adapter --accept-gpl3
```

`convert` and `holdout-dedup` require the same acknowledgement when an adapter
is selected. No acknowledgement is needed for default bulletformat + sidecar.
The shared path check recognizes Git worktrees and bare repositories; it checks
both the supplied alias and actual target, preserving symlink/`..` resolution.
Empty managed-filesystem `.git` placeholder directories are not repositories.

The separate audit likewise keeps its scratch database by default. Add
`--prune-indexes` to that audit's existing command only when cleanup is wanted;
its report records the path, retained bytes, requested policy, and actual result.
No default command deletes a retained converter/audit index. Earlier raw
measurements and checkpoints remain historical evidence rather than being edited.
