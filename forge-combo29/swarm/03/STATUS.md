# SEAT 03 STATUS

- seat: 03
- area: 3 (MOVE GENERATION against python-chess)
- branch: for-fable-and-opus/swarm-03
- seed: 301

## 2026-11-16T21:06:34Z

seat claimed, starting STEP 2 build

## 2026-11-16T21:14Z

HONESTY: all four pins MATCH (bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609).
Build: /home/ubuntu/build-rel/forge, g++ 13.3.0, -DFORGE_MARCH=native, sha256 68825bd5...

## 2026-11-16T21:35Z

Job 1 DONE (S-F1); job 2 DONE (S-F2, S-F3). HARNESS_AUDIT vs 19-F12 (pipelined quit): my perft/bench numbers
immune (inline in the UCI loop) and re-proved with honesty2.py.

## 2026-11-16T21:37Z

PARSE_AUDIT vs seat 19's NaN warning: `assert_measured.py` fails loudly on a missing/NaN/zero result, with
negative controls that both fail. Two real defects of mine found and recorded.

## 2026-11-16T21:50Z

- **03-C1: CONFIRMS seat 13's S-F1** — both halves measured with my own harness on their R_1301 set:
  their engine file vs my engine run 20,000/20,000 equal; my python-chess run vs my engine run 20,000/20,000 equal
  (sums 113,231 / 2,678,512 / 77,182,397 / 2,260,227,623). Their raw_ref.txt being byte-identical to raw_engine.txt
  is the expected consequence of 0 differences (run1 ref killed, exit 143; run2/ref_par.py regenerated in 616.8 s).
- **S-F4**: 320 constructed en-passant-pin positions — engine root move set = python-chess 320/320, plus a
  slider-removal control passing 320/320 (delete the pinner -> the same ep capture becomes legal, engine still
  matches). Goes beyond 23-F6's three hand-built cases.

## 2026-11-16T21:52Z — WARM-STATE AUDIT (seat 10's report)

Reproduced seat 10 (three `go depth 12` in one process: 56,720 / 4,951 / 4,516). Measured that it cannot reach my
tables: `go perft 4` on a mid-game position gives **1,110,595** ten times in ONE process, the same after
`ucinewgame`, the same after `Clear Hash`, and the same in ten separate processes — constant all three ways, while
the same harness shows the depth effect as a control. `Clear Hash` was never used by me (grep: zero occurrences).
Write-up: WARM_STATE_AUDIT.md, raw job0/warm_state.*.raw.

## 2026-11-16T22:10Z — JOB 3 COMPLETE (S-F5)

perft 1..5 on 230 positions (200 R + first 30 of G): **1,150 of 1,150 values equal to python-chess**, perft-5 sum
**3,925,995,728 on both sides**, 0 refused FENs, 0 crashes, 0 error lines; perft-1 move sets identical.
python side 1130.6 s. Files: job3/job3_table.txt, job3/job3_diffs.txt (0 lines), job3/py_all230.json.
A 60-position subset measured separately agrees too (sums incl. perft-5 1,552,941,785).

Runs: job1b (cycle step 2c, SEED 311) python perft 1..4 on 5,000 positions — engine half already done
(sums 112,193 / 2,606,301 / 74,557,281 / 2,159,914,969; 0 duplicate FENs vs the SEED-301 set).
Next: compare job1b; if it does not land by 22:30, push the engine half with the comparison marked incomplete and
the exact next command.

Next command:
`cd /agent/repos/dwqww/forge-combo29/swarm/03/job1b && tail -1 py.log && python3 ../assert_measured.py perft py.json 4 5000 && python3 ../job1/compare.py eng.json py.json diffs.txt | head -12`

## 2026-11-16T22:19:10Z CONTINUE: 12 more hours, ends at 2026-11-17T10:19:10Z

Seat kept: 03 (from ~/swarm_seat.txt). Branch for-fable-and-opus/swarm-03. Area 3 still.
Done so far: S-F1..S-F5, 03-C1, HARNESS_AUDIT, PARSE_AUDIT, WARM_STATE_AUDIT (see FINDINGS.md).
Next, per the owner's TEXT 2: read soak_all/FABLE_TO_swarm_5.md, build the PC build in a separate copy with
-DFORGE_MATE_ALPHA_GUARD=1, check its known bench numbers, then re-run my perft sets on it and compare node counts
to the base build.

