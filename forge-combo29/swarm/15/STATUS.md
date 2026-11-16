# SEAT 15
- seat: 15
- branch: for-fable-and-opus/swarm-15
- area: 5 (PRINCIPAL VARIATIONS AND SCORES)
- seed: 1501

## 2026-11-16T23:25:13Z FINAL

### 1. THE HEADLINE: at 6 s + 0.06 the clock is NEGATIVE-SUM

Measured on the PC's own path — PC r15 build, PC20, Threads 1, Hash 16, self-play, a real clock
decremented by the measured wall time of every search. **30 games, 3,834 searches** (`games/games30.jsonl`).

Per-move search time: **median 104 ms, p90 269 ms, p95 368 ms, p99 564 ms, max 1,293 ms, mean 139.3 ms.**
**80.3 % of all moves take longer than the 60 ms increment.**

The arithmetic, for any control the owner chooses:

> **moves until the clock is empty = B / (search_time - increment)**

| basis | search time | net drain/move | moves of one side from 6,000 ms |
|---|---|---|---|
| median | 104 ms | 44 ms | **136** |
| **p90** | **269 ms** | **209 ms** | **29** |
| mean | 139.3 ms | 79.3 ms | **76** |

**60 ms is below the median**, so the control is negative-sum on more than half of every game's moves.
The tail is what decides when the clock runs out: 136 moves at the median but only **29 at p90**.

- **0 forfeits in 36 games** — but the narrowest margin was **115 ms remaining at 160 plies** (game 13),
  and the 160-ply cap was reached repeatedly. A game a few moves longer forfeits.
- Sizing an increment that survives a bad stretch: **≥ 269 ms** covers p90, **≥ 368 ms** covers p95,
  **≥ 1,293 ms** covers every move seen. That is roughly **4x the current 60 ms**.
- Why it did not forfeit yet: search cost **falls** in the endgame (217 → 83 ms from the first to the
  last 40 plies), which decelerates the drain. The middlegame phase carries the cost.

This is not the engine mis-managing time. It is the control being negative-sum for the engine's actual
search cost, and it is sustained only because games end before the clock does.

### 2. Then: no movetime cutoff between 1000 and 3000 ms (15-F34)

Slice honoured at **99-100 %** of both; the only early stops are positions whose **depth ladder ends at
64** (identical node counts at both slices). All 10 cells node-identical across 5 runs.

### 3. ALL FINDS, WITH STATE, BUILD AND SETTINGS

Base tree = 6b98f217. PC build = r15 from FABLE_TO_swarm_5.md (sha256 d6bd72c531f785f4…, all nine known
numbers reproduced). Threads 1 in every run of mine, Hash 16 unless stated.

