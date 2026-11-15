# deepseek2, job 1 report: can a stored hash score hide a draw?

## 1. First line

**No, by my tests — with one important caveat about what "my tests" can see.**

The engine tests the draw (repetition, 50-move clock, material, stalemate) **before** it probes the
table, at every non-root node, so a repetition is caught even when the table holds "this position is
lost". 500/500 third-repetition cases played the only drawing move, fresh and warmed, at six search
settings. 100/100 stored mates were refused when the 50-move clock no longer left room.

**The caveat, and it is the most useful thing in this report:** the test forms the job prescribes are
much weaker than they look. I measured, with an instrumented build, how often each form actually
reaches a repetition node that is **not** a PV node (only those can take a stored score, because the
cutoff at `search.cpp:1638` requires `!pv_node`):

| test form | repetition nodes reached | of those, non-PV | can any of them take a stored score? |
|---|---|---|---|
| B1, C searched as the root | 74 (6 cases) | 8 | no — the draw test at 1569 returns first |
| B2 warmed walk | 4642 (6 cases) | 4414 | no, same reason; but it exercises the path heavily |
| Part C, same position at clock 0 then 97 | 0 (root-only searches) | 0 | **nothing on this path is touched** |
| my `sharper_test.py`, restricted root | 60 (6 cases) | **0** | **no — the child stays on the PV** |
| my `poison_s0_test.py` | the drawing node itself | — | yes — this is the one that really bites |

Read that table with the code order in mind: because the draw test precedes the probe, a repetition
node can never take a stored score *at all*, in any of these forms. So what a test form can
distinguish is not "does the repetition node trust the table" but "does the fault model, which makes
the repetition node trust the table, visibly change the answer". That is exactly what I measured with
the injected build, and the answer differs by form: 7% (B1), 23% (B2), 90% (poison_s0), **0%
(Part C)**.

And two facts that follow directly:

- **Part C cannot detect the fault it targets.** I built a version of the engine with *every* clock
  guard removed — `board.halfmove_clock() < 90` (search.cpp:1640), the mate-clock test inside
  `TTEntry::score_usable` (include/forge/search.hpp:112–115) and the `near50` move guard. Part C as
  written still reports **100 draws at clock 97** (`evidence/PartC_noguards.json`). It passes because
  the search starts at the root, and the root never takes a stored score. The only visible damage is
  in the clock-90 control (64 mate scores instead of 100), i.e. in the direction that makes the engine
  *more* pessimistic, not less.
- **My own `sharper_test.py` was also vacuous**, for the same reason: under `searchmoves a'` the child
  C stays on the PV, so `pv=1` at all 60 repetition nodes it reached. My earlier claim that it "puts C
  at a non-PV node" was wrong; the trace corrected it. I say this plainly because it was in a draft of
  this report.

So the honest answer: **the engine is clean on the tests that do reach the path (B2/B3 and
`poison_s0_test.py`), and the tests the job prescribes as decisive are not decisive.** Details and
counts below.

## 2. Step 0, expected against printed

| command | expected | printed |
|---|---|---|
| `bench 11` | 312866 | **312866** |
| `bench 13` | 862329 | **862329** |
| `go perft 5` from startpos | 4865609 | **4865609** |

Raw: `evidence/step0_raw.txt`. Build: `evidence/BUILD.txt` (g++ 13.3.0, GCC libstdc++,
`-DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=native`; the VM's default CXX is clang 18 whose cmake probe
fails with `cannot find -lstdc++`, so `g++` is named explicitly — which is what the job asks for).

## 3. Part A — the read, at the line numbers of 6b98f217

All `src/search.cpp` unless stated. `Worker::is_draw` = **1300–1310**.

### Main search `Worker::search` (1551)
1. **Draw test:** **1568–1569**, inside `if (!root_node)`. `is_draw` (1302–1309) tests
   `halfmove_clock >= 100` first (with "mate on the hundredth half-move still wins", 1304), then
   `is_repetition(root_history_index_)`, then insufficient material, then stalemate.