## 2026-11-16T22:21Z

Read FABLE_TO_swarm_2, _3, _4, _5 (all five now). File 5's PC source built and verified:
- patch extracted from lines 56..2374 of file 5, sha256 d6bd72c531f785f4… = the published prefix (an earlier
  extraction at 57..2374 gave 83ce05d8… — recorded, because a wrong extraction yields a silently different engine)
- applied with `patch -p1` in a SEPARATE worktree /agent/repos/pccopy (11 files, no fuzz), built with
  -DFORGE_MATE_ALPHA_GUARD=1 -> /home/ubuntu/build-pc/forge
- **all eight published numbers MATCH**: none-regime 312866 / 862329 / 3024920 / 4865609; S14 242796 / 656517;
  PC20 278024 / 587276. MateAlphaGuard verified present in the exe's own uci list before sending it.
- job1b (SEED 311) COMPLETE: 20,000/20,000 equal, move sets identical, 0 duplicate FENs vs SEED 301.
- job4 (PC build perft) under way: sets A and B done — **40,000 of 40,000 values identical to the base build**
  (perft-4 sums 2,196,757,662 and 2,159,914,969 exactly equal). Set D (perft 5) running.

Swarm rule Threads 1 (22:20Z): perft does not use threads or the hash at all — `Board::perft`
(src/board.cpp:1205-1222) is a plain recursive walk with no hash probe — but I now state `setoption name
Threads value 1` (and Hash 16) explicitly in job4/engine_perft_t1.py so no table of mine can be misread.

## 2026-11-16T22:23Z

**job4 DONE — the owner's first job for my area.** PC r15 vs base, perft: **62,406 of 62,406 (position, depth)
values identical** across five sets, depths 1..5:
A 5,000 R SEED 301 (perft-4 sum 2,196,757,662 both), B 5,000 R SEED 311 (2,159,914,969 both), C 314 special,
D 230 positions to depth 5 (perft-5 **3,925,995,728 both**), E 320 en-passant pins (320/320 + control 320/320).
Under the full PC20 option set set A is still 20,000/20,000 identical. Settings: Threads 1, Hash 16 stated
explicitly in every job4 process; `ucinewgame`+`isready` before each `go`.
Findings: S-F6, S-F7, S-F8. Report: REPORT_job4.md.
Also job1b complete (SEED 311): 20,000/20,000 equal, move sets identical, 0 duplicate FENs.

Next in the cycle: check another seat's unconfirmed finding with my own harness on BOTH builds (area 10 duty
inside my cycle step 2a), then re-run my own findings on the PC build where they are search-adjacent.

Next command:
`cd /agent/repos/dwqww/forge-combo29/swarm/03 && bash board2.sh 2>&1 | tail -20`

## 2026-11-16T22:38Z

Durable claim file: job4/pc_movegen_identical.md (the claim, five sets with all sums, both build recipes, exact
reproduction commands, and the wrong-extraction hash warning).

**job5 DONE — the legality/move-choice question.** 200 positions, depth 8, Threads 1, fresh process per search:
- 196/200 same bestmove; **4 differ**, all 4 legal on both builds; 0 measurement failures.
- all 4 are **endgames**: 4/26 = 15.4 % vs 0/174 elsewhere (two-sided Fisher p = 0.0002) — the same region as the
  patch's bare-king fixes (cause NOT proven; that needs a rebuild with those macros off).
- PC build is stronger on the two unresolved cases (mate 5 at depth 8 vs base needing depth 12; mate 8 at d12 where
  base sees cp +1101), verified by replaying the mate PV to checkmate.
- planted control through the same harness: 4/4 differences and 4/4 illegal flagged.
Findings S-F9, S-F10. Report REPORT_job5.md.

Next: rebuild the r15 tree with FORGE_FIX_BARE_KING_LMR_CAP / _ONE_THREAD turned off and re-run the 26 endgame
positions — that turns the endgame suspicion into a cause or refutes it.

Next command:
`cd /agent/repos/dwqww/forge-combo29/swarm/03/job5 && python3 - <<'PY' ... PY` (see job6/repro_endgame.txt once written)

## 2026-11-16T22:55Z

