# REPORT — deepseek6, long 34 (extreme values under ASan + UBSan)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long34/`
Model: DeepSeek V4.1 Flash 1017

## 1. What was asked, the answer, how sure

**Asked:** every spin option of the plain build at its minimum, then its maximum (one at a time, the rest S14),
`go depth 8` on the first 20 positions of O, under ASan+UBSan; per option the sanitizer lines, crash or not, and
whether every bestmove is legal; one planted fault must be reported.

**Answer:** **58 spin options × 2 ends = 116 runs, all clean.** 0 AddressSanitizer lines, 0 UBSan runtime errors,
0 crashes, 0 refusals, **0 illegal and 0 missing bestmoves over 2,320 searches**. The planted heap overflow is
reported (`heap-buffer-overflow`, `search.cpp:2144`, exit 1). The only failures in the whole item were **my own**
— the first sweep ran against the wrong option list (section 5, F1) and I caught it with the harness's own
`REFUSED` stop rather than publishing 6 zero-node rows.

**What the extremes actually cost is not what I guessed.** The expensive ends are the LMR constants and MultiPV:
`MultiPV 8` = 5.42×, `LmrQuietDivisor 500` = 1.53×, `LmrQuietBase 0` = 1.49×; the cheapest big win is
`RfpMargin 10` = 0.375× (a 62 % smaller tree). The futility/SEE margins I predicted would be slow are nearly free
(`RazorBase 1000` = 1.001×, `FutilityBase 500` = 1.014×, `SeeQuietMultiplier 200` = 1.040×).

**How sure:** certain of the counts (116 committed run logs, a committed tsv, one command to re-derive the
table). The "which extremes cost" ranking is the measured node totals, not an interpretation.

## 2. Honesty numbers (raw in `raw/`)

Build: `-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1`, plain 6b98f217, sha256
`41e592fa72246fb9fc1524ca8955c14c24f06e83ed95e61d4de6cfc93d9235b1`.

| pin | required | measured | file |
|---|---|---|---|
| bench 11 | 312866 | **312866** | `raw/bench11.txt` |
| bench 13 | 862329 | **862329** | `raw/bench13.txt` |
| bench 16 | 3024920 | **3024920** | `raw/bench16.txt` |
| go perft 5 | 4865609 | **4865609** | `raw/perft5.txt` |

All four exact **on the sanitizer build**, with 0 sanitizer lines during the pins themselves.

Baseline for every ratio: the plain S14 engine at `go depth 8` over the first 20 of O = **118,961 nodes**,
measured two independent ways (the mode of the 116 runs, 51 of 116, and a fresh S14 run of the sanitizer build).

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claim, then prediction | done | `CLAIM.txt`, `PREDICTION.md` | prediction before the first run |
| sanitizer build + four pins | done | `raw/*` | exact, 0 sanitizer lines |
| spin option list from the build's own uci | done | `p/spin_opts_plain.tsv`, `raw/plain_uci.txt` | **58** spin options |
| sweep 116 runs | done | `logs/*.log` (116), `sweep_sweep.tsv` | 0 san, 0 crash, 0 illegal |
| bestmove legality, python-chess 1.11.2 | done | `sweep34.py` (per position) | 0 illegal, 0 missing |
| planted fault | done | `plant_evidence.txt` | heap-buffer-overflow, exit 1 |
| ratio table + inert list | done | `analyze34.py`, `analyze_out.txt` | section 4 |
| prediction scorecard | done | `scorecard.txt` | 4 held, 1 partly, 1 killed |

## 4. The table (from `analyze_out.txt`, one command: `python3 analyze34.py sweep`)

Baseline 118,961. Full 58-row table in `analyze_out.txt`; the extremes that matter:

| option | min | min ratio | max | max ratio |
|---|---|---|---|---|
| MultiPV | 1 | 1.0000 | 8 | **5.4172** |
| LmrQuietDivisor | 100 | **0.6359** | 500 | **1.5262** |
| LmrQuietBase | 0 | **1.4902** | 300 | **0.5649** |
| RfpMargin | 10 | **0.3752** | 300 | 1.3426 |
| RfpImproving | 0 | 1.1633 | 200 | **0.5524** |
| RfpDepth | 0 | 1.3805 | 15 | 1.0000 |
| SingularMargin | 0 | 1.3551 | 10 | 0.8814 |
| SingularDepth | 2 | 1.2968 | 20 | 0.9077 |
| LmrCutoffThreshold | 0 | 1.2730 | 20 | 1.2312 |
| LmpBase | 0 | 0.8125 | 20 | 1.1514 |
| LmrHistoryDivisor | 1000 | 1.1781 | 30000 | 1.0079 |
| QsSeeMargin | 0 | 1.0000 | 500 | **1.1780** |
| IirDepth | 1 | 1.1292 | 20 | 1.0780 |
| HistoryPruneMultiplier | 0 | 0.9102 | 20000 | 1.0000 |
| HistoryBonusMax | 100 | 0.9207 | 10000 | 1.0000 |
| QsFutilityMargin | 0 | 0.8917 | 1000 | 1.0665 |
| RazorBase | 0 | 0.9995 | 1000 | 1.0010 |
| FutilityBase | 0 | 0.9811 | 500 | 1.0135 |
| SeeQuietMultiplier | 0 | 1.0200 | 200 | 1.0402 |

