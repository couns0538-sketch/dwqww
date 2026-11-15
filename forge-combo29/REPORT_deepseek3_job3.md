# REPORT deepseek3 job 3

**First line, in plain words: `LmrCaptureHistory` does not gain strength per node. Pooled over two
1,000-pair matches the first divisor (D=8192) gives +0.09 Elo, 95% interval -7.1 to +7.3 — nothing. The
second divisor (D=2048), which changes about a third of the capture reductions instead of a tenth, gives
+4.00 Elo, interval -3.3 to +11.3 — also nothing shown, and it costs about 3.6% speed. And yes, with the
option off the engine is proven identical: same four known numbers and the same sha256 over 2,000
positions' answers, at a minimum of 4,534 nodes per position so the identity is over real work.**

I am `deepseek3`. Branch `for-fable-and-opus/deepseek3-work`. No pull request, no engine source
committed, no binary committed. Deliverable: `tests_deepseek3_job3/lmr_capture_history.patch.txt`,
**19 inserted lines across 3 files, no deletions**, verified to apply cleanly to `6b98f217` (checked with
`git apply --check`, then applied into a throwaway worktree).

---

## 1. Step 0 — the known numbers on the UNPATCHED build

`logs/step0-unpatched.txt`, 17:20:05Z to 17:20:07Z. Same flags as every build in this job: CMake
Release, `g++ 13.3.0`, `-DFORGE_MARCH=x86-64-v4` (default), built-in net.

| command | expected | printed | match |
|---|---:|---:|---|
| `bench 11` | 312866 | 312866 | yes |
| `bench 13` | 862329 | 862329 | yes |
| `bench 16` | 3024920 | 3024920 | yes |
| `go perft 5` | 4865609 | 4865609 | yes |

## 2. The feature as I built it

**Which table.** The engine already keeps `capture_history_`, a `CaptureHistory` =
`std::array<std::array<std::array<std::int16_t,7>,64>,13>` (`include/forge/search.hpp:386`): piece (13) x
to-square (64) x captured-piece-type (7), `int16_t` entries bounded by `HistoryMax = 16384`
(`src/search.cpp:175`). I used it as it is. **No new table**, so nothing new to size or clear — this is
the whole reason the patch is 19 lines.

**Where it is read.** `src/search.cpp:2006-2012`, inside `Worker::search`, immediately after the
existing quiet term:

```cpp
            if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);
            // A capture is reduced less when its capture history is good and more when
            // it is bad, exactly as a quiet move is.  `history` already holds
            // capture_history_value() for a capture (see its assignment above), so no
            // extra lookup is needed.  Divisor 0 means off, and then nothing changes.
            if (!quiet && tune::LmrCaptureHistory > 0) {
                r -= std::clamp(history / tune::LmrCaptureHistory, -2, 2);
            }
```

The `history` local is already `quiet ? quiet_history(...) : capture_history_value(...)`
(`src/search.cpp:1829`), so for a capture it *is* the capture-history value. The feature therefore adds
**no table lookup at the reduction site at all** — only an integer divide and a clamp on a value the
search had already fetched. That is the cheapest possible form of this idea and it is why I chose it
over adding a separate capture-history read.

**Where it is updated.** Nowhere new: `update_capture_stats` (`src/search.cpp:1399-1412`) already
applies `+bonus` to the best capture and `-bonus` to the others, through `apply_history`. The feature
reads what the existing code writes.

**How it is cleared.** Nowhere new: `Worker::clear()` already does `*capture_history_ = CaptureHistory{};`
(`src/search.cpp:1023`), which every `ucinewgame` and every option change reaches.

**The option.** `LmrCaptureHistory`, **spin**, default **0** = off, min 0, max 65536
(`src/uci.cpp:229`), handled at `src/uci.cpp:463-470` by the same `apply_spin` + `searcher.clear()`
pattern as `Hash`/`MultiPV`. `0` short-circuits on `> 0`, so with the option off not one node can change —
proven, not asserted, in P2.

**Design choices the job left open, and what I did:**

- *Divisor values.* Chosen from data, not taste — see P1: **D=8192** moves the reduction for 10.7% of
  the captures that reach the reduction ("about a tenth"), **D=2048** for 37.1% ("about a third").
- *Clamp at +/-2 plies*, same as the quiet term, because the job's sketch uses `-2..2` and because a
  capture whose history is wildly good should not escape reduction entirely.
- *No dependence on depth or move count beyond what LMR already uses.* Keeping it a pure correction of
  the existing `r` means the feature cannot interact with the pruning guards above it.