**job6 DONE — causal attribution of the endgame divergence.** 7 builds x 26 endgame positions, depth 8, Threads 1,
fresh process per search, run twice byte-identically:
| build | 153 | 155 | 156 | 160 | =base | =PC |
| base | a4b4 | c6d6 | g5h3 | f1e2 | 4 | 0 |
| r15 PC | a4b5 | c6c7 | f2e3 | f1f2 | 0 | 4 |
| V1 both off | base | base | base | base | 4 | 0 |
| V2 LMR=0 OT=1 | a4b5 | c6d6 | f2e3 | f1f2 | 1 | 3 |
| V3 LMR=1 OT=0 | a4b5 | c6c7 | f2e3 | f1f2 | 0 | 4 |
| V4 both on | a4b5 | c6d6 | f2e3 | f1f2 | 1 | 3 |
| BASE+both | a4b5 | c6d6 | f2e3 | f1f2 | 1 | 3 |
LMR_CAP is the operative rule; the reverse test on base gives 3 of 4 PC answers with no other r15 change; idx 155
resists attribution (S-F12). Divergence set = exactly a subset of the 9 lone-king-root positions (S-F13).
Findings S-F11, S-F12, S-F13. Report REPORT_job6.md. Reverse-test patch: job6/base_bare_king_on.patch.txt.
Lapse recorded: no prediction file before job 6's measuring commands.

Next: isolate idx 155's partner change (build r15 variants with the other FORGE_FIX_* switches off), then return to
the cycle's area-10 duty (check someone else's unconfirmed finding on both builds).

Next command:
`cd /agent/repos/pccopy/forge-combo29 && grep -n "FORGE_FIX_" src/search.cpp include/forge/search.hpp | head -20`

## 2026-11-16T22:58Z

Read FABLE_TO_swarm_6 (all six files now). It cites my PC-build and move-generation results as settling the patch.

**job7 DONE.** 155 bisected: it needs `LMR_CAP=1` together with `ONE_THREAD=0` — the shipped PC combination — and no
third macro. Base + ported patch at `lmr1_ot0` reproduces **4 of 4** PC answers; `ot1` (either cap value) and
both-off all revert 155 to c6d6. Reruns byte-identical; c6c7 holds to depth 14. **S-F12 superseded by S-F14.**
Better/worse at depth 20, both builds as independent adjudicators: **156 better, 160 better, 155 WORSE (mate -14 vs
cp -1145), 153 undecided** (lost either way). S-F15. REPORT_job7.md.
Lapses recorded: no prediction file for jobs 6-7; exact mate-proof solver abandoned as exponential.

Next: file 6's suggested area — `go softnodes N` on the PC build under PC20, Threads 1: determinism run to run, does
it stop at a finished depth, how far past N does it go.

Next command:
`cd /agent/repos/dwqww/forge-combo29/swarm/03/job8 && python3 softnodes.py ~/build-pc/forge /tmp/sn.txt`

## 2026-11-16T23:10Z

**job9 DONE — S-F16/S-F17: position 155 is a LIVE defect on the PC build's real path.** PC build, PC20, Threads 1,
Hash 16, `1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183`: it plays c6c7 whose **own depth-20 score is mate -11**, while
c6d6 scores **cp -1142**; base scores the two moves cp -1145 / cp -1174 and plays the better one. PC spends 165.8M
nodes at depth 20 vs base's 169,686 (~1000x). Same move at depths 8/12/16/18/20; its own score becomes a mate
against itself at d18 and the move never changes. Control: `lmr0_ot0` is bit-identical to base (scores AND nodes).
Report REPORT_job9.md. Not done: instrumenting the reduction (mechanism is a labelled hypothesis), python-chess mate
proof.

Next: job8 — `go softnodes N` on the PC build under PC20, Threads 1 (prediction already written: determinism,
finished-depth stop, overshoot). Then scan more lone-king endgames from real games for the S-F16 signature.

Next command:
`cd /agent/repos/dwqww/forge-combo29/swarm/03/job8 && python3 softnodes.py ~/build-pc/forge soft.txt`

## 2026-11-16T23:20Z — HEADLINE

