# PROOF: do the job-2 candidates behave exactly like the lock combo29?

Job "Fable 5.2, job 3", correctness only. Generated 2026-11-10 22:17:12 Vienna by `harness/report.py` from this template and from the receipts and ledgers of the runs; no number in this file was typed by hand. Times are Europe/Vienna. Terms are defined in `README.md`.

## Recap

**Finding.** In every check that ran, each of the six candidates behaved exactly like the lock: no difference in any compared field, on either tier.

**Verdicts.** PASS: EVL, PCM, CKL, WNP, KPC, BUN.

| Candidate | Verdict | Tier A comparisons completed (all fields) | Tier R comparisons completed (move lists) | Open gates | Differences |
|---|---|---|---|---|---|
| EVL: EVADE_LEGAL | **PASS** (two tiers: checkers and static eval on the auxiliary probe, not on the release executable) | 20,000,000 | 20,000,000 | none | 0 |
| PCM: PAWN_CAPMASK v2 | **PASS** (two tiers: checkers and static eval on the auxiliary probe, not on the release executable) | 20,000,000 | 20,000,000 | none | 0 |
| CKL: CHECKERS_KL v3 (mode 1) | **PASS** (two tiers: checkers and static eval on the auxiliary probe, not on the release executable) | 20,000,000 | 20,000,000 | none | 0 |
| WNP: WITNESS_NOPIN | **PASS** (two tiers: checkers and static eval on the auxiliary probe, not on the release executable) | 20,000,000 | 20,000,000 | none | 0 |
| KPC: KING_PAWN_CACHE v2 | **PASS** (two tiers: checkers and static eval on the auxiliary probe, not on the release executable) | 20,000,000 | 20,000,000 | none | 0 |
| BUN: BUNDLE3 (EVL + PCM v2 + CKL v3) | **PASS** (two tiers: checkers and static eval on the auxiliary probe, not on the release executable) | 20,000,000 | 20,000,000 | none | 0 |

**What a PASS means here.** A PASS rests on two kinds of evidence, as Couns decided before the work started (decision D1). On the exact release executables, every check their UCI interface allows was completed without a difference: the 13 pins, the perft divide, the legal moves and their order on the edge suite and on the fuzz corpus, the warm-state transcript and the Threads soak. On auxiliary probes, which are new test code compiled with each candidate's unmodified source, at least 20,000,000 positions per candidate were compared in every field, including the two fields the release executables do not print: the checkers bitboard and the static eval. **Checkers and static eval were therefore not observed on the release executables themselves.** The required count of 20,000,000 is the auxiliary one (decision D2). Since the owner's code review of this pack a PASS also needs the fuzz on the release executables to cover the whole corpus of 200 chunks, each chunk tied to the lock probe; that count is given beside the auxiliary one.

**Completed work.**

- Harness self-test: `SELFTEST PASS 75/75`, after red runs against comparators that cannot fail.
- Pins, 13 per executable: matched by 9 of 9 executables (the lock, its copy, the lock-equivalent and the six candidates).
- Perft divide, ten runs on eight positions, every root move: equal to the lock for 8 of 8 compared executables.
- Edge suite: 410 legal positions, 17 rejected, 4 unreachable; 14,220 probe records and 7,725 release-exe perft blocks per tag; matching for 8 of 8 compared tags.
- Warm-state transcript: identical for 8 of 8 compared executables. Threads 2-4 soak: stable for 9 of 9.
- Fuzz, auxiliary tier: at least 20,000,000 completed position comparisons per candidate, every field, both net modes.
- Fuzz, release executables: 20,000,000 completed `go perft 2` comparisons per candidate (200 of 200 chunks), each chunk tied to the lock probe.
- Supplementary: cache-state variants, line coverage of every candidate's changed lines, 1,792 constructed WITNESS_NOPIN targets, search signatures on corpus positions, probe-against-executable move lists.

**What remains, and what this does not show.**

- Checkers and static eval on the release executables themselves: not observable. Reading them there would need a debug command in the engine source, that is a source change and new builds, which only Couns can approve. This job did not ask for it because decision D1 accepts the auxiliary probes.
- The limits in section 10 apply to every PASS.

Testing success does not authorise a lock change. Finite testing shows equivalence on the positions tested; it is not a proof for every position.

## 1. Identity of what was tested

Every executable was hashed before it was run, and the six MD5s supplied with the job all matched. Each source tree was compared file by file with the manifest of its build. BUN is BUNDLE3 from job 2's build `bn3_on` (source: the combo29 snapshot plus `BUNDLE3_after_combo29.patch`, md5 `ba2fcf2e78a0e2c85964a1e6e258d150`; built with job 2's lock recipe `tools\spd_build.ps1` and the three switches as `-D`; not rebuilt in this job). No commit holds the combo29 source and the lock executable cannot be rebuilt byte for byte, so BUN and the control LOCKEQ are **pin-equivalent, not byte-identical**: LOCKEQ is the same tree with the switches at 0 and differs from the lock executable in 89 bytes of its debug record only (job 2, `out\job3_prep\PIN_EQUIVALENCE.md`). QA's `build_v3\BUN` is another build (the five-flag bundle) and was not tested.

"ON" means: in the five QA builds the switch's default was changed from 0 to 1 in the source tree (`#define FORGE_SPD_... 1`); in BUN the three switches are passed as `-D...=1` to a tree whose defaults are 0. CHECKERS_KL is at mode 1 everywhere; mode 2 was never built or run. For each auxiliary probe the preprocessor was asked for the effective value of every candidate switch, and the table shows the answer. The net is the one compiled into every tree (`src/nnue_weights.inc`, sha256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`, 256 hidden units, a residual net that is added to the hand-crafted eval).

