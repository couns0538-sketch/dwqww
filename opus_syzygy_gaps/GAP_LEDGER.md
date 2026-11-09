# Syzygy gap ledger (P6 integration) - job opus-syzygy-gaps-20261107

Status words: RED (failing fixture on the parent, gap proven), CLOSED (fix + fixture GREEN + qualification, see BENCH.md), LIMIT (documented, not fixed), REJECTED (checked, no gap), UNVERIFIED
(evidence absent; absence of evidence is not a gap). Numbers: parent = plain build of the P6 tree, same nodes as kit exe 150374ff; candidate = current head with the switch named. All evidence
paths are under `logs/` in this pack or `out/` in the job root, listed in BENCH.md.

Parent for all rows: lock source d4f43124 + `opus_r13/p6/syzygy_port.patch` (md5 4342d24f) = kit exe 150374ff.
Gate outcome for all rows: P6 gates USYZP / USYZPD4 (+ held confirms; idx 221-224 in QA's dry-run manifest, 230-233 in the current `forge_gates.json`) have **no result**: 0 rows in FORGE_RESULTS.csv,
0 hits in forge_queue.log and in forge_queue_state.json attempts, no gate folder on C:/D:/E:/F:. Owner of gates and reservations (srand / openings of the confirms): QA. The only related result is R5C-N3, a
bundle with two other options, H0 (-26.61 nElo in 1126 games), not attributable to Syzygy. Nothing here says that the fixes gain strength.

| id | mechanism | gap | switch | evidence on the parent | evidence with the switch | status |
|---|---|---|---|---|---|---|
| G2 | TB-aware score bounds | shallow pruning keeps running while `best_score` is a TB loss, as the mate-loss band does not. The fail-soft TB loss is stored as an upper bound and reaches parents and the TT as a false TB win | `SyzygyTbBounds` bit 1 | 3000 roots above the tables, depth 10: 2991 of 10114 pruned TB-loss fail-lows wrong at the node; downstream 3532 false TB wins at node ends, 2700 + 1476 wrong TT cuts. Clock fixture: 85761 of 132694 pruned fail-lows wrong in 5678 of 19905 roots. Sample of 40 checked by python-chess and Fathom | 0 wrong at every site | CLOSED |
| G3 | TB-aware score bounds | correction history learns from TB-band best scores (clamped maximum update); mate scores are excluded | `SyzygyTbBounds` bit 2 | 96932 of 4414593 updates came from TB-band scores | 0 | CLOSED; harm not measured apart |
| G1 | TB-aware score bounds | a null move returns a TB-band score as a proven bound; mate scores are replaced by beta | `SyzygyTbBounds` bit 4 | after bit 1 and 2 still 12 wrong returned null cuts in 8 of 1250 roots two plies before a mutual zugzwang, plus false TB losses at their parents (R2 finding 1; my first fixture was one ply too shallow and could not show it) | 0 at depth 16, +0.03 % nodes | CLOSED |
| G5 | root DTZ | a root at exactly dtz + counter = 100: an exact win is shown as cursed (+2); a rounded loser move that really draws is mixed with moves that lose and shown as a TB loss; a rounded winner move that really draws is mixed with one that wins (R1 findings 1 and 3). A result is lost | `SyzygyRootExact` bits 1 and 2 | exact oracle, 2455 judged roots: 197 kept moves give up the result, 260 wrong reports; engine 26 wrong moves; 5 of 800 replays against an oracle opponent lose a draw. Table rule: 733 + 618 wrong reports on clock and promo fixtures | 0 kept moves wrong among decided roots, 0 wrong reports, 0 lost replays; 54 of 2455 roots undecided (search score shown), 3 engine moves worse there | CLOSED; undecided roots: LIMIT below |
| G6 | root DTZ / rule 50 | WDL-only ranks (DTZ table missing) report a TB win or loss at counter > 0, and at counter 0 when the root is cursed | `SyzygyRootExact` bit 1 | 2186 false TB wins, 2169 false TB losses shown on the clock fixture; 8 wrong on the clock-0 fixture; engine: 41 and 10 false TB root scores on partial table folders | 0 | CLOSED; move filter: LIMIT below |
| G7 | rule 50 | a TB-band or mate TT score is used at a clock where it cannot be completed before move 100; and a TB loss distance understates the longest line when that line ends in a mate, because a loser prefers any TB loss to any mate | `SyzygyRule50` bit 1 | warm table, 3000 roots: 1842 wrong TT cuts with bounds on; root level 5 false TB claims in 3000 rows; a drawn root is lost: `8/q7/8/8/8/3Q1RK1/k7/8 b - - 87 44` plays a7c7 (R2 finding 2). Cold, clock fixture: 5 wrong TT cuts | warm interior 0 returned at every site, root level 0 false in 3000 rows; cost: 288 true warm claims in the control rows against 308 on the parent (cold 292); the same FEN keeps the draw | CLOSED, see BENCH.md |
| G8 | rule 50 | changing `Syzygy50MoveRule` keeps TB scores stored under the other rule | `SyzygyRule50` bit 2 | 400 roots: 101 + 57 rows get another TB class than after a Clear Hash | 0, node-identical to a manual Clear Hash | CLOSED |

## Limits (documented, not fixed)
- **Boundary walk budget.** `SyzygyRootExact` bit 2 tries at most 1000 moves per root. A boundary root it cannot decide (54 of 2455 judged) keeps its possibly drawing or winning moves and reports the search score. No false claim, but the search may pick a worse one of the undecided moves (33 kept moves are worse, 3 engine moves at depth 8). A rejected two-phase variant at budget 2000 reached 32 undecided at 83 ms against 54 at 34 ms here; the budget stays low because the walk runs inside `go`.
- **Partial table sets at the boundary.** A walk that meets a missing table cannot decide its move: it stays undecided, as above, and may use the whole budget on retries.
- **WDL-only move filter.** With a DTZ table missing the ranks cannot see the counter; a kept move can be a 50-move draw at this clock. Only the report is corrected. Full table sets are not affected.
- **Body damage in a table file** that still parses can give wrong values: file checksums are not verified, and verifying them is a reader change outside this job. 44 damaged-folder runs under ASan with heap copies: no crash, no out-of-range read. The rest of the set stays usable. Files that fail validation (truncated, junk, empty) are rejected at load and counted.

## Rejected (checked, no gap)
| id | candidate | why rejected | evidence |
|---|---|---|---|
| G4 | PV nodes return a TB bound immediately, the parent stores it as exact | no result lost: 86 vs 107 blunders with and without tables on 59,547 roots; 17,406 of 45,649 mate roots report a TB win instead, which is what the score rule says; a PV TB return is also never wrong (0 of 10,777) | `logs/`, `tools/move_quality.py` |
| G9 | singular and ProbCut guards use the mate band only | 0 wrong at their sites once bit 1 is on, over 40,000 roots | claim harness |
| G10 | no UCI `tbhits` | new UCI output, no mechanism of this job; the claim and root harnesses read `probe_hits` and the kept moves directly | - |
| G11 | en passant absent from earlier oracle checks | 2000 legal ep roots agree with python-chess: probes and every kept move | fixture `s1.ep` |
| qs | qsearch prune gate as a part of bit 1 | removing it changes no claim at any site, nodes within 0.0003 % | `noqs` runs; R2 agrees |
| R1 | `setoption SyzygyPath` during a running search frees tables under the search | `setoption` calls `stop_search()` first | `src/uci.cpp` |
| R2 | stale `root_display` / `search_cardinality` after unloading | `load()` resets both first | `src/syzygy.inc` |
| R3 | reader disagreement on random positions | Forge vs Fathom 50,000 / 50,000 WDL, 49,678 / 49,678 DTZ | `opus-oss-scout-20261106: opus_oss_scout/trials/t5_fathom/RESULT.md` |

## Missing evidence (UNVERIFIED, not gaps)
- `QA_P6_SYZYGY_QUEUE_20261101.md` and `CR_OPUS_R13_P6_SYZYGY_DELTA_20261101.md`: found in no git ref and in no searched folder. What is known of them comes from `forge_gates.json` notes and P6 RESULTS.md.
- Receipt "145 WDL + 145 DTZ": corroborated: load line, QA `checks.log`, and all 290 file hashes = the project's list `opus_r3/R3-1L/syzygy345.sha256` (`fixtures/TABLES.sha256`). CI's "70 tables" is the 3-4 piece subset.
- Six-piece behaviour: no 6-piece tables on the PC, so the interior fixtures use 5-man roots with 3-4 piece tables loaded as the same situation one piece lower.
- Strength: no games by this job. QA's SPRT decides.