2. **Probe:** **1590/1591** — 21 lines *after* the draw test.
3. **A stored score ends the node at 1638–1642**:
   `!pv_node && excluded.is_none() && tt_hit && tt_score != ValueNone && tt_depth >= depth &&
   (mate_moves_ == 0 || (!is_mate_score(alpha) && !is_mate_score(beta))) &&
   board.halfmove_clock() < 90 && (Exact | Lower&>=beta | Upper&<=alpha)`.
   Clock/mate conditions: **`board.halfmove_clock() < 90`** (1640) and the `mate_moves_`/
   `is_mate_score` guard (1639). `tt_score` is separately gated at **1596–1598** by
   `tte.score_usable(clock)` and `rule50_score_for_this_clock` (205–209: reuse only at the *same*
   clock unless `EvalRule50Damp`, default **false**, search.cpp:96), then `score_from_tt` (188–199)
   refuses anything that would fall outside the mate band. The hash **move** has its own guard at
   **1595** (`!near50 || tte.rule50_clock == clock`).
   `TTEntry::score_usable` (include/forge/search.hpp:106–119) is where a stored mate is tested against
   the clock: `current_clock + distance > 100` → unusable; otherwise a different clock is accepted
   only when both clocks are < 90 and both `clock + depth < 100`.

### Quiescence `qsearch` (1416)
1. **Draw test:** **1425**, unconditional (no root special case).
2. **Probe:** **1439/1440** — after the draw test.
3. **Cutoff at 1451–1455**: `!pv_node && !near50 && tt_hit && tt_score != ValueNone &&
   (mate_moves_ == 0 || !is_mate_score(alpha)/beta) && bound condition`.
   Here the guard is `!near50` (`near50 = halfmove_clock() >= 90`, 1444) — stricter than the main
   search: qsearch never takes a stored score at clock ≥ 90.

### Root
- **The root call starts with a wide window** (`alpha = -Infinite; beta = Infinite`, 2401–2402) and
  narrows only from depth 4 (2406). A root node searched with any window of width > 1 is a PV node by
  `beta - alpha > 1` (1552), so line 1638's `!pv_node` can never hold at the root — and **1568**
  additionally skips the whole draw block there, so the root never draws either.
- Root moves are not pre-filtered for repetition: the move loop (1930–2066) plays each legal root
  move, and the child at ply 1 catches the repetition at its own 1569.
- An already-drawn root is caught at **2251–2253** (`root_drawn`: `board.is_repetition()` — the
  **two**-occurrence form — or clock ≥ 100 or insufficient material); the search is then skipped.

### The paragraph
**The draw test runs before the probe in both searches, so a node whose own position is already a
repetition, or whose clock has run out, can never take a stored score — even if the table says
"lost".** That is a genuine, correctly placed guard and it covers the first case in the job's question
for repetitions **at** the node. What the ordering cannot protect is a stored score that was
*contaminated by a repetition deeper in the subtree that produced it*: the table is keyed on the
position only (no repetition history in the key), so N inherits a score computed under a different
history. The engine's defence there is not the ordering but the fact that every node below N also
tests for repetition against the *current* history, which makes a repetition-based score wrong only
when the repetition was conditional on history N no longer has. I could not construct such a case
(§4, §6), but I also cannot prove it impossible — and note that the guard at 1640 (`clock < 90`)
shows the authors thought about exactly this class and chose a coarse, safe cutoff.

## 4. B0 controls

`evidence/B0i_20cases.txt`, `B0ii_random_player.txt`, `B0iii_planted_faults.txt`,
`B0iv_negative_control.txt`.

- **(i)** 20 cases with every check printed: legality per ply, no mate/stalemate in any prefix, C with
  black to move and not in check, `is_repetition(3)` true after k' and after no other black move,
  half-move clock.
