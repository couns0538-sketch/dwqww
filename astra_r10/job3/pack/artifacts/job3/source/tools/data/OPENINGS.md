# Astra A1 opening variety tool

`generate_openings.py` uses the unchanged Forge native probe to select deterministic
random early moves. Default lengths are 6–16 plies, chosen uniformly. Every selected
position, including the initial position, is searched at the configured fixed node
budget; an absolute score above 150 cp rejects that whole attempt. Final positions
must be nonterminal and not in check. Exact final piece-placement/side duplicates
are excluded even if clocks, castling rights or en passant differ. `--final-only`
explicitly weakens the band check to the final position; the report records this.
No extra lower-bound imbalance is implied: choose `--min-abs-cp 25`, for example,
when a trial specifically requires final scores between 25 and 150 cp. This is an
experimental input policy, not an engine constant or strength claim.

The seed controls Python's local RNG only. With the same Python implementation,
probe binary, settings and deterministic native responses, the book and selected
metadata are byte-identical. Native IPC logs include actual runtime accounting;
those logs and their hashes need not be identical across runs. The protocol uses
one single-threaded probe process, and the probe is responsible for resetting TT/
search state between independent analyses. Actual reported nodes/depth are retained;
a requested node budget is not advertised as an exact actual node count.

## Standard book for unchanged R8 v5

```sh
python3 tools/data/generate_openings.py \
  --probe /path/to/forge_data_probe --out /new/path/openings-seed-20261030 \
  --count 100 --seed 20261030 --nodes 5000 --hash-mb 1 \
  --min-plies 6 --max-plies 16 --max-abs-cp 150 --min-abs-cp 25
```

`openings.moves` contains only one whitespace-separated UCI move sequence per line,
from standard startpos. There are no comments, FENs, IDs, TSV columns or blank lines.
`metadata.jsonl` separately preserves the start/final FENs, every selected move,
intermediate score checks, side-to-move and White-perspective final scores, search
accounting and probe binary digest. `generation.json` counts every disjoint
rejection reason and reports White/Black/equal-score variety. The bounded default
attempt limit is `100 * count`; exhaustion returns exit 2 and leaves the actual
partial outputs without `SUCCESS.json`.

R8 source `5dd3a57d6f286f09b8881671ba8a368f6d34f717` consumes this file with
`--openings FILE`. Verify the successful seal, manifest, nonempty file and path
before giving it to R8: that driver's missing/empty-book path falls back to random
openings. The R8 process is Windows-only. Its `--priority idle` sets engine children
Idle, while the driver explicitly sets itself BelowNormal; that flag alone does
not prove the whole job is Idle. No live driver/trainer is touched by this tool.
The parent job supplies the reviewed spare-core/Idle wrapper separately.

## Optional Chess960-style arrangement export

```sh
python3 tools/data/generate_openings.py \
  --probe /path/to/forge_data_probe --out /new/path/backranks-seed-20261030 \
  --count 100 --seed 20261030 --nodes 5000 \
  --format fen --chess960-style
```

This original arrangement routine puts the bishops on opposite colours and the
king between its rooks, with a mirrored black back rank. **Castling rights are
explicitly absent (`-`). This is not true Chess960.** Both Forge's current castling
rules and R8's startpos-only move book are orthodox. Consequently this mode writes
`openings.fen`, refuses `--format r8`, and records `r8_compatible=false`. A later
reviewed FEN-capable driver or true Chess960 implementation is required to consume
these starts in self-play. Do not silently feed the FEN file to R8.

## Safety, evidence and tests

The output directory must be new. No existing file is changed, removed or reused.
Data and metadata are streamed as they are accepted; only a clean native-probe
shutdown followed by manifest creation produces `SUCCESS.json`. A partial or failed
run is not sealed and remains recoverable. The seal validates generation completion;
its `native_legal_replay` field explicitly says that an independent replay is not
performed by sealing alone. Root-owned native validation is a separate result.

```sh
python3 tests/data/test_generate_openings.py -v
```

These tests inject synthetic probe responses: no native engine, speed, Elo or
training result is inferred from them. They cover deterministic files, both score
perspectives, intermediate rejection, explicit final-only policy, terminal-before-
analysis handling, final check, duplicate/attempt caps, existing-output refusal,
no-castling arrangements, R8 incompatibility, malformed protocol responses, clean-
shutdown sealing and manifest hashes. Synthetic fixture directories are retained
under the system temporary directory rather than deleted.

IDEA_SOURCE: the user's Astra A1 data request; same-repository R8 v5 source and
README at `5dd3a57d6f286f09b8881671ba8a368f6d34f717`; Forge's Board and native probe
interfaces. No external engine code, book, games or tuned constants were copied.
