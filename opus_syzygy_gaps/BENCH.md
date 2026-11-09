# BENCH - opus-syzygy-gaps-20261107, frozen head 989399b

**Label: SEARCH/EVAL CHANGE, UNPROVEN.** With an option on, the search changes. No games were played and there is no Elo claim: QA's SPRT decides. Nothing is queued. NPS was not measured (the prompt forbids quiet ABBA runs here, and NPS is not Elo).

Compact logs are in `logs/`. Row files stay in the job root under `out/`, paths below.

## What was measured
| item | value |
|---|---|
| candidate | `out/src/cand`, commit 989399ba6a7f, parent ded9684 (the P6 tree) |
| `patches/syzygy_gaps_after_p6.patch` | md5 de4da16a5be55242422942de3b3e18de, sha256 7ebe07148ea336eb2d4d6e30571e14959c98ee27605b42b697bcb7bfe0fb4f29 |
| `patches/syzygy_gaps_after_w6p6.patch` | md5 bac6d5a57d016cd55397d4052253afaa, sha256 84443a828f90be4f4e1323f68ed2990ae5d3c29408cf62f077203d0262947e7c |
| `patches/syzygy_port_and_gaps_after_w6.patch` | 2224 lines, md5 f954d8792fa742381d4062b97dd6bb8d, sha256 626a509c9771dd62814923371b3f35c48248cdd3d417e27af9f53bd64ddd8bdc |
| parent | lock source d4f43124 + `opus_r13/p6/syzygy_port.patch` (md5 4342d24f) = kit exe sha256 150374ff4b9132b99b48e9ba6a51b36b89e22014c61cec3053d1f4f17b87d99f |
| Build A (macros off) | sha256 150374ff... = the parent, byte for byte |
| Build B (macros on, options 0) | sha256 db91700e745281a525b17d1553de40874da94185f1941a027dad85699132da46, md5 4730b028572373c172b65561ea8a8e80, pc1 = pc2 |
| compiler | g++ 15.2.0 (MSYS2 Rev14) |
| recipe | QA kit v2.3 lines, frozen workload v1 (sha256 checked by `tools/kit_build.ps1`): `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin`, then PGO |
| tables | `D:\syzygy345`, 145 WDL + 145 DTZ, all 290 file hashes = the project's list (`fixtures/TABLES.sha256`) |
| all on | `SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3` |
| placement | every run Idle on CPUs 12-15 (0xF000), Threads 1 unless a line says otherwise |

## OFF identity: frozen head against the parent
All IDENTICAL or EQUAL. Log: `logs/final_989399b.txt`, `logs/identity_buildB_c989399b.txt`.

| check | result |
|---|---|
| preprocessed source, macros off | ALL EQUAL. With macros on, 2 units differ (search, uci): expected |
| Build A against the parent exe | byte-identical (OFF verdict at compile time) |
| Build B pc1 against pc2 | byte-identical |
| macro combinations (each macro alone and together) | all compile, `logs/macro_combos_989399b.txt` |
| clean-room lint on the patch | CLEAN, `logs/lint_989399b.txt` |
| Build B pins, no tables, net on and off, perft | PINS ALL EQUAL: on 312866 / 862329 / 3024920 / 12389307 / 34048354, off 375354 / 907205 / 2448617 / 13573040 / 24506465, perft 4865609 / 193690690 |
| Build B pins, tables | PINS ALL EQUAL, P6 path: 313631 / 866959 / 2460490 / 11465604 / 31972996 |
| warm identity, no tables | IDENTICAL, 25,717 lines, 2000 searches, 80 state changes |
| warm identity, tables, 12k FENs | IDENTICAL, 25,988 lines, 2000 searches |
| warm identity, tables, clock fixture | IDENTICAL, 43,642 lines, 2000 searches |

Cold identity of Build B against the parent, depth as in `tools/identity_runs.ps1`:

| set | rows | different | nodes on both |
|---|---|---|---|
| net_on (12k FENs, depth 13) | 12000 | 0 | 1,534,521,761 |
| net_off | 12000 | 0 | 1,578,228,148 |
| tb_12k | 12000 | 0 | 1,464,257,271 |
| tb_roots (5-man, 3-4 piece tables, depth 10) | 30000 | 0 | 378,022,151 |
| tb_clock (depth 6) | 19905 | 0 | 16,672,350 |
| tb_promo | 4000 | 0 | 3,127,020 |
| tb_ep | 2000 | 0 | 1,107,330 |
| tb_rep | 2000 | 0 | 1,076,108 |
| tb_castle | 499 | 0 | 849,810 |
| tb_clock100 | 500 | 0 | 0 (the root reports a draw and does not search) |

**Reproduction from the pack** (`tools/repro_from_pack.sh`, `logs/repro_989399b.txt`): lock source + P6 patch + pack patch, both with `-F0`: fresh tree = `out/src/cand` HEAD; macros off and macros on rebuild the same exe hashes.

## Bench per option, Build B, depths 11 / 13 / 16 / 20 / 22
Without tables, every option value below gives the lock pins at all five depths. With `D:\syzygy345`:

| option | d11 | d13 | d16 | d20 | d22 |
|---|---|---|---|---|---|
| all 0 (P6 path) | 313631 | 866959 | 2460490 | 11465604 | 31972996 |
| SyzygyTbBounds=1 | 313659 | 867107 | 2458296 | 11661537 | 31281025 |
| SyzygyTbBounds=2 | 313632 | 866960 | 2469380 | 10687206 | 27772621 |
| SyzygyTbBounds=4 | 313631 | 866962 | 2461660 | 11820857 | 27639447 |
| SyzygyTbBounds=7 | 313659 | 867107 | 2458296 | 10663626 | 26408664 |
| SyzygyRootExact=1, 2 or 3 | 313631 | 866959 | 2460490 | 11465604 | 31972996 |
| SyzygyRule50=1 or 3 | 313631 | 866959 | 2460490 | 11195442 | 33899273 |
| SyzygyRule50=2 | 313631 | 866959 | 2460490 | 11465604 | 31972996 |
| all on | 313659 | 867107 | 2458296 | 10663627 | 26324444 |

Liveness: `SyzygyRootExact` never shows in the bench, because no bench root sits inside the tables, and `SyzygyRule50` bit 2 only acts when the rule option changes. Their evidence is the fixtures below, not the bench. These numbers are node counts, not strength: a lower count says nothing about Elo.

## Fixtures: parent against all on
Oracles: python-chess and Fathom for table values; `tools/oracle_exact.py` for the 50-move boundary, which does not use the DTZ rounding flag. The parent numbers are plain builds with the same nodes as kit exe 150374ff. The all-on numbers are the plain build of the frozen head, sha256 b5ce3df3969536890ca3c7eac1ca7b56030a411e97ae2964f0e84fb0cad2b509. Logs: `logs/suite_parent.txt`, `logs/suite_v9on.txt`, `logs/suite_v9on_special2.txt`.

"Bad" below means wrong against the oracle. Zero on the parent means that row does not separate the two; it is listed so nobody reads it as an improvement.

**Boundary roots, dtz + counter = 100, all 4569 rows** (`tools/exact_full.sh`, `tools/und_check.py`, `tools/exact_partial.py`)