| id | one line | build / settings | state |
|---|---|---|---|
| 15-F1 | mate -12 vs true mate -4 on `8/8/1p6/8/p3p3/8/2Kpk3/8 w`, PV never reaches mate | base / S14 d12 | **open on base**; repaired on PC (15-F18) |
| 15-F2 | 9 of 10 mate scores obey the PV-length rule, 1 violates it (553 pos) | base / S14 d12 | open |
| 15-F3 | KNN v K scored a win (+309); `DeadMaterial true` zeroes all 20 | base / S14 d10 | CONFIRMED by seat 05 (S-C5) |
| 15-F4 | dead-draw roots print an EMPTY pv, defeating a `" pv "` grep | base / S14 d10 | CONFIRMED by seat 05 (S-C6) |
| 15-F5 | terminal root walks the depth ladder to 64 with nodes 0 | base / S14 + ASan | open; score half withdrawn (15-R1) |
| 15-F6 | mate machinery exact on 8 fresh mate positions (negative result) | base / S14 d12 | open (bounds 15-F1) |
| 15-F7 | O depth-14 sum 21,812,100 exact | base / S14 d14 | open |
| 15-F8 | O carries 0 mate scores at d14; all 10 of job 1's were in G | base / S14 | open |
| 15-F9 | SECOND mate fault, wrong by 6 moves (`k7/6R1/…`) | base / S14 d14 | repaired on PC (15-F18) |
| 15-F10 | harness fidelity exact at four (set,depth) points | base / S14 | open |
| 15-F11 | 15-F9 self-corrects at d16; PV-shorter-than-score is the signature | base / S14 | open |
| 15-F12 | drawn-root thread all correct on PC → **patch is base-tree-only** | both | CONFIRMED by measurement |
| 15-F13 | *(withdrawn)* terminal `mate 0` is correct output | both | **WITHDRAWN (15-R1)** |
| 15-F14 | patch reproduces all nine known numbers | PC / none,S14,PC20 | open |
| 15-F15 | the UCI spec does not define terminal-root output | — | scoping note |
| 15-F16 | thrice-repeated ROOT is SEARCHED on the PC build | PC / PC20 | superseded by 15-F23 |
| 15-F17 | insufficient material short-circuits at 0 nodes on both builds | both | open (corrects my own claim) |
| 15-F18 | **both mate faults GONE on the PC build** (`mate -4`/`mate -3` at true distance) | PC / PC20 d12,d14 | open |
| 15-F19 | *(closed)* attribution to MateAlphaGuard was untested | PC / PC20 | closed by 15-F20 |
| 15-F20 | **`MateAlphaGuard true` ALONE fixes both**; CuckooRep worsens one | PC / S14+1 opt | CONFIRMED by seat 08 (08-C9) |
| 15-F21 | in-tree repetition works on PC → the ROOT check is the gap | both | framing corrected by 15-F23 |
| 15-F22 | 16 mate scores, 0 violations at d14 on PC | PC / PC20 d14 | open |
| 15-F23 | **root test IS called, returns TRUE, and the guard ignores it by design** | PC+base, instrumented | open |
| 15-F24 | `FORGE_FIX_ROOT_DRAWN` conflates two repairs | PC, flag ON/OFF | open |
| 15-F25 | **one-line split gives BOTH behaviours**, pins unchanged | PC / PC20 | open |
| 15-F26 | a drawn root still returns a REAL move (18/18 cells) | both, 3 builds | open |
| 15-F27 | pawn/capture reset makes a counter-100 mate reachable | both | open |
| 15-F28 | **counter-100 gap: base misses 7 of 7, PC finds 7 of 7** | both | open |
| 15-F29 | softnodes deterministic + finished-depth, overshoot to +233 % | PC / PC20 | open |
| 15-F30 | `nodes` = hard ceiling; `softnodes` = soft, brackets from opposite sides | PC / PC20 | open |
| 15-F31 | under-budget cell resolved: 1-legal-move position, not a hidden stop | PC / PC20 | open |
| 15-F32 | **clock path is a THIRD kind**; 6 s clock buys 22-358 ms | PC / PC20 | open |
| 15-F33 | one non-determinism at `movetime 100` (4/5 vs 1/5) | PC / PC20 | open |
| 15-F34 | no movetime cutoff 1000-3000; depth-64 ladder ends first | PC / PC20 | open |
| 15-F35 | 36 games 0 forfeits, but 115-174 ms margin | PC / PC20 6s+0.06 | open |
| 15-F36 | **p90 269 ms; 80.3 % of moves exceed the increment** | PC / PC20 6s+0.06 | open |

CHECKS I wrote: 15-C1 CONFIRMS 05-F8 | 15-C2 CONFIRMS 07-F1 | 15-C3 CONFIRMS 10-F6 |
15-C4 CONFIRMS 05-F1 | 15-C5 CONFIRMS 19-F33 | 15-C6 CONFIRMS 08-F22 (measurement; defect framing
withdrawn as 15-R3) | 15-C7 CONFIRMS 08-F23 + 08-C9 (both switch claims).

SELF-CORRECTIONS (7): 15-R1 terminal `mate 0` was correct output · 15-R2 a harness measured a REFUSED
FEN's stale board · "insufficient material is searched" (it is 0 nodes) · 15-R3 the fifty-move band is
correct, not a defect · the 15-F21 "gap" framing · 15-F19 (attribution now isolated) · the softnodes P3
overshoot band, and the movetime P1-P3 bands, were my under-specified predictions.

### 4. WHAT I DID NOT DO
No match against another engine; no `movetime` above 3000 at other builds; no frequency estimate for the
counter-100 gap; no clock-path test above 6 s or with a stronger opponent. The 30-game sample gives no
forfeit *rate* — only "0 in 36" and a 115 ms worst margin.


## 2026-11-16T23:15:15Z

