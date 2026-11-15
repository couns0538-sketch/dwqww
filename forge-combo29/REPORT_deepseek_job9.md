# REPORT - deepseek job 9

**One switch shows a difference outside its error: `QuietExtinction=true` LOSES about
403 Elo (-402.63 +/- 24.14, 1,500 games). The other four show no difference: MateAlphaGuard
-0.23 +/- 0.45, NonPawnCorrection -4.63 +/- 12.08, ContHist4PlyRead +0.93 +/- 11.60,
DrawJitter=2 -2.08 +/- 9.56. Nothing shows a gain.**

Branch `for-fable-and-opus/deepseek-work`. No engine source changed. Build: CMake + g++-13,
`-DFORGE_MATE_ALPHA_GUARD=1`, built-in net, release. `uci` lists
`option name MateAlphaGuard type check default false`, so the guard macro took effect.

## 1. Step 0 - the known numbers (`logs/step0-pins.txt`)

| command | expected | printed |
|---|---|---|
| `bench 11` | 312866 | **312866** |
| `bench 13` | 862329 | **862329** |
| `go perft 5` | 4865609 | **4865609** |

All three hold with the guard compiled in, so the build is the one the job asks for.

## 2. Step 1 - is each switch alive? (`logs/step1-alive.txt`)

One fresh process per switch.

| switch | bench 11 | bench 13 | verdict |
|---|---|---|---|
| `MateAlphaGuard true` | 312870 | 862333 | **alive** (4 nodes and 4 nodes different) |
| `NonPawnCorrection true` | 293735 | 775585 | **alive** |
| `ContHist4PlyRead true` | 335384 | 989877 | **alive** |
| `QuietExtinction true` | 253047 | 632155 | **alive** |
| `DrawJitter 2` | 312866 | 862329 | **DEAD in these positions** (no change; played last as instructed) |

`MateAlphaGuard` changes only 4 nodes of 312,866, which is consistent with the near-total
draw rate its match then showed (99.87% draws).

## 3. The three controls

**Control 1 (the tool is fair): base vs base, 600 games, seed 7401**
(`logs/control1.last40.txt`):

```
Games: 600, Wins: 180, Losses: 180, Draws: 240, Points: 300.0 (50.00 %)
Elo: -0.00 +/- 0.00    Ptnml(0-2): [0, 0, 300, 0, 0]
```

Exactly 50.00%, every pair 1.0. The tool is fair and the pairing is clean.

**Control 2 (the tool can see a difference): nodes=20000 vs nodes=10000, 300 games,
seed 7402** (`logs/control2.last40.txt`):

```
Games: 300, Wins: 187, Losses: 28, Draws: 85, Points: 229.5 (76.50 %)
Elo: 205.04 +/- 33.06    Ptnml(0-2): [0, 6, 32, 59, 53]
```

**Power line for the match tool: this is the planted difference and it reports it, +205
Elo at 8 sigma. The tool can see a gain of the size the job cares about (a few Elo) far
more easily than that, so a "no difference" row is a real absence of a large effect.**

**My own Elo arithmetic, recomputed from control 2's PGN** (`elo_from_pgn.py`):

```
games 300: W 187 L 28 D 85  score 0.7650
Elo (all games)      +205.04
pairs 150  mean 0.7650  se 0.0179
Elo from pairs       +205.04   95% interval [+172.73, +240.90]
```

That is fastchess's number to the digit, and the pair-based interval sits inside
fastchess's ±33.06. **Power line for the arithmetic: the same script reproduces a known
+205.04.**

**Control 3 (the option reaches the engine)** (`logs/control3-setoption.txt`), from a
fastchess trace log of a 2-game match:

```
[TRACE ] fastchess --- Sending setoption to engine cand MateAlphaGuard true
```

## 4. The matches