| check | parent | all on |
|---|---|---|
| roots the solver finished, judged | 2821 | 2821 |
| kept moves worse than the best, on decided roots | 197 | **0** |
| kept moves worse, on undecided roots | 259 (its ranks 900, -900) | 34 |
| wrong root reports | 430 | **0** |
| roots undecided: search score shown, nothing claimed | 0 | 107 |
| engine depth 8: worse moves | 27 | 4, all on undecided roots |
| engine depth 8: wrong score class | 389 | 105, all on undecided roots |
| rows the solver did not finish (8 s per root), resolved moves only | 1719 | 1719 |
| ... provably worse kept moves | 7 | **0** |
| ... provably wrong reports | 24 | **0** |
| ... claimed win or loss the solver refutes | 6 | **0** |
| ... engine moves and scores provably wrong | 2 and 24 | **0 and 0** on the 933 decided roots |
| lines played out against an oracle opponent, 800: result lost | 5 | **0** |
| mate lines replayed, 282 | no result (tool error on that run) | 275 verified, 7 cut off, 0 broken |

The earlier 2500-row snapshot of the oracle gives the same picture (2455 judged: parent 197 + 258, 260; all on 0 + 33, 0, 54 undecided). All undecided counts and the reach by clock: `GAP_LEDGER.md`, Limits: 919 of 4569 rows of this purpose-built fixture.

**Table-rule fixtures** (python-chess and Fathom values, `tools/root_check.py`, `tools/root_move_check.py`)

| fixture, roots | parent: wrong reports (root) / wrong scores (engine) | all on |
|---|---|---|
| clock, 19905 | 733 / 696 | **0 / 0** |
| promo, 4000 | 618 / 530 | **0 / 0** |
| ep, 2000 | 0 / 0 | 0 / 0 |
| rep, 2000 | 0 / not run | 0 / not run |
| castle, 500 (499 not ranked, by design) | 0 / not run | 0 / not run |
| clock 100, 500 | 0 / 0 | 0 / 0 |
| rule off: promo 4000, rep 2000 | 0 | 0 |

Kept moves worse (column A) and engine moves worse (M) are 0 on both for these fixtures. On both exes 2418 clock rows and 41 promo rows have a rounded move exactly on the boundary, which the table rule cannot judge; the exact solver above can.

**Special rows, all on** (`logs/suite_v9on_special2.txt`): 7-ply repetition 1500 rows, 305 with a third occurrence at the root: root and engine 0 bad. Underpromotion 300 rows, found in 1,273,647 tries: 0 bad. WDL tables only, clock 0, 528 rows: 0 bad reports, 190 kept moves at the documented move-filter limit. WDL tables only, clock fixture: 0 false TB scores shown; the 56,314 "A" rows there are the same limit. Rule off, clock fixture: 0 bad.

**Interior claims** (`tools/tb_claims.cpp`, a test-only instrumented tree: every TB-band score at a node is checked against the full tables). The harness searches the same nodes as the real exe (checked by the hunter on 300 roots, 3,388,358 both). Parent: `logs/suite_parent.txt`.

| run | sites and events | parent wrong | all on wrong |
|---|---|---|---|
| 3000 roots above the tables, depth 10 | pruned TB-loss fail-lows, 10114 on the parent | 2991 | **0** |
| same | false TB wins at node ends | 3532 | **0** |
| same | wrong TT cuts, main + qsearch | 2700 + 1476 | **0 + 0** |
| same | correction updates from TB-band scores, of about 4.3 M | 96,932 | **0** |
| clock fixture 19905 roots, depth 10 | pruned TB-loss fail-lows | 85,761 of 132,694, in 5678 roots | **0** |
| same | correction updates from TB-band scores, of about 71 M | 436,277 | **0** |
| 3000 roots, warm table, depth 12 | every site | 134,398 pruned, 143,037 node ends, ... | **0** returned; `null_raw` 1 of 974: a raw null score that is replaced, never returned |
| zugzwang roots, 199, depth 16 | every site | 8705 pruned, 9501 node ends, 11,117 TT cuts, ... | **0** |

**Warm table and rule change**

| check | parent | all on |
|---|---|---|
| warm table at clock 0, same FEN at a later clock, 3000 rows: false TB claims | 5 | **0** |
| ... control rows, true warm claims kept (cold: 292) | 308 | 288: **a cost**, 20 true claims withheld |
| `Syzygy50MoveRule` toggled, 400 roots: rows with another TB class than after a Clear Hash | 101 + 57 | **0** |
| ... rows with other nodes than a manual Clear Hash | 398 | **0** |

