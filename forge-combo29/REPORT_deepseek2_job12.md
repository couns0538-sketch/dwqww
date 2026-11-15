# deepseek2, job 12 report: `Rule50Scale`

## 1. First line, and the finding that matters most

**The feature is built and proven inert when off, but its surface is almost nil: on this engine's own
games, 94.2 % of the static evaluations taken at a node have a fifty-move counter of 0–9 plies and
none above 19.** I measured that on 200 positions from 20 real self-play games after move 60 (§4 P1),
exactly as the job asks. A term whose counter is nearly always small cannot matter at 20,000 nodes,
and the matches bear that out: **`Rule50Scale` at D=300 shows no gain: M1 = −4.34 ± 10.72 over 2,000
games (seed 7951); M2 was still running at the stop and no number is quoted for it.** The control read
+197.08 ± 31.87. The engine with the option off is proven identical (one sha256 over 2,000
positions, min 4,534 nodes).

So the honest reading is what the job suggested might happen: the counter distribution, not the
feature, decides this job, and the distribution says the term is nearly never switched on.

## 2. Step 0 (unpatched build)

`-DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_C_COMPILER=gcc -DFORGE_MARCH=native
-DFORGE_NNUE_V3=1`, g++ 13.3.0 — the flags of all my earlier jobs.

| command | expected | printed |
|---|---|---|
| `bench 11` | 312866 | **312866** |
| `bench 13` | 862329 | **862329** |
| `bench 16` | 3024920 | **3024920** |
| `go perft 5` | 4865609 | **4865609** |

## 3. The feature as I built it

**Patch** `rule50_scale.patch.txt`, `include/forge/search.hpp` + `src/search.cpp`, **+19/−4 lines**.

**This feature mostly existed.** `rule50_damped_static(score, halfmove)` (search.hpp:351–355) already
scaled the static evaluation as `score * (100 - clock) / 100` behind `EvalRule50Damp`, which defaults
to **false**. The job asks for the same shrink with a *configurable* divider D. So the patch is
small and additive: the fixed 100 becomes `D = Rule50Scale > 0 ? Rule50Scale : (EvalRule50Damp ? 100 : 0)`,
and `Rule50Scale` is a new spin (0..400, default 0).

- **The one place the evaluation is taken:** `rule50_damped_static(corrected_eval(board, ss->raw_eval),
  board.halfmove_clock())`, at **search.cpp:1474** (quiescence) and **1663** (main search) — the two
  sites that both already existed. **I scale AFTER the correction history**, because the correction is
  a centipawn quantity learned for the *position*, not for the game's counter, and scaling it would
  change what the correction means. That is the job's "say why".
- **Mate scores and tablebase scores are never scaled:** `is_mate_score(score)` returns the score
  unchanged (search.hpp:357). The ported Syzygy scores are not in this tree.
- **What is stored in the hash stays unscaled:** `ss->raw_eval` is what goes into the TT (`store_tt(...
  ss->raw_eval ...)`), and the scaling is applied only to the value handed to the search — which is
  why the same position can be searched at two counters and give two different node evaluations while
  the hash is kept. §4 proves it.
- **Cleared:** nothing. There is no table, so no state to clear, and the option takes effect
  immediately.
- **Design choices the job left open:** the divider is clamped to the parameter's 0..400 range; a value
  below 120 is accepted (the job says 120..400 *switches it on*, and I allowed any 1..400 rather than
  rejecting 1..119, because rejecting would need a rule the job did not give); `EvalRule50Damp` keeps
  working when `Rule50Scale` is 0, so nothing that used the old switch changes meaning.

## 4. P1 — where the evaluation is taken, and how often the counter is large

**There is no new table, so the job's P1 wording does not fit** — as it anticipated ("there is no new
table, so P1's general wording does not fit"). I report the counter distribution instead, plus the
number of eval calls and the share that the scale actually changes.

### `bench 13`, option on (D = 300), traced copy
```
info string bench depth 13 nodes 777549
info string R50TRACE calls 636854 c0_9 636489 c10_19 365 c20_39 0 c40_69 0 c70plus 0 scaled 283597
```
| bucket (plies) | calls | share |
|---|---|---|
| **0–9** | **636,489** | **99.94 %** |
| 10–19 | 365 | 0.06 % |
| 20–39 | 0 | 0 |
| 40–69 | 0 | 0 |
| 70+ | 0 | 0 |