| Tag | What | Release exe MD5 | Release exe SHA256 | Probe SHA256 (harness 2) | Effective candidate switches in the probe |
|---|---|---|---|---|---|
| LOCK | combo29 lock | `c0051c99695f48bf93272d96fe7548c3` | `e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e` | `509e10996b474de7b45227a73ba54b51b46d54f0e2a91bde203065bbe3318d74` | none |
| LOCKEQ | lock-equivalent (BUNDLE3 tree, switches 0) | `c8084074dc8180f6e6b62e7013cf5b4b` | `74bb3cfa3121bc2e260406b24409fbb2c0eeb760fa3bc413d524bdcf04ab9f9b` | `c40583f2a61260446597e090f75822cae331114daa09b639dc04de5d0bdab31d` | CHECKERS_KL=0, EVADE_LEGAL=0, PAWN_CAPMASK=0 |
| EVL | EVADE_LEGAL | `35781e5cac204370584ff4cb1f5ee93e` | `b89df40fce1726e316e7fb8e3348866401bd86a406aa689e9967f4a487c30237` | `565cfd95a47bee6aecf33d13677c433a400411078c163bae66c5ed0ea50bca62` | EVADE_LEGAL=1 |
| PCM | PAWN_CAPMASK v2 | `2cd6d44845e343f8b206b60f876c2165` | `a60aa7cff6163b172dc4e0c88afffa41516c70b8722ce600817ff39c5feb482e` | `baacf05857699784a056e4dab0e9b9ca98662a5badbfc210119f772584cc77cb` | PAWN_CAPMASK=1 |
| CKL | CHECKERS_KL v3 (mode 1) | `8a159aed19f0d1ff0a9ee468e279794f` | `c643808f19905387cc5b6328f2c464d63208579998777257b179762b33869dbd` | `695e3ce136474a6c82c9fe155ddb1c967217b569299a1c35a2edc29a12f2a4b0` | CHECKERS_KL=1 |
| WNP | WITNESS_NOPIN | `1bf0291be0b2936c394c9a908f7432fe` | `5c8f0ec88a73dc7c1049d47a7a69724f2079834a6c4cd47df61f8308287b478b` | `e5d60da73cb6e33f91a8517d6ce6137f695c447f9b6f13ae12ff82673d80fd23` | WITNESS_NOPIN=1 |
| KPC | KING_PAWN_CACHE v2 | `55e1fe1230b5d19bd5382636a86f9c90` | `67eea5dc9d0deb59c2248c6488ab70c6aa5e22a01d247d2497f2454a8083d4aa` | `7f6c70a5519f69efa240124337460432e38efc82209d1fc559b5841483b66477` | KING_PAWN_CACHE=1 |
| BUN | BUNDLE3 (EVL + PCM v2 + CKL v3) | `ec5dc9d16897fe00f9e788edd9707180` | `db12981c4c840be4e9a93f04e88f12b1d7e90beb11f73070d0df9c316cc17d3c` | `83e355912d6e27025af209d0c278bf6c451a1274f6392f370868cb4dae1eb814` | CHECKERS_KL=1, EVADE_LEGAL=1, PAWN_CAPMASK=1 |

Harness source `mgprobe.cpp` compiled into every probe: sha256 `42efd61dd819eb7dda65546fb1344dc408850fe6ef4f01bea75873704a70786d`. LOCKCOPY is a second file with the lock's bytes (same hashes), used as a control.

Every receipt and ledger row used below names the executable or probe hashes of this table; a receipt or row that names another binary is not counted. Such receipts: none; such ledger rows: 0.

## 2. What the release executables expose

The lock's `uci.cpp` accepts `uci`, `isready`, `ucinewgame`, `setoption`, `position`, `go` (with `go perft N`), `bench`, `ponderhit`, `stop` and `quit`. The commands `d`, `eval`, `checkers`, `moves`, `legalmoves` and `help` were sent to the lock executable and produced no output (`evidence/observe/`). `go perft N` walks `board.legal_moves()` and prints one line per move, so it shows the legal moves in generation order. Nothing prints the checkers bitboard or the static eval, and `has_legal_move` (the function WITNESS_NOPIN changes) and the pawn-cache eval (KING_PAWN_CACHE) run only inside search.

The auxiliary probe reads those fields through the engine's public interface and its existing test hook (`friend struct SearcherTestProbe`). A probe is tied to its release executable in two ways: for the lock, every `go perft` block of the release executable had to equal the probe's legal list at every position of the release-executable fuzz (column "tied" in section 7); and for every tag the same was checked on 2,000 positions (section 8).

## 3. Harness self-test

Result of the last run: `SELFTEST PASS 75/75` (`evidence/selftest/GREEN10.log`).

The self-test never touches an engine binary or engine source. Its positive controls run the lock against a verified byte-for-byte copy of itself, and the lock probe against the lock-equivalent probe (another binary that must behave the same). Its negative controls take a real output of the lock and change one thing in memory: a legal move removed, a move added, two moves swapped, a checkers bit, the eval with the net on, the eval with the net off, `has_legal_move`, each of the 37 fields of a record in turn, a wrong position, two different inputs, a missing record, a cut transcript, garbage, a transcript from the wrong probe, a probe from another harness source, and for the release executables a removed move line, swapped lines, a changed count, a missing block, a malformed line, a refused FEN, a cut output, an engine that never answers. Each must be refused with the field named. Seven more controls (L1 to L7) test the report generator and the replay tool: a chunk that was run twice counts once; a row that names other binaries than the frozen ones counts nothing, also when the candidate's file is the lock's file; there is no PASS below 20,000,000 or with an open gate or a difference; only a line `SELFTEST PASS n/n` is a passed self-test; a replay reproduces a ledger row only if every hash is the row's; the release-executable fuzz is not complete before all 200 chunks; a harness error on a chunk that also ran clean does not block, a difference always does, and a confirmed difference is FAIL. The controls were watched failing first, against comparators that always answer "equal" (red runs 1 and 2), against the code before the review fixes (red run 3), against a counter that counts every row and a verdict that ignores the gates (red run 4), and against the report generator before the fixes of the owner's code review (red run 5).

The full runs and the red runs of the self-test are kept as logs, including the runs made while the harness was being written. The name of a log says what the run was meant to show, not how it ended:

