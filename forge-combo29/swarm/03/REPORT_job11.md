# REPORT — seat 03, job 11: the 50-position real-game lone-king scan (headline rate)

**What was asked.** Whether the S-F20 defect happens in the population the owner's matches reach: 50 real-game
lone-king positions at depth 16, report the rate of the signature (chosen move scored worse than an alternative by
more than a queen), and for hits, whether the wrong move costs measurable plies by play-out.

**The answer, plainly: the signature rate is 0 of 50 — my prediction said 5-20, and its own kill range was "fewer
than 2", so my prediction is KILLED.** The strict S-F20 signature (a self-contradiction of more than a queen) does
not occur in this sample. But the scan was not fruitless: **11 of 45 scorable positions had the chosen move scored
worse than an available alternative by any margin at all**, and in a play-out sample of 8 the engine's choice died
sooner in **5 of 8**, by up to **49 plies**. So the defect is real in this population at a smaller magnitude than my
threshold, not absent.

I am not widening the definition of a hit: the hit column stays 0 of 50 exactly as predicted and measured. The
smaller-magnitude results are reported separately below as a distribution, which is what the coordinator asked for.

**How sure.** High on the counts (every position measured, every score line present, 50/50). Moderate on the
play-out costs: 8 positions at depth 8, and play-out length is sensitive to the driver's depth.

## The position set had to change, and that is itself a finding

My first generator played engine-vs-engine games at depth 6. It produced **0 candidates from 40 games** because
**every game collapsed into the same position**, `8/8/8/8/8/5n2/4K1k1/4N3 b - - 11 60` (K+N vs K+N), where the engine
answers `cp 0` after 492 nodes at depth 12 and python-chess reports the position is NOT insufficient material. That is
the known drawn-root behaviour, reached here through bare-king play: low-depth self-play cannot produce a varied
lone-king population at all.

So the set was rebuilt (`gen_endgames.py`) from **material-imbalanced starts** — the strong side a rook, two rooks, a
queen, rook+minor, or two minors up — which is how real games actually reach a lone king. 50 distinct endings from
143 games, no duplicates, both colours represented. Sampling changed; the signature definition and threshold did
**not**.

I also found and fixed a real bug in my first generator while diagnosing this: `lone_side()` compared
`occupied_co[col]` (an int) with `b.pieces(KING, col)` (a `SquareSet` in python-chess 1.11), which is silently always
False. The fixed version carries a **known-answer self-test** that refuses to generate anything unless it detects a
lone king and does not fire on K+N vs K+N or on a full board.

## Results (`scan50.txt`)

```
scanned 50 lone-king positions, depth 16, PC20, Threads 1, Hash 16
signature threshold: chosen scores worse than the best alternative by more than 900 cp-equiv
HITS: 0 of 50
PARTIAL scans (more than 12 legal moves, only the first 12 by name scored): 2
```

- 45 positions scorable (5 have exactly one legal move, where "chosen versus alternative" is undefined — verified
  individually, not assumed: `8/K7/1r5r/8/2k5/8/8/8 w - - 0 11` has 1 legal move, etc.).
- 2 partial scans (>12 legal moves) — below my predicted ceiling of 20.
- 0 missing score lines, 0 crashes, 0 illegal bestmoves, 0 `0000` answers.

### Gap distribution (chosen score minus best alternative, cp-equivalent)

```
n=45  min=-9490  median=-10  max=+161
chosen worse by ANY margin (gap>0): 11 of 45
gap exactly 0: 6 of 45
```

So in **11 of 45** positions the engine's own depth-16 scores say a different available move is better, but by a
median of only 36 cp — far below my 900 cp signature. The largest was 161 cp.

## Ply cost for misses (the distribution asked for)

Play-out at depth 8, the 8 positions with the largest |gap| (`plycost.txt`):

| idx | gap | chosen | alt | plies after chosen | plies after alt | cost |
|---|---|---|---|---|---|---|
| 36 | -9490 | c4d5 | c4b3 | 30 | 14 | −16 |
| 30 | -9457 | c7d7 | c7b8 | 28 | 4 | −24 |
| 16 | -7787 | h7g6 | h7g8 | 32 | 16 | −16 |
| 22 | -1039 | g5f6 | g5g6 | 1 | 50 | **+49** |
| 37 | -973 | f6f7 | f6g7 | 1 | 24 | **+23** |
| 6 | -955 | e3f3 | e3d3 | 1 | 22 | **+21** |
| 10 | -899 | f2g2 | f2g3 | 30 | 34 | +4 |
| 44 | -529 | c7d6 | c7b8 | 1 | 39 | **+38** |