- **(ii) Random player at C:** 500 cases × 20 picks = 10000 trials, **2090 hits (0.2090)** against
  2150.1 expected (0.2150) from `1/legal_moves`. Legal-move distribution at C: 3×111, 4×58, 5×146,
  6×69, 7×45, 8×71.
- **(iii) Planted faults, 500/500 rejected each.** Fault 1 = one cycle less (3 plies). Fault 2 = the
  full 7-ply list with a *different legal* white 7th move, so C occurs once. Fault 2 is legal
  move-for-move, so the rejection comes from the repetition test, not from illegality. (My first
  fault 2 was rejected as an illegal move; I rebuilt it, because that proves nothing.)
- **(iv) Engine negative control:** the same material and bare king to move but with no repetition
  anywhere scores as lost in 500/500 — 42 `mate -`, 345 `cp <= -500`, 9 `cp 0` — and those 9 are
  exactly the cases where black captures the queen on that move, so `cp 0` is correct there.

## 5. B1–B3

500 cases each, `Threads 1`, Hash 16 except last row. "played k'" = final bestmove is the unique
drawing move. Rows in `evidence/*.tsv`, full info lines in `evidence/B1_fresh_d12.json` etc.

| run | cases | played k' | did not | errors |
|---|---|---|---|---|
| B1 fresh, `go depth 12` | 500 | **500** | 0 | 0 |
| B2 warmed walk, no `ucinewgame`, `go depth 12` | 500 | **500** | 0 | 0 |
| B3a `go nodes 2000` | 500 | **500** | 0 | 0 |
| B3b `go nodes 20000` | 500 | **500** | 0 | 0 |
| B3c `go depth 20` | 500 | **500** | 0 | 0 |
| B3d `go depth 12`, `Hash 1` | 500 | **500** | 0 | 0 |

Score at C in all 3000 searches: `cp 0`.

**Control that a failure is counted at all** (`evidence/control1_harness.txt`): B1 on 100 cases with
a deliberately wrong expected move → runner reports **0/100 played**, while the engine still played
the true k' 100/100. The counter is live.

**Control that the fault class is detectable** (`evidence/fault_model_rep_ignored.patch.txt`, a
15-line text patch on a private /tmp copy, never committed): a repetition whose node holds a usable
stored score returns that score instead of the draw.
- B1 fresh on that build: **93/100** played k' → **7/100 failures**.
- B2 warmed walk: **23/100 failures**.
So B1 and B2 do have real detection power (7% and 23%), unlike Part C (0%) and my sharper test (0%).

## 6. B4 findings

**None.** No case had B1 play k' while a warmed run did not; all six runs agreed on all 500.

### The test that does bite: `poison_s0_test.py` (`evidence/poison_s0.json`, 500 cases)
The node that must return "draw" is **S0 itself**, one ply below C. This test poisons exactly it:
1. `position fen S0` + `go depth 18` — S0 is not yet a repetition, so the engine scores it a white
   win: 248 are `mate N` (N from 1 to 24) and 252 are `cp +334…+1200`. That is the poisoning, and it
   is the engine's own deep score for the exact key that is about to be reused.
2. `position fen S0 moves <a k a' k' a k a'>` + `go depth 12` — root C, black to move; k' reaches S0
   for the third time.

| arm | played k' | score at C |
|---|---|---|
| fresh process (no poisoning) | **500/500** | `cp 0` ×500 |
| poisoned, same process | **500/500** | `cp 0` ×500 |

On the fault build the same test gives fresh 93/100 and **warm 10/100**, with scores like
`mate -3`, `cp -1033` — i.e. it detects the fault on 90% of cases. Against the real engine: 0 failures.

## 7. Part C — a stored mate against the 50-move clock

**Done as specified, 0 findings — and the test is not decisive (see §1).**

100 KQ-vs-K positions, white to move, shortest mate exactly 5 plies
(`evidence/partc100_mate_in_5plies.json`).