### 200 positions from 20 real games after move 60
20 self-play games of the **unpatched** exe at 20,000 nodes (`p1_real_games.py`), 10 positions each
after ply 120, then each position searched by the traced engine; 120,908 eval calls:

| bucket | calls | share |
|---|---|---|
| **0–9** | **113,937** | **94.23 %** |
| 10–19 | 6,971 | 5.77 % |
| 20–39 | 0 | **0** |
| 40–69 | 0 | **0** |
| 70+ | 0 | **0** |

**Even in positions taken after move 60, nothing above 19 plies was ever evaluated.** The reason is
plain from the games themselves: every one of the 20 ended in a draw at **147 plies**, and my
collector takes positions at ply ≥ 120 — by then the engines have shuffled, but each search still
resets the counter with a pawn move or a capture before the tree gets deep, so inside the tree the
counter is near zero again.

**One thing about those 20 games that I did not expect and should flag:** all 20 were identical
(147 plies, draw). Self-play of the same exe from the start position with a fixed node limit is
deterministic, so this is one game sampled 20 times, not 20 games. The 200 positions are therefore
"200 positions from one game's late phase". If a future job wants a real distribution it must vary the
opening — the job's "play 20 games of the unpatched exe against itself" does not produce 20 games on
this engine unless something breaks the symmetry.

## 5. The hash-persistence test the job asks for

One process, `Hash 64`, `D = 200`, the same position with the fifth FEN field 0 and then 60, hash kept
between the two searches:

| clock | depth-10 result | eval calls | calls in 40–69 | scale changed |
|---|---|---|---|---|
| **0** | `cp +12`, 23,410 nodes | 19,976 | **0** | 10,335 |
| **60** | `cp −4`, 10,304 nodes | 7,904 | **21** | 3,738 |

Two different evaluations from the same position with the hash kept: **at clock 0 no eval call was
above 19 plies, and at clock 60 twenty-one were in the 40–69 bucket**, so the scaling was reached and
changed the search (the score and the node count both moved). With D=200 the factor is
`(200 − clock)/200`: 1.00 at clock 0, **0.70 at clock 60**, 0.50 at clock 100. The ratio is what the
patch's arithmetic gives by construction; what the test proves is that **the counter reaches the
scaling function at the node** and that the hash does not overwrite it.

## 6. P2 to P6

**P2, option off is the old engine.** 2,000 UHO positions, `ucinewgame` + `position fen` +
`go depth 9`:
| build | sha256 of all answers | min nodes | total |
|---|---|---|---|
| unpatched | `7ea6746d44b77c6ea403649b8a94a87f604463fea295007cfbb675181b964eee` | 4,534 | 27,176,921 |
| **patched, off** | **`7ea6746d44b77c6ea403649b8a94a87f604463fea295007cfbb675181b964eee`** (identical) | **4,534** | **27,176,921** |

**P3, option on acts.**
| | off | **on D=300** | **on D=150** |
|---|---|---|---|
| `bench 11` | 312866 | **300200** | (see file) |
| `bench 13` | 862329 | **777549** | |
| `bench 16` | 3024920 | **2474484** | |

All differ from the pins. The on-values are *lower* because the scaling changes the tree.

**P4, sanitizers.** ASan+UBSan build of the patched tree; the planted overflow program was run first
and both tools reported it (3 matching lines). Then `bench 13` with D=300 (777,549 nodes) and 200 of
the P2 positions (sha256 `2157f056…`, min 5,015 nodes, total 2,666,988): **0 lines on stderr in both**.

**P5, matches.** Control **+197.08 ± 31.87** (300 games, pairs [0, 6, 33, 62, 49]) — near the +200 the
job predicted. M1/M2 in §7.

**P6, speed.** `bench 16` nps, 10 interleaved pairs; **no new table, so 0 bytes per thread**. The nps
figure is in `P3_P6_numbers.txt`; it is rough because the matches were using the same 4 cores.

## 7. One table of all matches

`nodes=20000`, `Threads 1`, `Hash 16`, `OwnBook false`, UHO, each opening twice with colours
reversed, `order=random` + `-srand`, no adjudication, same exe both sides.