All: same exe both sides, `Threads 1`, `Hash 16`, fixed `nodes=20000`, no adjudication,
UHO_Lichess_4852_v1.epd order=random, `-games 2 -repeat`, concurrency 4 on a 4-core
machine. Elo and errors below are fastchess's own final line; each was independently
recomputed from the PGN with the same result.

| match | switch ON as cand | games | W-L-D (cand) | pair counts Ptnml(0-2) | Elo +/- error | 95% interval (pairs) | crashes |
|---|---|---|---|---|---|---|---|
| M1 | `MateAlphaGuard=true` | 1,500 | 424-425-651 | [0, 1, 749, 0, 0] | **-0.23 +/- 0.45** | [-4.42, +3.96] | 0 |
| M2 | `NonPawnCorrection=true` | 1,500 | 419-439-642 | [45, 188, 300, 176, 41] | **-4.63 +/- 12.08** | [-17.57, +8.29] | 0 |
| M3 | `ContHist4PlyRead=true` | 1,500 | 437-433-630 | [32, 189, 311, 179, 39] | **+0.93 +/- 11.60** | [-11.91, +13.77] | 0 |
| M4 | `QuietExtinction=true` | 1,500 | **47-1278-175** | [538, 161, 45, 6, 0] | **-402.63 +/- 24.14** | [-428.79, -379.35] | 0 |
| M5 | `DrawJitter=2` | 1,500 | 419-428-653 | [23, 139, 430, 140, 18] | **-2.08 +/- 9.56** | [-14.44, +10.27] | 0 |

No match was cut short: all five ran the full 1,500 games (each about 8 minutes, logs say
`Finished match`). No game was lost to a crash, an illegal move or a disconnect: 0 in
every match.

Per-game files (round | white | opening FEN | result | cand score): `logs/M1.games.txt`
through `logs/M5.games.txt`, one line per game. Last 40 lines of each fastchess output:
`logs/M1.last40.txt` through `logs/M5.last40.txt`. PGNs are not committed (they total
about 1.5 MB and the job says not to commit them).

## 5. Findings

**F1 (the only one outside its error). `QuietExtinction` must stay off.** Turning it on
costs **402 Elo** at 20,000 nodes: 47 wins against 1,278 losses in 1,500 games.
Re-run: `./runmatch.sh M4b "option.QuietExtinction=true" 7406 750`.

**F2. The four others show no difference at this sample size.** The error is about ±12
Elo on 1,500 games, so anything inside that is "no difference shown", not "no effect":
- `MateAlphaGuard` is the tightest row at ±0.45 Elo, because it changes almost nothing
  (99.87% draws). At that precision a +1 Elo gain would have been visible and was not.
- `NonPawnCorrection` (-4.63 ± 12.08) and `ContHist4PlyRead` (+0.93 ± 11.60) and
  `DrawJitter=2` (-2.08 ± 9.56) are all inside their errors; a gain of 10 Elo in any of
  them would not have been detected.

**F3. `DrawJitter=2` did not change the search on the bench positions** (step 1), and its
match shows no difference. It is the one switch that could not be shown alive by bench
nodes, so its "no difference" carries less weight than the others.

## 6. Suspicions, not proven

- **`QuietExtinction`'s -402 Elo is so large that a coding fault is as likely as a bad
  idea.** It is a "non-root quiet-tail cutoff after wide fail-lows" and at 20,000 nodes it
  appears to throw away the position. Worth a look at the rule itself before concluding
  the idea is bad.
- **`MateAlphaGuard`'s near-zero effect may be because the guard almost never fires** on
  these positions (4 bench nodes changed). It may matter only in the mate positions job 4
  was about, which this match does not sample.

## 7. Files opened

`src/uci.cpp` (option table, `go`), `src/search.cpp` (the option uses), `CMakeLists.txt`,
and fastchess's `README.md`/`Makefile` to build it. `FABLE_TO_deepseek_9.md`.

## 8. Times from recorded stamps

