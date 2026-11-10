# TESTS (selftest.ps1)

Run: 20261110T091414Z (UTC, PC clock - see STATUS.md for the clock offset). Scratch: D:\forge_jobs_20261107\opus3\out\tests\selftest\20261110T091414Z
All tests use synthetic outcomes or saved/generated PGNs: no engine, no games, no Elo.

## R9 saved-run replay equivalence: PASS (exit 0)

```
PASS R9 stc1 replay, bounds_mode r9_clamp: 208 batches, 0 mismatches
PASS R9 stc1 replay, bounds_mode inner: 208 batches, 0 mismatches, batches that differ from R9 by design (shrink/projection/cap/E-006) 0, mismatches outside them 0
PASS R9 sanity3 replay, bounds_mode r9_clamp: 120 batches, 0 mismatches
PASS R9 sanity3 replay, bounds_mode inner: 120 batches, 1 mismatches first [(0, 'plus/minus')], batches that differ from R9 by design (shrink/projection/cap/E-006) 1, mismatches outside them 0
R9 EQUIVALENCE OK
```

## SPSA harness: PASS (exit 0)

```
PASS synthetic: every parameter moves toward a known interior optimum (>=25% of the distance): RazorBase 150->241.7 (opt 250, 92% of the way); RazorMultiplier 350->298.1 (opt 300, 104% of the way); QsFutilityMargin 160->121.1 (opt 120, 97% of the way); rc 0
PASS synthetic: no plus/minus engine value violates a bound or C1/C3': 0 violating plans
PASS synthetic: a run started at the optimum stays within 3 c_end: RazorBase 148.7, RazorMultiplier 352.6, QsFutilityMargin 158.0
PASS synthetic interaction: joint tuning heads for the joint optimum, one-family tuning does not: joint QsFutilityMargin 113.5 RazorBase 235.3 (joint opt 120/250); QsFutilityMargin alone 74.7 (coordinate-wise opt 72)
PASS synthetic constrained optimum: every plus/minus/theta feasible, run ends on the C1 boundary: violating plans 0, infeasible updates 0, inner projections 68, final RB+RM-QFM = 7.9, active ['C1']
PASS synthetic levels (harness capability, not the recommended config): only level values, C1/C2/C3' hold, both level coordinates carry updates: rc 0, plans 200, violating 0, batches with a QsSeeMargin level difference 45, RazorDepth 55; 
PASS crash reference: uninterrupted synthetic run of 10 batches: 25 state files
PASS crash at B0@0: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at B1@0: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at I6@0: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at I7@0: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at B2@3: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at P6@3: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at P7@3: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at B3@3:1: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at B3@3:3: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at B4@3: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at B5@3: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at B6@3: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at B7@3: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at B8@3: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at BC@10: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at C6@10: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS crash at C7@10: crashed (77), resumed, state byte-identical to the uninterrupted run, verify OK: rc 77/0/0 
PASS double crash (B3@2:2 then B6@5): byte-identical after the second resume: rc 77/77/0
PASS torn ledger tail (cut-off write): quarantined to ledger.torn.0.bin, run completes byte-identical: rc 0, torn files 1
PASS refuse a changed pinned exe on resume (exit 20): \\dummy_engine.exe sha256 42570f2ec6ce4bb8ce85982a6a80052061bb88fc4c5187611b587e8ab9b4247d != ca28f089d780b9720ec5e9ce61740681cc7db3be096e23acfa43c6f8a59d2b79"}
PASS refuse a changed config on resume (exit 11): {"refused": true, "exit": 11, "reason": "config differs from the run's RUN.json (a resume keeps its config)"}
PASS refuse resuming in another mode (exit 11): {"refused": true, "exit": 11, "reason": "run was created in mode synthetic, not replay"}
PASS refuse a corrupted HEAD checkpoint (exit 30): {"refused": true, "exit": 30, "reason": "ckpt_000008.json is malformed"}
PASS verify refuses a tampered older checkpoint (exit 30): {"refused": true, "exit": 30, "reason": "ckpt_000002.json differs from the ledger-derived state"}
PASS refuse a missing HEAD while several checkpoints exist (exit 30): {"refused": true, "exit": 30, "reason": "HEAD.json is missing while several checkpoints exist"}
PASS refuse a checkpoint more than one step past HEAD (exit 30): {"refused": true, "exit": 30, "reason": "ckpt_000099.json is more than one step past HEAD"}
PASS refuse a malformed record inside the ledger (exit 30): {"refused": true, "exit": 30, "reason": "ledger line 6: hash or encoding mismatch"}
PASS refuse a re-hashed pair record whose score does not match its games (exit 31): {"refused": true, "exit": 31, "reason": "pair test:0:1d7115a10aac/b000000/p000 score does not match its games"}
PASS refuse a re-hashed update that its pairs do not reproduce (exit 30): {"refused": true, "exit": 30, "reason": "update of batch 0 is not reproduced by its pairs"}
PASS refuse a pair recorded twice (duplicate result, exit 31): {"refused": true, "exit": 31, "reason": "pair test:0:6b943ba09447/b000004/p001 recorded twice"}
PASS refuse a result for a pair that was never planned (exit 31): {"refused": true, "exit": 31, "reason": "pair test:0:5834eea3ab60/b000004/p777 was not planned"}
PASS refuse a correctly chained ledger record of another run (stale run_id, exit 31): {"refused": true, "exit": 31, "reason": "ledger line 26 belongs to run test:0:85e64ca61e08 (stale)"}
PASS refuse an openings file listed as holdout/screen (exit 41, also in dry-run): {"refused": true, "exit": 41, "reason": "the openings file is a holdout/screen partition"}
PASS the holdout refusal ignores hex case (an uppercase pin as Get-FileHash prints it, exit 41): {"refused": true, "exit": 41, "reason": "the openings file is a holdout/screen partition"}
PASS refuse an unknown --mode before anything is written (exit 10): {"refused": true, "exit": 10, "reason": "unknown mode 'bogus' (dry-run, synthetic, replay, live)"}
PASS refuse identity_check 'start' outside synthetic qualification (exit 10, nothing written): {"refused": true, "exit": 10, "reason": "identity_check 'start' is for synthetic qualification only; game runs re-check the pins before every batch"}
PASS live mode refused without --live, without config.live.enabled, without LIVE_ACK (exit 40 x3): 91414Z\\harness\\ref_live\\run\\LIVE_ACK.txt containing the config sha256 bdac53190051401191e9ff75d38ca9aec1173b6e1e4e139323ef0b40862612e7"}
PASS dry-run (the default mode) starts no process and writes nothing; prints the fastchess command: rc 0, batch 0
PASS replay of R9's saved fastchess smoke PGN (2 games = 1 pair, both drawn): rc 0 
PASS replay of PGNs written from a synthetic run reproduces its theta trajectory exactly: rc 0, 6 updates 
PASS replay refuses incomplete pair (round 2 has one game) (exit 31): {"refused": true, "exit": 31, "reason": "PGN round 2 has 1 games (a pair needs exactly 2)"}
PASS replay refuses duplicate result (round 1 has three games) (exit 31): {"refused": true, "exit": 31, "reason": "PGN round 1 has 3 games (a pair needs exactly 2)"}
PASS replay refuses foreign engine name (exit 31): {"refused": true, "exit": 31, "reason": "PGN round 1: engines ['minus', 'other'] are not one game each as White"}
PASS replay refuses unfinished game (result *) (exit 31): {"refused": true, "exit": 31, "reason": "PGN round 1: unfinished or invalid result '*'"}
PASS replay refuses round outside the planned pairs (exit 31): {"refused": true, "exit": 31, "reason": "PGN round 9 is not a planned pair (1..4)"}
PASS replay refuses a manifest of another run (stale, exit 31): {"refused": true, "exit": 31, "reason": "replay manifest belongs to another run or config (stale)"}
PASS replay refuses a truncated PGN (sha256 differs from the manifest, exit 20): {"refused": true, "exit": 20, "reason": "replay PGN batch000.pgn changed"}
PASS rollback --to-ckpt 5 restores theta and k of checkpoint 5 as a new logged checkpoint; verify OK: rc 0/0 
PASS a rolled-back run resumes and still verifies: rc 0/0
PASS rollback --baseline prints the lock values and writes nothing: ": 350,
  "QsFutilityMargin": 160,
  "RazorDepth": 2,
  "QsSeeMargin": 40
 },
 "note": "lock exe: no options; gate exe: switches at 0 restore the lock values"
}
PASS export writes history.csv and candidate.json from the ledger: rc 0
PASS rollback of a COMPLETE run reopens it; the resumed run plays the missing batches, completes again, verifies: rc 0/0/0  
PASS rollback refuses a checkpoint that differs from the ledger-derived state (exit 30): {"refused": true, "exit": 30, "reason": "checkpoint 4 differs from the ledger-derived state; refusing to adopt its theta"}
PASS live attempt numbering skips attempts that left only a .out (no FileExistsError lock-up on resume): b000003_j000_a0 b000003_j000_a1 b000003_j000_a2
PASS E-006: plus = minus after rounding -> no update in inner mode; r9_clamp updates as R9 does: {'inner': (True, 0, 0.0, True), 'r9_clamp': (True, 0, 0.00080269111398934, True)}
PASS complete-record values: plain rounding breaks C1 by 1 here; the feasible repair gives the nearest feasible integers: plain {'RazorBase': 100, 'RazorMultiplier': 200, 'QsFutilityMargin': 301, 'RazorDepth': 2, 'QsSeeMargin': 40} fixed {'RazorBase': 100, 'RazorMultiplier': 201, 'QsFutilityMargin': 301, 'RazorDepth': 2, 'QsSeeMargin': 40}
63/63 PASS; HARNESS TESTS OK
```