**Roots above the tables, 200,000, depth 10** (information): false root claims 0 on both, so this set does not separate them at the root; the claim harness above does. Mates 28,203, of which 28,034 verified, 169 cut off, 0 broken. Scores printed as `cp` inside the mate band: 0. Sign agrees with Fathom on 154,682 of 154,738 decided roots against 154,683 on the parent. Nodes 2,523,734,827 against 2,519,706,483.

**Protocol** (`tools/uci_misc_checks.py`): searchmoves 219 + 219, castling 400, protocol 84, Threads 2 / 3 / 4 soak 120 searches each: all legal; bench 13 afterwards answers 867107 with tables.

**Partial table folders**, engine at depth 5, 3000 rows each. TB-band root scores against the full-set oracle: nodtz 2039, nochild 1603, dtzonly 1738, rejected 1228 claims: **0 wrong, 0 illegal moves** (`logs/partial_v9on.txt`). The parent showed 41 and 10 false root scores here.

## Per bit (information, no verdict)
At e0ad013, the same code as the head (the head differs by one comment). `logs/info_v8.txt`. A bit that closes a gap only with another one shows that here.

200,000 roots above the tables, depth 10, moves on 198,507 oracle roots. False root claims are 0 for every row, so that column is left out:

| option | nodes | blunders | only parent / only this | sign test p |
|---|---|---|---|---|
| parent | 2,519,706,483 | 333 | - | - |
| SyzygyTbBounds=1 | 2,530,426,407 | 339 | 50 / 56 | 0.63 |
| SyzygyTbBounds=2 | 2,514,742,060 | 334 | 41 / 42 | 1.00 |
| SyzygyTbBounds=4 | 2,520,408,164 | 331 | 3 / 1 | 0.62 |
| SyzygyRootExact=3 | 2,519,706,483 | 333 | 0 / 0 | 1.00 |
| SyzygyRule50=3 | 2,515,445,130 | 333 | 0 / 0 | 1.00 |
| all on | 2,523,734,827 | 336 | 50 / 53 | 0.84 |

Interior claims by `SyzygyTbBounds` mask, all other options 0. "Wrong" is the sum over returned sites, so `null_raw` (a raw null score, replaced before it is returned under bit 4) is left out:

| mask | 3000 roots, depth 10: wrong at node ends / TT cuts | correction updates from TB-band scores | 1250 two-plies-back zugzwang roots, depth 16: wrong null cuts / node ends / TT cuts |
|---|---|---|---|
| 1 | 0 / 0 | 88,050 | 4 / 1 / 0 |
| 2 | 6760 / 4357 | 0 | 1356 / 34,559 / 28,195 |
| 4 | 6548 / 4145 | 98,752 | 0 / 40,863 / 35,165 |
| 7 | 0 / 0 | 0 | 0 / 0 / 0 (`null_raw` 12 of 907, in 8 roots: replaced, not returned) |

So bit 1 does most of the work and bits 2 and 4 alone do not close G2: all three together give 0.

## Warm table, moves played
At e0ad013, the same code as the head. Judged by the exact solver rows (`tools/warm_move_check.py`, `logs/info_v8.txt`), 3000 rows: moves that keep less than the best result, warm table: parent 386, all on 362; cold: parent 374, all on 367. Only the parent wrong 97 rows, only all-on wrong 73. No verdict: this is one fixture.

## Move quality
Cold, 198,507 clock-0 roots with an oracle, depth 10: **parent 333 blunders, all on 336.** Only the parent 50, only all on 53, sign test p = 0.84 (`logs/suite_v9on_move_quality.json`). **Neutral**: the suite does not show that the switches help moves in general. What they do is remove false claims and fix boundary roots. QA's SPRT decides whether that matters in games.

