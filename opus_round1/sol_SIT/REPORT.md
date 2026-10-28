# S-IT Intended-threefold claim (FIDE 9.2.1, GitHub issue #7), UCI `IntendedThreefold` (default false) — DONE

**Branch.** `opus-sol-SIT` = `d4f4312` (AL1 s198 lock tree) + `0d99f02` cherry-picked + this job (`edc2519`, report
`fc3bd2a`) + the code-review follow-up (`027c7e7`, evidence `1a85ce3`). It is a fresh implementation from the issue
text, not the issue's run38-run49 lineage code. No Elo claim; UNPROVEN until gated.

## What it does
- **The claim.** `Board::can_claim_threefold_by_next_move()` asks whether the side to move has a legal quiet
  non-pawn move whose exact resulting key occurred at least twice before. It counts only genuine reversible
  history after the most recent null move, on the right side-to-move parity. It first collects every key that
  occurs at least twice in that window (exact matches; bucket masks only skip comparisons) and stops if there is
  none. Otherwise it walks the quiet moves of knights, bishops, rooks, queens and the king, builds each resulting
  key incrementally, looks it up in that set and tests legality only on a hit.
- **Search use.** With `IntendedThreefold=true`, non-root search and quiescence treat the right as a floor at the
  existing draw score 0:
  - `beta <= 0` returns 0;
  - otherwise alpha is raised to 0 and the node returns `max(value, 0)`, so a mate still wins (mate precedence);
  - in search() a window (a, 1) with a < 0 is searched as the null window (0, 1) it became, and a node whose alpha
    the floor raised gives the parent's move no fail-low continuation bonus.
- **TT.** At such a node no TT score is used (no cutoff, no eval refinement), no score is stored (main, stand-pat
  and ProbCut stores), and correction history is not taught. The main stores of search() and qsearch() keep a
  placeholder: the best move and the static evaluation with the raw score `ValueNone`, BoundUpper, depth 0,
  written only into an empty slot or over an earlier placeholder.
- **Root.** The root is not claimed: there is no UCI draw-claim action. Details: `README.md`.

