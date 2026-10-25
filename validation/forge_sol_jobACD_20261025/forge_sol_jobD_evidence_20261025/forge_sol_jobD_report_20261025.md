# Forge Sol Job D — offline data filter, 20261025

**Implemented and sample-validated. No engine, GPU training, trainer or network change. No training-gain claim.** Real holdouts013/014 are absent, so their production position/game overlap is **UNVERIFIED**. Counts below apply to the supplied synthetic data32 sample and h000 stand-in only.

Tool: `forge_sol_datafilter_20261025.py`  
SHA256: `6ccf78c864c44155cea22044fe05d0584bec5241acdc5ebb2b71e23886007ab3`

The original reader and writer are included as `Reader`, `read_records` and `write_records` in that file. Separate `forge_sol_datafilter_tests_20261025.py` includes the round-trip regression and20 other behavioral checks. Tool dependencies are Python standard library only; the separate actual-trainer CPU smoke requires NumPy/PyTorch.

## What it does

- Reads documented FPOS/FHCE version1, columnar layout: POS header16bytes, board32*n, STM score int16*n, meta uint8*n; paired HCE header16bytes plus aligned int16*n. Selected field bytes are preserved; only row selection/counts change. Malformed headers, size mismatches and corrupted authoritative holdout rows fail closed.
- Uses SHA256(board32 plus STM1), with full33-byte collision guards. Castling, en passant and clocks are not in POS and are not invented. Globally dedupes first eligible retained records in a fixed-seed deterministic shard order while preserving record order within each shard.
- Excludes supplied holdout positions and entire source aliases (including resolved symlinks/hardlinks). Paired HCE rows remain aligned. Invalid training fields are counted and dropped separately.
- Optional `--disagreement-threshold CP` is OFF by default. At threshold300, a decisive STM loss with score>=300, STM win with score<=-300, or draw with |score|>=300 is excluded. WHITE game result is explicitly converted to STM. Reasons remain separate in each shard's report. This is an experimental data-selection policy, not evidence that training improves.
- Uses mmap and a SQLite working index, with streaming game segments. No million-record Python sets/lists. New output directory must not exist; all explicit writes stay below it. Original shards are never changed, moved or overwritten. A completed run removes only its own newly created scratch DB, independently rereads outputs, writes a deterministic MD5 manifest and sets all final payloads read-only0444. Failure leaves its own unsealed directory and diagnostic report for inspection; never train from a failed run.

## Position versus game exclusion

Without ordered text, position overlap is audited but `game_overlap` explicitly remains `UNVERIFIED_NO_ORDERED_TEXT`. POS contains no game IDs. This applies to the supplied data32 sample.

Optional `--text-map` JSON maps every training AND holdout source stem to its corresponding text; `--ordered-stems` supplies their complete chronological order. Each text row must match its POS board/STM/score/result exactly. A new conservative group starts only when fullmove decreases, piece count increases or the recorded WHITE result changes. Groups continue across file boundaries. Missing boundaries merge games, so removing every group touching any holdout conservatively removes neighboring games too. The report states the required normal-trajectory assumptions (chronological data, nondecreasing fullmove, nonincreasing piece count and constant result within each game). It does not claim authentic game IDs or independently authenticate the supplied chronology. Malformed/missing/misaligned text fails instead of guessing game identities.

The provided real916-line self-play text also matches all916 supplied POS rows, yielding12 conservative groups. Its HCE pair was not supplied, so real-text paired-output/training validation is UNVERIFIED and no HCE values were fabricated. Synthetic tests planted a holdout in a group spanning three source files and verified all its training rows were removed, with conservative-group overlap0. A deliberately undetectable boundary merges groups and excludes extra data. These tests are not a measurement of the absent production holdouts.

## Tests and results