- 15-F34 NO movetime cutoff between 1000 and 3000 ms: honoured at 99-100% of both slices on every
  board with real work; the only early stops are the two depth-64 boards (identical nodes at both
  slices — the ladder ended, not the clock). All 10 cells node-identical across 5 runs.
- 15-F35 CLOCK CAN LOSE A GAME? 36 self-play games, 4,648 searches at 6s+0.06: **0 forfeits,
  0 illegal moves**, clock never <= 0 — **but the margin is 174 ms and a game past ~165 plies would
  forfeit.** Median 105 ms used vs a 60 ms increment = **-45 ms/move net**; heaviest games drained
  5,826 of 6,000 ms over 160 plies (~73 ms/move). Saved only because search cost FALLS in the
  endgame (217 -> 83 ms, first to last 40 plies). 6s+0.06 with a 105 ms search is a negative-sum
  clock by construction.

TOTALS: 35 findings, 6 checks, 5 self-corrections. Every line names build + settings; Threads 1.

Running now: nothing.

Next exact command:
  cd /agent/repos/dwqww && git fetch -q --depth 1 origin for-fable-and-opus/swarm-05 && git show FETCH_HEAD:forge-combo29/swarm/05/FINDINGS.md | grep -E "^\| S-F2[0-9]" | head -6
  -> cycle 2(a): find another unconfirmed NEW finding and reproduce it with my own harness on the
     PC build under PC20.

## 2026-11-16T22:55:30Z

CLOCK PATH FILLED IN — all four budget modes are now characterised on the same five boards.

- 15-F32: the clock path is a THIRD kind, neither ceiling nor depth-complete. `movetime 100` uses
  ~90 ms of 100, but `wtime 6000+60` uses only **22-358 ms of 6,000 (0.4%-6%)** — a 6 s clock does not
  buy a 6 s search. And on the one-legal-move board BOTH clock modes stop at depth 64 / 94,406 nodes /
  22 ms identically: the depth ladder (clamp max 64) ends before the clock is consulted.
- 15-F33: one genuine non-determinism on a SHORT slice — G-mid-2 movetime 100 gave depth 15 in 4 of 5
  runs, depth 14 in 1, same 90 ms, same move, scores -251 vs -262. Absent at the 6 s setting.
- Two predictions refuted (P1 wall-time band, P5 node variation), recorded as such: this engine's clock
  search is far more deterministic and thrifty than I assumed.

THE COMPLETE PICTURE: `nodes` = hard ceiling (never exceeds, down to -78%); `softnodes` =
depth-complete soft budget (overshoots by the next depth, to +233%); `movetime` = short slice honoured
(~90%); `wtime/btime/winc` = 2.5%-6% of a 6 s clock, deterministic at that setting.

TOTALS: 33 findings, 6 checks, 5 self-corrections. Threads 1 throughout, build+settings on every line.

Running now: nothing.

Next exact command:
  cd /agent/repos/dwqww && for s in 26 27 28 30; do git fetch -q --depth 1 origin for-fable-and-opus/swarm-$s; git show FETCH_HEAD:forge-combo29/swarm/$s/FINDINGS.md 2>/dev/null | grep -cE "CONFIRMS"; done
  -> find an unconfirmed NEW finding of another seat and reproduce it with my own harness.

## 2026-11-16T22:51:31Z

TWO DELIVERABLES DONE since the last block.

1. **COUNTER-100 GAP, one page** — `file6/APPLY_counter100_gap.md`. Seven boards (3 pawn-mate,
   4 capture-mate), each verified single-mate with python-chess, all at counter 100, both builds with
   node counts. Base tree misses **7 of 7** (`cp 0`, 0 nodes); PC build finds **7 of 7** (`mate 1`).
   The one-line rule gap and the corrected inequality are on the page, plus the sentence that shows why
   four capture cases were needed: *in the pawn cases the base tree plays the right move for the wrong
   reason, but in the capture cases it plays a different move entirely (`h1g2`), losing the win
   outright.* Scope limit stated: minimal demonstrations, not a frequency estimate.