| Log in `evidence/selftest/` | Written | Last line |
|---|---|---|
| `RED1.log` | 19:09:36 | SELFTEST FAIL 4/20 |
| `RED2.log` | 19:11:12 | SELFTEST FAIL 6/42 |
| `GREEN1.log` | 19:13:25 | SELFTEST FAIL 40/42 |
| `GREEN2.log` | 19:14:18 | SELFTEST PASS 43/43 |
| `RED3.log` | 19:49:13 | SELFTEST FAIL 16/27 |
| `GREEN3.log` | 19:52:54 | SELFTEST FAIL 64/66 |
| `GREEN4.log` | 19:54:25 | SELFTEST FAIL 66/67 |
| `GREEN5.log` | 19:55:01 | SELFTEST PASS 67/67 |
| `RED4a.log` | 20:25:59 | SELFTEST FAIL 0/4 |
| `RED4.log` | 20:28:07 | SELFTEST FAIL 0/5 |
| `GREEN6.log` | 20:42:47 | SELFTEST PASS 72/72 |
| `GREEN7.log` | 20:53:08 | SELFTEST PASS 72/72 |
| `RED5.log` | 21:43:02 | SELFTEST FAIL 5/6 |
| `RED6.log` | 21:47:56 | SELFTEST FAIL 0/7 |
| `GREEN8.log` | 21:48:16 | SELFTEST FAIL 74/75 |
| `GREEN9.log` | 21:49:03 | SELFTEST PASS 75/75 |
| `GREEN10.log` | 22:17:11 | SELFTEST PASS 75/75 |

`GREEN1` was the first run against the real comparators of harness 1. It failed in two release-executable controls because their fixtures were wrong: the changed block's counts no longer added up, so it was refused as malformed before the intended difference was looked at. The fixtures were corrected and the inconsistent block was kept as a control of its own; `GREEN2` is the pass of harness 1. `GREEN3` and `GREEN4` were runs of harness 2 that still failed: in `GREEN3` a missing block and an early end of the output were reported as a move-list difference, a defect of the comparator that had just been changed to compare from the start (missing output is not a difference; corrected); in `GREEN4` one diagnostic did not yet name the missing output. `GREEN5` is the first pass of harness 2, made before every counted run. `RED4a` and `RED4` are the red runs of the report controls alone (four of them at first, then five), and `RED5` and `RED6` those of the controls added after the owner's code review (against the report generator as it was, and against a gate that one chunk satisfies); they start no engine. `GREEN8` failed in one control that was new (A36, the edge runner refuses a dead lock probe): its fixture counted the two framing records of a transcript as position records; the control was corrected. The last log in the table is the run that counts for the verdicts: a full run made after the last change to the report generator and to the edge runner.

The reviews are recorded in `REVIEW_LOG.md`. The first one, by a read-only reviewer on another model at 19:41, found no way for a real difference to come out as equal, but it found gaps (how a probe build is bound to its switches, answers that were computed and thrown away, unlabelled transcripts, three controls that could not fail). All were fixed, the probes were rebuilt as harness 2, and every counted run was started again. The runs made before that are kept as an earlier run and are not added to any count (section 7). The second review, of the runners and the report generator, was started the same way at 20:09 and stopped at 20:34 on the owner's instruction to use no subagents, before it had reported anything. **It was then done by the author of the code, which is weaker than an independent review.** It changed the report generator (every gate is now tied to the frozen binaries, the self-test result is read from the newest log, the tie between probe and executable is a gate) and corrected descriptions in this file; it changed none of the six files that produced the counted fuzz rows. A third review came from the owner's side (Code Review of the pushed tools, no blocker, two required changes). Both were made: the logs of the two verification scripts are committed and listed in `DONE.md` and `MANIFEST.tsv`, and the release-executable fuzz has a minimum, the whole corpus. Its optional points that touch the probe or `fuzz.py` were not taken, because changing those files would require every counted run to be made again; they are listed as open in `REVIEW_LOG.md`.

## 4. Pins

Settings as recorded for the lock: Threads 1, Hash 16, OwnBook false, UseNNUE true or false; one process for the five net-on depths, one for the five net-off depths, one for the three perft pins. The lock was run first and reproduced all 13.

| Tag | bench net on d11/13/16/20/22 | bench net off d11/13/16/20/22 | startpos perft 5 | kiwipete perft 4 | kiwipete perft 5 | Result |
|---|---|---|---|---|---|---|
| LOCK | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 375354 / 907205 / 2448617 / 13573040 / 24506465 | 4865609 | 4085603 | 193690690 | MATCH 13/13 |
| LOCKCOPY | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 375354 / 907205 / 2448617 / 13573040 / 24506465 | 4865609 | 4085603 | 193690690 | MATCH 13/13 |
| LOCKEQ | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 375354 / 907205 / 2448617 / 13573040 / 24506465 | 4865609 | 4085603 | 193690690 | MATCH 13/13 |
| EVL | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 375354 / 907205 / 2448617 / 13573040 / 24506465 | 4865609 | 4085603 | 193690690 | MATCH 13/13 |
| PCM | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 375354 / 907205 / 2448617 / 13573040 / 24506465 | 4865609 | 4085603 | 193690690 | MATCH 13/13 |
| CKL | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 375354 / 907205 / 2448617 / 13573040 / 24506465 | 4865609 | 4085603 | 193690690 | MATCH 13/13 |
| WNP | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 375354 / 907205 / 2448617 / 13573040 / 24506465 | 4865609 | 4085603 | 193690690 | MATCH 13/13 |
| KPC | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 375354 / 907205 / 2448617 / 13573040 / 24506465 | 4865609 | 4085603 | 193690690 | MATCH 13/13 |
| BUN | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 375354 / 907205 / 2448617 / 13573040 / 24506465 | 4865609 | 4085603 | 193690690 | MATCH 13/13 |

## 5. Perft divide

Every root move's count was compared with the lock's, not only the total. The lock's totals equal the published values wherever one exists.

