# Syzygy gap ledger (P6 integration) - job opus-syzygy-gaps-20261107

Status words: OPEN (candidate, no proof yet), RED (failing fixture on the parent, gap proven), CLOSED (fix + fixture
GREEN + qualification), REJECTED (checked, no gap), UNVERIFIED (evidence absent; absence of evidence is not a gap).
Every row names: existing implementation / fixture / gate outcome / owner / evidence / missing behaviour.

Parent for all rows: lock source d4f43124 + `opus_r13/p6/syzygy_port.patch` (md5 4342d24f) = kit exe 150374ff.
Gate outcome for all rows: P6 gates USYZP / USYZPD4 (+ held confirms; idx 221-224 in QA's dry-run manifest, 230-233 in the
current `forge_gates.json`) have **no result**: 0 rows in FORGE_RESULTS.csv, 0 hits in forge_queue.log and in
forge_queue_state.json attempts, no gate folder on C:/D:/E:/F:. Owner of gates and reservations (srand / openings of the
confirms): QA. The only related result is R5C-N3, a bundle with two other options, H0, not attributable to Syzygy.

| id | mechanism | candidate gap | existing implementation | existing fixture | evidence | status |
|---|---|---|---|---|---|---|
| G1 | score bounds | null-move returns a TB-band score as a proven bound; mate scores are replaced by beta (`search.cpp` null move) | `is_mate_score` guard only | none | `logs/claims_p6_d10_3k.txt`: 206 of 815 TB-band null-move returns wrong at the node (5-man roots, probes limited to 4 pieces, 5-man tables as truth) | RED |
| G2 | score bounds | shallow pruning keeps running while `best_score` is a TB loss; the mate-loss band stops it (`best_score > -MateInMaxPly`). The fail-soft TB loss is stored as an upper bound and its negation reaches parents and the TT as a false TB win | mate band only | none | `logs/claims_p6_d10_3k.txt`: 2991 of 10114 pruned TB-loss fail-lows wrong; downstream 3532 wrong TB wins at node ends, 2700 + 1476 wrong TT cuts, 584 of 996 razor returns, 591 RFP returns | RED |
| G3 | score bounds | correction history learns from TB-band best scores (clamped maximum update); mate scores are excluded | `!is_mate_score(best_score)` only | none | `logs/claims_p6_d10_3k.txt`: 96932 of 4414593 updates came from TB-band scores | RED |
| G4 | interior WDL | PV nodes return a TB win / loss bound immediately, parent stores it as BoundExact; a real mate below that node is hidden | `probe_tablebase` "PV nodes take the TB value" | none for mates below TB nodes | code reading; R14 mate probe covers TB roots only | OPEN |
| G5 | root DTZ | a root win with exact dtz + counter = 100 is reported as cursed (+2) although it is a win; selection is sound (0 of 19905 kept moves give up the result). A loser's rounded d + counter = 100 is not treated as a possible save | `dtz_rank` / `rank_score` | C1 suite passes (no such row) | `logs/root_p6_clock.txt`: 733 display errors at sum 100, python-chess and Fathom agree on the win | RED (display), OPEN (rounded loser) |
| G6 | root DTZ / rule 50 | WDL-only fallback (DTZ table missing) reports a TB win at counter > 0, where WDL alone cannot decide | `wdl_rank` ignores the counter | none | code reading | OPEN |
| G7 | rule 50 | a TB-band TT score is read at a clock where the stored distance no longer fits before move 100 (`score_usable` only guards clock >= 90) | `TTEntry::score_usable` | none | code reading | OPEN |
| G8 | rule 50 | `Syzygy50MoveRule` change does not clear TB scores stored under the other rule | `SyzygyPath` clears the hash, this option does not | none | code reading | OPEN |
| G9 | score bounds | singular and ProbCut guards use the mate band only | `is_mate_score` | none | code reading; no soundness argument yet | UNVERIFIED |
| G10 | test tooling | no UCI `tbhits`, `probe_hits` is not visible, no root counter | `syzygy::probe_hits` | C1 tests read it directly | code reading | OPEN (test harness, not an engine mechanism) |
| G11 | reader | en passant positions are absent from the 220 + 50,000 oracle checks (generators write `-`) | reader handles ep | C1 fixtures (to check) | `opus_oss_scout/trials/t5_fathom/CMDS.md` | OPEN |
| G12 | fallback | corrupt table bodies (bit flips, truncation) | `parse_file` validation, C1 `robustness` | C1 robustness: pass on the P6 tree (36825 checks, 0 failures, `logs/c1_full.txt`) | header-level only so far | OPEN |

## Root-level check, no false claims so far
E1: 200,000 random 5-man roots, 3-4 piece tables loaded, full set as truth (Fathom): depth 8 and depth 10: 0 false TB or mate claims at the root in 76,227 + 82,963 TB claims (`logs/e1_p6_d8.json`, `logs/e1_p6_d10.json`). The PV re-search cleans the root score; the false claims of G1 / G2 live below the root.

## Rejected so far
| id | candidate | why rejected | evidence |
|---|---|---|---|
| R1 | `setoption SyzygyPath` during a running search frees tables under the search | `setoption` calls `stop_search()` first | `src/uci.cpp` lines 195-196 of the P6 tree |
| R2 | stale `root_display` / `search_cardinality` after unloading | `load()` resets both first | `src/syzygy.inc` lines 1221-1222 of the P6 tree |
| R3 | reader disagreement on random positions | Forge vs Fathom 50,000 / 50,000 WDL, 49,678 / 49,678 DTZ | `opus-oss-scout-20261106: opus_oss_scout/trials/t5_fathom/RESULT.md` |

## Missing evidence (UNVERIFIED, not gaps)
- `QA_P6_SYZYGY_QUEUE_20261101.md` and `CR_OPUS_R13_P6_SYZYGY_DELTA_20261101.md`: found in no git ref and in no searched
  folder (`out/logs/find_docs.txt`). What is known of them comes from `forge_gates.json` notes and P6 RESULTS.md.
- Receipt "145 WDL + 145 DTZ" is corroborated by P6 logs (`logs/kit_syz/pc1_opt1.ltopgo.uci_excerpt.txt`, QA
  `checks.log`: rtbw 145, rtbz 145, 983980865 bytes). CI's "70 tables" is the 3-4 piece subset (35 + 35), not a conflict.
