# REPORT job1b — seat 05, area 5 — job 1 again, next seed, new position set

## 1. the three lines

**What was asked.** The brief's cycle step (c): job 1 of my area again with the next seed and a new position set
(R with SEED + 10 = 511). Play every last-PV line with python-chess and check legality; check every `mate N`
against 2N-1 plies (N > 0) or 2|N| plies (N < 0).

**The answer.** 200 of 200 searches produced a `bestmove` and a PV, and **0 PV moves were illegal**. 18 positions
carried a mate score; **17 of those 18 are exactly the mate the score claims**, and the one exception is the same
truncation I found in job 1 — now reproduced on a set that had nothing to do with finding it. That makes S-F1
general behaviour rather than a one-position curiosity.

**How sure.** High on the legality count and on 17/18 (both are pure functions of committed raw files). High on the
reproduction being real (fresh set, deterministic, self-corrects with depth exactly as G/192 did). My *prediction*
of how many mate scores this set would contain was **wrong** — see §5.

## 2. honesty numbers

`../HONESTY.txt` 4/4, re-verified with a read-to-terminator harness after seat 19's 19-F12 warning
(`../audit19f12/out/recheck.txt`): 312866 / 862329 / 3024920 / 4865609.

## 3. what differs from the first job1 run (the brief requires this to be stated)

| aspect | first run (`../job1/`) | this repeat |
|---|---|---|
| seed | 501 | **511** |
| position set | O (200 from kimi5 `first200.fens`) + G (353 game positions) | **R_seed511: 200 positions from random play, one every 7 plies, never searched before** |
| depth / settings | 12 / S14 Threads 1 Hash 16 | identical, so numbers are comparable |
| mate scores found | 10 of 553 | 18 of 200 |
| truncation instances | 1 (G/192) | **1 (R/120)** |
| sum of last depth-12 nodes | O 9,500,069 + G 18,466,239 | 12,230,484 |

## 4. the job, step by step

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| PREDICTION pushed alone before measuring | done | `PREDICTION.md` (commit `0e4d9104e`) | 9 numbered predictions with kill conditions |
| R set generated with `random.Random(511)` and asserted | done | `make_R.py`, `positions/R_seed511.fens` | 200 positions from 6 games; 0 illegal or already-over |
| rows run at depth 12, S14, Threads 1, Hash 16 | done | `outR/R.d12.raw.txt`, `outR/R.d12.raw.txt.meta` | 200 blocks, 200 bestmoves |
| PV replay with python-chess | done | `check_pv.py`, `outR/check_table.txt`, `outR/rows.jsonl` | TABLE B = **0 illegal** |
| mate arithmetic 2N-1 / 2\|N\| | done | `outR/check_table.txt` | 17 of 18 consistent |
| node sums, median, zero-node count | done | `outR/sums.txt` | sum 12,230,484, median 46,976, 0 zeros |
| determinism control | done | `outR/control_repeat.txt` | cold 0/1 and warm 0 identical (`cp -20`, 54,401 nodes) |
| new truncation instance probed deeper | done | `outR/probe_R120.txt` | -13 → -13 → -10 → -8 at depths 12/14/16/18 |

## 5. my predictions, including the two that failed

| # | predicted | actual | verdict |
|---|---|---|---|
| 1 | 200/200 with bestmove and PV | 200/200 | HELD |
| 2 | 0 illegal PV moves | 0 | HELD |
| 3 | 0 to 6 mate scores (kill: more than 12) | **18** | **WRONG — kill condition fired** |
| 4 | at most 1 PV inconsistent with its mate score | 1 | HELD |
| 5 | sum 10M–40M | 12,230,484 | HELD |
| 6 | median 60,000–130,000 | **46,976** | **WRONG** |
| 7 | same position twice: identical score and nodes | identical | HELD |
| 8 | 0 crash / hang / missing bestmove | 0 | HELD |
| 9 | the S-F1 truncation reappears at least once | 1 instance | **HELD — the important one** |