| Position | FEN | Depth | Root moves | Total (lock) | Published total | LOCKCOPY | LOCKEQ | EVL | PCM | CKL | WNP | KPC | BUN |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| startpos | `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1` | 6 | 20 | 119060324 | 119060324 | same | same | same | same | same | same | same | same |
| kiwipete | `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1` | 5 | 48 | 193690690 | 193690690 | same | same | same | same | same | same | same | same |
| position3 | `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1` | 6 | 14 | 11030083 | 11030083 | same | same | same | same | same | same | same | same |
| position4 | `r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1` | 5 | 6 | 15833292 | 15833292 | same | same | same | same | same | same | same | same |
| position5 | `rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8` | 5 | 44 | 89941194 | 89941194 | same | same | same | same | same | same | same | same |
| position6 | `r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10` | 5 | 46 | 164075551 | 164075551 | same | same | same | same | same | same | same | same |
| castle_gives_check_d5 | `5k2/8/8/8/8/8/8/4K2R w K - 0 1` | 5 | 15 | 120330 | 120330 | same | same | same | same | same | same | same | same |
| castle_gives_check_d6 | `5k2/8/8/8/8/8/8/4K2R w K - 0 1` | 6 | 15 | 661072 | none used | same | same | same | same | same | same | same | same |
| check_with_castling_rights_d5 | `r3k2r/8/8/8/8/4R3/8/R3K2R b KQkq - 0 1` | 5 | 4 | 2629267 | 2629267 | same | same | same | same | same | same | same | same |
| check_with_castling_rights_d6 | `r3k2r/8/8/8/8/4R3/8/R3K2R b KQkq - 0 1` | 6 | 4 | 90033768 | none used | same | same | same | same | same | same | same | same |

## 6. Edge suite, warm states, Threads

**Edge suite.** The suite has 410 distinct legal positions, 17 positions that `set_fen` rejects and 4 that it accepts although no legal game reaches them. Every entry has a category, a provenance and a predicate that an independent rules oracle checked (own Python code that shares nothing with the engine; validated on published perft counts and on deliberately wrong labels). The suite is `suite/edge_suite.tsv`. For every legal entry and for every position reached from it by one made move, all fields were compared on the probes; on the release executables the entry was asked `go perft 1` and `go perft 2`, and every position after one move `go perft 1`. The lock's move set (probe and executable) and its checkers (probe) were also compared with the oracle's. Entries that `set_fen` rejects, and entries it accepts although no legal game reaches them, are kept apart: they are robustness evidence, not legal-position evidence. For the rejected ones the engine's refusal text and the unchanged board were compared; the unreachable ones ran one process each.

Legal entries by category (336 from hand-made bases and their colour and file mirrors, 74 mined from playouts): castling_blocked 4, castling_gives_check 4, castling_into_attack 4, castling_legal 8, castling_out_of_check 4, castling_through_attack 4, check_by_capture 8, check_knight 6, check_pawn 4, check_slider 16, checkmate 14, discovered_check 24, double_check 10, double_check_given 12, ep_discovered_check 8, ep_gives_check 4, ep_illegal_diagonal_pin 4, ep_illegal_rank_pin 4, ep_in_check 4, ep_legal 4, ep_pinned_but_legal 4, ep_removes_checker 8, ep_square_only 4, evasion_gives_check 8, has_legal_move_witness 12, high_move_count 8, king_pawn_structure 24, mined_castle_gives_check 5, mined_checkmate 7, mined_discovered_check 7, mined_double_check 7, mined_double_check_given 7, mined_ep_illegal 1, mined_ep_in_check 6, mined_ep_legal 7, mined_high_move_count 8, mined_pinned_capture_of_checker 3, mined_promotion_gives_check 8, mined_promotion_in_check 4, mined_stalemate 4, pawn_capture_edge 4, pawn_capture_order 4, pawn_push_check 8, pinned_evasion 20, promotion_capture 14, promotion_discovered_check 4, promotion_gives_check 8, promotion_illegal 4, promotion_in_check 8, promotion_push 4, stalemate 16, standard_perft 16, underpromotion_check 8. Rejected: invalid_adjacent_kings, invalid_castling, invalid_en_passant, invalid_inventory, invalid_kings, invalid_opponent_in_check, invalid_pawn_rank, invalid_syntax. Unreachable: unreachable_double_knight_check, unreachable_ep_in_check, unreachable_pawn_structure, unreachable_triple_check.

| Tag | Legal entries | Tier A records identical | Tier R perft blocks identical | Rejected entries handled like the lock (A / R) | Unreachable entries like the lock (A / R) | Search signature depth, net on / off | Lock against oracle, differences | Result |
|---|---|---|---|---|---|---|---|---|
| LOCKCOPY | 410 | EQUAL 14220 | EQUAL 7725 | True / True | True / True | d12: True / True | 0 | MATCH |
| LOCKEQ | 410 | EQUAL 14220 | EQUAL 7725 | True / True | True / True | d12: True / True | 0 | MATCH |
| EVL | 410 | EQUAL 14220 | EQUAL 7725 | True / True | True / True | d12: True / True | 0 | MATCH |
| PCM | 410 | EQUAL 14220 | EQUAL 7725 | True / True | True / True | d12: True / True | 0 | MATCH |
| CKL | 410 | EQUAL 14220 | EQUAL 7725 | True / True | True / True | d12: True / True | 0 | MATCH |
| WNP | 410 | EQUAL 14220 | EQUAL 7725 | True / True | True / True | d12: True / True | 0 | MATCH |
| KPC | 410 | EQUAL 14220 | EQUAL 7725 | True / True | True / True | d12: True / True | 0 | MATCH |
| BUN | 410 | EQUAL 14220 | EQUAL 7725 | True / True | True / True | d12: True / True | 0 | MATCH |

**Warm states.** One process per executable, Threads 1, in this order: twelve positions searched to depth 16 twice in a row (cold, then warm tables); four of them to depth 17 after `ucinewgame`; six with Hash 1 and six with Hash 64, without `ucinewgame`; twelve searches with the net off and four with it on again; four searches after `Clear Hash`, each followed by a perft 3; then a 40-ply game line searched to depth 12 at every ply with the tables kept; at the end `bench 13` must still be the pin. That is 101 searches. Every info line (depth, selective depth, score, nodes, hash fill, principal variation; without time and speed) and every bestmove must equal the lock's.

**Threads.** Six blocks per executable with Threads 2, 3, 4, 3, 2 and 4 and 16 MiB of hash per thread; each block has twelve searches of one million nodes and one `go infinite` ended by `stop`, and is followed by `ucinewgame` and `Clear Hash`: 78 searches. Checked are the exit code, a bestmove for every search, its legality, and the bench-13 pin afterwards at Threads 1. This shows stability only. **Multithreaded search is not deterministic, so these runs do not establish node identity.**