## Stress
| run | result |
|---|---|
| UBSan trap and MSVC ASan, off and all on, root fixtures, 5-man roots above the tables (`logs/san_v9.txt`) | all exit 0. Bench 13: UBSan 862329; ASan 819221 (the MSVC port searches other nodes, as it does on the lock) |
| damaged table files under ASan with heap copies (`logs/flips_v9.txt`) | 44 runs, 0 non-zero: no crash, no read out of range |
| 15,495 KQvKR boundary roots with a missing child table, folders nochild, nodtz, rejected, wdl_only (`logs/green_v8.txt`, at e0ad013: the head differs by one comment; UBSan trap on the commit before the fix) | UBSan and ASan exit 0; nochild: 14,887 undecided, none false |
| option churn: 3000 random option, table and clock changes between searches, per run (`tools/uci_churn.py`, `logs/churn_v9.txt`) | plain, UBSan, ASan at Threads 1, plain and ASan at Threads 2: all PASS, 1637-1675 searches and 22 state checks each, bench after the churn = pin |
| the same 15,495 roots at the frozen head under ASan with heap copies, 4 folders | exit 0, 0 bad rows. Slowest `prepare_root` 238 ms under ASan with a missing table; 34 ms plain on full tables |
| a root stored at clock 0, read at an inner node of a later search (R3 finding 6, `tools/run_pred.sh`, `logs/pred1_v9.log`, `logs/pred2_v9.log`), depth 12, all on | One reversible move earlier, 4024 rows: 2,979,697 main and 2,658,266 qsearch TT cuts, **0 wrong at every site**. Two moves earlier, 3078 rows: 2,944,650 and 2,496,248 TT cuts, **0 wrong**; `null_raw` 1 of 548, replaced, not returned. Control without `SyzygyRule50` bit 1: 2290 and 529 wrong TT cuts (one move), 826 and 28 (two moves), so these rows can fail |
| bug hunter's mutants of the new code | PENDING |

## trial_w6 line
The live lock line is trial_w6: the lock source + six node-identical speed switches. `tools/after_w6.sh`, log `logs/after_w6_989399b2.txt`, row files under `out/ident/`. Kit recipe with the six defines. Verdict: **ALL CHECKS PASS**.

The first attempt failed at the patch step, correctly: one hunk's context has the store line that trial_w6 wraps in `#if FORGE_SPD_TT_NOTLS` (`REVIEW_LOG.md`, B3, `logs/after_w6_989399b_rejected.txt`). The tool's own first version also cut the compare's JSON before its verdict field, so all 15 compares counted as failed although the rows were identical. `tools/after_w6_compare.sh` repeated the compares from the same row files with the verdict in full, the cut is fixed, and the fixed check was tried on one identical and one different pair.

| check | result |
|---|---|
| gaps patch for this line against `syzygy_gaps_after_p6.patch` | same 234 changed lines, same order; applied with `-F0`, no reject |
| preprocessed source, speed switches 0, macros off, against the P6 tree | ALL EQUAL |
| preprocessed source, speed switches 0, macros on, against the frozen candidate | ALL EQUAL |
| changed lines inside a speed conditional (`tools/w6_arm_check.py`) | none |
| Build A' (six defines, macros off) against the w6 + port parent exe | byte-identical |
| Build B' (six defines, macros on, options 0) | sha256 5fee7ff82c7d42a2488561a65a98ab7db498fb0e7e7ec1f201623bea6934b441 |
| B' pins without tables, net on and off, perft | PINS ALL EQUAL |
| B' pins with tables | PINS ALL EQUAL, P6 path |
| one patch `syzygy_port_and_gaps_after_w6.patch` on a fresh trial_w6 tree | same tree |

Options 0, B' against the w6 + port parent and against the P6 parent 150374ff: IDENTICAL both ways.