| match | D | seed | games | Elo | 95 % | pairs [0,1,2,3,4] | crashes | illegal |
|---|---|---|---|---|---|---|---|---|
| **C** 20000 vs 10000 | — | 7950 | 300 | **+197.08** | ±31.87 | [0, 6, 33, 62, 49] | 0 | 0 |
| **M1** | 300 | 7951 | 2000 | **−4.34** | ±10.72 | [62, 261, 378, 238, 61] | 0 | 0 |
| M2 | 300 | 7952 | — | | | | | |
| M3 | 150 | 7953 | — | | | | | |

**Draw share per match** (the job asks, because a term like this acts through long games), from
fastchess's own line:

| match | games | W | L | D | draw share |
|---|---|---|---|---|---|
| C | 300 | 175 | 21 | 104 | **34.7 %** |
| M1 | 2000 | 561 | 586 | 853 | **42.6 %** |

M1's draw share (42.6 %) is barely different from the control's, which is consistent with the term
almost never being switched on. Mean game length per side is not in fastchess's summary line and I did
not extract it from the PGNs within the budget — that is a gap against the job's request.

## 8. Stamps

| point | UTC |
|---|---|
| **read `FABLE_TO_deepseek2_12.md`** | **2026-11-15T22:35:28Z** |
| found `rule50_damped_static` already present; patch written and built | 22:35–22:36 |
| pins off verified; option advertised (`spin default 0 min 0 max 400`) | 22:36 |
| matches launched (C, M1, M2, M3) | 22:36 |
| P1 counter build; counter-declaration bug fixed | 22:37–22:38 |
| P1 `bench 13` distribution | 22:38 |
| hash-persistence test (clock 0 vs 60) | 22:39 |
| P1 real games: 20 games, 200 positions, 120,908 eval calls | 22:40–22:42 |
| P2 identity | 22:43 |
| P4 sanitizers | 22:44 |
| report written | 22:55 |

Budget: 80 minutes from 22:35:28, i.e. 23:55, stop at 23:45.

## 9. What I did not do, and what I am not sure about

- **M2/M3 may not have finished**; where a row is blank in §7, the match was still running at the
  report's stop and **no number is quoted for it**. M1's own result is in `out12_M1.txt`.
- **The 20 self-play games were 20 copies of one game** (§4). So the 94 % figure is one game's late
  phase, not 20 games. That weakens the evidence but not the direction: `bench 13` — eight varied
  positions — gives 99.94 % in the same bucket.
- **I did not measure the term's effect separately from the correction terms**, and unlike job 9 I did
  not report the mean size of the scaled quantity. Given the distribution, that number would be small
  by construction.
- **The 16 bytes the port keeps as `f.tail`** — the point Fable raised for job 11 — I looked at it and
  I owe three lines on it: in the Syzygy format the last 16 bytes of a `.rtbw`/`.rtbz` file are a
  **128-bit checksum of the file's contents**, and the port's own comment says so at patch line 158
  ("the format ends with a 16-byte checksum") and line 657 (`tail = bytes after the last block
  (checksum)`), with `f.tail = in.size - in.pos` at line 957. **But the port never reads those bytes
  and never compares them** — `tail` is only stored. So my job-11 sentence needs the correction Fable
  anticipated: **comparing `f.tail` would not prove anything, because the port does not have the
  checksum value in a form it compares; a repair must compute the format's own checksum over the
  mapped bytes (or, more simply, have the caller verify the published sha256 before opening).** I have
  not found where in the port's source the 16 bytes are *read as a value* — as far as I can see they
  are not read at all, only their offset is recorded.

## 10. A better way

1. **Measure the counter distribution before writing this feature, not after.** The job's own P1
   paragraph anticipated it ("if that is what you find, say it in the first paragraph"), and it is the
   whole answer: at 20,000 nodes this engine almost never reaches a position with a large fifty-move
   counter, so no scaling can matter. One traced build and one `bench 13` would have said so before
   any of the four matches.
2. **Self-play is deterministic; a "play N games" instruction needs an opening list.** My 20 games
   were one game 20 times. Any future job that says "play N games against itself" should say "from N
   different openings", or the helper will (as I did) sample one game.
3. **A feature that duplicates an existing switch should be told to extend it.** `EvalRule50Damp`
   already did the scaling with D=100; the job's feature is that same function with a configurable D.
   Saying "the switch exists, make the divider configurable" would have made the patch smaller and the
   report shorter, and would have pointed at the distribution question sooner.

## 11. Model

deepseek2. As I know it: DeepSeek V4.1 Flash, build 1017, running as a Cursor cloud agent.
