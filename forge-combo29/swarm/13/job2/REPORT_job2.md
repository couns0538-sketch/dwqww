# REPORT_job2 — seat 13, area 3, job 2: 500 special positions at perft 1..4

## What was asked
Area 3 job 2: 500 special positions found by filtering R and G with python-chess (castling with an
attacked transit square, en passant that would expose the king, a capture-promotion with check,
double check, a pinned piece that can capture its pinner), then perft 1 to 4 on each.

## The answer
Over 494 special positions and 1,976 (position, depth) pairs — **1,976 compared, 0 different** from
python-chess. Additionally, on every one of the 494 positions the engine's own perft-2 divide
matches python-chess **move by move**: same root-move set, same count for every root move.

## How sure
High, and this time the tooling was hardened first (see ../INTEGRITY_AUDIT.md). The numbers below
come from a re-run made *after* I found that my first attempt had been compared against a stale
reference file; the earlier attempt is void and its numbers appear nowhere except as the reason the
audit exists.

## Honesty numbers
All four pins MATCH, and were re-run **interactively** (no stdin close during a command, after the
19-F12 warning): bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609.
Raw: `../honesty/honesty_recheck.txt`.

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| Seven class definitions, each a predicate returning computed facts | done | `classes.py` | single source of truth for the set and the checker |
| Density pool: 3,000 random games, every ply tested | done | `dense_pool.py`, `dense_hits2.tsv` | 464 class hits |
| Targeted pool for the rook-path class (random play never produced it) | done | `pool_rook_path.py`, `hits_rookpath.tsv` | 70 verified positions |
| Set built by re-classifying every candidate FEN | done | `build_set.py`, `special500.fens`, `special500.tsv` | 494 positions, all seven classes |
| Prediction committed before measuring | done | `prediction.txt` | predicted 0 differences at all depths; 0–1 at perft 1 |
| Engine perft 1..4 | done | `raw_engine.txt` + `.meta` | 1,976/1,976 records, all OK |
| Reference perft, 4 shards, fresh workdir, counts asserted | done | `ref_par.py`, `raw_ref.txt`, `ref_par.log` | 1,976 records = 494 x 4 |
| Comparison (hardened: fails on empty/missing/nan) | done | `compare.py`, `comparison.md` | 1,976 compared, 0 differing |
| Divide check: move set + per-move counts, plus class properties | done | `divide_check.py`, `out_divide/VERDICT.md` | 0 of 494 differ; 0 property failures |
| Five-class coverage of the original job text | partly | `special500.tsv` | see coverage note below |

Composition of the 494, each verified by `classes.py`:

| class | count |
|---|---|
| castle_transit_attacked | 78 |
| ep_pseudo_but_illegal | 7 |
| ep_legal | 83 |
| castle_rook_path_attacked | 77 |
| capture_promo_check | 83 |
| double_check | 83 |
| pinned_captures_pinner | 83 |

## Coverage note (said plainly, not hidden)
The job names five cases. I have all of them, but two are thinner or reframed than the wording
suggests:

- **"en passant that would expose the king"** is genuinely rare: 7 positions out of 3,000 random
  games at every ply. 7 is what exists in my pool, and I kept all 7 rather than inflate the class.
  To give the ep code real weight I added the matching `ep_legal` class (83), which exercises the
  same generation and make/unmake path from the other side. Both classes are reported separately.
- **"castling with an attacked transit square"**: 78 found. I also discovered while building this
  that the case "the *rook's* destination square is attacked" cannot exist — the rook's destination
  (d1/f1) is the same square the king crosses, so such castling is already illegal. I first wrote
  that class, found it empty for that reason, and replaced it with the case that does exist: a legal
  queenside castling while b1/b8 (a square only the rook crosses) is attacked, 77 positions. That
  is a corrected class, and I say so rather than quietly dropping it.

## Findings
- S-F2: the engine's move generation agrees with python-chess on 494 positions selected for exactly
  the cases that a random sample almost never contains: **1,976 perft pairs, 0 differences**, and
  **0 root-move-set or per-move-count differences** at perft 2. Show it again with
  `cd forge-combo29/swarm/13/job2 && python3 compare.py raw_engine.txt raw_ref.txt special500.fens /tmp/o.md 494`
  then `grep 'differing pairs' /tmp/o.md`, and
  `python3 divide_check.py ~/b/rel/forge special500.fens special500.tsv /tmp/div`.
  Reported honestly as a null result: it is strong evidence the generator is right on these
  classes, not proof it is right everywhere.

## Suspicions, not proven
- None from the engine. Every suspicion this job produced was about my own tooling, and all three
  are in `../INTEGRITY_AUDIT.md` with the fix and the control that proves the fix.

## What I did NOT do
- Depth 5 / the first 30 of G: that is job 3.
- I did not run this under a sanitizer; job 2 does not ask for it.
- I did not use R's one-in-seven sample as the pool; I used every ply of 3,000 games because the
  sparse sample yielded only 129 hits and no ep cases at all. `R_1301.fens` is unchanged and still
  the job 1 set.

## What I am NOT sure about
- The 7 ep-exposing positions are few. If the engine had an ep-specific bug that needs a particular
  geometry, 7 samples is weak protection, and I would not claim the ep path is proven right — only
  that these 7 (plus 83 legal ep positions) are right.
- My `double_check` class asserts only that the engine's move set equals python-chess's; it does not
  separately verify that only king moves were generated. The divide covers it (the move sets are
  identical), but I did not assert the property directly.

## Times
See `stamps.txt`.

## Last command output
```
$ ls
assemble_special.py
build_set.py
classes.py
compare.py
comparison.md
dense2.log
dense_hits2.tsv
dense_hits.tsv
dense.log
dense_pool.py
divide_check.py
engine_perft.py
gen_special.py
hits_all.tsv
hits_rookpath.tsv
out_divide
pool_rook_path.py
prediction.txt
R_1301.fens
raw_engine.txt
raw_engine.txt.meta
raw_ref.txt
refdone.txt
ref_par.log
ref_par.py
ref_perft.py
REPORT_job2.md
set_G.epd
special500.fens
special500.tsv
special.fens
special.tsv
stamps.txt
```