| Tag | Pins | Perft divide | Warm transcript | Threads 2-4 soak | Edge suite |
|---|---|---|---|---|---|
| LOCK | MATCH 13/13 | MATCH 10/10 positions, every root move | MATCH 101 searches, 1677 lines, bench13 pin kept | STABLE 78 searches, exit 0, bench13 after 862329 | reference |
| LOCKCOPY | MATCH 13/13 | MATCH 10/10 positions, every root move | MATCH 101 searches, 1677 lines, bench13 pin kept | STABLE 78 searches, exit 0, bench13 after 862329 | MATCH |
| LOCKEQ | MATCH 13/13 | MATCH 10/10 positions, every root move | MATCH 101 searches, 1677 lines, bench13 pin kept | STABLE 78 searches, exit 0, bench13 after 862329 | MATCH |
| EVL | MATCH 13/13 | MATCH 10/10 positions, every root move | MATCH 101 searches, 1677 lines, bench13 pin kept | STABLE 78 searches, exit 0, bench13 after 862329 | MATCH |
| PCM | MATCH 13/13 | MATCH 10/10 positions, every root move | MATCH 101 searches, 1677 lines, bench13 pin kept | STABLE 78 searches, exit 0, bench13 after 862329 | MATCH |
| CKL | MATCH 13/13 | MATCH 10/10 positions, every root move | MATCH 101 searches, 1677 lines, bench13 pin kept | STABLE 78 searches, exit 0, bench13 after 862329 | MATCH |
| WNP | MATCH 13/13 | MATCH 10/10 positions, every root move | MATCH 101 searches, 1677 lines, bench13 pin kept | STABLE 78 searches, exit 0, bench13 after 862329 | MATCH |
| KPC | MATCH 13/13 | MATCH 10/10 positions, every root move | MATCH 101 searches, 1677 lines, bench13 pin kept | STABLE 78 searches, exit 0, bench13 after 862329 | MATCH |
| BUN | MATCH 13/13 | MATCH 10/10 positions, every root move | MATCH 101 searches, 1677 lines, bench13 pin kept | STABLE 78 searches, exit 0, bench13 after 862329 | MATCH |

## 7. Differential fuzz

**Corpus.** Random and semi-random legal playouts, generated by the lock probe. Seeds: the start position, the eight positions of the engine's `bench`, the 12,000 positions of `fens_12k_v2.txt` (md5 `e7dbf2c8151188c03ef52054557a531e`), and edge positions. Per playout the seed class is drawn 70 % fens12k, 20 % edge, 5 % bench, 5 % start position; half the playouts choose uniformly among the legal moves, half weight en passant 16, captures 4, promotions 8, castling 8, double pushes 2, king moves 2 and checks 6 (multiplied); the length is 8 to 80 plies, 20 to 160 from the start position and the bench seeds, or until there is no legal move. Master seed `4D47465A20261110`; the chunk seed is the master seed xor (chunk + 1) x `9E3779B97F4A7C15`, through SplitMix64 into xoshiro256**. A chunk is 100,000 visited positions. Chunks 0 to 99 use the seed file `v1` (33 edge positions known before the suite existed), chunks 100 to 199 use `v2` (all legal suite entries); both files are identified by sha256 in every ledger row (`evidence/corpus/`). Nothing of the corpus is stored: a chunk is regenerated from its definition, and the ledgers keep its sha256.

**What one comparison is.** On the auxiliary tier one position comparison is one record: the generated lists All, Captures and Quiets in order, `is_legal` and `gives_check` for every generated move in three king-line states, the legal lists, the checkers on four routes, the checkers after every legal move, `has_legal_move` twice, eight eval values (net off, net on by refresh and incrementally, raw net, uncached, and re-evaluations of the positions one and eight plies back), and the null-move child. The lock's transcript and the candidate's must be byte-identical after their identity frames. On the release executables one comparison is one `go perft 2` block reached by `position fen <parent> moves <move>`: the legal moves in order and the number of legal replies to each (one process per executable and chunk, options Threads 1, Hash 16, OwnBook false; perft does not use the net).

A chunk counts only with status OK, and one candidate and chunk counts once however often it is run. Excluded or failed comparisons are the rows in the "not OK" columns.

| Candidate | Tier A: auxiliary probes, all fields | chunks | in check | quiet | eval net off | eval net on | not OK | Tier R: release exe, go perft 2 | chunks | tied to the lock probe | not OK |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EVL | 20,000,000 | 200 | 1,746,584 | 18,253,416 | 20,000,000 | 20,000,000 | 0 | 20,000,000 | 200 | 200 | 0 |
| PCM | 20,000,000 | 200 | 1,746,584 | 18,253,416 | 20,000,000 | 20,000,000 | 0 | 20,000,000 | 200 | 200 | 0 |
| CKL | 20,000,000 | 200 | 1,746,584 | 18,253,416 | 20,000,000 | 20,000,000 | 0 | 20,000,000 | 200 | 200 | 0 |
| WNP | 20,000,000 | 200 | 1,746,584 | 18,253,416 | 20,000,000 | 20,000,000 | 0 | 20,000,000 | 200 | 200 | 0 |
| KPC | 20,000,000 | 200 | 1,746,584 | 18,253,416 | 20,000,000 | 20,000,000 | 0 | 20,000,000 | 200 | 200 | 0 |
| BUN | 20,000,000 | 200 | 1,746,584 | 18,253,416 | 20,000,000 | 20,000,000 | 0 | 20,000,000 | 200 | 200 | 0 |

Every tier A record holds the static eval with the net off and with the net on, so the eval coverage by mode equals the tier A count in both modes.

The corpus has 200 chunks. Tier R covers all of them, each tied to the lock probe, for 6 of 6 candidates. Rows with a harness error or a timeout whose chunk also ran clean (listed, not counted, not blocking): 0.

A row is counted only if it names the frozen executables or the probes of the build receipts; rows that do not: 0. The tier A rows also carry the sha256 of the six harness files together (mgprobe.cpp, mg_format.py, mg_compare.py, uci_session.py, fuzz.py, pinguard3.py): `a234987c31fdbb18082ab1462ed157f482478a6f30705f09a2e57d4c1a46a3a7`. When this report was generated those files had the hash `a234987c31fdbb18082ab1462ed157f482478a6f30705f09a2e57d4c1a46a3a7`, which is the same. The rows of the release-executable ledger carry the executable, input and output hashes but not this one; they were written in the same hours by the same files.