- Generator `partc_find.py` (memoised AND/OR), cross-checked against `verify_exact.py`, an
  independent second implementation written straight from the definition (no memo, no pruning).
  They agree on **25/25** random KQ positions including 2 mate-in-5 and 2 mate-in-3. My first
  hand-guessed expected values for two control positions were wrong and the independent classifier,
  not my guess, is the reference.
- 10 of the 100 justified by hand listing (`evidence/partc_handcheck10.txt`): every white first move,
  every black reply, and the mate that follows.
- Engine test, one process per case, no `ucinewgame`, `go depth 12` (`evidence/PartC_50move.json`):

| search | mate for white | draw | other |
|---|---|---|---|
| clock 0 | **91** | 0 | 9 × `cp +1000…+1200` (no mate proved at depth 12 — correct) |
| clock **97** | **0** | **100** | 0 |
| clock 90 (control) | **100** | 0 | 0 |

- **Power check:** with all clock guards removed (`evidence/PartC_noguards.json`) the clock-97 row is
  *unchanged at 100 draws*. Only the clock-90 control moves (64 instead of 100). Part C therefore
  cannot distinguish a correct engine from one with the guard deleted; its clean result is not
  evidence about the guard.
- I also built the version where the high clock is at a **non-root** node
  (`fifty_nonroot.py`, `evidence/fifty_nonroot.json`): Q is black-to-move at clock 96, one black king
  move k gives P at clock 97, and P is searched at clock 0 first. 40 cases: fresh **40 draws**,
  warm **40 draws**, with the poison arm holding a mate in 38/40. Still clean — and with the guards
  removed it is *still* 40 draws, because the search is restricted to k and the child stays on the PV.
  The unrestricted variant (`fnr2.py`, `evidence/fnr2_real.json`) does put the high-clock child off
  the PV (fresh plays k in only 12/40, i.e. 28 of the 40 roots have another move); the score stays
  `cp 0` in 40/40 fresh and warm, and the unguarded build shows the guard's absence only as
  9/40 → 3/40 plays of k. That is a weak but real signal, and it points the same way: **no hidden
  draw**.

## 8. Suspicions, not proven

- **`search.cpp:1640` `board.halfmove_clock() < 90` is coarse.** It refuses *every* stored score at
  clock ≥ 90 including mates the clock can still deliver. My instrumented build logged **517** such
  events at clock ≥ 90 in 8 Part C positions, every one at a non-PV node, every one saved by that
  one condition (`evidence/` trace output quoted in §1 table). Cost, not correctness. A match with
  the condition relaxed to "mate whose distance still fits" would measure it; I did not run one.
- **`search.cpp:1638` is not keyed on repetition history.** A score computed in a subtree containing
  a repetition can be inherited by a node that no longer has it. `poison_s0_test.py` is the direct
  attack and finds nothing in 500 cases, but absence of a case is not proof.
- **`root_drawn` at 2251 uses the two-occurrence `is_repetition()`.** Legal in play (a threefold is
  needed to claim), but it means the engine reports `cp 0` and never searches from a twofold — a
  position that is twofold and still winning is scored as drawn by the root shortcut. Whether the
  UCI/GUI layer relies on that I did not check.
- **`EvalRule50Damp` defaults to false** (search.cpp:96), so `rule50_score_for_this_clock` returns
  true for every clock and the only clock protections in a default build are `score_usable`,
  `near50` and `clock < 90`. I tested only default builds.

## 9. Files of the repository I opened

`forge-combo29/CMakeLists.txt` (14–43), `src/search.cpp` (1300–1310, 1416–1466, 1551–1700,
1930–2095, 2143–2280, 2395–2470), `src/board.cpp` (1180–1260, key/halfmove bookkeeping by grep),
`include/forge/search.hpp` (60–120, 335–360), `src/uci.cpp` (27–71, 240–270, 470–520),
`handoff/fable-opus-combo29-all-20261114: forge-combo29/soak_all/FABLE_TO_deepseek2_1.md`
(and, to check whether a later job file existed, nothing else on that branch was read).

