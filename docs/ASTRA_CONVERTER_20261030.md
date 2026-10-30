# Astra FEN conversion — 2026-10-30

Branch: `astra-fen-convert-20261030`. Base: `110f0c4a819756b79a77d88a5ef525b6dafd925b`.
This is offline tooling. Engine source, search, live trainers and gates are unchanged.

## Verified results

| Check | Result | Original evidence |
|---|---|---|
| First 1,000,000 original shard 003 rows, lossless FEN/score/result sidecar | PASS, 0 mismatches against original text | `roundtrip_1m_original_compare.json` |
| Official MIT bulletformat loader and parser on all 1M records | PASS, 0 mismatches | `bullet_loader_1m/` |
| Native MIT binpack reader on all 1M records | PASS, byte-identical decoded text | `binpack_final/roundtrip_1m.json` |
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
- `rows.binpack` and the adapter input/logs when `--binpack-tool` is provided.

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
repeated index construction is not an optimized 305M driver; that throughput and
resource workload remains unmeasured. Omitting earlier outputs does not certify
zero cross-shard duplicates.

## Build and Linux commands

Fetch only the pinned five-header MIT dependency, outside the repository:

```bash
python3 tools/data2/fetch_binpack_dependency.py --out /new/external/binpack-mit
c++ -std=c++20 -O2 -Wall -Wextra -I/new/external/binpack-mit \
  tools/data2/forge_binpack_adapter.cpp -o /new/bin/forge_binpack_adapter
FORGE_BINPACK_ADAPTER=/new/bin/forge_binpack_adapter \
  python3 -m unittest discover -s tests/data2 -v
```

Production filtering and both formats, one new output directory:

```bash
python3 tools/data2/convert_dataset.py convert \
  --input /data/forge_selfplay_003.txt --pos /data/forge_selfplay_003.pos \
  --shard-id 003 --out /new/filtered003 \
  --probe /path/forge_data_probe --nodes 1024 \
  --binpack-tool /new/bin/forge_binpack_adapter \
  --holdout /private/forge_selfplay_013.pos \
  --holdout /private/forge_selfplay_014.pos
python3 tools/data2/convert_dataset.py verify --out /new/filtered003 \
  --binpack-tool /new/bin/forge_binpack_adapter
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
  --holdout /private/forge_selfplay_014.pos --out /new/dedup003
python3 tools/data2/convert_dataset.py verify --out /new/dedup003
```

Sequential cross-shard use: keep a stable order of the 37 training shard IDs,
exclude 013/014 entirely, and use filtered 003 in place of raw 003. Verify each
completed output before using every retained chunk to seed the next shard. For
example, after verified shard 001 output:

```bash
python3 tools/data2/convert_dataset.py convert \
  --input /data/forge_selfplay_002.txt --pos /data/forge_selfplay_002.pos \
  --shard-id 002 --out /new/filtered002 \
  --probe /path/forge_data_probe --nodes 1024 \
  --binpack-tool /new/bin/forge_binpack_adapter \
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

Windows execution remains unverified. After building the standalone probe and
adapter in new directories, use the existing checked launcher with one explicitly
spare logical CPU. Supply the actual approved executable paths; do not replace a
running engine, trainer, or gate. This example converts shard 003 in a new output
folder; add all prior retained chunks with `--dedup-against` for a cumulative run.

```powershell
$Repo = (& git rev-parse --show-toplevel).Trim()
$PosDir = 'D:\grok-pc-data\forge_push\nnue_data\pos'
$TxtDir = 'D:\grok-pc-data\selfplay_out'
$Probe = 'C:\EDIT\new-probe-build\forge_data_probe.exe'
$Adapter = 'C:\EDIT\new-binpack-build\forge_binpack_adapter.exe'
$Cpu = [int](Read-Host 'One logical CPU confirmed spare; do not guess')
$Run = Join-Path 'D:\grok-pc-data' ('astra_convert_' + [Guid]::NewGuid().ToString('N'))
$ConverterArgs = @('convert', '--input', (Join-Path $TxtDir 'forge_selfplay_003.txt'),
  '--pos', (Join-Path $PosDir 'forge_selfplay_003.pos'), '--shard-id', '003',
  '--out', $Run, '--probe', $Probe, '--nodes', '1024', '--binpack-tool', $Adapter,
  '--holdout', (Join-Path $PosDir 'forge_selfplay_013.pos'),
  '--holdout', (Join-Path $PosDir 'forge_selfplay_014.pos'))
& (Join-Path $Repo 'tools\data\run_idle_spare.ps1') `
  -Python (Get-Command python.exe).Source `
  -Script (Join-Path $Repo 'tools\data2\convert_dataset.py') -CpuList @($Cpu) `
  -LogDirectory ($Run + '_logs') -ScriptArguments $ConverterArgs
```

Verify with the same launcher, a fresh log directory, and script arguments
`@('verify', '--out', $Run, '--binpack-tool', $Adapter)`. Avoid rerunning the sealed
A1 10M job. Prior A1 Windows path errors are corrected in `ASTRA_A1_WINDOWS.md`;
that document is a historical reproduction runbook, not a reason to repeat it.

## Restart and evidence contract

Every input, tool and native executable is hashed. Actual reads use the initially
resolved paths; original symlink bindings are checked again before completion.
Chunks and final receipts are published by atomic exclusive hard links after data
fsync. Existing outputs, source data and failed attempts are never deleted or
overwritten. Filesystems must support same-volume hard links. Resume uses the
same command with `--resume`, verifies the same source/tool hashes and every
sealed chunk, rebuilds dedup state from those chunks, and retains unsealed tails.
A changed tool cannot silently resume an older protocol; frozen 1M tool bytes are
included in the evidence.

The default disk guard reserves 256 MB before indexing and before each chunk.
It is a guard, not a hard disk or memory quota. Indexes and original logs are
retained, including on retries; budget disk for them. Run shard-by-shard on the PC,
one Idle worker on an explicitly available logical CPU, and avoid competing gates.
No full 305M throughput or resource estimate is asserted by this slice test.

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
`eddd9a2d77dbc1391d68f23ba524657e91bd9a73`; independently MIT-licensed binpack format
headers at `ec2ead9feeb5677b828536fc53000d1379a1d207`. New wrappers and conversion
code are original. No GPL/AGPL code is incorporated. The upstream nnue-pytorch
repository as a whole is GPL; only the explicitly MIT five-file include closure
is fetched externally with exact SHA256 pins and its full notices retained.