**S-F20 (headline): losing-move misevaluation in the shared search, proven by play-out.** Position
`1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183`: engine plays c6c7 (loses in 20 plies) while c6d6, which it rejects and
rates mate -11, holds out 22 plies (python-chess adjudicated, 3/3). PREDATES the PC build (base under S14 makes the
same choice) and is NOT fixable by removing the bare-king cap.
**S-F21**: instrumented cap fires 4,680,728x at depth 18 (1.4M clamping 3-ply to 1; 11 clamping 11-ply to 1) but
only 6x at the root, always on c6d7 — never on the two candidates. The cap is the COST (~1000x nodes), not the cause.
Reports REPORT_job10_item2.md, job10/item1_item2.md; traces job10/cap_depth8.err, cap_depth18_summary.txt.

Next: item 3 — 50 real-game lone-king positions at depth 16, count how many show the signature (chosen move scored
worse than an alternative by more than a queen).

Next command:
`cd /agent/repos/dwqww/forge-combo29/swarm/03/job11 && python3 scan_loneking.py ~/build-pc/forge scan.txt`

## 2026-11-16T23:16Z — job11 DONE (scan)

**Headline stands: S-F20 (losing-move misevaluation, play-out proven) + S-F21 (cap fires 6x at root, never on the
candidates → cap is the cost, root comparison the cause).**
job11 — 50 real-game lone-king positions, depth 16, PC20, Threads 1, Hash 16:
- **strict S-F20 signature: 0 of 50. My prediction (5-20) is KILLED.**
- any-margin mismatch: **11 of 45 scorable** (median 36 cp, max 161).
- ply cost on the 8 largest gaps (play-out d8): **chosen dies sooner in 5 of 8**, +4/+21/+23/+38/**+49** plies;
  four lose at once where the alternative survives 22-50.
- Set rebuilt mid-job: 40 self-play games all collapsed to the same K+N vs K+N drawn position (S-F24), so endings
  were generated from material-imbalanced starts instead (50 from 143 games). Also fixed a silent SquareSet-vs-int
  bug in my own generator, now guarded by a known-answer self-test.
Findings S-F22, S-F23, S-F24. Report REPORT_job11.md.

Next: depth-16 play-out on the 4 instant-loss cases (are they the same root fault or a d8 quiescence artefact?),
then assemble the FINAL block with S-F20/S-F21 at the top.

Next command:
`cd /agent/repos/dwqww/forge-combo29/swarm/03/job11 && PC_TOPN=4 PC_DEPTH=16 python3 plycost.py eg50.tsv scan50.txt plycost_d16.txt`

## 2026-11-16T23:17Z FINAL

Every find of mine, with its state, build and settings. Builds: **base** = 6b98f217 (sha256 68825bd5…);
**PC r15** = patch from FABLE_TO_swarm_5 lines 56..2374 (sha256 d6bd72c531f785f4…), built with
-DFORGE_MATE_ALPHA_GUARD=1 (sha256 8a…/pcbuild). Settings are named per line: **none** = no setoption;
**S14** = the 14 search settings; **PC20** = S14 + CuckooRep/HistRework 2/TtPruneV2/CorrHistV2/MateAlphaGuard/
OwnBook false. Threads 1 and Hash 16 everywhere except the pinned-bench lines (which are default-option by rule).

### HEADLINE

**S-F20 — losing-move misevaluation in the shared search, proven by play-out.** Build: base and PC r15; settings:
S14/PC20, Threads 1, Hash 16, `go depth 12/20`. On `1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183` the engine plays
`c6c7`, which loses in **20 plies**, while `c6d6` — which it rejects and rates `mate -11` in its own root scores —
holds out **22 plies** (python-chess adjudication, 3 of 3 paired repeats). The engine mis-scores the alternative and
therefore chooses the faster loss. **State: open, not confirmed by another seat.** It predates the PC build
(reproduces on base under S14) and is not fixable by removing the cap.
File: REPORT_job10_item2.md, job10/playout_base_d12.txt.

**S-F21 — the mechanism boundary.** Build: PC r15 with a guarded fprintf at the cap site (scratch copy, bench 11 =
312866); settings: PC20, Threads 1, Hash 16, `go depth 18`. The bare-king LMR cap fires **4,680,728 times**
(1,395,047 clamping a 3-ply reduction to 1; 11 clamping an 11-ply reduction to 1) but only **6 times at the root
ply, always on `c6d7`, never on `c6d6` or `c6c7`**. So the cap is the ~1000x node COST, and the root comparison is
the CAUSE. **State: open, not confirmed.** File: REPORT_job10_item2.md, job10/cap_depth18_summary.txt.

**Population rate, stated plainly: mostly benign — and my own later work withdrew the case I thought was worst (see the CORRECTION below).** Build: PC r15; settings PC20, Threads 1, Hash 16, depth 16,
50 real-game lone-king positions. Strict S-F20 signature (chosen worse than an alternative by > a queen):
**0 of 50** — my prediction of 5-20 was killed by its own <2 kill range. Any-margin mismatch: **11 of 45** scorable,
median 36 cp, max 161 cp. Play-out on the largest gaps: only **one** position shows a large, depth-stable ply cost
(S-F23, weakened by its own depth-16 re-test). S-F22/S-F23/S-F24. **The population does not show the defect at
anything like 155's severity.**

### CORRECTION (23:35Z) — S-F23 and S-F25 are WITHDRAWN; S-F20 stands

I ran the drawn-root experiment and it **refuted my own hypothesis, and with it my own S-F23 and S-F25.**

1. **The hypothesis test (S-F27).** Rebuilt with `FORGE_FIX_ROOT_DRAWN=0`: the four positions answer **identically**
   to the shipped build, every move and score. And it could not have mattered — `is_insufficient_material`,
   `is_repetition(3)` and `halfmove_clock>=100` are all false at those four roots, so the root adjudication never
   fires there.
2. **Why: there was no defect in those four positions.** In **all four**, the engine's chosen move captures the
   opponent's last material and forces an **immediate draw by insufficient material**; the "alternative" my metric
   preferred keeps the enemy material and **loses**. The engine was **right** in all four.
3. **My error (S-F28).** `plycost.py` treated more plies as better. In a bare-king ending the SHORTEST game over is a
   **draw** (best) and the longest is a **loss** — the sign convention was inverted for exactly the population I was
   measuring. **S-F23 is withdrawn** (the "four lose at once" cases are forced draws). **S-F25 is withdrawn as
   stated** (there was no wrong move at the match budget); what survives from that job is only that `go nodes 20000`
   and `go depth 16` agree on the move in 7 of 7 cases.
4. **S-F22's count stands but its interpretation changes**: the 0/50 strict result is now *stronger* than I reported,
   since the engine's choice was correct in the cases I actually examined. The 11 any-margin cases are unexamined
   and, on this evidence, likely also correct.
5. **S-F20 is unaffected and I re-verified it under the corrected lens.** In position 155 **both** moves continue the
   game (neither forces a draw) and both play-outs end in "black mates", so that comparison is loss-versus-loss where
   longer IS better — and the engine's own scores agree with the play-out (c6d6 cp −1142 vs c6c7 mate −11). S-F20
   rests on the engine contradicting its own score table, not on my flawed metric. **It remains the headline.**

**What the owner should take from this**: S-F20/S-F21 still stand; the population-rate claim is weaker than my job-11
report implied in the other direction — the four cases I put forward as worst were the engine getting it right. My
remaining honest position is that the strict defect is demonstrated on **one** position (155) and my scan did **not**
find others, with the caveat that the metric I used to look was broken.

### Area 3 — move generation (all CONFIRMED elsewhere where marked)

| id | claim | state | build / settings |
|---|---|---|---|
| S-F1 | perft 1-4 on 5,000 random positions: 20,000/20,000 equal to python-chess, root move SETS identical | **CONFIRMED by seat 08 (08-C5)** | base / none |
| S-F2 | 314 special positions (castling-transit, ep-pin, capture-promotion-check, double check, pinner-capture): perft 1-4 all equal | open | base / none |
| S-F3 | a raw ep capture exposing the owner's own king is never generated (14 real + 320 constructed + controls) | **CONFIRMED by seat 08 (08-C4)** | base / none |
| S-F4 | 320 constructed ep-pin positions: move sets equal 320/320, slider-removal control 320/320 | open | base / none |
| S-F5 | perft 5 equal on 230 positions, 1,150/1,150, sum 3,925,995,728 both sides | open | base / none |
| S-F6 | PC build's move generation node-for-node identical to base: 62,406/62,406 over five sets | open (file 6 cites it as settling the patch) | base vs PC r15 / none |
| S-F7 | PC20 options do not change perft (20,000/20,000 identical) | open | PC r15 / PC20 |
| S-F8 | the patch reproduces the PC's engine off-PC: all eight published numbers match | **CONFIRMED by seat 07 (07-C21)** | PC r15 / none, S14, PC20 |
| S-F9 | depth-8 move choice differs PC vs base in 4 of 200, all endgames (4/26 vs 0/174, p=0.0002) | open | base vs PC r15 / none |
| S-F10 | where the builds disagree, the PC's mate evidence is stronger | open | base vs PC r15 / none |
| S-F11 | the two bare-king rules cause 3 of the 4 endgame differences, both directions | open | base + 4 variants, base+patch / none |
| S-F12 | (155 needs a third r15 change) — **SUPERSEDED by S-F14** | withdrawn | — |
| S-F13 | the divergence set is exactly a subset of the 9 lone-king-root positions | open | base vs PC r15 / none |
| S-F14 | 155's difference is `LMR_CAP=1` **together with** `ONE_THREAD=0`, the shipped combination | open | base+patch 2x2 / none |
| S-F15 | at depth 20 the rules give 2 better, 1 worse, 1 undecided | open | base + r15 adjudicators / S14, PC20 |
| S-F16 | PC build plays a move it scores `mate -11` vs an alternative at `cp -1142` — with the corrected attribution (pre-existing, not a PC regression) | open | PC r15 / PC20 |
| S-F17 | that choice holds at depths 8-20; score becomes a mate against itself | open | PC r15 / PC20 |
| S-F18 | play-out verdict: `c6d6` is better (22 vs 20 plies, 3/3) | open | base / S14 |
| S-F19 | hash 16..1024 and depth 18..22 do not change the wrong choice | open | base / S14 |
| S-F22 | strict signature 0/50, any-margin 11/45 in 50 real-game lone-king positions | open | PC r15 / PC20, depth 16 |
| S-F23 | play-out ply cost — **WITHDRAWN (S-F28): the metric was unsound; the four "instant losses" are forced draws the engine was right to take** | withdrawn | PC r15 / PC20, d8 then d16 |
| S-F25 | wrong move at `go nodes 20000` — **WITHDRAWN AS STATED (S-F28): no wrong move existed; only the 7-of-7 node/depth agreement survives** | withdrawn | PC r15 / PC20 |
| S-F26 | cp 0 as a drawn-root bug — **REFUTED (S-F27/S-F28): the cp 0 was the engine being right (forced draws)** | refuted | PC r15 / PC20 |
| S-F27 | drawn-root fix off changes nothing on those four (and cannot, the predicate is false at those roots) | open | PC r15 w/ -DFORGE_FIX_ROOT_DRAWN=0 / PC20 |
| S-F28 | **withdrawal of S-F23/S-F25: my ply-count metric's sign was inverted for bare-king endings; S-F20 re-verified and stands** | self-correction, open | both builds |
| S-F24 | low-depth self-play cannot produce a varied lone-king population: 40 games all collapse to the same K+N vs K+N drawn position (cp 0, 492 nodes, python-chess says NOT insufficient material) — **a hand-rolled self-play endgame sample is not a sample at all** | open | PC r15 / S14, depth 6 |

### Checks I made of other seats

| id | verdict | of |
|---|---|---|
| 03-C1 | CONFIRMS, both halves, 20,000/20,000 twice | seat 13's S-F1 |

### Method and integrity notes (my own defects, all disclosed)

- HARNESS_AUDIT.md — 19-F12 (pipelined `quit`) audited across my harnesses; perft/bench proven immune and re-proved.
- PARSE_AUDIT.md — `assert_measured.py` fails loudly on a missing/NaN/zero result, with negative controls that fail;
  two real defects of mine recorded (honesty.sh's dead grep; an unsaved summary).
- WARM_STATE_AUDIT.md — perft is cold-equivalent (1,110,595 ten times in one process, after ucinewgame, after
  Clear Hash, and across ten processes) while the same harness shows the depth-search warm effect as a control.
- job10/METHOD_NOTE_quit_at_prompt.md — the quit trap in commands typed at a prompt (a gap my file-level audit left);
  no published number was affected, and why.
- Corrections I issued against myself: S-F12 superseded; S-F16's "base ranks them sanely" withdrawn (settings
  mismatch); S-F23 and S-F25 WITHDRAWN and S-F26 refuted (S-F27/S-F28 — my ply-count metric scored draws as losses);
  no prediction file before jobs 6/7/9/10 (four lapses, all recorded).

Branch tip at FINAL: see `git log` on for-fable-and-opus/swarm-03.