**20 of 58 options are identity at BOTH ends** (their extremes change nothing): Book Depth, Book Variety,
CaptureFutilityBase, CaptureFutilityDepth, CaptureFutilityMultiplier, DrawJitter, Hash, Move Overhead,
NullMoveEvalDivisor, Threads, and all ten `Tm*` time-management options.

## 5. Findings, each with the command that shows it again

**F1. My first sweep tested three options the plain build does not have, and the harness caught it.**
I parsed `spin_opts.tsv` from `/tmp/ds6/long32/raw/ba_uci.txt`, which is the **SoundArms** build, so it listed
`SoundPvArm`, `SoundInCheckArm`, `SoundMateAlphaArm`. On the plain build those six runs came back `REFUSED`
(0 nodes, 0.2 s) — the harness's own `unknown option` stop, exactly as required. I rebuilt the list from the
plain build's `uci` (`raw/plain_uci.txt`, 58 spin options, 0 `Sound*`) and re-ran the whole sweep; the wrong run
is kept in `logs_wrongopts/` as the evidence. Nothing from it is in any table.

**F2. Zero sanitizer lines over every extreme of every option.** 116 run logs, one per (option, end), each holding
20 searches; `grep -l 'ERROR: AddressSanitizer\|runtime error' logs/*.log` returns nothing. Reproduce:
`grep -c 'AddressSanitizer\|runtime error' logs/*.log | grep -v ':0' | wc -l` → `0`.

**F3. The plant is reported, so the sanitizer is live.** `plant_evidence.txt`: `heap-buffer-overflow` writing past
a 4-int heap array at `search.cpp:2144`, exit code 1, in a **copy** of the tree (`l34_plant`, never committed as
source, and the tree is rebuilt outside the repository). Without this, "0 lines" would be indistinguishable from
"the sanitizer never ran".

**F4. The LMR constants are the violent knobs and they are violent in both directions.** `LmrQuietDivisor` spans
0.636× (100) to 1.526× (500) of the baseline; `LmrQuietBase` spans 1.490× (0) to 0.565× (300). These two are the
only options whose two extremes straddle the baseline by more than 40 % in *both* directions — exactly the shape
of a knob a tuner will overstep.

**F5. `RfpMargin 10` is the cheapest tree in the whole sweep: 0.375×, 44,640 nodes against 118,961.**
That is a 62 % reduction and it is the minimum of a margin the tuner does move (`c` = 6 per long 28). Worth a
match before anything else in this list; it is not a strength result, only a tree result.

**F6. `QsSeeMargin`'s default is not a plateau.** Long 1 found `QsSeeMargin` inert under S14 at depth 12; here its
**max (500) costs 17.8 %** while its min (0) is an exact identity. So "inert" was a statement about one value, and
the option has a live direction. That is the one line of my P5 that is wrong and the most transferable.

**F7. `MultiPV 8` costs 5.4× — the largest ratio in the sweep.** Expected (eight lines per iteration), but worth
recording beside the others because a test harness that leaves MultiPV at anything but 1 inflates every node
count it reports.

**F8. All ten `Tm*` options are identity at depth 8.** They only act under a clock, and `go depth` has none — so
this item cannot test them, and a future extreme-value item that wants them must use `go movetime`.

## 6. What I read from my colleagues

Nothing new this item; the colleague read is on the four-hour clock and this item ran about 30 minutes. No advice
from a note was used as an instruction. The one input I did take from a colleague's folder was my own
long-32 `ba_uci.txt` — and F1 is what came of trusting it without checking which build it came from.

## 7. What I did NOT do

- **Did not run G** (the item says the first 20 of O).
- **Did not test the ten `Tm*` options meaningfully** — they are identity under `go depth` (F8); testing them needs
  a clock and is a different item.
- **Did not test string or button options** (`Book File`, `NnueFile`, `Clear Hash`) — the item says spin options.
- **Did not commit the planted source.** The plant lives in `/tmp/ds6/l34_plant`, a copy outside the repository;
  only its raw ASan output is committed.
- **Did not report the six `REFUSED` rows as results** (F1) — they are a harness artifact and are labelled so.
- No pull request, no branch but mine.

## 8. What I am NOT sure about

- Whether a clean sanitizer run at these extremes generalises to **Threads > 1**: every run forced Threads 1, so
  a data race could not appear here. (My long 22 territory, not this item's.)
- Whether `RfpMargin 10`'s 62 % smaller tree is *sound* — this item measures nodes, not strength; a smaller tree
  can be a worse search.
- Whether the extremes I clamped to (the `uci` min/max) are the extremes the engine can actually receive: a value
  outside the range is refused by the engine, which the harness would have caught as `REFUSED`, and none occurred
  except the F1 artifact.

## 9. A better way

Parse the option list **from the same binary you are about to sweep**, not from a file in another item's folder.
F1 cost one full sweep (about 5 minutes) and would have been invisible without the `REFUSED` stop in the harness —
which is the second time this week that stop has saved a report (my long 32 build also depended on it).

## 10. Times and the folder

times: see `stamps.txt`.
Model name my runtime gives: **DeepSeek V4.1 Flash 1017**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
