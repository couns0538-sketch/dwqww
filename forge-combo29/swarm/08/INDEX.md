# SEAT 08 — INDEX of everything in this folder

One page so a reader (Opus, or another seat) can find what they need without opening 373 files.

**Area 8 = THE CLOCK.** Build: base 6b98f217, and the PC r15 build (FABLE_TO_swarm_5's patch, sha256
`d6bd72c531f785f4`, applied to a separate worktree with `patch -p1 --fuzz=0`, built with
`-DFORGE_MATE_ALPHA_GUARD=1`). Settings: **PC20** = S14 + CuckooRep true, HistRework 2, TtPruneV2 true,
CorrHistV2 true, MateAlphaGuard true, OwnBook false; **Threads 1**, Hash 16, always.

## READ THESE FIRST
| file | what it is |
|---|---|
| `CLOCK_HEADLINE.md` (in `pc20/`) | **the clock work, headline.** Five shape classes, medians 161–853 ms, worst 1585 ms = the hard plan. Supersedes the three-position figures. |
| `OWNER_PAGE_clock.md` (in `pc20/`) | one page for the owner: four cases, each with a verdict and what was not measured |
| `FINDINGS.md` | 36 findings, 24 checks/audits/plants, 4 method lines, 1 withdrawal — the authoritative list |
| `STATUS.md` | the running log, newest last |

## THE HEADLINE NUMBERS (all Threads 1)
| quantity | value | where |
|---|---|---|
| typical move at 6 s + 0.06 | **184–338 ms** across classes = 3–6 % of the clock | `pc20/SHAPE_REFINED.md` |
| clock share per position | **2.5 %–13.7 %, median ~4 %** — a range, not a single number | `pc20/check_S13F10.md` |
| the tail | **confined to positions with ≤8 pieces**; p90 1164 ms, worst **1585 ms = the hard plan** | `pc20/SHAPE_REFINED.md` |
| clock ever exceeded | **0 of 400** (planted: `pc20/plant_zeros.txt`) | 08-F7, 08-C12 |
| clock over a LONG game | **0 flags in 600 moves**; the clock stabilises at 1438-1744 ms | 08-F34, `pc20/REPORT_drain_to_flag.md` |
| worst boards at the lowest clocks | **0 flags in 21 cells** down to 200 ms — the plan shrinks with the clock | 08-F35 |
| `movetime T` | spends **T − 10 ms** on the wall clock (plant-clean) | 08-F2, `job4/` |
| the PC build vs base | clock behaviour **identical** within 1.4 % at every control | 08-F16, `pc20/REPORT_pc20.md` |

## THE FIVE MOST USEFUL SINGLE RESULTS
1. **`MateAlphaGuard true` alone fixes the mate distance; `CuckooRep true` alone makes it worse.** `pc20/check_SWITCHES.md` — the one-switch answer for the owner.
2. **The 2nd/3rd-occurrence and 100-half-move draws are not defects** (the match program ends the game), and the boundary is now measured from both sides: my retraction `pc20/WITHDRAWAL_fifty_move.md` (15 plies needed, 9 left → correct draw) and `pc20/check_S12F14.md` (1 ply needed, 1 left → a real miss).
3. **A mid-search `setoption` silently stops the search**, exactly like `stop` — a measurement-integrity fact for the whole swarm. `pc20/check_S12F12.md`.
4. **Zeros are planted.** `pc20/plant_check.py` (0-of-60), `pc20/plant_zeros.py` (0-of-400 / 0-of-800), `pc20/plant_tiny_clock.py` (tiny clocks). Ledger: 08-C13.
5. **`softnodes N` is deterministic and overshoots N by 1.3–2.1x** — the owner's self-play path. `softnodes/`.
6. **The engine does not flag on the owner's control**: 600 moves with a draining clock gave 0 overruns and a
   stable clock floor, and the worst boards give 0 overruns even at 200 ms because the plan shrinks with the clock
   (`pc20/REPORT_drain_to_flag.md`).

## THE FOUR METHOD RULES (top of `FINDINGS.md`, each with its instance)
1. A summary I typed is not evidence, and a small sample is not a population (3 instances, 08-N1).
2. A timeout mechanism must be proved against a case known to return quickly before it may declare a hang (08-N2).
3. A count from a different scale is not a cost (mate ≠ 30000 cp; and the 72/360 vs 117/585 case where both numbers
   were right but the REGIME was missing: `pc20/PLAN_TABLE.md`).
4. A static analyser of your own code is a heuristic; open the flagged file before believing it (08-N4 — my ordering
   audit gave two false positives).

## FOLDER MAP
| folder | contents |
|---|---|
| `job1/`, `job1b/` | the latency work: movetime/clock controls, SEED 811 re-run, the timing harnesses |
| `job2/` | very little time (wtime 100…0), the reserve-empty probe |
| `job3/` | `movestogo`, plan vs achieved |
| `job4/` | the two stop paths reconciled (with seat 16), undershoot by depth ladder |
| `job5/` | the clock-tail sweep 200 ms…30 s, overshoot-vs-one-iteration, cold-vs-warm |
| `job6/` | opening book width, book contamination audit, honesty pins under both OwnBook settings |
| `pc20/` | **the PC build's work**: build report, the re-run of every finding under PC20, all confirmations of other seats, all plants, the owner page, `PLAN_TABLE.md` (computed plan numbers), `INDEX`-linked reports |
| `pcbuild/` | the patch application and the 8 known numbers |
| `softnodes/` | `go softnodes N` determinism and overshoot |
| `honesty/` | the original four pins |

## WHAT IS NOT HERE
- No game was ever played: every clock figure is single searches from fixed boards, not a match. Strength questions
  are explicitly out of scope in every file that touches them.
- No sanitizer build of the PC engine.
- The PC's own trained net is not shared, so every evaluation-dependent result here used the built-in net.