```
costs: n=8 min=-24 median=+21 max=+49 mean=+9.88
positive (the engine's choice dies sooner) 5, zero 0, negative 3
```

**5 of 8 chosen moves die sooner**, and four of those five lose the game almost immediately (1 ply) where the
alternative survives 22-50 plies. That is the practical shape of the defect: not a mate-score contradiction, but a
move that hands the game over at once.

The three negative-cost rows are the interesting counter-case: there the engine's chosen move survives LONGER while
its own score says it is worse by up to 9,490 cp. Those are positions where the engine is being mated in every line
and chose the slower loss despite the score — i.e. the score and the choice disagree in the *safe* direction. That is
the same inconsistency as S-F20, seen from the other side, and it means the score-versus-choice mismatch is not
systematically harmful.

## Prediction against result

| # | predicted | killed? | measured |
|---|---|---|---|
| 1 | 5-20 hits of 50 | **KILLED** | **0 of 50** (kill range was <2) |
| 2 | >=60% of hits report a mate against the mover | n/a | no hits |
| 3 | partial scans <=20 | no | 2 |
| 4 | 0 missing score lines | no | 0 |
| 5 | 0 crashes/illegal/0000 | no | 0 |
| 6 | scan under 60 min | no | ~4 min |
| 7 | report ply-cost distribution for misses | done | table above: 5/8 positive, median +21, max +49 |

## Findings

| id | one sentence | reproduce |
|---|---|---|
| S-F22 | In 50 real-game lone-king positions at depth 16 (PC build, PC20, Threads 1, Hash 16) the strict S-F20 signature (chosen move scored worse than an available alternative by more than a queen) occurs **0 of 50** times; the smaller-magnitude version (any margin) occurs 11 of 45 scorable positions, median 36 cp, max 161 cp. | `cd forge-combo29/swarm/03/job11 && python3 scan_loneking.py ~/build-pc/forge eg50.tsv /tmp/s.txt` |
| S-F23 | Among the 8 positions with the largest score gaps, play-out at depth 8 shows the engine's chosen move dying **sooner** than the alternative in 5 of 8 (cost +4 to +49 plies, four of them losing at once where the alternative survives 22-50 plies), and *later* in 3 of 8 — so the score-versus-choice mismatch is real in this population but is not systematically harmful. | `cd forge-combo29/swarm/03/job11 && PC_TOPN=8 PC_DEPTH=8 python3 plycost.py eg50.tsv scan50.txt /tmp/p.txt` |
| S-F24 | Low-depth engine self-play cannot produce a varied lone-king population at all: 40 consecutive depth-6 games all collapsed into the same `8/8/8/8/8/5n2/4K1k1/4N3 b - - 11 60` (K+N vs K+N), answered `cp 0` in 492 nodes at depth 12 while python-chess reports it is NOT insufficient material — the known drawn-root behaviour reached through bare-king play. | `cd forge-combo29/swarm/03/job11 && python3 gen_loneking.py 5 301 /tmp/lk.tsv` (prints 0 candidates and the self-test line) |

## Suspicions, not proven

- That the 4 instant-loss cases (chosen move loses in 1 ply, alternative survives 22-50) are the same root-comparison
  fault as S-F20 rather than a quiescence artefact at depth 8. A depth-16 play-out on those 4 would settle it; not run.

## What I did NOT do

- Play-outs only at depth 8, 8 positions, not all 45.
- Did not re-run the scan on the base build for comparison (the PC build is the one the owner plays).
- No sanitizer runs.

## What I am NOT sure about

- Whether the 11 any-margin cases would grow or shrink with a different position class: these are all converted-advantage
  endings, which is realistic, but they are still one generation method.
- Whether play-out length at depth 8 is a fair proxy for move quality at depth 16; it measures survival, not score.

## Times

`job11/stamps.txt`, `gen.log`, `scan50.log`.