## Acceptance
| requirement (user / issue #7) | result | evidence |
|---|---|---|
| `Board::can_claim_threefold_by_next_move()` | **PASS**. Issue fixture: the positive history claims and the control does not; same FEN without history: no claim. The query leaves the board unchanged; history before a null move is not scanned and undo restores the claim. Lost castling rights make positions differ. A random cross-check against a make_move() brute-force reference: **11,720 positions, 801 claims, 0 mismatches** (unchanged with the follow-up's set-based check) | `logs/step2_unit_tests.log`, `logs/followup2_unit_tests.log` |
| used in qsearch and non-root search, UCI option default OFF | **PASS**. `option name IntendedThreefold type check default false`; true/false/invalid handled | `logs/step4_uci_regression.log`, `logs/followup4_uci_regression.log` |
| issue test: FEN `8/7k/8/8/8/8/8/K1R5 w - - 0 1`, positive history 0 cp, control unchanged | **PASS**. Non-root qsearch, full window: positive **−391 → 0** with the option, control −391 both ways. UCI `go depth 1 searchmoves a2a1`: positive **+391 (off) → 0 (on)**; control +391 both ways; depths 2, 4, 6 on vs off equal for the control (390, 390, 394); same numbers on the follow-up exe | `logs/step2_unit_tests.log`, `logs/step6_issue_uci_matrix.log`, `logs/followup10_issue_uci_matrix.log` |
| reuse the draw score, keep mate precedence | **PASS**. A claim node whose side to move mates in one returns the mate score (31998) with the option on and off. With material for the claimer the claim stays a floor: QC (Rc8xc1+ wins the queen) 424/424/441 cp at depths 0/1/2, option on = off | `logs/step2_unit_tests.log`, `logs/followup2_unit_tests.log` |
| no TT store / cut at claim-sensitive nodes | **PASS**. TT warmed by the control history (same key), then the positive history with null windows (0,1), (100,101), (−50,−49) at depths 0-2: always the floor, never the cached −391/−390. No store path writes a score at a claim node (final stores at depths 0-3 × 5 windows, stand pat, ProbCut). The placeholder, copied alone into an empty table, leaves the control equal to a fresh search. Synthetic ValueNone entries (every bound, depth 60) never change a search | `logs/step2_unit_tests.log`, `logs/followup2_unit_tests.log` |
| floor semantics over windows | **PASS**. Depths 0-2 × 8 windows (incl. (−1,1), (−50,1)): positive in [0, alpha] when the window is above 0, exactly 0 otherwise (= max(0, off) at full window); control identical on/off. QR (rook against queen; the claiming move is pruned): 0 at depths 1-3 × 4 windows, option off −242/−250/−274 | same |
| planted bugs | **PASS 20/20** (`mutate_sit.py`: the original 6, patterns updated, + 14 for the review findings) and the reviewer's own generators **7/7** (5 single guards, qsearch forced draw, five guards at once) | `logs/followup3_mutants.log` (first run 6/6: `logs/step3_mutants.log`) |
| option OFF: bench and perft identical | **PASS**. Box recipe: bench 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, ALL OK; FMA 0. Follow-up build too (sha256 `0a570a83…`, 0 warnings); CI release and quiet runner ALL OK | `logs/step1_build_identity_off.log`, `logs/followup1_build_identity_off.log`, `logs/ci_40520727413/identity_sit_off.log` |
| CTest | **PASS**. 15 tests: everything passes except the 4 known `forge_tests` lines (known-failure check PASS); `forge_intended_threefold_tests` (288 checks) PASS; `uci_regression` PASS; CI release, ASan and TSan known-only | `logs/step5_ctest.log`, `logs/followup5_ctest.log` |
| NPS cost | **measured: no cost** with the option off, and on bench with the option on (quiet runner, CIs include 0). Shuffling positions with duplicated keys (code review): option-on cost 1.34x / 1.71x CPU per node before the follow-up, 1.15x / 1.17x after (PC); 1.10x / 1.15x on the quiet runner | below, `logs/step7_*`, `logs/step8_*`, `logs/followup6*`, `logs/ci_40520727413/` |

## NPS cost (advisory; no speed claim)
The PC runs used `nps_ab_opts.py` (ABBA, 8 runs per side, bench d16/d20, Threads 1, Hash 16, Idle priority) on the
loaded PC: a conc-8 gate, NNUE training, self-play and 7 sub-agents starting builds.

| comparison | d16 CPU-time NPS | d20 CPU-time NPS | wall NPS |
|---|---|---|---|
| same binary, option on vs off | −1.29% (95% CI −3.31 .. +0.74) | −1.44% (−3.88 .. +0.99) | −0.8% / −3.5%, wide CIs |
| option-off build vs lock exe | −4.41% (−7.79 .. −1.02) | −5.68% (−7.12 .. −4.25) | −0.2% (±7.5) / −10.3% (−20.7 .. +0.1) |

- Nodes are identical in every run: bench positions have no game history, so no claim can fire. With the option
  on, the cost is the per-node scan.
- The option-off build grew: qsearch 4080 → 4480 bytes, search 12304 → 12576 bytes; search moved from 32 to 48
  bytes mod 64 (`logs/step8_hot_function_sizes_pc.log`). A real layout cost is possible.
- The PC numbers were taken under unusually heavy, changing load. The quiet-runner A/B is the measurement to
  quote.

**Quiet runner (the measurement to quote).** Workflow `opus-sol-sit-ci` run 40504311743 on `edc2519`, AMD EPYC
7763, `ci_sit.sh`, 10 ABBA runs per side, nodes identical:

| comparison | d16 CPU-time NPS | d20 CPU-time NPS |
|---|---|---|
| option-off build vs lock (same g++-14 Release flags) | +0.06% (95% CI −0.70 .. +0.81) | +0.59% (+0.01 .. +1.17) |
| same binary, option on vs off | +0.00% (−0.77 .. +0.78) | −0.25% (−1.36 .. +0.87) |

- **Option off:** no cost. The PC's −4.4/−5.7% came from the load, not the code.
- **Option on:** no measurable cost on the bench positions. With no game history the scan almost always stops at
  the span or duplicate check. Games with long reversible histories run the full check more often: the code review
  measured 1.4-1.6x CPU per node there; the follow-up below reduces it.
- On Linux the code grew too: qsearch 4233 → 4716 bytes, search 12737 → 12912 bytes.
- opus-ci run 40504311593 on the same push: release identity ALL OK, ctest known-only; ASan and TSan known-only,
  0 sanitizer reports.

**Quiet runner after the follow-up.** Workflow `opus-sol-sit-ci` run 40520727413 on `027c7e7`, 10 ABBA runs per
side, nodes identical (`logs/ci_40520727413/`):

| comparison | d16 CPU-time NPS | d20 CPU-time NPS |
|---|---|---|
| option-off build vs lock | +0.41% (95% CI −2.80 .. +3.63) | −0.40% (−5.72 .. +4.91) |
| same binary, option on vs off (bench) | −0.29% (−2.53 .. +1.94) | −1.53% (−3.46 .. +0.40) |

- The runner was noisier than in run 40504311743 (wider CIs); every CI includes 0.
- Claim-check cost on the review's shuffling positions (`perf_claim_ab.py --same-tree`, same binary, 6 rounds,
  identical trees on/off), on/off CPU NPS:
  - shuffle_hist 0.906 (1.10x CPU per node);
  - walk34_castle 0.871 (1.15x);
  - longwalk_hist 0.995;
  - shuffle_nohist 1.002.
- Linux code size: qsearch 4233 (lock) → 4918, search 12737 → 13028 bytes.
- opus-ci run 40520727160 on `027c7e7`: release identity ALL OK, FMA 0, ctest known-only; ASan and TSan
  known-only, 0 sanitizer reports.

## Code-review follow-up (`027c7e7`)
The review of `fc3bd2a` (scratch evidence `F:\opus_scratch\review_sit`) found seven issues. All are fixed. Option
off stays the lock (bench/perft ALL OK, FMA 0).

| # | finding | change | evidence |
|---|---|---|---|
| 1 | **Perf** (`board.cpp`): any duplicated key in the window made each check run full pseudo-legal movegen plus an O(window) history rescan per quiet non-pawn move (1.4-1.6x CPU per node in shuffling positions) | The pre-check collects every key that occurs twice; an empty set means no claim. Only the quiet moves of N/B/R/Q/K are walked (no MoveList, no pawn/capture/castling generation). Each resulting key is built incrementally and looked up in the set (64-bit bucket mask first); legality is tested only on a hit. The semantics are unchanged: cross-check 11,720/801/0, and a build with only this change searches the same trees as the old code in all 8 probe positions, option off and on (claims fire in 4 of them) | `logs/followup2_unit_tests.log`, `logs/followup6b_claim_cost_isolation_pc.log`, `logs/followup6_claim_cost_pc.log`, `logs/followup8_claim_call_micro.log` |
| 2 | **Test gap**: every fixture gave the claimer a bare king, so deleting the search() floor or a forced draw in qsearch passed all 67 checks | Fixtures with material: QR (the claiming Rb8-b7 is pruned at depth 1, so only the floor gives 0), QC (Rc8xc1+ keeps 424 cp), WC (white queen against rook). Guard tests: final stores (depths 0-3 × 5 windows), stand pat (WC), ProbCut (QC, depths 5-6, null windows), correction history (WC, with an option-off sanity check). 67 → 288 checks. `uci_regression.py`: QR `go depth 2 searchmoves a2a1` gives 0 cp on (242 off); QC `go depth 1` gives −424 on = off. The reviewer's mutant engines now fail it (QR 250, QC 0) | `logs/followup2_unit_tests.log`, `logs/followup3_mutants.log`, `logs/followup4_uci_regression.log` |
| 3 | **Tooling**: `uci_regression.py` asserted the option in the handshake and ran its block unconditionally, so it aborted on older engines | Both are gated on the option being advertised; otherwise a note on stderr and `"skipped"` in the JSON. Lock copy (`5d4df7f1…`) with `--known-v56`: rc 0; follow-up exe: rc 0 | `logs/followup4_uci_regression.log` |
| 4 | **CI**: the exit status of the `python3 … \| tee` pipelines in `ci_sit.sh` was never checked | `PIPESTATUS[0]` is checked after uci_check.py, both NPS runs and the new claim-cost run. Replica of the script's own lines with a python3 stub exiting 1: old script status 0, new status 1 | `logs/followup7_ci_exit_replica.log` |
| 5 | **Search**: claim nodes skipped every TT store, so they had no hash move (IIR on every PV/cut visit) and recomputed the eval | Placeholder in the main stores (see "What it does"), never written over an entry with a score; audit below. Tests: placeholder format; the placeholder copied alone into an empty table leaves the control equal to a fresh search (depths 0-3 × 5 windows); synthetic ValueNone entries (Upper/Lower/Exact, depth 60, null-move pruning live) equal a fresh search at depths 0-8 × 4 windows, and with a hash move give the same value for every bound; a claim node re-searched over its own placeholder keeps the floor. Mutants caught: real score in the placeholder (qsearch, search), ValueNone passed through score_to_tt | `logs/followup2_unit_tests.log`, `logs/followup3_mutants.log` |
| 6 | **Latent**: with `FailLowContinuationBonus > 0`, a PV claim node whose moves all score ≤ the raised alpha gave the parent's quiet move the fail-low bonus | No bonus when the floor raised alpha. Test with the tunable at 100, window (−100,100): the parent entry stays 0 (old code: 36 at depth 1, 144 at depth 2). Real fail lows (window (50,100), option off and on) still get it | `logs/followup2_unit_tests.log`, `logs/followup2b_old_engine_with_new_tests.log` |
| 7 | **Minor**: pv_node came from the original window; (a, 1) collapses to (0, 1) but kept PV treatment | `pv_node` is recomputed in the claim branch (two lines: const → mutable plus one assignment). Values cannot change: the node then runs the same code as a node entered with (0, 1), which the old code already ran. Its PV is empty whenever the parent uses it (a move above 0 fails high), and the bound and store that read pv_node are the skipped or placeholder ones. Option-off paths are unchanged (bench identity) | windows (−1,1), (−50,1) in `logs/followup2_unit_tests.log` |

**TT audit (finding 5)**, `src/search.cpp` at `027c7e7`:
- **Probe reads ValueNone.** `score_from_tt()` (l.119) returns ValueNone for a raw ValueNone before any mate
  adjustment. Both probes (qsearch l.803, search l.950) therefore read `tt_score == ValueNone`, whatever the
  bound, depth and rule-50 clock.
- **Score uses all need a score.** Every use requires `tt_score != ValueNone`:
  - qsearch cutoff (l.807) and eval refinement (l.823);
  - search cutoff (l.957) and eval refinement (l.974);
  - ProbCut veto (l.1039);
  - singular extension (l.1127-1128), which also excludes BoundUpper; the `tt_score >= beta` at l.1145 is inside
    that branch.
- **Null-move veto.** It reads the bound together with `tt_score < beta` (l.1004). beta ≤ Infinite (32001) <
  ValueNone (32002), so it never fires.
- **Other fields are heuristics.** The move (MovePicker after `is_pseudo_legal`, IIR, `tt_capture`, the singular
  gate), the raw static evaluation (position-only; ValueNone in check, then recomputed), the PV flag (LMR).
- **No other readers.** No other TT reader exists; the remaining `probe(` calls in uci.cpp are opening-book probes.
- **The score_to_tt trap.** Passing ValueNone through `score_to_tt` would store 32002 + ply, a mate-like score
  when probed at another ply. Mutant `placeholder_via_score_to_tt` is caught.

**Claim-check cost (PC, advisory).** `perf_claim_ab.py` setup:
- Idle priority, CPU time from GetProcessTimes, Threads 1, Hash 16, `go depth N`, 4 rotating rounds.
- old = `fc3bd2a` box build, final = follow-up box build; loaded PC.

| position (from the review) | depth | nodes (old = final, off = on) | on/off CPU NPS, old | on/off, final | option-on CPU NPS old → final |
|---|---|---|---|---|---|
| shuffle_hist: `rn2k1nr/8/1p1p1p1p/pPpPpPpP/P1P1P1P1/8/8/RN2K1NR w KQkq - 0 1 moves b1c3 b8c6 c3b1 c6b8 b1c3 b8c6 c3b1 e8f8 e1f1` | 22 | 1,629,687 | 0.746 (1.34x CPU/node) | 0.871 (1.15x) | 1,830k → 2,162k |
| walk34_castle (review verifier's 34-ply walk, 6 duplicated keys) | 25 | 1,707,300 | 0.586 (1.71x) | 0.858 (1.17x) | 1,253k → 1,782k |
| shuffle_nohist (same root, no history) | 22 | 1,629,687 | 0.977 | 0.971 | — |
| longwalk_hist (62-ply knight walk) | 23 | 1,608,185 | 0.980 | 0.981 | — |

- **Finding 1 alone** (board change only) already searches the old trees in all 8 positions, off and on. It moves
  shuffle_hist on/off 0.787 → 0.878 and walk34_castle 0.605 → 0.805 (`logs/followup6b_…`).
- **Bucket mask over the set:** about +5% option-on NPS in walk34_castle, same trees (`logs/followup6c_…`).
- **Per call** (the review's `micro/claim_cost.cpp`, unchanged):

  | case | old | final |
  |---|---|---|
  | rook endgame, claim | 77 ns | 28 ns |
  | rook endgame, duplicate without claim | 95 ns | 32 ns |
  | middlegame, duplicate without claim | 202 ns | 65 ns |
  | middlegame, claim | 164 ns | 54 ns |
  | no duplicate (early exit) | 4.3 ns | 5.2 ns |

  One `generate_pseudo_legal` call costs about 66 ns.
- **Claim positions:** where claims fire, option-on trees change by design (findings 5 and 7: hash moves stop IIR at
  claim nodes; collapsed windows):

  | position | depth | nodes, old → final |
  |---|---|---|
  | issue_positive | 26 | 2,089,944 → 696,121 |
  | middlegame_dup | 18 | 940,607 → 2,237,930 |
  | rook_walk41 | 44 | 169,579 → 166,781 |
  | review_qr | 28 | unchanged |

  Fixed-depth node counts are not a strength measure; no Elo claim. With the option off, trees are identical
  everywhere.
- **Box-build code size:** `can_claim_threefold_by_next_move` 752 → 9,392 bytes (five inlined per-piece walks);
  `Worker::qsearch` 4,480 → 4,688 and `Worker::search` 12,576 → 12,656 bytes (placeholder branches)
  (`logs/followup9_hot_function_sizes_pc.log`).

**Not mutated (equivalent by construction):**
- **Legality test on a claim hit.** A position reached by an illegal move never occurred in a legal history.
- **Castling rights dropped by the claiming move.** The resulting position has fewer rights than every window
  position, and the same placement with the old rights never occurs either. A mutant that kept the old rights
  survived (`logs/followup3_mutants.log` (c)) and was replaced by `castling_base`.
- **pv_node recompute.** Values are unchanged by design.

**Process notes (main session, from the sub-agent's hand-back).** The review fixes were made by a sub-agent. Two edit
scripts mangled by a Bash heredoc (a known PC quirk with backslashes) were caught before commit and redone. The
reviewer's folder was only read; its generator scripts wrote to new folders. Nothing was deleted or killed.

## Limitations / UNVERIFIED
- History-dependent values can still reach TT entries of ancestor nodes, as with ordinary repetition draws. The
  issue states the same limit; it is not solved here.
  - Test evidence: after the positive search at depth 2, the control with window (0,1) on the same table returns 0
    instead of the fresh −390. The old code does the same (INFO line in `logs/followup2_unit_tests.log` and
    `logs/followup2b_old_engine_with_new_tests.log`).
  - Only the claim node's own entry is clean (placeholder).
- The root position's own claim right is not used (no UCI claim action); a root search still finds the draw by
  searching the claim move at depth >= 1.
- In shuffling positions with duplicated keys, the option on still costs about 1.10-1.17x CPU per node: the set
  collection and the quiet-move walk run at every node of such a subtree.
- Finding 7's fix is two lines (const → mutable plus the recompute), not one; it only runs in the claim branch.
- No gate; no Elo claim.

## Files
- Engine: `include/forge/board.hpp`, `src/board.cpp`, `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`.
- Tests: `tests/intended_threefold_tests.cpp` (CTest `forge_intended_threefold_tests`, 288 checks),
  `tools/uci_regression.py` (process-level checks; the IntendedThreefold part runs only when the option is
  advertised), `CMakeLists.txt`.
- CI: `.github/workflows/opus-sol-sit-ci.yml`, `opus_round1/sol_SIT/ci_sit.sh`.
- `opus_round1/sol_SIT/`:
  - `README.md`, `IDEA_SOURCE.md`, `REPORT.md`, `nps_ab_opts.py`, `mutate_sit.py`, `ci_sit.sh`;
  - follow-up tools: `build_unit_tests.sh`, `run_mutants.sh`, `perf_claim_ab.py`, `ci_exit_check.sh`,
    `issue_uci_matrix.py`;
  - `logs/`: `step*` first run, `followup*` code review, `ci_*` quiet runner;
  - `FILES.txt`, `SHA256SUMS`.
- Machine exclusive: no.