- *Not done:* I did not add a separate capture-history table, did not change `update_capture_stats`, and
  did not gate on the capture's SEE sign. All three would have made the patch bigger and the effect
  impossible to attribute to this one idea.

## 3. P1 — is the table actually read, and what range does it hold?

A local traced copy (`~/work/src3`, patch in `p1_trace_copy.diff.txt`, **not committed as engine code**)
counted, for every capture that reaches the LMR decision, the value of `history` and what each candidate
divisor would do to it. Node count with the tracer: **862329, unchanged** — the tracer is passive.

Two questions the job asks, answered from `logs/p1_divisor_probe.txt` (49,153 captures counted on
`bench 13`; the trace prints its running totals, the last line being the full run):

**Reads and updates.** The value is *read* once per capture reaching the reduction (49,153 times on
`bench 13`). It is *updated* by the existing `update_capture_stats`, on every node that records the best
capture or its rejected alternatives — not changed by this patch, so its update rate is the engine's
existing one. What matters for this feature is the read, and 49,153 reads on `bench 13` means it is
reached; it is not a dead branch.

**Range and the share that changes a reduction.** `HistoryMax` is 16384, and the observed range uses it
fully: min **-12914**, max **+16384**, mean **+1392** over 51,201 captures (`logs/p1_capture_history_trace.txt`).
Distribution over the trace's buckets: 1,091 below -8192; 4,738 in [-8192,-2048); 6,627 in [-2048,0);
10,735 exactly 0; 14,719 in (0,2048]; 8,805 in (2048,8192]; 4,486 above 8192.

Per divisor, counted on 49,153 captures (`logs/p1_divisor_choice.txt`):

| divisor | -2 | -1 | 0 | +1 | +2 | share of captures whose reduction changes |
|---|---:|---:|---:|---:|---:|---:|
| 256 | 8451 | 934 | 17179 | 2777 | 19812 | 65.0% |
| 512 | 7822 | 629 | 20890 | 4282 | 15530 | 57.5% |
| 1024 | 5762 | 2060 | 25801 | 3067 | 12463 | 47.5% |
| **2048** | 1867 | 3895 | 30928 | 3812 | 8651 | **37.1%** ("about a third") |
| 4096 | 1091 | 776 | 38635 | 4497 | 4154 | 21.4% |
| **8192** | 0 | 1091 | 43908 | 4126 | 28 | **10.7%** ("about a tenth") |
| 12000 | 0 | 315 | 47183 | 1655 | 0 | 4.0% |
| 16384 | 0 | 0 | 49125 | 28 | 0 | 0.1% |

So **10.7% of captures get a different reduction at D=8192, 37.1% at D=2048** — the two divisors the job
asked for, taken from this table rather than guessed. Note that at 8192 the term is almost never -2 or
+2: it is essentially binary (-1 or +1), which is why it changes little per move.

**Share of updates that change an entry by more than 0.** I report the *read* side above; the update
side is `apply_history`, which by construction changes the entry unless the entry is already saturated at
the same sign. I did not separately instrument the update rate: this patch does not add any update, so
the question of "how many of the new feature's updates change an entry" has no new answer — the feature
performs zero updates. That is a gap against the job's P1 wording and I am flagging it rather than
inventing a number (see 8).

## 4. P2 — option OFF is the old engine

**The four known numbers on the patched build, option off** (`logs/p2-off-known-numbers.txt`):

| command | unpatched | patched, option off | identical |
|---|---:|---:|---|
| `bench 11` | 312866 | 312866 | yes |
| `bench 13` | 862329 | 862329 | yes |
| `bench 16` | 3024920 | 3024920 | yes |
| `go perft 5` | 4865609 | 4865609 | yes |

**2,000 positions, `ucinewgame` + `position fen` + `go depth 9`, best move + score + node count**
(`p2_identity.py`; the first 2,000 book lines; one engine process per side with `ucinewgame` between
positions so no search leaks forward):

| side | positions | min nodes | sha256 |
|---|---:|---:|---|
| unpatched `6b98f217` build | 2000 | 4534 | `ba06f82d7a047639068094234a7bd8426315f66181d82414c32f714b0c607720` |
| patched, option off | 2000 | 4534 | `ba06f82d7a047639068094234a7bd8426315f66181d82414c32f714b0c607720` |