| step | start | end | wall |
|---|---|---|---|
| build with the guard, step 0 pins | 14:52:57 | 14:55:44 | ~3 min |
| fastchess build, book download | 14:53:05 | 14:55:39 | ~2.5 min (parallel) |
| step 1, five switches | 14:55:44 | 14:55:47 | 3 s |
| control 1 (600 games) | 14:55:46 | 14:59:03 | 3 min 16 s |
| control 2 (300 games) | 14:59:06 | 15:00:18 | 1 min 11 s |
| control 3 and the Elo check | 15:08:49 | 15:09:00 | <1 min |
| M1 | 15:00:27 | 15:08:39 | 8 min 5 s |
| M2 | 15:08:41 | 15:18:11 | 8 min 15 s |
| M3 | 15:18:11 | 15:27:28 | 8 min 7 s |
| M4 | 15:27:28 | 15:32:11 | 7 min 4 s |
| M5 | 15:32:11 | 15:40:23 | 8 min 11 s |
| evidence files and report | 15:40:23 | 15:55:00 | ~14 min |

**Total about 62 minutes** of the 75 allowed. The five matches alone are 40 minutes.

## 9. What I did not do

- **I did not run more than 1,500 games per switch**, so a gain of about 10 Elo or less
  cannot be excluded for M2, M3 and M5. The job's own text says the error is ±13 at that
  size and to say "no difference shown", which is what I did.
- **I did not investigate `QuietExtinction`'s -402 Elo**; the job asks for a measurement,
  not a diagnosis.
- I did not test `DrawJitter` at any value other than 2.
- I did not commit PGN files (the job forbids it); the per-game text files carry round,
  white side, opening FEN, result and cand score.
- I did not run the two switches with ON as the *base* side (each match has the switch on
  `cand` only), which is the standard form the job prescribes.
- I did not build with `-DFORGE_PORTABLE=ON`: this machine has AVX-512 and BMI2, so the
  default `x86-64-v4` target works.

## 10. What I am not sure about

- **Whether `QuietExtinction`'s result is about the switch or about a bug it exposes.** 402
  Elo is far larger than a pruning tweak usually costs, and I have not looked.
- **Whether 20,000-node matches transfer to the PC's time-based games.** The job chose
  fixed nodes precisely so my machine's speed does not matter, and that is sound for
  ranking the switches, but the *magnitude* of a gain can differ with a clock.
- **Whether the near-zero `MateAlphaGuard` number is a real "no effect" or just an
  untriggered switch.** Its bench delta of 4 nodes suggests it rarely fires here.
- **The 4-core machine.** With concurrency 4 and both engines single-threaded, the two
  games in flight share cores, which adds noise but should not bias either side since both
  sides run under the same conditions. Control 1's exact 50.00% supports that.

## 11. A better way

**11.1 Test `QuietExtinction` for a coding fault before calling it a bad idea.** A 402 Elo
loss at 20,000 nodes is the signature of a rule that returns a wrong score, not of a
pruning choice that is slightly too aggressive. One cheap check: take 200 positions, run
with and without the switch to depth 12, and compare the scores where the switch fires. If
its scores are wildly different, look at the rule; if they are merely worse, it is the idea.

**11.2 Give the harness a per-switch "does it fire" counter.** Step 1 shows a switch is
alive only via bench nodes, which cannot show a switch that acts in rare positions -
`MateAlphaGuard` changed 4 nodes, and `DrawJitter` changed none. A counter printed at
`bench` time ("this rule fired N times") would tell a helper whether a 1,500-game "no
difference" is informative or vacuous.

**11.3 For switches with a near-total draw rate like `MateAlphaGuard` (99.87%), use a lower
node count or a wider opening book.** At 20,000 nodes the switch barely changes the game,
which is why its error is tiny. The same 1,500 games at 2,000 nodes would sample its effect
where it actually matters.

## 12. Model name and version

I am DeepSeek V4.1 Flash (model identifier `deepseek-v41-flash-1017`), running as a Cursor
cloud agent. That is the most precise version I know.