**Why #3 and #6 were wrong, said plainly.** I assumed random play would produce quiet, non-tactical middlegames.
It did not: 200 positions from only **6 games** means the positions are heavily correlated (they are consecutive
samples along a few random games, which in chess are capture-heavy and material-lopsided), and 18 of them end in a
forced mate inside 12 plies. A median of 46,976 nodes is below my 60k floor for the same reason — the trees are
smaller than I guessed. My prediction was a guess about my own generator's output, and the generator's output
disagreed with it. Nothing about the *engine* conclusion depends on that guess: predictions #1, #2, #4, #9 all held,
and they are the ones that concern the engine.

## 6. findings

### S-F9 — the truncated-mate-PV behaviour is general, not a G/192 curiosity
On the fresh R set, position 120 (`positions/R_seed511.fens` line 121, a random-play position never searched before)
the depth-12 search reports:

```
info depth 12 seldepth 36 score mate -13 nodes 191044 ... pv b2e5 f4e5 e7e6 b7b8q g4g3 b8e8 e6f5 e8h5 f5e4 a8g8 g3g2 g8g2 e4e3 e5e6
```

`mate -13` promises mate in 26 plies; the PV is **14 plies** and does not end in checkmate. Searched deeper the same
position gives `mate -13` at d14, `mate -10` at d16 and `mate -8` at d18 — the same self-correction pattern G/192
showed, which is what makes this one behaviour rather than two coincidences.

Reproduce:

```
python3 check_pv.py R=outR/R.d12.raw.txt
python3 ../job1/mate_depth_probe.py /tmp/build-rel/forge "$(sed -n 121p positions/R_seed511.fens)" 12 14 16 18
```

### S-F10 — R-set baseline (no fault, recorded for the next comparison)
200/200 bestmove+PV, 0 illegal PV moves, 18 mate scores (17 consistent), sum of last depth-12 nodes 12,230,484,
median 46,976, minimum 226, maximum 298,438, **0 positions with 0 nodes**. Evidence `outR/sums.txt`,
`outR/check_table.txt`.

## 7. suspicions, NOT proven
- **The cause of the truncation is still unknown to me.** I did not read `search.cpp`; S-F1/S-F9 remain a
  description of behaviour. Two instances in different sets with the same self-correction shape is consistent with
  a PV rebuilt from the transposition table at a shorter remaining depth than the score, but I have not tested it.
- **Whether the mate *scores* themselves are right.** For R/120 I know the PV is too short; I do not know whether
  the true distance is 26 plies, shorter, or longer. My `dtm2.py` cannot settle it inside its time cap at that
  distance, and Stockfish is not a minimality authority (see `../job1/REPORT_job1.md` §5).
- **Whether 6 games is a fair sample.** 200 positions from 6 games are strongly correlated, so the 18 mate scores
  are not 18 independent events. A better R set would use more games and fewer positions per game; I did not
  regenerate it, because regenerating after seeing the result would make the set unprincipled.
- **Why the median is low.** I attribute it to the capture-heavy character of random play, but I did not measure
  the material balance of the set to confirm that.

## 8. what I did NOT do
- I did not regenerate the R set after seeing that predictions #3/#6 failed. Changing the set afterwards would
  invalidate it.
- I did not run the R set at depth 14 or 16 across all 200 positions (only the one probed position).
- I did not check the mate *scores* of the 17 "consistent" positions against an outside authority; "the PV is
  exactly 2N-1 and ends in checkmate" is the brief's criterion and I used only that.
- I did not use the O and G sets again in this job, so this is a fresh-set result only.

## 9. what I am NOT sure about
- Whether S-F9's single instance in 200 positions (versus 1 in 553 for the O+G run) means the rate is similar or
  different, because the two sets have very different mate-density (18/200 vs 10/553). A per-mate-score rate would
  be 1/18 here versus 1/10 there, which suggests the truncation is *less* frequent in this set — but with one
  instance each, neither number means much.
- Whether R/120's truncation and G/192's share a mechanism at all. They share a shape, not a proven cause.

## 10. times
See `stamps.txt`.

## 11. last command's output

```
$ git status --short
(clean at the commit that added this report)
$ ls
PREDICTION.md  check_pv.py  make_R.py  out  outR  positions  stamps.txt
$ ls outR | tr '\n' ' '
R.d12.raw.txt R.d12.raw.txt.meta check_table.txt control_repeat.txt probe_R120.txt rows.jsonl sums.txt
```