2. **SOFTNODES answered** (15-F29) — `softnodes/RESULT.md`, PC r15 PC20 Threads 1, 5 boards x
   N{500,2000,20000} x 5 reps:
   - **deterministic: YES** — 15 of 15 cells identical score/nodes/bestmove across 5 runs;
   - **finished depth: YES** — depth sequence exactly 1..D, no gaps, 15 of 15;
   - **overshoot: THE WHOLE NEXT DEPTH, not a margin** — at N=2000 (the PC's own self-play value)
     **+1.2% to +106.1%** (2,025-4,121 nodes); at N=500 up to **+233.4%**; at N=20000 +5.4% to +58.9%.
   - one cell finished UNDER budget (G-end-2 N=500, 442 nodes) — unexplained, stated as such.
   - **My P3 prediction (overshoot <= 20%) was REFUTED and its own kill threshold triggered.** I had
     guessed "one depth past N" would be a small fraction of N; for small N a depth can cost more than
     the whole budget.

TOTALS: 29 findings, 6 checks, 5 self-corrections. Threads 1 throughout; every line names build and
settings.

Running now: nothing.

Next exact command:
  cd /agent/repos/dwqww/forge-combo29/swarm/15/softnodes && python3 -u softnodes.py ~/builds/pc/forge --ns 500,2000 --reps 5 --out clock_cmp.jsonl
  -> then compare `go nodes N` against `go softnodes N` on the same boards, which is the PC's
     other stated budget mode and the obvious companion measurement.

## 2026-11-16T22:35:57Z

Both closing items for area 5 are DONE, plus one confirmation of another seat.

- **APPLY SHEET written**: `pcbuild/APPLY_root_drawn_split.md` — one page, the conflation with both
  flag states and measured outputs, the one-line change, the five case outputs, the four pins, and an
  explicit "no match was run; the drawn-root policy is the owner's choice".
- **15-F26 GUI CONTRACT tested**: with the split applied, a thrice-repeated root still returns a REAL
  move (`a2a3`), and `0000` appears only where there is genuinely no legal move (checkmated and
  stalemated roots, both verified 0 legal moves). 18 of 18 cells correct across three builds. So the
  draw adjudication does not break the GUI contract — the game can continue if the draw is not claimed.
- **15-C5 CONFIRMS 19-F33** with my own harness: PC r15, PC20 with only CorrHistV2 toggled, Threads 1,
  depth 12, 200 of G — 156 (78.0%) same bestmove, 44 (22.0%) different, 183/200 different scores,
  node delta -1.46%, 148 same-move cp positions mean +0.4 / median +1 cp, range -358..+435. Every
  derived number matches seat 19 exactly; my "off" node total differs by 28 in 10,146,239 (flagged,
  not chased).

TOTALS: 26 findings, 5 checks, 4 self-corrections. Threads 1 throughout; every line names its build
and settings.

Running now: nothing.

Next exact command:
  cd /agent/repos/dwqww && git fetch -q --depth 1 origin for-fable-and-opus/swarm-08 && git show FETCH_HEAD:forge-combo29/swarm/08/FINDINGS.md | grep -E "08-F2[0-9]"
  -> cycle step 2(a) again: their 08-F22 (the fifty-move score BAND at H=91..99 vs a single node
     spike at 91) is unconfirmed and is my thread; check it on the PC build myself.

## 2026-11-16T22:32:55Z

AREA 5 IS COMPLETE, on BOTH builds. The thrice-repeated root is instrumented and answered.

- 15-F23 INSTRUMENTED: `is_repetition()` at the root returns TRUE at 3 and 4 occurrences on the PC
  build, exactly as on the base tree and in agreement with python-chess — but `FORGE_FIX_ROOT_DRAWN`
  does not consult it (`root_drawn = !legal.empty() && is_insufficient_material()`), with the source's own
  comment saying a third occurrence "is searched like any other root". Text patch committed; honesty
  pins unchanged on both instrumented builds.
- 15-F24 that flag CONFLATES two repairs: ON finds the halfmove-100 mate but searches repetitions;
  OFF declares the repetition but loses the mate again.
- 15-F25 a ONE-LINE SPLIT does both at once, tested: `root_drawn = !legal.empty() &&
  (is_repetition() || is_insufficient_material())` -> repetition drawn AND both halfmove-100 mates
  found, twice-repeated still searched, checkmate/stalemate unchanged, pins unchanged,
  patch applies with `patch -p1 --fuzz=0`.
- 15-F18/F20/F22 both my mate faults are GONE on the PC build and `MateAlphaGuard true` ALONE is the
  fix (isolated one option at a time); G at d12 and d14 gives 28 mate scores, 0 PV violations.

TOTALS: 25 findings, 4 checks, 4 self-corrections (15-R1 terminal score, 15-R2 REFUSED-FEN harness,
the insufficient-material claim, and the 15-F21 "gap" framing). Every claim names its build and
settings; **Threads 1 throughout, audited.**

Running now: nothing.

Next exact command:
  cd /agent/repos/dwqww && for s in 05 07 10 19 25; do git fetch -q --depth 1 origin for-fable-and-opus/swarm-$s && git show FETCH_HEAD:forge-combo29/swarm/$s/FINDINGS.md | grep -E "^\| .*-[CF][0-9]+" | tail -3; done
  -> cycle step 2(a): find an unconfirmed NEW finding of another seat and check it with my own
     harness on the PC build under PC20.

## 2026-11-16T22:29:47Z

Both items the coordinator asked for are DONE and pushed. **Threads 1 and the build are named in
every finding line.**

1. REPETITION, TWO READINGS SEPARATED (15-F21) — **the ROOT check is the gap; the machinery is intact.**
   On `8/8/1K6/q7/7r/1k6/3Q4/1r6 w` (white a rook down) BOTH builds return `cp 0` at depth 10 and 12,
   and the base tree's PV visibly loops back to an already-seen position at ply 15 — in-search
   repetition works. Yet a thrice-repeated ROOT is still searched on the PC build (15-F16). Same
   build, same regime, same session: repetition recognised in the tree, not at the root.
   Two of my three solver candidates did NOT behave as predicted and are recorded as failures.

2. MATE DISTANCE ON PC20 (15-F18, 15-F20) — **both of my faults are GONE on the PC build**, and
   **`MateAlphaGuard true` ALONE is the fix.** Isolated one option at a time on top of S14:
   MateAlphaGuard fixes both positions; CuckooRep fixes the second but worsens the first (-13);
   HistRework / TtPruneV2 / CorrHistV2 / OwnBook fix neither. G set at depth 12 under PC20:
   12 mate scores, **0** PV-length violations (base tree: 1 at d12, 2 at d14), control 5/5.

STATE: 21 findings + 4 checks + 3 retractions/corrections. Two of my own claims withdrawn today
(15-F13 terminal scores, and 15-R2 a harness bug that measured a REFUSED FEN's stale board) — both
found by testing instead of reasoning, both recorded as their own lines.

Running now: nothing.

Next exact command:
  cd /agent/repos/dwqww/forge-combo29/swarm/15/pcbuild/matecheck && python3 pc_regimes.py ~/builds/pc/forge '8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1' 20 --regime PC20
  -> whether MateAlphaGuard keeps the mate right at greater depth, and then 15-F6's 8 R-set mates on
     the PC build to check the repair holds on positions that were already correct.

## 2026-11-16T22:23:47Z

PC BUILD PHASE. Build verified: patch from FABLE_TO_swarm_5.md, sha256 d6bd72c531f785f4…,
11 files, `patch -p1` clean, built with -DFORGE_MATE_ALPHA_GUARD=1. All nine known numbers match
(none / S14 / PC20). **Threads 1 in every run of mine; audited, none used more.**

DRAWN-ROOT THREAD (the priority question) — ANSWERED:
- mate-in-1 at halfmove 100: PC `mate 1` / 144 nodes / a1a8  |  base `cp 0` / 0 nodes / a1b1  -> REPAIRED
- pawn-move mate a7a8=Q# at halfmove 100: PC `mate 1` / 265 nodes  |  base `cp 0` / 0 nodes  -> REPAIRED
- **THE COMBINED PATCH IS NOT NEEDED FOR THE PC BUILD; it is base-tree-only.** (15-F12)

TERMINAL SCORES — I WAS WRONG, NOW RETRACTED (15-R1):
- `score mate 0` at a checkmated root is CORRECT. python-chess's own parser turns the engine's
  exact line into `PovScore(Mate(-0))`, `.mate()=0`, `.is_mate()=True`, converted **-100000** =
  the worst possible score, and its documented ordering is `Mate(-0) < Mate(-1) < … < MateGiven`.
- All three terminal cases are correct on BOTH builds: checkmate `mate 0`/`0000`, stalemate
  `cp 0`/`0000`, insufficient material `cp 0` + a real move. No inversion. 15-F13 WITHDRAWN.
- 15-F5 keeps only its real half: a terminal root walks the depth ladder to 64 with 0 nodes.

REPETITION (open, 15-F16): PC build SEARCHES a thrice-repeated root (`cp 23` / 13,424 nodes) and
four-times too, while the base tree declares the third occurrence drawn (`cp 0` / 0 nodes). Only the
history length varied; counts verified with python-chess. Two readings I cannot separate (check does
not fire vs it needs in-search repetition) — stated as such, not claimed.

ALSO CORRECTED MYSELF (15-F17): insufficient-material roots are SHORT-CIRCUITED at 0 nodes on both
builds. I had claimed they were searched, from counting info lines instead of nodes.

Next exact command:
  cd /agent/repos/dwqww/forge-combo29/swarm/15/job4 && python3 probe2.py 'k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1' 14 --opts s14   # then the same on the PC build under PC20
  -> re-run 15-F1 / 15-F9 (mate distance) on the PC build, which is the next thing the owner needs.

## 2026-11-16T22:18:36Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18:36Z

Starting the 12-hour continuation on the same seat (15), branch for-fable-and-opus/swarm-15.
Order of work from here:
1. Read every unread forge-combo29/soak_all/FABLE_TO_swarm_N.md from the lowest N to the highest.
2. Apply the FABLE_TO_swarm_5.md patch to a SEPARATE copy, build with -DFORGE_MATE_ALPHA_GUARD=1,
   check the known bench numbers it states.
3. Re-run my own findings on the PC build under settings PC20 and state build+settings per finding.
4. THE CYCLE as before; STATUS every 25 minutes at most, even mid-job.

State at the start of the continuation: 13 findings + 4 checks pushed; all three area-5 jobs and a
job-1 repeat done with reports; harness fidelity proven at four (set,depth) points at diff 0.

## 2026-11-16T22:15:27Z — 22:30 checkpoint: 12 findings, 4 checks, 5 reports

DONE — every one pushed with raw files:
- STEP 1 seat 15. STEP 2 build 6b98f217, sha256 e06310ec…16a83, honesty 4/4 (HONESTY.txt, with the
  default-regime caveat added after 15-C3).
- **HARNESS FIDELITY, four exact matches** (15-F10): O d12 9,500,069 | G d12 18,466,239 |
  O d14 21,812,100 | G d14 43,345,893 — every difference 0.
- job 1  (REPORT_job1.md): 553 pos d12 — 0 illegal PV moves, 10 mate scores, 1 violation.
- job 1b (REPORT_job1b.md): 200 R pos seed 1511 — 8 mate scores, 0 violations, 3 truth-checked exact.
  My predictions P3/P4 were REFUTED there; recorded as such. Finding 15-F6.
- job 2  (REPORT_job2.md): 120 pos d10 — KvK/KNvK/KBvK/threefold all cp 0; KNN v K nonzero 19/20
  (15-F3); empty-pv dead draws (15-F4).
- job 3  (REPORT_job3.md): 20 terminal roots x 3 go kinds under ASan+UBSan, BOTH sanitizer proofs
  present; 60/60 bestmove 0000, 0 sanitizer lines; but 64 info lines with nodes 0 (15-F5).
- job 4  (REPORT_job4.md): O and G at depth 14 — sums exact; G gives 2 mate-fault violations, one a
  NEW position wrong by 6 moves (15-F9), and violations get more frequent with depth.

CHECKS written and pushed: 15-C1 CONFIRMS 05-F8 | 15-C2 CONFIRMS 07-F1 | 15-C3 CONFIRMS 10-F6 |
15-C4 CONFIRMS 05-F1. Two of my findings (15-F3, 15-F4) are confirmed by seat 05 (S-C5, S-C6).

Running now: nothing.

Next exact command:
  cd /agent/repos/dwqww/forge-combo29/swarm/15/job4 && python3 probe2.py 'k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1' 16 --opts s14 2>&1 | grep -E "^info depth 16 |^bestmove"

(after copying probe2.py from job1) — to see whether idx 69 self-corrects with depth as idx 192 did,
which would separate "deepening artefact" from "wrong at every depth".
