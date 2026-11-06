# TtCutNodeDepth - numbers

All runs on CPUs 0-1 at Idle (tools pin themselves). Pins = the live lock trial_w6 4181A589 (net-on bench
312866 / 862329 / 3024920 / 12389307 / 34048354; net-off 375354 / 907205 / 2448617 / 13573040 / 24506465; perft 5
startpos 4865609, kiwipete 193690690).

## Identity build (macro FORGE_TT_CUT_NODE_DEPTH = 0, tree `tcn_id`)
| check | result |
|---|---|
| exe sha256 | 4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0 = trial_w6, `cmp` byte-identical |
| build quick pins | 312866 / 862329 / 3024920 OK |
| bitexact_check -Quick -SkipSan vs trial_w6 (`logs/bx_id.log`) | **BIT-EXACT** L1-L3: net on + off d11-d22 = pins, perft 5 startpos + kiwipete = pins, 2,000 / 2,000 FENs identical at depth 13 |

## Gate build (macro = 1, tree `tcn_gate`), runtime TtCutNodeDepth = 0 (default), TtCutNodeForm = 1 (default)
| check | result |
|---|---|
| exe sha256 (pc1 = pc2) | 8151e220360126264da984432ca2d5ad077c39aade78170b020d38ec35666d6b |
| advertised (MCP pin_check) | `TtCutNodeDepth type spin default 0 min 0 max 14`, `TtCutNodeForm type spin default 1 min 1 max 2` |
| build quick pins | 312866 / 862329 / 3024920 OK |
| bitexact_check -Quick -SkipSan vs trial_w6 (`logs/bx_gate_off.log`, started 03:33:50) | **BIT-EXACT** L1-L3: net on + off d11-d22 = pins, perft = pins, 2,000 / 2,000 FENs identical -> runtime defaults = the lock path |

## Gate build, runtime TtCutNodeDepth = 6, TtCutNodeForm = 1 (the gate ON line)
MCP `pin_check -Full TtCutNodeDepth=6;TtCutNodeForm=1`, 2026-11-06 03:33:47-03:34:32, priority Idle, mask 0x3:
verdict **LIVE**.

| bench (net on) | ON nodes | OFF = lock pin | ON / OFF |
|---|---|---|---|
| d11 | 354466 | 312866 | 1.133 |
| d13 | **759020** | 862329 | 0.880 |
| d16 | 3049356 | 3024920 | 1.008 |
| d20 | 10771342 | 12389307 | 0.869 |
| d22 | 25468915 | 34048354 | 0.748 |

- perft 5: startpos 4865609 and kiwipete 193690690, both = the pins.
- d13 != 862329, so the term is wired and live.
- The spec's ON sanity band "bench d20 within 1.5x of OFF" holds (0.87).
- The spec expected ON nodes to go up; at d13-d22 the bench totals are lower. Bench totals are no strength evidence.
- Form 2 ON bench, net-off ON benches and the counter box tests were not run (not in this brief).