Corpus v1:0-99, v2:100-199: 20,000,000 visited positions, 17,595,079 distinct by 64-bit position key and 2,404,921 repeats; 18,253,416 quiet and 1,746,584 in check, of which 6,865 in double check; 14,231 checkmates and 5,479 stalemates; 417,649 playouts; moves played: 2,372,110 captures, 118,981 promotions, 18,608 castlings, 14,765 en passant captures, 1,715,547 checks; 0 seeds rejected.

**Stale caches.** Inside every chunk the worker's pawn cache stays warm across playouts and is cleared at recorded points; every record also re-evaluates the positions one and eight plies back, which then meet cache entries written for later positions (often the same pawns with a king on another square). In addition, some chunks were replayed with two other cache histories:

| Candidate | never cleared: chunks OK | cleared before every playout: chunks OK | positions per chunk | not OK |
|---|---|---|---|---|
| EVL | 10 | 10 | 100,000 | 0 |
| PCM | 10 | 10 | 100,000 | 0 |
| CKL | 10 | 10 | 100,000 | 0 |
| WNP | 10 | 10 | 100,000 | 0 |
| KPC | 10 | 10 | 100,000 | 0 |
| BUN | 10 | 10 | 100,000 | 0 |

Chunks replayed: 0, 1, 2, 3, 4, 100, 101, 102, 103, 104. `never cleared` removes every cache-clear mark of the chunk, so every evaluation after the first meets a warm pawn cache; `cleared before every playout` starts every playout cold. To reproduce a row, the whole chunk is replayed in order (`README.md`): the state depends on the sequence, not on one FEN.

**Earlier run.** Before the first review the same corpus had been run with harness 1, which recorded fewer fields. It found no difference either. It is listed for completeness and is not added to the counts above.

| Candidate | Tier A positions | not OK | Tier R positions | not OK |
|---|---|---|---|---|
| EVL | 13,000,000 | 0 | 1,300,000 | 0 |
| PCM | 13,000,000 | 0 | 1,300,000 | 0 |
| CKL | 13,000,000 | 0 | 1,300,000 | 0 |
| WNP | 13,000,000 | 0 | 1,300,000 | 0 |
| KPC | 13,000,000 | 0 | 1,300,000 | 0 |
| BUN | 13,000,000 | 0 | 1,300,000 | 0 |

## 8. Supplementary evidence

**Do the inputs execute the changed lines?** The job forbids mutated engines, so sensitivity was shown another way: each candidate tree was also built with the compiler's source-based coverage (unchanged source, extra compiler flags), and the count of every instrumented line inside the candidate's `#if` region was read.

| Candidate | Switch | Instrumented lines in the `#if` region | Executed | Lowest count of a line | Highest count | Never executed |
|---|---|---|---|---|---|---|
| EVL | FORGE_SPD_EVADE_LEGAL | 16 | 16 | 2,173 | 8,729,308 | 0 |
| PCM | FORGE_SPD_PAWN_CAPMASK | 1 | 1 | 1,465,124 | 1,465,124 | 0 |
| CKL | FORGE_SPD_CHECKERS_KL | 8 | 8 | 3,387,775 | 14,922,010 | 0 |
| WNP | FORGE_SPD_WITNESS_NOPIN | 3 | 3 | 249,925 | 446,018 | 0 |
| KPC | FORGE_SPD_KING_PAWN_CACHE | 28 | 28 | 39,346 | 2,786,154 | 0 |
| BUN | FORGE_SPD_PAWN_CAPMASK | 1 | 1 | 1,465,124 | 1,465,124 | 0 |
| BUN | FORGE_SPD_EVADE_LEGAL | 16 | 16 | 2,173 | 8,729,308 | 0 |
| BUN | FORGE_SPD_CHECKERS_KL | 8 | 8 | 3,381,288 | 14,922,010 | 0 |

Inputs of the coverage runs: fuzz chunk 0 of seeds v1 (100,000 positions); fuzz chunk 100 of seeds v2 (100,000 positions); edge suite, 410 legal entries and their children. For WNP also: WITNESS_NOPIN targets, 1792 positions.

**WITNESS_NOPIN.** `has_legal_move` answers true almost everywhere, so random play says little about its shortcut. Its answer can only become wrong in a stalemate whose pawn pushes all belong to pinned pawns. Such positions were constructed for the king and pawn pairs on a common rank or diagonal, in both colours, and confirmed by the oracle. They are statically valid; whether a legal game reaches each one is not established, so they are reported here and not counted as fuzz or legal edge coverage.

| Tag | Targets | Decisive for the lock | Identical records | Result |
|---|---|---|---|---|
| LOCKEQ | 1,792 | 1,792 | 1,792 | MATCH |
| EVL | 1,792 | 1,792 | 1,792 | MATCH |
| PCM | 1,792 | 1,792 | 1,792 | MATCH |
| CKL | 1,792 | 1,792 | 1,792 | MATCH |
| WNP | 1,792 | 1,792 | 1,792 | MATCH |
| KPC | 1,792 | 1,792 | 1,792 | MATCH |
| BUN | 1,792 | 1,792 | 1,792 | MATCH |

For comparison, fuzz chunks 0-9 of seeds v1 (1,000,000 positions) contain 214 stalemates, 131 of them with a generated pawn push, that is decisive for WITNESS_NOPIN. Execution counts of the lines of the WITNESS_NOPIN region in the coverage build, which show how often the new test ran and how often its shortcut was taken: line 714 `if (checkers_ == 0 && attacks::line(king_square(side_), to - pawn_push_delta(side_)) == 0)` 446,018; line 718 `return true;` 249,925; line 719 `}` 249,925.

**Search output of the release executables.** The code of WITNESS_NOPIN and KING_PAWN_CACHE runs inside a release executable only during search. Search output does not stand in for move order, checkers or static eval; it is listed as supplementary evidence that those executables search identically.

