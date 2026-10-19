# Forge development report — 2026-10-19

Accepted integration remains **9108d012526be80c6d163f7cab684e6acd9abf8d**.
Latest isolated candidate: **6.4.8**, source
**7125b3379a850de34041d42529cf95993607f93c**, on
`forge/root-effort-20261019`. No equal-clock Elo gain has been accepted, and
Stockfish superiority has not been demonstrated.

## Implemented and tested

| Candidate / source | Change | Verified result |
| --- | --- | --- |
| 6.4.5 / `82cd2c2` | Exact legal pawn witness before the unchanged fallback | Parent and candidate each passed 18,947 Boolean/state comparisons; exact parent search parity |
| 6.4.6 / `4e15dea` | Defer qsearch `gives_check()` until its use guard | Actual checked-evasion regressions and exact parent parity passed |
| 6.4.7 / `2c0c7ef` | Initialize direct-check masks only for quiet/evasion generation | 60,138 actual ordered-picker rows, 9,590,268 bytes, exactly match parent |
| 6.4.8 / `7125b337` | Key cumulative root effort by full Move identity | All 28 traced iterations match independent child-event sums; c3d5 correctly records 601 rather than 1,355 mixed nodes |

The first three changes avoid unnecessary work without changing the measured
untimed search behavior. The fourth repairs the input to time management: the
old cumulative ordinal could refer to different moves across iterations.
Actual changed timed stopping decisions have not yet been measured.

All four preserve the accepted residual NNUE and earlier candidate repairs.
Each passed **Release 8/8 and ASan/UBSan 8/8**, including core/perft, TT,
rule-50, legal-query, UCI, ponder and support-tool suites. Each passed seven
Windows checks under Wine and an independent package audit. The 6.4.8 standalone
audit passed 52/52; its offline bundle audit passed 43/43. Complete C++20 engines
compiled with GCC 14.2 and LLVM-MinGW Clang 23.1.3.

## Performance and strength

Exact cold/warm one-thread parity and benchmark signatures remain **419,798
nodes on Linux / 351,063 on Windows**. **NPS difference is unverified.** Shared-host
whole-engine and pinned-kernel A/A controls failed their noise gates. The separate
hosted benchmark A/A passed, but that protocol did not measure candidate NPS.
Fewer calculations and unchanged node signatures do not establish Elo.

[Hosted run 39325939081](https://github.com/couns0538-sketch/dwqww/actions/runs/39325939081)
compared **6.4.7 against 6.4.4** (`816423b1ddac23a00244449deef59dba736055a9`),
not against 6.4.8 or the accepted integration. Both used identical GCC 14 generic
x86-64-v3 builds on an EPYC 7763 host: Threads=1, Hash=32, OwnBook=false,
restart=on, serial paired fresh openings, equal **2+0.02** clocks. Both benchmark
A/A gates and eight readiness games passed. Preregistered logistic SPRT was
**[0,+5] Elo, alpha=beta=0.05**; the match reached its 16-minute cap.

The unchanged original PGN contains **147 normal completed games: 62 wins,
43 draws, 42 losses**. There are 73 complete pairs plus an orphan; game 148
started but has no PGN record. Strict whole-PGN acceptance fails. Independent
python-chess replay verified all 20,018 match plies and 1,048 readiness plies.

The **last native 144-game snapshot** reported 60 wins, 42 draws, 42 losses,
**+43.66 ±28.69 Elo**, LLR 0.79 (independently 0.789742). This earlier snapshot is
promising and descriptive, not a final 147-game estimate or an accepted gain.
The 73 complete pairs give descriptive GLR 0.815077, inside ±2.944439: **no H0/H1
decision**. No records were trimmed, reconstructed, pooled or resumed.

Two stop/quit warnings occurred during deadline shutdown; no pre-deadline engine
fault is attributed. Actual hosted executable bytes were not archived, and the
deadline path lacks a successful final frozen-input rehash. All 59 original
snapshot files match results commit
**1e9361d0e35a17c0d63a90d9431a6bb875d0817d** on
`results/hosted-strength-39325939081-1`. Original logs, PGNs, source/build hashes
and public observations are retained unchanged.

## Decision and deliverables

Retain all four correctness-tested candidates. **6.4.7 is SPRT-inconclusive;
6.4.8 has zero strength games.** No candidate was merged into accepted `9108d012`.
Failed fixtures, controls, packaging attempts and corrected audit false positives
remain saved. The [machine ledger](EXPERIMENTS.json) preserves all 76 experiments.

- [6.4.8 Windows Zen5 package](../releases/forge-6.4.8-candidate-windows-zen5.zip):
  SHA256 `4b4de385808f5a383aa60de6bfc09cf48c02e5d23c191624540026cdac95b55e`.
- [6.4.8 offline Windows validator](../releases/forge-6.4.8-windows-validation-bundle.zip):
  SHA256 `253f33c129c0f5d4301354f755e03e876c7a76c6da18e13307facaceba7b4e73`.
  Extract and run `run-validation.cmd`. Native A/A, pilot and SPRT remain pending;
  this compares 6.4.8 against the exact original 6.4 release.
- [Root-effort evidence](root-effort-20261019/STATUS.md),
  [hosted originals and audit](hosted-strength-20261019/STATUS.md),
  [current baseline](../docs/CURRENT_BASELINE.md),
  [next experiments](../docs/NEXT_EXPERIMENTS.md).

Next: preregister a longer 6.4.7 confirmation with fresh openings, complete-pair
headroom, archived executable bytes and final rehash even on interruption. Then
test 6.4.8 time management separately and run native Ryzen validation. No further
hosted job is scheduled. Environment draft revision 5 is saved; publication and
fresh-task restoration remain unverified.
