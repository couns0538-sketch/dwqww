| gate | why | recorded | replay | decided at pair (games) | LLR recorded / replay(printed pairs) | singles | exit | s |
|---|---|---|---|---|---|---|---|---|
| gate_sf26bundle14_vs_AL1 | [0,10] cap 1500, LLR -1.68 | CAP | CAP | None (None) | -1.68 / -1.6767 at 750 | 0 | 0 PASS | 2.5 |
| gate72_B4_bundleint_vs_h256e12_confirm | [0,10] H1 at 2108 games | H1 | H1 | 1054 (2108) | 2.96 / 2.9631 at 1054 | 2 | 0 PASS | 4.1 |
| gate68_bundle_g43g33g49_vs_h256e12 | [0,10] H1 with 2 in-flight singles | H1 | H1 | 695 (1390) | 2.99 / 2.9921 at 695 | 2 | 0 PASS | 2.6 |
| gate71_B3_bundleint_vs_h256e12 | [0,10] H0 at 2160 games | H0 | H0 | 1080 (2160) | -2.99 / -2.9895 at 1080 | 1 | 0 PASS | 4.2 |
| gate_stB_lmrttcapall1_vs_AL1 | [0,10] cap 3000 at LLR -2.88 (near the bound) | CAP | CAP | None (None) | -2.88 / -2.8835 at 1500 | 0 | 0 PASS | 6.5 |
| gate69_B1_bundleint_vs_h256e12_confirm | [0,10] cap 3000 at LLR 2.77 (near the bound) | CAP | CAP | None (None) | 2.77 / 2.7659 at 1500 | 0 | 0 PASS | 4.8 |
| gateR7_ttexclusive_nonreg_vs_r7off | [-10,0] non-regression H1 | H1 | H1 | 1267 (2534) | 2.96 / 2.9577 at 1267 | 1 | 0 PASS | 4.7 |
| uhoO30U8soup_v2p4_v2net_vs_AL1lp | [0,5] H1, net gate with early-stop rule, UHO book | H1 | H1 | 1264 (2528) | 2.95 / 2.9483 at 1264 | 1 | 0 PASS | 5.7 |
| uhoE3a_evalmatscale12_r6k_vs_AL1lp | [0,10] cap 6000 (largest PGN, 36 MB) | CAP | CAP | None (None) | 0.78 / 0.785 at 3000 | 0 | 0 PASS | 13.3 |
| uhoE3b_evaloptimism40_r6k_vs_AL1lp | [0,10] H0 at 2360 games, UHO | H0 | H0 | 1180 (2360) | -2.99 / -2.9912 at 1180 | 0 | 0 PASS | 4.6 |
| gateR5A_2_corrext1_vs_r5aoff | [0,10] cap, recorded NOT CLEAN (3 time losses) | CAP | CAP | None (None) | 0.41 / 0.408 at 1500 | 0 | 0 PASS | 4.2 |
| uhoT2_sf26b14 | [0,10] cap, recorded TRIAL-ONLY | CAP | CAP | None (None) | -1.44 / -1.4436 at 750 | 0 | 0 PASS | 3.3 |
| gate_npts3_ep06_vs_AL1 | [0,10] early H0 (net far below), 288 games; also used with --verify-moves | H0 | H0 | 144 (288) | -2.99 / -2.9941 at 144 | 0 | 0 PASS | 0.7 |

Deliberate failures (copies of gate_npts3_ep06_vs_AL1/gate_npts3_ep06_vs_AL1.pgn under F:/ospd/jobc/tmp_verify):

| copy | what was done | with log | exit | error line (stderr) | verdict printed? | result |
|---|---|---|---|---|---|---|
| truncated | file cut at byte 982649 inside a movetext | yes | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_truncated.pgn: game at line 16244 has no result token (truncated) | no | PASS |
| truncated | file cut at byte 982649 inside a movetext | no | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_truncated.pgn: game at line 16244 has no result token (truncated) | no | PASS |
| truncated_headers | file ends after a header block | yes | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_truncated_headers.pgn: file ends inside the headers of the game at line 13320 (truncated) | no | PASS |
| truncated_headers | file ends after a header block | no | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_truncated_headers.pgn: file ends inside the headers of the game at line 13320 (truncated) | no | PASS |
| corrupt_move | game 11: one SAN token replaced by Zz9 | yes | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_corrupt_move.pgn: game at line 944: not a SAN move: 'Zz9' (corrupt movetext) | no | PASS |
| corrupt_move | game 11: one SAN token replaced by Zz9 | no | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_corrupt_move.pgn: game at line 944: not a SAN move: 'Zz9' (corrupt movetext) | no | PASS |
| corrupt_result | game 21: result token changed, Result tag kept | yes | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_corrupt_result.pgn: game at line 1844: result token 0-1 differs from the Result tag 1-0 | no | PASS |
| corrupt_result | game 21: result token changed, Result tag kept | no | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_corrupt_result.pgn: game at line 1844: result token 0-1 differs from the Result tag 1-0 | no | PASS |
| corrupt_plycount | game 31: one move with its comment deleted | yes | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_corrupt_plycount.pgn: game at line 2797: PlyCount 49 but 48 moves in the movetext (truncated or corrupt) | no | PASS |
| corrupt_plycount | game 31: one move with its comment deleted | no | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_corrupt_plycount.pgn: game at line 2797: PlyCount 49 but 48 moves in the movetext (truncated or corrupt) | no | PASS |
| corrupt_binary | NUL / 0xFF bytes written over the middle | yes | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_corrupt_binary.pgn line 8853: NUL byte (binary garbage) | no | PASS |
| corrupt_binary | NUL / 0xFF bytes written over the middle | no | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_corrupt_binary.pgn line 8853: NUL byte (binary garbage) | no | PASS |
| unpaired | game 41 removed, its pair partner kept | yes | 2 | gate_replay: ERROR: round 21 has a single game: unpaired PGN (partner game 41 finished in the log but is missing from the PGN) | no | PASS |
| unpaired | game 41 removed, its pair partner kept | no | 2 | gate_replay: ERROR: round 21 has a single game: unpaired PGN (no log to prove the partner game was aborted in flight) | no | PASS |
| duplicated | game 51 written twice | yes | 2 | gate_replay: ERROR: round 26 has 3 games (expected 2): unpaired / duplicated PGN | no | PASS |
| duplicated | game 51 written twice | no | 2 | gate_replay: ERROR: round 26 has 3 games (expected 2): unpaired / duplicated PGN | no | PASS |
| corrupt_tag | a tag line without its closing bracket | yes | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_corrupt_tag.pgn line 1040: malformed tag line '[Round "7"' | no | PASS |
| corrupt_tag | a tag line without its closing bracket | no | 2 | gate_replay: ERROR: gate_npts3_ep06_vs_AL1_corrupt_tag.pgn line 1040: malformed tag line '[Round "7"' | no | PASS |

--verify-moves on gate_npts3_ep06_vs_AL1: exit 0, 288 games replayed move by move with python-chess in 2.9 s, verdict H0 vs recorded H0: PASS

Formula check on FORGE_RESULTS.csv: 111 rows with a Ptnml, LLR / Elo / nElo recomputed from the Ptnml: 0 differ by more than 0.006 (worst LLR difference 0.0050)