| Check | Result | Evidence |
|---|---|---|
| Missing-tool RED before implementation | PASS negative control | Original missing-module failure retained |
| Independent final21 behavioral tests | PASS | Frozen tool SHA above; actualexit0 |
| Original reader/writer round-trip | PASS | Exact board/score/meta/HCE fields, headers/counts and empty-pair cases |
| Same-seed determinism | PASS | All sealed data, summary and manifest bytes equal across new output directories and reversed input argument order |
| Input protection / new-output-only / aliases | PASS | Before/after hashes unchanged; existing destination refused; holdout aliases excluded and counted |
| Independent MD5 payload check | PASS | Every sealed payload matches its manifest; manifest self excluded |
| Corruption / invalid holdouts / bad text | PASS | Structural errors reject; malformed authoritative fields reject; training invalid fields have counted reasons |
| Optional filter orientations | PASS | WHITE/black STM win/loss and draw thresholds, OFF behavior |
| Cross-shard conservative game exclusion | PASS on planted text fixture | Independent input/output row assertions; overlap0 for supplied groups |
| Independent bounded source review | PASS | Three requested repairs applied: streaming segments, alias accounting, exact text king/count validation |
| Supplied data32 OFF filter | PASS |200000 inputs kept200000, dropped0; all8 entire POS/HCE output files byte-identical to original sample |
| Supplied data32 threshold300 | PASS |200000 inputs kept157666, dropped42334 |
| Supplied stand-in h000 overlap | PASS |0 for independently reread outputs in both runs; no output duplicates |
| Real013/014 position and game overlap | UNVERIFIED | Actual files/hash lists absent |
| Data32 whole-game isolation | UNVERIFIED | Binary synthetic sample has no ordered game text |
| Unchanged v3b CPU CLI smoke | PASS | Actual3steps/768positions, seed20261025; printed train_mse0.029621; actualexit0 |
| Actual unchanged v3b RAM and mmap loaders | PASS | All157666 threshold300 retained records load through both original readers; all four arrays equal |
| Original retained-field lookup | PASS | Each of157666 retained board/score/meta/HCE tuples matches its original sample record |
| Actual provided916-line text alignment | PASS | All916 board/score/meta rows match the provided POS;12 conservative groups, authentic gameIDs UNVERIFIED |
| Training quality / strength gain | UNVERIFIED, no claim | Engine NNUE must review and run its own training line |

The actual CPU result comes from the unchanged supplied v3b trainer SHA256 `5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f`, CPU PyTorch2.5.1, H256/residual, batch256 and3steps. All original inputs and trainer hash remained unchanged. This is a fresh native smoke, not the historical pack QA loss. Parent preserves its exact argv/stdout/stderr and CPU helper separately.

### Full sample counts, seed20261025

Each input shard has50000 rows. OFF kept50000 per shard, with zero drops for every reason.

| Shard | threshold300 kept | total dropped | draw large | loss / positive score | win / negative score |
|---|---:|---:|---:|---:|---:|
|t00000|39533|10467|5288|2676|2503|
|t01000|39447|10553|5174|2714|2665|
|t02000|39342|10658|5378|2665|2615|
|t03000|39344|10656|5282|2701|2673|
|Total|157666|42334|21122|10756|10456|

Neither full sample contained duplicate positions or intersections with the50000-record h000 stand-in; planted regression fixtures exercise those drop paths. Invalid-field and holdout-game-group drops were0 on these POS-only sample runs. Zero sample overlap is not zero production overlap.

## Run on Linux

Use a NEW output directory for each run. The tool never starts training.

```bash
python3 -B forge_sol_datafilter_tests_20261025.py
python3 -B forge_sol_datafilter_20261025.py --train data32/t00000.pos data32/t01000.pos data32/t02000.pos data32/t03000.pos --holdout-pos data32/h000.pos --hce-dir data32 --out forge_sol_filtered_off_20261025 --seed 20261025
python3 -B forge_sol_datafilter_20261025.py --train data32/t00000.pos data32/t01000.pos data32/t02000.pos data32/t03000.pos --holdout-pos data32/h000.pos --hce-dir data32 --out forge_sol_filtered_threshold300_20261025 --seed 20261025 --disagreement-threshold 300
```

For real data replace the train arguments and supply BOTH authoritative013/014 holdout files. Add a complete text map/chronological stem list to request conservative whole-game exclusion; otherwise do not claim it. Text-map paths are interpreted relative to the invocation working directory unless absolute. Training consumes output `*.pos` and matching `*.hce` unchanged through the existing trainer `--hce-dir`.

Idea sources only: user's JobD contract, supplied FPOS/FHCE format documentation and the supplied text converter's recorded layout; the supplied handoff's idea of game groups from ordered text. All implementation/tests are original. No other engine code, tuned constants, ZIP, LICENSE, AGENTS or .agents file is delivered.

Failed approaches are retained: genuine initial missing-tool RED, intermediate strict source-hash receipt failure while source changed during testing, pre-repair tool versions, and the old-text-guard behavioral RED. The final21-test run and both full native sample runs used the unchanged frozen SHA above. No owned filtering/test/native job remains. Next: independent Engine NNUE review, then run against authoritative013/014 and complete ordered production text before approving any data for training.