| set | rows | different | nodes |
|---|---|---|---|
| net_on | 12000 | 0 | 1,534,521,761 |
| tb_roots | 30000 | 0 | 378,022,151 |
| tb_clock | 19905 | 0 | 16,672,350 |

All on, B' against frozen P6-line Build B: IDENTICAL, so the suite's results on the P6 line carry over to this line for what these rows exercise.

| set | rows | different | nodes |
|---|---|---|---|
| bench 11 / 13 / 16 / 20 / 22, tables | 5 | 0 | 313659 / 867107 / 2458296 / 10663627 / 26324444 |
| bench, no tables | 10 + perft | 0 | lock pins |
| tb_roots (depth 10) | 30000 | 0 | 380,901,117 |
| tb_clock (depth 6) | 19905 | 0 | 16,303,099 |
| tb_promo | 4000 | 0 | 3,126,712 |
| tb_ep | 2000 | 0 | 1,107,330 |
| tb_rep | 2000 | 0 | 1,076,108 |
| tb_castle | 499 | 0 | 850,959 |
| tb_clock100 | 500 | 0 | 0 |
| boundary roots (depth 8) | 4569 | 0 | 14,637,186 |
| warm rows, tables, clock fixture | 2000 searches, 43,645 lines | 0 | IDENTICAL |

UBSan trap with the six defines and all on: bench 13 = 862329, 4569 boundary rows identical to the kit build's rows (14,637,186 nodes), `tb_root` 19,905 rows, all exit 0. ASan was not run on this line: the MSVC port has no AVX-512 and PEXT variant of these switches. The clang recipe of the live exe (`forge_clang_combo29_trial_w6.exe`, E1284F7F, same pins per `CURRENT_LOCK.json`) was not built here; that recipe is QA's.

## Not measured
- Strength. No games, no SPRT, no tuning.
- Speed. No ABBA. The kit profile is trained with the options off, so on-paths are cold-optimised: say so in any comparison.
- 6-piece tables: none on this PC. The interior fixtures use 5-man roots with 3-4 piece tables loaded as the same situation one piece lower.
- The clang recipe of the live lock exe (`forge_clang_combo29_trial_w6.exe`, E1284F7F): see the trial_w6 line.

## Evidence paths (job root `D:\forge_jobs_20261107\opus1`)
| what | where |
|---|---|
| source trees | `out/src/cand` (git), `out/src/p6_port`, `out/src/w6p6g_989399b2` (git), `out/src/trial_w6.patch` (md5 5786e9b87a0c3cec4707af521cec85bc) |
| exes | `out/builds/p6_parent_pc1`, `out/builds/buildA_c989399b`, `out/builds/buildB_c989399b_pc1`, `_pc2`, `out/builds/w6p6_parent_989399b2`, `w6p6_A_989399b2`, `w6p6_B_989399b2`; plain `out/exe/cand_v9_plain.exe`, `tb_root_v9.exe` |
| identity row files | `out/ident/parent_150374ff`, `buildB_c989399b`, `on_buildB_c989399b`, `w6p6_parent_989399b2`, `w6p6_B_989399b2`, `on_w6p6_B_989399b2`, `warm_c989399b_*`, `warm_on_w6_989399b2` |
| suite | `out/qual/p6` (parent), `out/qual/v9on`, `out/qual/info_v8`, `out/exp/partial/v9on` |
| oracle rows | `out/exp/exact/b1.boundary.exact2.jsonl` (all 4569), `b2500.exact.jsonl` (snapshot), `out/exp/e1/roots200k.oracle.jsonl`, `roots200k.fathom` |
| stress | `out/san/v9`, `out/san/w6_989399b2`, `out/exp/hunt/churn_v9`, `out/exp/hunt/pred_v9_*` |
| bug hunter's scratch | `out/hunt_agent` |

Disk cleanup runs on this PC, so a build folder may be gone later: every exe and row file above can be rebuilt with `tools/final_chain.sh` and `tools/after_w6.sh`. `logs/` in this pack keeps the compact results.
