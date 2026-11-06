# CutNoTtLmr - numbers

All runs on CPUs 0-1 at Idle (tools pin themselves). Pins = the live lock trial_w6 4181A589 (net-on bench
312866 / 862329 / 3024920 / 12389307 / 34048354; net-off 375354 / 907205 / 2448617 / 13573040 / 24506465; perft 5
startpos 4865609, kiwipete 193690690).

## Identity build (macro FORGE_CUT_NO_TT_LMR = 0, tree `cnl_id`)
| check | result |
|---|---|
| exe sha256 | 4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0 = trial_w6, `cmp` byte-identical |
| build quick pins | 312866 / 862329 / 3024920 OK |
| bitexact_check -Quick -SkipSan vs trial_w6 (`logs/bx_id.log`) | **BIT-EXACT** L1-L3: net on + off d11-d22 = pins, perft 5 startpos + kiwipete = pins, 2,000 / 2,000 FENs identical at depth 13 |

## Gate build (macro = 1, tree `cnl_gate`), runtime CutNoTtLmr = 0 (default)
| check | result |
|---|---|
| exe sha256 (pc1 = pc2) | dcdec9a7d71aec370cba9516ed75183f2ee433f71f6024ebdfa4e23c8a56a0c4 |
| advertised (MCP pin_check / uci) | `option name CutNoTtLmr type spin default 0 min 0 max 2` |
| build quick pins | 312866 / 862329 / 3024920 OK |
| bitexact_check -Quick -SkipSan vs trial_w6 (`logs/bx_gate_off.log`, started 03:29:14) | **BIT-EXACT** L1-L3: net on + off d11-d22 = pins, perft = pins, 2,000 / 2,000 FENs identical -> runtime 0 is the lock path |

## Gate build, runtime CutNoTtLmr = 1 (the gate ON value)
MCP `pin_check -Full CutNoTtLmr=1`, 2026-11-06 03:29:18-03:29:54, priority Idle, mask 0x3: verdict **LIVE**.

| bench (net on) | ON nodes | OFF = lock pin | ON / OFF |
|---|---|---|---|
| d11 | 318696 | 312866 | 1.019 |
| d13 | **780755** | 862329 | 0.905 |
| d16 | 2738962 | 3024920 | 0.905 |
| d20 | 16243524 | 12389307 | 1.311 |
| d22 | 26960018 | 34048354 | 0.792 |

- perft 5: startpos 4865609 and kiwipete 193690690, both = the pins.
- d13 != 862329, so the term is wired and live.
- The spec's ON sanity band "bench d22 total within 0.7x-1.5x of OFF" holds (0.79).
- d20 needs more nodes ON and d22 fewer. Bench totals at one depth are no strength evidence.
- Net-off ON benches were not run (not in this brief).
