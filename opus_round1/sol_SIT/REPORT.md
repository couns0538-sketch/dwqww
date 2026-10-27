# S-IT Intended-threefold claim (FIDE 9.2.1, GitHub issue #7), UCI `IntendedThreefold` (default false) — DONE (NPS cost: see below)

**Branch.** `opus-sol-SIT` = `d4f4312` (AL1 s198 lock tree) + `0d99f02` cherry-picked + this job. It is a fresh
implementation from the issue text, not the issue's run38-run49 lineage code. No Elo claim; UNPROVEN until gated.

## What it does
- **The claim.** `Board::can_claim_threefold_by_next_move()` asks whether the side to move has a legal quiet
  non-pawn move whose exact resulting key occurred at least twice before. It counts only genuine reversible
  history after the most recent null move, on the right side-to-move parity, and needs an exact duplicated key
  first (a 64-bucket mask only skips comparisons).
- **Search use.** With `IntendedThreefold=true`, non-root search and quiescence treat the right as a floor at the
  existing draw score 0:
  - `beta <= 0` returns 0;
  - otherwise alpha is raised to 0 and the node returns `max(value, 0)`, so a mate still wins (mate precedence).
- **TT.** At such a node no TT score is used (no cutoff, no eval refinement), nothing is stored (main, stand-pat
  and ProbCut stores), and correction history is not taught.
- **Root.** The root is not claimed: there is no UCI draw-claim action. Details: `README.md`.

## Acceptance
| requirement (user / issue #7) | result | evidence |
|---|---|---|
| `Board::can_claim_threefold_by_next_move()` | **PASS**. Issue fixture: the positive history claims and the control does not; same FEN without history: no claim. The query leaves the board unchanged; history before a null move is not scanned and undo restores the claim. Lost castling rights make positions differ. A random cross-check against a make_move() brute-force reference: **11,720 positions, 801 claims, 0 mismatches** | `logs/step2_unit_tests.log` |
| used in qsearch and non-root search, UCI option default OFF | **PASS**. `option name IntendedThreefold type check default false`; true/false/invalid handled | `logs/step4_uci_regression.log` |
| issue test: FEN `8/7k/8/8/8/8/8/K1R5 w - - 0 1`, positive history 0 cp, control unchanged | **PASS**. Non-root qsearch, full window: positive **−391 → 0** with the option, control −391 both ways. UCI `go depth 1 searchmoves a2a1`: positive **+391 (off) → 0 (on)**; control +391 both ways; depths 2, 4, 6 on vs off equal for the control (390, 390, 394) | `logs/step2_unit_tests.log`, `logs/step6_issue_uci_matrix.log` |
| reuse the draw score, keep mate precedence | **PASS**. A claim node whose side to move mates in one returns the mate score (31998) with the option on and off | `logs/step2_unit_tests.log` |
| no TT store / cut at claim-sensitive nodes | **PASS**. TT warmed by the control history (same key), then the positive history with null windows (0,1), (100,101), (−50,−49) at depths 0-2: always the floor, never the cached −391/−390. The claim node stores no entry; the control after a positive search equals a fresh search | `logs/step2_unit_tests.log` |
| floor semantics over windows | **PASS**. Depths 0-2 × 6 windows: positive in [0, alpha] when the window is above 0, exactly 0 otherwise (= max(0, off) at full window); control identical on/off | same |
| planted bugs | **PASS 6/6 caught**: qsearch TT cut, search TT cut, claim as a forced draw (mate lost), null-move boundary ignored, TT store at claim nodes, twofold instead of threefold | `logs/step3_mutants.log`, `mutate_sit.py` |
| option OFF: bench and perft identical | **PASS**. Box recipe: bench 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, ALL OK; FMA 0 | `logs/step1_build_identity_off.log` |
| CTest | **PASS**. 15 tests: everything passes except the 4 known `forge_tests` lines (known-failure check PASS); new `forge_intended_threefold_tests` PASS; `uci_regression` PASS | `logs/step5_ctest.log` |
| NPS cost | **measured, see below** | `logs/step7_*`, `logs/step8_*` |

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
- The PC numbers were taken under unusually heavy, changing load. The quiet-runner A/B (`ci_sit.sh`, 10 runs per
  side, workflow `opus-sol-sit-ci`) is the measurement to quote. Result: pending CI on this push.

## Limitations / UNVERIFIED
- History-dependent values can still reach TT entries of ancestor nodes, as with ordinary repetition draws. The
  issue states the same limit; it is not solved here.
- The root position's own claim right is not used (no UCI claim action); a root search still finds the draw by
  searching the claim move at depth >= 1.
- No gate; no Elo claim. The NPS cost on a quiet machine: CI (pending).

## Files
- Engine: `include/forge/board.hpp`, `src/board.cpp`, `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`.
- Tests: `tests/intended_threefold_tests.cpp` (CTest `forge_intended_threefold_tests`), `tools/uci_regression.py`
  (process-level checks), `CMakeLists.txt`.
- CI: `.github/workflows/opus-sol-sit-ci.yml`, `opus_round1/sol_SIT/ci_sit.sh`.
- `opus_round1/sol_SIT/`: `README.md`, `IDEA_SOURCE.md`, `REPORT.md`, `nps_ab_opts.py`, `mutate_sit.py`,
  `ci_sit.sh`, `logs/`, `FILES.txt`, `SHA256SUMS`.
- Machine exclusive: no.
