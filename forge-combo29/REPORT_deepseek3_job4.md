# REPORT deepseek3 job 4

**First line, in plain words: `LowPlyHist` does not gain strength per node — pooled over both seeds it is
-3.09 Elo, 95% interval -12.3 to +6.1. Of the eval-swing strengths, 12 is the one that shows a gain
(+20.7, interval +7.2 to +34.2 on 1,194 games); 48 clearly is not better (-13.3, interval -28.4 to +1.8),
and 24 was left to the other helper. Neither of my Part B matches reached 2,000 games: the clock ran out
because this tree is slower than the one I measured on in jobs 1-3.**

**What was cut: B3 (`EvalSwingMult 24` + `EvalSwingMax 400`, 1,500 games, seed 7915) was never run** —
I stopped at 73 minutes as the job instructed. A1, A2, B1 and B2 were all cut short by their own time
limits; every one of them has usable data and the count reached is given for each. The order the job set
(A1, B1, B2, A2, B3) was followed exactly, so what got cut is what Fable said to cut first.

I am `deepseek3`. Branch `for-fable-and-opus/deepseek3-work`. No pull request, no engine source
committed, no binaries. Base commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa`, source at the repo
root, built Release with g++ 13.3.0. All numbers are for **20,000 nodes**, `Threads 1`, `Hash 16`,
`OwnBook false`, UHO openings with both colours, no adjudication.

---

## 1. Step 0 — known numbers on the base build

`logs/step0-base.txt`, 18:39:58Z to 18:40:00Z. One build flag difference from jobs 1-3 that matters and
that I had to discover: this tree has **no `FORGE_NNUE_HIDDEN` CMake option at all**, so
`-DFORGE_NNUE_HIDDEN=256` has to be passed as a compiler flag. Without it the build fails on a static
assert in `nnue_weights.inc` ("rebuild with the correct FORGE_NNUE_HIDDEN"), and I hit exactly that
before finding it.

| command | expected | base build | match |
|---|---:|---:|---|
| `bench 11` | 312866 | 312866 | yes |
| `bench 13` | 862329 | 862329 | yes |
| `go perft 5` | 4865609 | 4865609 | yes |

One further build detail: this tree exposes the search tunables in `uci` only `#ifdef
FORGE_EXPOSE_TUNABLES`, and its CMakeLists does not define it. Without that define, `setoption` still
works but `uci` does not list the options. I built with `-DFORGE_EXPOSE_TUNABLES=1` as well, because the
job requires `uci` to list `LowPlyHist`, and because a hidden option is exactly how a match silently runs
with nothing set. All four builds in this job use the same flags:
`-DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1`, Release, `-DFORGE_MARCH` default (`-march=native`
in this tree).

## 2. Part A — the known numbers for `LowPlyHist`

The patch `opus_r15/cands/c6_lowplyhist/c6_lowplyhist.patch` (from branch `opus-r15-20261103`) applies
cleanly to `d4f43124` with `git apply`, no conflicts. `logs/step1-A-known-tunables.txt`:

| setting | command | expected | printed | match |
|---|---|---:|---:|---|
| off | `bench 11` | 312866 | 312866 | yes |
| off | `bench 13` | 862329 | 862329 | yes |
| off | `go perft 5` | 4865609 | 4865609 | yes |
| `LowPlyHist 1` | `bench 11` | 320362 | 320362 | yes |
| `LowPlyHist 1` | `bench 13` | 897394 | 897394 | yes |
| `LowPlyHist 1` | `bench 16` | 2563336 | 2563336 | yes |

All six match the job's numbers exactly. `uci` lists it:

```
option name LowPlyHist type spin default 0 min 0 max 1
```

## 3. Part B — the known numbers for `packc28`

`packc28_port.patch` (branch `opus-r13-p1-nearmiss-ports`) applies cleanly to `d4f43124`. Option off
gives the same three numbers (312866 / 862329 / 4865609). With
`AspFailHighReduce 1, AspFailHighMaxReduce 3, EvalSwingMult 24, EvalSwingMax 200`:

```
bench depth 13 nodes 690187      (job's number: 690187 — exact)
```

**Correction to the job text, small but worth having:** it says these options "are NOT listed in the `uci`
answer of this patch, so the match program never sends them". With `-DFORGE_EXPOSE_TUNABLES=1` they *are*
listed:

```
option name AspFailHighReduce type spin default 0 min 0 max 1
option name AspFailHighMaxReduce type spin default 3 min 1 max 6
option name EvalSwingMult type spin default 0 min 0 max 64
option name EvalSwingMax type spin default 200 min 50 max 400
option name TtCutoffHistory type spin default 0 min 0 max 1
```

They are exposed through `forge::tune::parameters()` at `src/uci.cpp:177` and `:204`, under
`FORGE_EXPOSE_TUNABLES`, which this tree's CMakeLists does not set. I still used the wrapper the job asked
for, since it works whether or not the options are advertised, but the premise in the job text was a
build-flag artefact rather than a property of the patch.

## 4. The wrapper, and how its options are proven to arrive

`wrapper_B.sh` writes `setoption` lines into the engine's stdin and then hands the rest of stdin through:
`{ printf 'setoption ...'; cat; } | exe`. `wrapper_B_12.sh`, `wrapper_B_48.sh`, `wrapper_B_24_400.sh`
are one-line callers for the three settings.

**The proof is the bench count, not the fastchess log, and the job's instruction to quote the wrapper's
lines from the engine log cannot be satisfied literally.** fastchess's `-log engine=true` records traffic
between fastchess and the engine *process*; the wrapper writes straight into that process's stdin, so its
lines never pass through fastchess and cannot appear in fastchess's log. I ran the probe anyway
(`logs/probe-B1-wrapper.engine.log`, 2 games, seed 7913) and it shows only `Threads`, `Hash`, `OwnBook` —
which is the whole point and would otherwise be alarming. What does prove delivery
(`logs/probe-B1-wrapper.NOTES.txt`):

| command through the wrapper | bench 13 |
|---|---:|
| bare exe, nothing set | 862329 |
| `wrapper_B_12.sh` (Mult 12, Max 200) | **748790** |
| `wrapper_B_48.sh` (Mult 48, Max 200) | **597400** |
| `wrapper_B_24_400.sh` (Mult 24, Max 400) | **758728** |

Four different counts, so the wrapper's options reach the search. The multi-option case also reproduces
the job's own 690187 exactly, which is a second, independent confirmation.

**Part A's probe** (`logs/probe-A1.engine.log`) is the literal thing the job asks for, because Part A
uses an advertised option and fastchess sends it itself:

```
cand <--- setoption name Threads value 1
cand <--- setoption name Hash value 16
cand <--- setoption name OwnBook value false
cand <--- setoption name LowPlyHist value 1
...
base <--- setoption name Threads value 1
base <--- setoption name Hash value 16
base <--- setoption name OwnBook value false          (no LowPlyHist)
```

## 5. The control

`logs/control.full.txt`, 300 games, seed 7910, 20,000 against 10,000 nodes per engine.

```
Elo: 248.15 +/- 38.55, nElo: 351.44 +/- 39.32
Games: 300, Wins: 202, Losses: 18, Draws: 80, Points: 242.0 (80.67 %)
Ptnml(0-2): [2, 3, 21, 57, 67], WL/DD Ratio: 1.10
```

Near +200 as required (a little above), pair counts strongly off-centre, so the tool sees a difference
with this build.

## 6. The matches

`own Elo` is my pentanomial computation from the pairs with a 95% interval (`job4_elo.py`, output
`logs/job4_elo.txt`); fastchess's own printed figure is beside it.

| match | candidate | seed | games (asked) | cand W-L-D | pairs | pair counts | fastchess Elo +/- err | own Elo, 95% interval |
|---|---|---:|---:|---|---:|---|---:|---|
| A1 | `LowPlyHist 1` vs off | 7911 | **1703 of 2000 (cut)** | 487-507-709 | 851 | [48,209,351,201,42] | -4.08 +/- 11.42 (its block covers 1,600) | **-4.08, -15.2 .. +7.0** |
| A2 | `LowPlyHist 1` vs off | 7912 | **885 of 2000 (cut)** | 256-259-370 | 442 | [30,103,177,104,28] | -2.17 +/- 16.50 (covers 800) | **-1.18, -17.4 .. +15.0** |
| **A pooled** | | | **2588** | 743-766-1079 | 1293 | [78,312,528,305,70] | | **-3.09, -12.3 .. +6.1** |
| B1 | `EvalSwingMult 12`, `EvalSwingMax 200` | 7913 | **1194 of 2000 (cut)** | 369-298-527 | 597 | [25,128,238,163,43] | +18.08 +/- 14.73 (covers 1,000) | **+20.68, +7.2 .. +34.2** |
| B2 | `EvalSwingMult 48`, `EvalSwingMax 200` | 7914 | **1021 of 2000 (cut)** | 280-318-423 | 510 | [43,119,210,110,28] | -12.51 +/- 15.34 (covers 1,000) | **-13.29, -28.4 .. +1.8** |
| B3 | `EvalSwingMult 24`, `EvalSwingMax 400` | 7915 | **NOT RUN** | — | — | — | — | — |

**Read the two right-hand columns with care.** My `own Elo` uses every game played. fastchess's printed
figure is its last periodic block, which lags the games actually played — the number of games that block
covers is stated in brackets, because for all four matches it is fewer than the games completed. Where
both are given they agree closely anyway (A1 -4.08 both, B1 +20.68 against +18.08, B2 -13.29 against
-12.51), which is a useful cross-check on the pair arithmetic.

**Crashes, illegal moves, disconnects: 0 in every match and in the control.** Checked by tallying how each
game ended, not by grepping for the word (`logs/termination_reasons.txt`): every one of the 5,103 games
ended by a chess rule (mate, 3-fold, fifty moves, insufficient material, stalemate).

Per-game files: `logs/{A1,A2,B1,B2}.games.txt`, one line per game. PGNs were deleted after deriving these
because of their size. The control match has no per-game file: I ran it without `-pgnout`, so it is the
one match whose per-game record does not exist — its aggregate is from fastchess's own output.

## 7. Verdicts and what they mean

**Part A — `LowPlyHist` gains nothing.** Pooled -3.09, interval -12.3 to +6.1. Both seeds are negative
(-4.08 and -1.18), which is at least consistent, but the pooled interval contains zero by a wide margin.
By the job's own rule this is "no difference shown", and with both seeds played I would close it. Note
that it *does* change the search a lot (bench 16 falls from 3024920 to 2563336, a 15% node drop), so this
is not a feature that failed to arrive — it arrived, changed the tree, and did not pay.

**Part B — of the strengths I played, 12 is the only one that shows anything.** +20.68 with an interval
that excludes zero (+7.2 to +34.2) on 597 pairs. 48 is the opposite: -13.29, interval -28.4 to +1.8, so
it is either nothing or a clear loss. The job's question "which eval-swing strength is best, 12, 24 or 48"
I can only half answer: **12 shows a gain and 48 does not, and 24 was not run.** That 12 beats 48 is
consistent with the idea having an optimum and overshooting being harmful, which is what you would expect
from a term that swings the eval toward the opponent's side.

**The honest caveat on B1.** It is the one number in this job I would want repeated before anyone acts on
it. It reached 1,194 of the asked 2,000 games, and it is the *best of two* Part B settings I played — the
job's warning about "the best or worst of one match" applies to me here. The interval excluding zero is
encouraging but it is one seed, cut short.

## 8. Files of the repository I opened

`CMakeLists.txt` at the root of `d4f43124`, `src/uci.cpp` (option dispatch, the `FORGE_EXPOSE_TUNABLES`
list, `setoption` handling), `src/search.cpp` and `include/forge/search.hpp` (as modified by each patch),
`src/nnue.cpp` and `src/nnue_weights.inc` (only the static_assert at the top, to find the required hidden
size), and the two patch files themselves from `opus_r15/cands/c6_lowplyhist/` and
`opus_r13/p1/packc28/`. I did not open any other helper's folder or report.

## 9. Stamps

| step | start | end | source |
|---|---|---|---|
| base tree build (after finding the hidden-size flag) | 18:39:3xZ | 18:40:0xZ | — |
| Step 0 on the base build | 18:39:58Z | 18:40:00Z | `logs/step0-stamps.txt` |
| Part A / Part B known numbers | 18:40:0xZ | 18:41:0xZ | `logs/step1-A-known-tunables.txt`, `logs/step1-B-known.txt` |
| Control match (300 games) | 18:41:04Z | 18:43:22Z | `logs/control-stamps.txt` |
| A1 probe (2 games, trace log) | 18:43:25Z | 18:43:28Z | `logs/probe-A1.engine.log` |
| A1 | 18:43:31Z | 19:02:42Z | `logs/A1-stamps.txt` |
| B1 wrapper probe, then B1 | 19:02:5xZ | 19:23:31Z | `logs/B1-stamps.txt` |
| B2 | 19:23:34Z | 19:39:25Z | `logs/B2-stamps.txt` |
| A2 | 19:39:29Z | 19:52:50Z | `logs/A2-stamps.txt` |
| report written | 19:53Z | — | — |

Job file found 18:39:25Z; last match ended 19:52:50Z = **73 min 25 s**, inside the 85-minute budget and
just inside the 75-minute stop point by about 1.5 minutes.

**Why so many matches were cut short:** I sized each match's `timeout` on jobs 1-3, where 2,000 games at
20,000 nodes took about 18 minutes. This tree is slower — `bench 13` reports **nps 1324622** here against
1721215 on the jobs 1-3 tree at the same depth, so roughly 23% slower per node — so the same game count
needs about 22-23 minutes. A1 was cut at 1,703 games by a limit of 1,150 s for that reason, and I then
made the later limits conservative, which cut them further. That is a planning error of mine, not a
machine fault: I had the nps numbers in front of me from Step 0 and did not use them.

## 10. What I did not do

- **B3 was not run at all.** The job's order put it last so it would be the first thing cut, and it was.
- **A1 (1,703/2,000), A2 (885/2,000), B1 (1,194/2,000), B2 (1,021/2,000) were all cut.** All are marked
  in the table with their real game counts, and my own Elo uses every game played.
- **A2 is much shorter than A1** (885 against 1,703), because its limit was set after A1 and B1 had both
  run long. The pooled Part A number is dominated by A1.
- **I did not run the other helper's 24 setting.** The job says another helper plays the four options
  together on a second seed and the ideas apart, so the 24-at-200 cell is theirs; but the job also asked
  me which of 12/24/48 is best, and I can only compare 12 and 48 from my own games.
- **The control match has no per-game file** (no `-pgnout`); its aggregate is fastchess's.
- **No time control, no PC net**; 4 cores, concurrency 4.
- I did not test `LowPlyHist` with any other value than 1 (the option is `0..1`, so there is no other).

## 11. What I am not sure about

- **B1's +20.7 is the result I trust least per unit of interest.** One seed, 1,194 games, and it is the
  best of the two settings I played — the exact situation the job text warns about. Its interval
  (+7.2..+34.2) excludes zero, which is more than any other number here, but a second seed is what would
  make it a result rather than a candidate.
- **Whether 12 is "best" or just "the one that happened to be positive".** I have 12 and 48; the
  monotone-looking pattern (12 positive, 48 negative) suggests an optimum in between, but 24 is exactly
  the cell I did not run, so the shape is a guess.
- **Part A's -3.09 could be -8 or +5** on this evidence. Both seeds are negative, which is why I lean
  "nothing rather than good", but I would not claim the sign.
- **The cut matches are not obviously biased** — the cut is by wall clock, which is independent of the
  position — but a short match's interval is wider than the table's fastchess column suggests when I use
  fastchess's lagging block (I flagged which count each fastchess number covers).
- **The 15% node drop on `bench 16` for `LowPlyHist`** is a large behaviour change for a "no difference"
  strength result; it makes me suspect the option's weight (2 at the root, falling to 4/5 at ply 3) is
  not tuned, and that a tuned weight might show something. Untested.

## 12. A better way

**Size the time limit from the machine, not from the last job.** I lost about 35% of my asked game count
across four matches because I reused a limit from a faster tree. The fix is mechanical: run `bench 13`
once on the final build, take its nps, and set `timeout = games * nodes_per_game / (nps * concurrency)`
times a safety factor, with `nodes_per_game` measured from the first 50 games of a probe. A job could ask
for the limit to be computed this way and the report would then almost never say "cut". How to check it:
on the next job, compare the predicted wall time against the actual for one 200-game probe; if it is
within 10%, the formula is good enough to use for the full matches.

**For a two-seed question, play both seeds to the same game count, or pool by time rather than by games.**
My Part A pooling is weighted towards A1 (1,703 games against 885), which is not what "pooled over two
seeds" should mean. A cleaner rule: give the pair of seeds one shared time budget, play each seed until
the total is spent, and pool by pairs *and* report each seed's own count — which is what I did, but with
the imbalance visible.

**The wrapper question is worth settling once.** The job's premise (options not advertised, so use a
wrapper) depends on a compile flag, and the wrapper cannot be verified through fastchess's own log
because it bypasses it. A build that advertises its tunables makes every future option-delivery check a
one-line grep of `uci` output instead of a wrapper plus an inference from bench counts. I would ask that
this tree's CMakeLists define `FORGE_EXPOSE_TUNABLES` for match builds, or that the job say explicitly
that it is expected to be absent.

## 13. Questions for Fable

1. Do you want a second seed of B1 (`EvalSwingMult 12`, `EvalSwingMax 200`) at 2,000 games? It is the only
   positive here and it deserves one clean repeat before the PC sees it.
2. Do you want `EvalSwingMult 24`/`Max 400` (B3) at all, given 12 beats 48? If the other helper has the 24
   cell at 200, the 24-at-400 cell is the one nobody has.
3. Should match builds define `FORGE_EXPOSE_TUNABLES`? It would make option delivery provable by grep.