| Candidate | net on | net off | positions | depth | exit codes |
|---|---|---|---|---|---|
| EVL | identical | identical | 100,000 | 7 | 0 / 0 |
| PCM | identical | identical | 100,000 | 7 | 0 / 0 |
| CKL | identical | identical | 100,000 | 7 | 0 / 0 |
| WNP | identical | identical | 100,000 | 7 | 0 / 0 |
| KPC | identical | identical | 100,000 | 7 | 0 / 0 |
| BUN | identical | identical | 100,000 | 7 | 0 / 0 |

One process per run, Threads 1, Hash 16, every info line and bestmove of `go depth` compared; tables kept between positions and reset every 500.

**Probe against its own release executable.**

| Tag | Positions | Identical lists | Result |
|---|---|---|---|
| LOCK | 2,000 | 2,000 | MATCH |
| LOCKEQ | 2,000 | 2,000 | MATCH |
| EVL | 2,000 | 2,000 | MATCH |
| PCM | 2,000 | 2,000 | MATCH |
| CKL | 2,000 | 2,000 | MATCH |
| WNP | 2,000 | 2,000 | MATCH |
| KPC | 2,000 | 2,000 | MATCH |
| BUN | 2,000 | 2,000 | MATCH |

## 9. Differences found

None. No check reported a difference, so there is no first offending FEN, field or replay to give.

The failure folder `out\job3\fail` is empty: no run ever wrote failure evidence.

## 10. Limits

- **Finite testing.** Equivalence is shown on the positions tested, not for every position.
- **How much ran on the release executables.** On the release executables themselves the fuzz compared 20,000,000 positions per candidate (200 of the 200 chunks of the corpus), and what it compares there is the legal moves, their order and the number of replies to each move, nothing else. A PASS requires all 200 chunks; a candidate with fewer is INCOMPLETE.
- **Two artifacts.** Checkers, `has_legal_move`, `is_legal`, `gives_check` and static eval were compared on auxiliary probes: the same source files, but compiled at `-O3` without link-time and profile-guided optimisation and with another `main`. A defect that only the release build's code generation introduces would have to show in what the release executables print: pins, perft divide, move lists and reply counts, warm transcripts, search signatures.
- **No planted faults.** Job 3 did not build mutated engines. That the comparator can fail is shown by the self-test's corrupted fixtures; that the inputs reach the patches is shown by line coverage. Job 2 ran mutants against its own harness.
- **WITNESS_NOPIN.** The positions that decide its answer are rare in play (see section 8) and the targeted set is constructed. Inside the release executable its code runs only during search, where a wrong answer at a stalemate node would most likely not change the printed output.
- **Threads.** The soak shows no crash, hang or illegal move; it does not show node identity.
- **The corpus** is what random and weighted playouts from the given seeds reach. The counts of distinct positions, checks, mates and special moves are in section 7.
- **The oracle** was validated on published perft counts to depth 3 or 4 and on wrong labels. It vouches for labels, move sets and checkers of the edge entries and the targets, not for move order.
- **The incremental accumulator path** was exercised one ply at a time inside windows of 64 plies; the multi-ply walk-back of the search was not, and no candidate changes that code.
- **Review.** A second model reviewed only the first version of the probe, the comparators and the UCI driver. The changes that made harness 2, the runners (`fuzz.py`, `checks_release.py`, `edge.py`), the oracle, the coverage and target tools and the report generator were reviewed by their author only (`REVIEW_LOG.md`). What stands in for that review is the self-test, whose controls ran against the final code.
- **Timing** was not measured and nothing here is a statement about speed.

## 11. Replay

Every ledger row can be replayed from its chunk number: `README.md` gives the commands. The probes report their identity (`mgprobe id`), and every transcript begins with it. After the counted runs some of their rows were run again from their definition (seeds file, master seed, chunk number), and every hash of the new run was compared with the row: the input, both outputs and both binaries.