## 10. Stamps

| part | UTC | source |
|---|---|---|
| start | 2026-11-15T14:04:57Z | `date -u` written to a file |
| Step 0 done | 2026-11-15T14:05:17Z | same |
| Part A done | 2026-11-15T14:07:02Z | same |
| B1–B3 done | 2026-11-15T14:21:31Z | same |
| last command before the report | 2026-11-15T14:28:36Z | same |

I wrote stamp files only at those five points, not at every part boundary. Per-run times are the
runtimes the scripts printed (B1 13 s, B2 28 s, B3a 14 s, B3b 24 s, B3c 75 s, B3d 24 s, Part C 17 s,
poison_s0 54 s).

## 11. What I did not do

- No self-play or game-level test; all positions are synthetic KQ/KR endings.
- The 50-move question at a **genuinely non-PV** node is only weakly covered: my restricted-root form
  kept the child on the PV (measured), and the unrestricted form gives a `cp 0` at both arms, so the
  comparison has little room to differ. I did not find a construction where a stored mate at a
  non-PV, clock-97 node is the *only* thing that could produce a mate score.
- No match to measure the cost of the `clock < 90` cutoff.
- B1/B2/B3 share one 500-case set (seed 20261115), not several.
- I did not test `EvalRule50Damp=true`.
- No engine source is committed; fault models are text patches (`evidence/*.patch.txt`) and the
  builds lived in `/tmp`. No pull request was opened.
- **A lapse:** the draft of this report claimed the sharper test put C at a non-PV node. The trace
  showed `pv=1` there and I corrected it. Anyone reading an earlier copy should discard that claim.

## 12. What I am not sure about

- Whether a contaminated subtree at high depth can hide a draw in a real game. My tests reach the
  path (B2: 4414 non-PV repetition nodes over 6 cases) and find nothing, but "not observed" is not
  "impossible".
- Part C's clean result: I know it does not depend on the clock guard, so it is evidence only that
  the engine plays the drawn position sensibly, not that the hash table is safe.
- The 9 `cp 0` in the negative control are explained by queen captures; I verified the mechanism on
  all 9 by re-checking legality of the capture, not by hand-analysing each.
- `is_repetition(root_index)` vs `is_repetition()` disagreement in a long game history: read but not
  tested.

## 13. A better way

1. **Replace Part C with the poison form.** Part C as written has zero power against the fault it
   targets, because both searches start at the root and the root never takes a stored score; that is
   a measurement, not an opinion (`PartC_noguards.json`: guards deleted, result unchanged). The form
   that works is `poison_s0_test.py`: poison the exact key with the engine's own deep score, then ask
   for the drawing move. It catches the fault on 90% of cases and is clean on the real engine.
   Check: run it against `fault_model_rep_ignored.patch.txt` (must fail) and against the real build
   (must pass).
2. **Keep a fault model in the job folder for every future "can X hide Y" job.** A test that cannot
   fail is worse than no test: Part C would have passed a build with the guard deleted, and that
   build is exactly what the job is worried about. One 15-line patch, one rebuild, and the report can
   state its own detection power. I would make "state your test's power on a planted fault" a
   standing line in every job file.
3. **`DrawJitter` is a reproducibility trap** (search.cpp:1313–1319): a repetition/fifty-move leaf
   returns `local_nodes_ % (2*span+1) - span`, a node-count-dependent value. Harmless for this
   question (span ≤ 8) but it will make any future "same drawn position must score the same" check
   fail for reasons unrelated to the code under test. Worth a note in the test-writing guidance.

## 14. Model

deepseek2. As I know it: DeepSeek V4.1 Flash, build 1017, running as a Cursor cloud agent.
Job time used: about 26 minutes of the 60 allowed.
