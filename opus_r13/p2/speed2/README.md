# FORGE_SEARCH_SPEED2 - node-identical search speed build switch on the lock tree (R14 Main item 2) - UNPROVEN

## Exe (not in git)
- `D:\o14a\handoff\speed2\forge_ltopgo_speed2_de20653c.exe`, sha256 **de20653cea8ce61027223ae3a11e79e75d08a09df57a0e5de02959ad9ed235c8**
  (kit v2.3 md5 729fe727, `-Expose`, workload v1, two clean rebuilds pc1 = pc2). Source: lock d4f4312 + `speed2_port.patch`
  (-p1) with `#define FORGE_SEARCH_SPEED2 1` (the kit takes no -D flags; `port_speed2.py --default 1`).
- No UCI option: the switch is compiled in. `uci` output is identical to the lock's (61 options).

## What it changes (speed only; every search decision and node count stays the lock's)
1. TT prefetch of the child cluster right after the null move and after the ProbCut make (the lock already prefetches
   after make_move in qsearch and the main loop) -> every make on the search paths prefetches.
2. MovePicker: quiet scores through one helper with the history row and the two continuation tables read once per
   generation and the moved piece once per move; capture scores with moved / captured piece read once (crew's speedmp2).
3. piece_type() by a 16-entry table instead of the modulo (speedmp2 form).

## Proof (details and evidence paths: ../RESULTS.md, section "R14 Main item 2")
| check | result |
|---|---|
| plain builds at 0 and 1: bench d11-d22, perft 5, 8 FENs nodes + bestmoves | identical, = lock pins 312866 / 862329 / 3024920 / 12389307 / 34048354, 4865609 / 193690690 |
| switch is live (codegen) | prefetch instructions 3 -> 5, modulo-by-6 sequences 68 -> 11 |
| kit build with the switch at 0 | sha256 = FD3A5190 (the lock exe, byte for byte) |
| kit build with the switch at 1, pc1 = pc2 | de20653c, NODE IDENTITY ALL OK vs the pins, 0 missing-profile warnings |
| T1 / T4 movetime smoke | 8 / 8 legal bestmoves; mate probe 19 = the lock's |
| CI ASan+UBSan (Threads 1 and 2, switch 0 and 1) | 0 illegal, 0 sanitizer lines |
| advisory ABBA vs the lock (10 pairs, CPU 2) | d16 +3.0 % / d20 +2.8 % engine nps (cpu nps +2.6 / +2.9 %), A/A noise up to +2.6 %: advisory, UNPROVEN - QA does the official timing |

## For the crew
Engine A = this exe with no setoption, engine B = lock FD3A5190. PC precondition: bench 13 = 862329 (all pins = lock).
Being node-identical, any strength change can only come from speed: QA's timing decides whether a gate is worth it.
