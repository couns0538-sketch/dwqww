# R14-B item 2 - resumable relabel with original FENs and a game-level validation split - IN PROGRESS, UNPROVEN

Branch `opus-r14b-relabel` (from `opus-r13-p5-nnue-data`). Own code `relabel2.py`; unchanged copies of R13's probe
client `forge_probe.py` (sha256 980c20cc...) and Astra's `astra/records.py` (from astra-r8-datafilter 8ebcf115,
sha256 444e854e...). Labels come from the R13 probe `C:\o13\p5\forge_data_probe.exe` (sha256 ed76de96..., lock
source d4f4312; transposition table, histories and caches cleared before every search). Engine NNUE decides whether
any of these labels are used; nothing here is a strength claim. The 50M run is not started.

## What R13 had and what is new
| R13 / R14 P5 (`opus_r13/p5/`) | R14-B `relabel2.py` |
|---|---|
| input .pos + FEN sidecar (sidecar fix proven on 1,000 rows) | input = self-play text (`FEN | stm cp | white result`) or Astra normalized JSONL: the original FEN with castling / en passant / clocks is the input itself |
| shards redone into `_r<attempt>` dirs; no kill / resume proof | `.part.N` shard dirs published by one rename after fsynced labels + manifest + summary; resume re-hashes every published shard; interrupted attempts kept |
| no game ids; split by position (Astra's converter) | game id per input file and game (leak-safe rule), split by sha256(salt, game id) |
| one slice per call | `prepare` / `run` / `assemble` / `status`; exit codes 2 bad input, 3 configuration differs, 4 integrity |

## Checks
| check | result | evidence |
|---|---|---|
| prepare on 2,000 rows: games found | 1,986 rows in 21 whole games, lengths 40-147, every game starts at ply 8-11 (the opening-book plies) | smoke, 13:20 |
| tiny-budget guard: 500 nodes, a position that cannot finish depth 1 | the run stops (not an exact searched label), assemble refuses (exit 4) | smoke |
| mini kill / resume (1,986 rows, 5,000 nodes, shards of 300; hard exit during start-up, resume) | md5 of train.txt / val.txt / labels.tsv identical to the uninterrupted job | smoke |
| bad input / configuration / integrity exit codes | **19 / 19 PASS**: 8 bad inputs (FEN fields, piece letter, score, result token, missing field, empty line, terminal position, no result) -> exit 2 naming the row, no rows.tsv published; missing file -> 2; existing job -> 3; changed nodes / shard size / run id -> 3; unfinished assemble, tampered shard, tampered rows.tsv -> 4; `--drop-terminal` -> 0 | logs/test_relabel2.log |
| 1M sample prepared twice (jobs A and B, `prove_resume.sh prepare`): `forge_selfplay_001.txt` (466,506 lines) + the start of `_002.txt`, cut at a game boundary | **999,921 rows in 10,880 whole games**; train 991,077 rows / 10,781 games, validation 8,844 rows / 99 games (1 % of games); game length 2-276 (median 85, p99 227); every game starts at ply 8-15 (no fragment); 0 terminal positions; rows.tsv A = B byte for byte (sha256 eefb1662...); 21 min wall for both at Idle next to BelowNormal training | `D:\o14b\r2\proof\job{A,B}\prepare.json` |
| 1,000,000-row proof: A uninterrupted vs B hard-killed twice (exit at an arbitrary point from a watchdog thread, sessions 1 and 2) and resumed | TODO (starts after item 1's CPU checks) | - |
| RELABEL_HANDOFF.md (positions / hour, 50M cost) | TODO | - |