| Tier | Candidate | Chunk | Seeds | Row written | Replayed | Result | Hashes equal to the ledger row |
|---|---|---|---|---|---|---|---|
| A | BUN | 0 | v1 | 19:58:30 | 20:43:01 | REPRODUCED | 7 of 7 |
| A | BUN | 57 | v1 | 20:08:36 | 20:43:14 | REPRODUCED | 7 of 7 |
| A | BUN | 99 | v1 | 20:16:15 | 20:43:27 | REPRODUCED | 7 of 7 |
| A | BUN | 100 | v2 | 20:16:30 | 20:43:41 | REPRODUCED | 7 of 7 |
| A | BUN | 143 | v2 | 20:25:10 | 20:43:54 | REPRODUCED | 7 of 7 |
| A | BUN | 199 | v2 | 20:35:40 | 20:44:08 | REPRODUCED | 7 of 7 |
| A | CKL | 0 | v1 | 19:58:25 | 20:42:56 | REPRODUCED | 7 of 7 |
| A | CKL | 57 | v1 | 20:08:31 | 20:43:09 | REPRODUCED | 7 of 7 |
| A | CKL | 99 | v1 | 20:16:11 | 20:43:22 | REPRODUCED | 7 of 7 |
| A | CKL | 100 | v2 | 20:16:24 | 20:43:36 | REPRODUCED | 7 of 7 |
| A | CKL | 143 | v2 | 20:25:05 | 20:43:49 | REPRODUCED | 7 of 7 |
| A | CKL | 199 | v2 | 20:35:36 | 20:44:03 | REPRODUCED | 7 of 7 |
| A | EVL | 0 | v1 | 19:58:22 | 20:42:52 | REPRODUCED | 7 of 7 |
| A | EVL | 57 | v1 | 20:08:28 | 20:43:06 | REPRODUCED | 7 of 7 |
| A | EVL | 99 | v1 | 20:16:08 | 20:43:19 | REPRODUCED | 7 of 7 |
| A | EVL | 100 | v2 | 20:16:21 | 20:43:32 | REPRODUCED | 7 of 7 |
| A | EVL | 143 | v2 | 20:25:01 | 20:43:46 | REPRODUCED | 7 of 7 |
| A | EVL | 199 | v2 | 20:35:33 | 20:43:59 | REPRODUCED | 7 of 7 |
| A | KPC | 0 | v1 | 19:58:28 | 20:42:59 | REPRODUCED | 7 of 7 |
| A | KPC | 57 | v1 | 20:08:34 | 20:43:12 | REPRODUCED | 7 of 7 |
| A | KPC | 99 | v1 | 20:16:14 | 20:43:26 | REPRODUCED | 7 of 7 |
| A | KPC | 100 | v2 | 20:16:28 | 20:43:39 | REPRODUCED | 7 of 7 |
| A | KPC | 143 | v2 | 20:25:08 | 20:43:53 | REPRODUCED | 7 of 7 |
| A | KPC | 199 | v2 | 20:35:39 | 20:44:06 | REPRODUCED | 7 of 7 |
| A | PCM | 0 | v1 | 19:58:24 | 20:42:54 | REPRODUCED | 7 of 7 |
| A | PCM | 57 | v1 | 20:08:30 | 20:43:07 | REPRODUCED | 7 of 7 |
| A | PCM | 99 | v1 | 20:16:09 | 20:43:21 | REPRODUCED | 7 of 7 |
| A | PCM | 100 | v2 | 20:16:23 | 20:43:34 | REPRODUCED | 7 of 7 |
| A | PCM | 143 | v2 | 20:25:03 | 20:43:48 | REPRODUCED | 7 of 7 |
| A | PCM | 199 | v2 | 20:35:34 | 20:44:01 | REPRODUCED | 7 of 7 |
| A | WNP | 0 | v1 | 19:58:27 | 20:42:57 | REPRODUCED | 7 of 7 |
| A | WNP | 57 | v1 | 20:08:33 | 20:43:11 | REPRODUCED | 7 of 7 |
| A | WNP | 99 | v1 | 20:16:12 | 20:43:24 | REPRODUCED | 7 of 7 |
| A | WNP | 100 | v2 | 20:16:26 | 20:43:38 | REPRODUCED | 7 of 7 |
| A | WNP | 143 | v2 | 20:25:06 | 20:43:51 | REPRODUCED | 7 of 7 |
| A | WNP | 199 | v2 | 20:35:37 | 20:44:04 | REPRODUCED | 7 of 7 |
| R | BUN | 3 | v1 | 20:01:03 | 20:45:14 | REPRODUCED | 8 of 8 |
| R | BUN | 31 | v1 | 20:20:51 | 20:46:18 | REPRODUCED | 8 of 8 |
| R | BUN | 99 | v1 | 21:07:14 | 22:13:37 | REPRODUCED | 8 of 8 |
| R | BUN | 100 | v2 | 21:07:55 | 22:15:00 | REPRODUCED | 8 of 8 |
| R | BUN | 199 | v2 | 22:12:05 | 22:16:10 | REPRODUCED | 8 of 8 |
| R | CKL | 3 | v1 | 20:00:47 | 20:44:46 | REPRODUCED | 8 of 8 |
| R | CKL | 31 | v1 | 20:20:32 | 20:45:51 | REPRODUCED | 8 of 8 |
| R | CKL | 99 | v1 | 21:06:59 | 22:13:07 | REPRODUCED | 8 of 8 |
| R | CKL | 100 | v2 | 21:07:39 | 22:14:26 | REPRODUCED | 8 of 8 |
| R | CKL | 199 | v2 | 22:11:48 | 22:15:46 | REPRODUCED | 8 of 8 |
| R | EVL | 3 | v1 | 20:00:36 | 20:44:27 | REPRODUCED | 8 of 8 |
| R | EVL | 31 | v1 | 20:20:20 | 20:45:33 | REPRODUCED | 8 of 8 |
| R | EVL | 99 | v1 | 21:06:49 | 22:12:45 | REPRODUCED | 8 of 8 |
| R | EVL | 100 | v2 | 21:07:29 | 22:14:04 | REPRODUCED | 8 of 8 |
| R | EVL | 199 | v2 | 22:11:35 | 22:15:23 | REPRODUCED | 8 of 8 |
| R | KPC | 3 | v1 | 20:00:57 | 20:45:05 | REPRODUCED | 8 of 8 |
| R | KPC | 31 | v1 | 20:20:45 | 20:46:09 | REPRODUCED | 8 of 8 |
| R | KPC | 99 | v1 | 21:07:09 | 22:13:27 | REPRODUCED | 8 of 8 |
| R | KPC | 100 | v2 | 21:07:50 | 22:14:48 | REPRODUCED | 8 of 8 |
| R | KPC | 199 | v2 | 22:12:00 | 22:16:02 | REPRODUCED | 8 of 8 |
| R | PCM | 3 | v1 | 20:00:42 | 20:44:37 | REPRODUCED | 8 of 8 |
| R | PCM | 31 | v1 | 20:20:26 | 20:45:42 | REPRODUCED | 8 of 8 |
| R | PCM | 99 | v1 | 21:06:54 | 22:12:57 | REPRODUCED | 8 of 8 |
| R | PCM | 100 | v2 | 21:07:34 | 22:14:15 | REPRODUCED | 8 of 8 |
| R | PCM | 199 | v2 | 22:11:41 | 22:15:35 | REPRODUCED | 8 of 8 |
| R | WNP | 3 | v1 | 20:00:52 | 20:44:55 | REPRODUCED | 8 of 8 |
| R | WNP | 31 | v1 | 20:20:38 | 20:46:00 | REPRODUCED | 8 of 8 |
| R | WNP | 99 | v1 | 21:07:04 | 22:13:17 | REPRODUCED | 8 of 8 |
| R | WNP | 100 | v2 | 21:07:45 | 22:14:37 | REPRODUCED | 8 of 8 |
| R | WNP | 199 | v2 | 22:11:54 | 22:15:55 | REPRODUCED | 8 of 8 |

## 12. Evidence

`evidence/TABLES.md` holds all generated tables, `evidence/VERDICTS.json` the gates per candidate. Receipts: `evidence/freeze`, `probes`, `pins`, `divide`, `warm`, `soak`, `edge`, `crosstier`, `search_sig`, `coverage`, `wnp_targets`, `replay`; ledgers: `evidence/fuzz_aux`, `fuzz_uci`, `fuzz_warm`, and `h1_earlier_run`; logs: `evidence/logs`, `evidence/selftest`. `MANIFEST.tsv` lists every file of the pack and every artifact that stays on the PC under `D:\forge_jobs_20261109\fable2\out\job3`, with MD5 and SHA256.