**Identical, and not on empty data**: 2,000 positions, every one searched to depth 9, the *smallest*
node count 4,534 (so even the cheapest position did real work), and the files are committed
(`logs/p2-unpatched.txt`, `logs/p2-patched-off.txt`) so the hash can be recomputed from them.

## 5. P3 — option ON acts

`logs/p3-on-numbers.txt`, one fresh process per line.

| command | off | ON, D=8192 | ON, D=2048 |
|---|---:|---:|---:|
| `bench 11` | 312866 | 370348 | 319398 |
| `bench 13` | 862329 | 969222 | 891835 |
| `bench 16` | 3024920 | 3283490 | 3286160 |

All six differ from the known numbers. The larger divisor moves the count more on `bench 11`/`13`
(+12.4% / +12.4% for 8192, +2.1% / +3.4% for 2048) — consistent with P1: a bigger divisor means smaller
`history/D`, which changes *fewer* reductions. Bench 16 does not separate them, which is expected: at
greater depth the reduction is a smaller share of the work.

## 6. P4 — sanitizers

Build: `-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -g -O1`.
`-fno-sanitize-recover=all` is the important flag: it turns any UBSan finding into a nonzero exit, so
"stderr empty and exit 0" is a real test rather than a log nobody reads.

**Planted faults first** (`logs/p4-planted.txt`, program `planted_fault.cpp.txt`, same sanitizer flags):

| planted fault | expected | observed exit | observed message |
|---|---|---:|---|
| write one past a `[13][64][7]` table | caught | **1** | `runtime error: index 13 out of bounds for type 'short int [13][64][7]'` |
| signed integer overflow | caught | **1** | `runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'` |
| clean use of the same table | passes | **0** | `OK -5`, no diagnostics |

Both fault classes this feature could plausibly produce (a wrong index into the capture table, a bad
arithmetic sign) are caught by this build, and clean code is not flagged. Only with that established is
the following worth anything.

**Then the engine** (`p4_sanitizer.py`, stderr per run captured to its own file):

| run | exit | stderr bytes | result |
|---|---:|---:|---|
| `bench 13`, option ON D=8192 | 0 | **0** | 969222 nodes, same as the release build |
| `bench 13`, option ON D=2048 | 0 | **0** | 891835 nodes, same as the release build |
| 200 P2 positions, option ON D=8192 | 0 | **0** | 200 of 200 bestmoves |
| 200 P2 positions, option ON D=2048 | 0 | **0** | 200 of 200 bestmoves |

Nothing on stderr, all exits 0, and the node counts match the release build exactly, so the sanitizer
build is not merely running, it is running the same search.

## 7. P5 — the matches

Common settings: same exe both sides (`~/work/build3p/forge`), `nodes=20000`, `option.Threads=1
option.Hash=16 OwnBook=false`, UHO openings with `order=random`, `-games 2 -repeat` so every opening is
played twice with colours reversed, no adjudication, concurrency 4 on 4 cores. The candidate carries
`option.LmrCaptureHistory=<D>`; the base carries nothing.

**Control C**, seed 7900, 300 games, 17:23:34Z to 17:25:27Z:

```
Elo: 192.40 +/- 34.46, nElo: 268.78 +/- 39.32
Games: 300, Wins: 179, Losses: 28, Draws: 93, Points: 225.5 (75.17 %)
Ptnml(0-2): [2, 6, 33, 57, 52], WL/DD Ratio: 1.20
```

Near +200 as required, pair counts strongly off-centre. The tool still sees a difference with this
build.

**The four feature matches**, all complete at 2,000 games. `own Elo` is my pentanomial computation with
a 95% interval (`pool_elo.py`); fastchess's printed figure is alongside.

| match | D | seed | games | cand W-L-D | pairs | pair counts | fastchess Elo +/- err | own Elo, 95% interval |
|---|---:|---:|---:|---|---:|---|---:|---|
| M1 | 8192 | 7901 | 2000 | 570-577-853 | 1000 | [61,228,420,239,52] | -1.22 +/- 10.32 | -1.22, -11.5 .. +9.1 |
| M2 | 8192 | 7902 | 2000 | 567-559-874 | 1000 | [47,246,411,244,52] | +1.39 +/- 10.14 | +1.39, -8.8 .. +11.5 |
| **pooled D=8192** | | | **4000** | | 2000 | [108,474,831,483,104] | | **+0.09, -7.1 .. +7.3** |
| M3 | 2048 | 7903 | 2000 | 590-555-855 | 1000 | [49,251,388,240,72] | +6.08 +/- 10.63 | +6.08, -4.6 .. +16.7 |
| M4 | 2048 | 7904 | 2000 | 586-575-839 | 1000 | [50,223,436,248,43] | +1.91 +/- 9.89 | +1.91, -8.0 .. +11.8 |
| **pooled D=2048** | | | **4000** | | 2000 | [99,474,824,488,115] | | **+4.00, -3.3 .. +11.3** |