## Confirmation pack: PASS (exit 0)

```
PASS negative control A/A (true nElo 0): H1 accepted at most alpha + 3 sigma: 0.000 of 300 runs (bound 0.088); H0 0, cap 300 [SYNTHETIC]
PASS positive control (true nElo 25; the 5000-game cap leaves little power below ~20): H1 accepted in >= 80%: 0.963 of 300 runs [SYNTHETIC]
PASS fake optimizer: the training-selected best of 20 equal candidates (selection-noise edge) is confirmed on fresh pairs; H1 at most alpha + 3 sigma: mean apparent training edge of the selected candidate +0.039 pair score, confirmation H1 rate 0.000 (bound 0.088) [SYNTHETIC]
PASS confirm dry-run (default) writes nothing and prints the fastchess command: rc 0
PASS refuse a cap that needs more pairs than the holdout has openings (exit 10, even in dry-run); allowed only with allow_opening_reuse: rc 10/0 enings would repeat. Lower cap_games to <= 600 or set allow_opening_reuse (a written QA decision)."}
PASS confirm synthetic run (true nElo 10): sequential GSPRT reaches a recorded decision, labelled SYNTHETIC: verdict cap, no decision (no claim), pairs 300, LLR 0.3307 
PASS confirm verify OK on the finished run: rc 0
PASS confirm crash at after_meta: resumed run records the same pairs and decision exactly once, verify OK: rc 77/0/0 
PASS confirm crash at after_start: resumed run records the same pairs and decision exactly once, verify OK: rc 77/0/0 
PASS confirm crash at after_register: resumed run records the same pairs and decision exactly once, verify OK: rc 77/0/0 
PASS confirm crash at after_pair@1: resumed run records the same pairs and decision exactly once, verify OK: rc 77/0/0 
PASS confirm crash at after_pair@37: resumed run records the same pairs and decision exactly once, verify OK: rc 77/0/0 
PASS confirm crash at ckpt_tmp@1: resumed run records the same pairs and decision exactly once, verify OK: rc 77/0/0 
PASS confirm crash at ckpt_renamed@1: resumed run records the same pairs and decision exactly once, verify OK: rc 77/0/0 
PASS confirm crash at after_decision: resumed run records the same pairs and decision exactly once, verify OK: rc 77/0/0 
PASS refuse a second confirmation run on a used holdout group (exit 41): fbd2 is registered in D:\\forge_jobs_20261107\\opus3\\out\\tests\\selftest\\20261110T091414Z\\confirm\\cli_basic\\run; it cannot run again elsewhere"}
PASS refuse a re-run in the same directory after it was deleted, and another candidate there (exit 41 x2): rc 41/41 un, but its CONFIRM.json is gone: a re-run is refused (one confirmation per group, ever)"} | \\selftest\\20261110T091414Z\\confirm\\cli_basic\\run (one confirmation per group, ever)"}
PASS synthetic without protocol.synthetic (10), replay without protocol.replay (10), live (40), unknown mode (10): refused before anything is written; no registry line, no run directory: rc 10/10/40/10 ion from that PGN with --mode replay (protocol.replay), or audits QA's own gate PGN with audit-pgn"}
PASS dry-run reports a synthetic candidate as not confirmable (mode and config pin), and a live candidate whose training config the protocol pins as confirmable: ['candidate comes from a synthetic training run, not a live one', "the protocol does not pin training_config_sha256 (QA's live tuning config, RUN.json config_sha256)"] | []
PASS refuse a peeking optimizer whose training read the holdout group (exit 41): {"refused": true, "exit": 41, "reason": "the holdout group was read by the training run (peeking)"}
PASS refuse a candidate spec whose content does not match its spec_sha256 (exit 10): {"refused": true, "exit": 10, "reason": "candidate spec_sha256 does not match its content"}
PASS refuse a changed candidate/baseline exe (exit 20):  "reason": "pinned base_exe changed: D:\\forge_jobs_20261107\\opus3\\out\\tests\\selftest\\20261110T091414Z\\confirm\\changes\\env\\dummy_engine.exe"}
PASS refuse resuming with a changed protocol (exit 11): {"refused": true, "exit": 11, "reason": "protocol, candidate or mode differ from this run's CONFIRM.json"}
PASS refuse a duplicated pair result (exit 31): {"refused": true, "exit": 31, "reason": "pair 4 recorded twice"}
PASS refuse a corrupt checkpoint (exit 30): {"refused": true, "exit": 30, "reason": "checkpoint does not match HEAD"}
PASS confirm live mode refused (exit 40) even with --live, protocol.live.enabled and LIVE_ACK: this runner never starts a game; nothing written: recomputes the decision from that PGN with --mode replay (protocol.replay), or audits QA's own gate PGN with audit-pgn"}
PASS replay refuses a candidate from a synthetic training run (not confirmable, exit 10), nothing written: es from a synthetic training run, not a live one; the protocol does not pin training_config_sha256 (QA's live tuning config, RUN.json config_sha256)"}
PASS confirm replay of a saved confirmation PGN (40 pairs) recomputes pentanomial counts and LLR; 40 < min_pairs 50, so no decision: rc 0 penta [8, 0, 16, 16, 0] verdict replay exhausted, no decision (no claim) 
PASS degenerate sample (40 identical pair scores): finite LLR, no decision before min_pairs: LLR 42.03, verdict None
PASS confirm replay refuses an incomplete pair (exit 31): {"refused": true, "exit": 31, "reason": "PGN round 7 has 1 games (pairs need exactly 2)"}
PASS audit-pgn (read-only) recomputes QA's SPRT data and finds the one leaked training position (FEN tags): rc 0 leaked 1 
PASS audit-pgn rebuilds the start position from {book} moves (PGN book, no FEN tag) and finds the 2 leaked pairs; the candidate is reported as not confirmable: rc 0 leaked 2 from {'book': 20} 
PASS audit-pgn fails closed on book moves it cannot replay (exit 31): GN game whose book moves cannot be parsed: IllegalMoveError(\"illegal san: 'Qxh7' in rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2\")"}
PASS select_candidate refuses an incomplete training run (fixed rule, exit 10): {"refused": true, "exit": 10, "reason": "training run is not COMPLETE (fixed rule: only the final theta of a complete run)"}
PASS select_candidate refuses a complete but synthetic training run unless --allow-nonlive; the spec then records training_mode: rc 10/0 rmable candidate (--allow-nonlive is for tests and demonstrations; the spec then records the mode)"}
35/35 PASS; CONFIRM TESTS OK
```