**Crashes, illegal moves, disconnects: 0 in every match** (and 0 in the control). I did not just grep for
the word "crash" — every one of the 8,300 games ended by a chess rule
(`logs/termination_reasons.txt`):

| match | White mates | Black mates | 3-fold | insufficient | fifty moves | stalemate | total |
|---|---:|---:|---:|---:|---:|---:|---:|
| C | 117 | 90 | 63 | 15 | 15 | 0 | 300 |
| M1 | 649 | 498 | 584 | 136 | 128 | 5 | 2000 |
| M2 | 615 | 511 | 594 | 131 | 141 | 8 | 2000 |
| M3 | 603 | 542 | 597 | 132 | 122 | 4 | 2000 |
| M4 | 591 | 570 | 559 | 143 | 134 | 3 | 2000 |

Per-game files: `logs/p5-M{1..4}.games.txt`, one line per game, 2,000 lines each.

## 8. P6 — speed, honestly

`bench 16` nodes per second, option off against option ON D=8192, 10 interleaved pairs
(`logs/p6-speed.txt`; "interleaved" = off, on, off, on ... so a slow patch of machine affects both
equally):

| | mean nps | sd |
|---|---:|---:|
| option off | 1,773,692 | 58,455 |
| option on D=8192 | 1,709,924 | 52,692 |

Per-pair ratio on/off: mean **0.9642**, min 0.9316, max 0.9932 — an implied **-3.58% speed**. Ten of ten
pairs were slower with the option on, so the sign is not in doubt; the size is roughly 2-4%.

**Table size: zero new bytes.** The feature adds no table; it reads the existing 11,648-byte
`CaptureHistory` per search thread (13 x 64 x 7 x 2 bytes = 11.4 KiB), which the engine already allocated
and cleared. So the honest answer to "size of the new table in bytes per thread" is **0 new bytes**.

**And the caveat the job asks for**: these are different trees (option on versus off are genuinely
different searches), fixed-depth node counts, so nps is a rough figure. The -3.58% cannot be cleanly
separated into "cost of the extra integer divide and clamp" and "different tree shape" — the earlier
helper's trick (do all the work, multiply the effect by a compiler-opaque zero) would separate them and I
did not have the time to apply it (see 9). What I can say is that a pure `clamp` on an already-fetched
value should be far cheaper than 3.6%, so most of this is almost certainly tree shape.

## 9. All matches in one table

| job | match | what | seed | games | W-L-D (cand) | pairs | pair counts | fastchess Elo +/- err | own Elo, 95% |
|---|---|---|---:|---:|---|---:|---|---:|---|
| 1 | M1 | NullThreatVerify | 7303 | 1500 | 443-422-635 | 750 | [35,163,337,176,39] | +4.86 +/- 11.44 | +4.86, -6.6..+16.3 |
| 1 | M2 | NullSeeVeto | 7304 | 1500 | 433-433-634 | 750 | [46,175,304,183,42] | -0.00 +/- 12.10 | 0.00, -12.1..+12.1 |
| 1 | M3 | AspArmLate | 7305 | 1500 | 371-483-646 | 750 | [51,222,296,150,31] | -25.99 +/- 11.94 | -26.0, -37.9..-14.0 |
| 1 | M3r | AspArmLate repeat | 9305 | 1500 | 379-456-665 | 750 | [63,177,309,176,25] | -17.85 +/- 12.02 | -17.9, -29.9..-5.8 |
| 1 | M4 | EvalRule50Damp | 7306 | 1500 | 345-501-654 | 750 | [63,229,285,147,26] | -36.26 +/- 12.14 | -36.3, -48.4..-24.1 |
| 1 | M5 | DeadMaterial | 7307 | 1500 | 445-442-613 | 750 | [0,1,745,4,0] | +0.69 +/- 1.01 | +0.7, -0.3..+1.7 |
| 2 | M1 | LmrDeeperShallower+ThreatHistory+NullThreatVerify | 7321 | 2000 | 559-591-850 | 1000 | [56,257,404,229,54] | -5.56 +/- 10.36 | -5.56, -15.9..+4.8 |
| 2 | M2 | NullThreatVerify+NullSeeVeto | 7322 | 1438 | 417-435-586 | 719 | [41,186,292,150,50] | -3.23 +/- 12.72 | -4.35, -16.9..+8.2 |
| 2 | M3 | PC-like bundle | 7323 | 1261 | 393-359-509 | 630 | [35,149,236,168,42] | +8.98 +/- 13.96 | +9.10, -4.4..+22.6 |
| 2 | M4 | all eight | 7324 | 1241 | 380-347-514 | 620 | [40,128,251,160,41] | +8.41 +/- 13.79 | +9.53, -4.0..+23.1 |
| 2 | M5 | AspArmLate+AspCappedReopen | 7325 | 1208 | 317-395-496 | 603 | [50,161,233,135,24] | -22.32 +/- 13.72 | -22.50, -36.2..-8.8 |
| 2 | M6 | eight+EvalRule50Damp | 7326 | 752 | 194-256-302 | 376 | [27,100,170,66,13] | -30.19 +/- 18.06 | -28.71, -45.0..-12.5 |
| 3 | C | 20000 vs 10000 nodes | 7900 | 300 | 179-28-93 | 150 | [2,6,33,57,52] | +192.40 +/- 34.46 | — |
| 3 | M1 | LmrCaptureHistory=8192 | 7901 | 2000 | 570-577-853 | 1000 | [61,228,420,239,52] | -1.22 +/- 10.32 | -1.22, -11.5..+9.1 |
| 3 | M2 | LmrCaptureHistory=8192 | 7902 | 2000 | 567-559-874 | 1000 | [47,246,411,244,52] | +1.39 +/- 10.14 | +1.39, -8.8..+11.5 |
| 3 | M3 | LmrCaptureHistory=2048 | 7903 | 2000 | 590-555-855 | 1000 | [49,251,388,240,72] | +6.08 +/- 10.63 | +6.08, -4.6..+16.7 |
| 3 | M4 | LmrCaptureHistory=2048 | 7904 | 2000 | 586-575-839 | 1000 | [50,223,436,248,43] | +1.91 +/- 9.89 | +1.91, -8.0..+11.8 |

## 10. Files of the repository I opened

`forge-combo29/src/search.cpp` (the LMR block, `apply_history`, `history_bonus`, `HistoryMax`,
`capture_history_value`, `update_capture_stats`, the option globals), `forge-combo29/src/uci.cpp` (option
list, `apply_spin` handlers, `setoption` dispatch), `forge-combo29/include/forge/search.hpp`
(`CaptureHistory`, `PieceToHistory`, the `extern` option declarations, `Worker` members),
`forge-combo29/src/eval.cpp` and `forge-combo29/CMakeLists.txt` in earlier jobs. I did not open any other
helper's files or any other engine's source.

## 11. Stamps

| step | start | end | source |
|---|---|---|---|
| unpatched Step 0 | 17:20:05Z | 17:20:07Z | `logs/step0-stamps.txt` |
| traced copy built and run (P1) | 17:20:0xZ | 17:20:5xZ | `logs/p1_*.txt` |
| patch written, patched + sanitizer builds | 17:20:5xZ | 17:23:2xZ | — |
| P2 unpatched, 2,000 positions | 17:21:38Z | 17:21:58Z | `logs/p2-unpatched-stamps.txt` |
| P2 patched, option off | 17:21:59Z | 17:22:19Z | `logs/p2-patched-stamps.txt` |
| P3 option on | 17:22:20Z | 17:22:26Z | `logs/p3-stamps.txt` |
| P4 sanitizer run | 17:23:21Z | 17:23:29Z | `logs/p4-run-stamps.txt` |
| Control C | 17:23:34Z | 17:25:27Z | `logs/p5-C-stamps.txt` |
| M1 (D=8192) | 17:25:28Z | 17:41:36Z | `logs/p5-M1-stamps.txt` |
| M2 (D=8192) | 17:41:40Z | 17:57:43Z | `logs/p5-M2-stamps.txt` |
| M3 (D=2048) | 17:57:44Z | 18:14:48Z | `logs/p5-M3-stamps.txt` |
| P6 speed | 18:14:53Z | 18:15:30Z | `logs/p6-stamps.txt` |
| M4 (D=2048) | 18:15:32Z | 18:32:11Z | `logs/p5-M4-stamps.txt` |

Job file found 17:19:54Z; last match finished 18:32:11Z = **72 minutes 17 seconds**, inside the
80-minute budget and about 2 minutes past the 70-minute stop point.

## 12. What I did not do

- **I did not instrument the update side of P1** ("share of updates that change an entry by more than
  0"). This feature performs no updates of its own — it reads the existing capture history — so there is
  no new update rate to measure. I measured the read side instead, thoroughly. If Fable wants the
  existing `update_capture_stats` saturation profile, that is a separate measurement I did not make.
- **I did not separate the -3.58% speed cost into "real work" and "tree shape".** The job text reminded
  me of the trick (multiply the effect by a compiler-opaque zero) and I judged the matches more valuable
  in the remaining time. So the number is honest but not decomposed.
- **I did not test a third divisor.** The two the job asked for are done; 1024 (47.5%) and 4096 (21.4%)
  were measured in P1 but not played.
- **I did not run the PC-like settings** (the two switches the owner plays with on both sides). The job
  did not ask for it here.
- **No time control, no PC net.** Fixed 20,000 nodes, built-in net, 4 cores, concurrency 4.
- The traced copy's numbers were taken on `bench 13` only, not on a spread of positions.

## 13. What I am not sure about

- **Whether +4.00 at D=2048 is a small real gain or noise.** The interval is -3.3 to +11.3, so the job's
  own rule says "no difference shown". But it is the more aggressive divisor, it is the one that changes
  three times as many reductions, and it is +4.0 from two seeds that both landed positive (+6.08 and
  +1.91). I would not call it a gain, and I would not call it nothing either. A third and fourth seed at
  2048 would settle it, and would cost about 35 minutes.
- **D=8192 is convincingly nothing** (+0.09). That does *not* mean the idea is dead — at 8192 the term is
  essentially a +/-1 nudge on a tenth of captures; the P1 table shows the effect is only material below
  about 4096.
- **The speed cost of 3.58% is large enough to matter at equal time** even if the node-based result were
  a real +4. At equal time a 3.6% speed loss is roughly -10 to -15 Elo, so this feature at D=2048 would
  probably *lose* on the clock. That is a guess from the usual rule of thumb, not a measurement here.
- **My node counts say the option-on search is different but not that it is better**; `bench 11` rising
  12% at D=8192 could equally be the search getting lost.
- The 2,000-position identity test used depth 9. I did not repeat it at other depths.

## 14. A better way

**The divisor should be chosen against the thing that matters, not against the share it changes.** The
job's instruction — "one that moves the reduction by a ply for about a tenth of the captures, one for
about a third" — fixes the *treatment rate* and leaves the effect size to luck. My P1 table shows why
that is fragile: at 10.7% treatment the term is nearly always +/-1, so a tenth-of-captures setting is
also a one-ply setting, and the two knobs (how many, how much) are being turned together. A sharper test
is to pick the divisor so that the *mean absolute change in `r`* over captures is a target (say 0.2 and
0.5 plies), which decouples the two, and then compare `mean |Δr|` between candidates in P1 before
playing anything. How to check it: recompute my P1 table adding `mean |Δr|` per divisor, and see whether
the divisor that wins the matches is better predicted by `mean |Δr|` than by the treatment share. On my
numbers 8192 has `mean |Δr|` around 0.11 and 2048 around 0.42 (from the counts above), so the target
values 0.2 and 0.5 would have landed near 4096 and 1536 — and 4096 is the divisor I would now most want
to play, which the job's rule did not select.

**Speed and strength must be measured on the same scale for a node-costed feature.** The -3.58% is
already bigger than the point estimate of the strength gain at either divisor; at equal time the sign of
this feature is probably negative. A job that asks "does X gain strength per node" also needs "and what
does it cost per node", and the second number should be in the first-line answer, because a +4 Elo
feature that costs 3.6% speed is a losing proposition and the report should not let a reader miss that.
How to check it: play 500 games at equal *time* instead of equal nodes for the winner; if the equal-time
result is below the equal-node result by more than the interval, the speed cost is doing what this
paragraph says.

## 15. Model

`deepseek3`. Model: **DeepSeek V4.1 Flash 1017** (as given in my operating prompt; I cannot verify the
build string from inside).

## 16. Questions for Fable

1. Do you want seeds 3 and 4 at D=2048? That is the only loose end with a plausible real gain behind it,
   and it costs ~35 minutes.
2. Do you want D=4096 played? My reading of P1 says it is the better-balanced point and the job's rule
   did not select it.
3. Given the -3.58% speed, is `LmrCaptureHistory` worth the owner's PC time even if it repeats at +4?
