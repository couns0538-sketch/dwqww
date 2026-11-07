# T5 Fathom as an oracle for Forge's own Syzygy reader - RESULT

Tools: Fathom (MIT, jdart1/Fathom c9c6fef0); Forge's own reader from R13 P6 (`include/forge/syzygy.hpp`,
`src/syzygy.inc`; "no third-party probing code"). Tables: the PC's 3-4-5 piece set (145 WDL + 145 DTZ), read in place.
Commands: CMDS.md; hashes: SHA256SUMS; per-FEN outputs are hashed (not committed, 50,000 lines each).

## Agreement (tools/t5_compare.py, `logs/t5_compare_50k.txt`, `t5_result.json`)
50,000 seeded random legal 3-5 piece positions from all 145 materials (`tools/t5_gen_fens.py`, seed 20261106, sha256
a1b3ca09...; own stdlib generator, no python-chess). Each was probed by both readers.

| Check | Result |
|---|---|
| Forge probe failures (NA) / Fathom failures | 0 / 0 |
| WDL equal (-2..2, incl. cursed wins / blessed losses) | **50,000 / 50,000** |
| DTZ rows (Fathom root status ok) | 49,678 |
| DTZ exact (signed, Fathom root DTZ vs Forge `probe_dtz`) | **49,678 / 49,678** (0 within-1 cases needed) |
| Mate / stalemate rows (Fathom special results, WDL still compared) | 229 / 93 |
| **Verdict** | **AGREE** |

This extends R13 P6's check (220 positions vs python-chess's prober, 220/220) by about 227x, using a permissively
licensed oracle.

## Probe speed (warm, same compiler flags `-O2 -march=x86-64-v3`, g++ / gcc 15.2, CPUs 2-3 at Idle next to the trainer)

| Reader | Pass 1 | Pass 2 | Pass 3 |
|---|---|---|---|
| Forge `syzygy::probe_wdl` (`tools/t5_forge_wdl_timing.cpp`) | 1.59 us (cold) | 0.95 us | 1.00 us |
| Fathom `tb_probe_wdl` (`tools/t5_fathom_batch.c`) | 0.59 us (already warm: an output pass ran first) | 0.55 us | 0.54 us |

- Fathom's WDL probe is about **1.8x faster** on this set (warm passes), measured once on a shared core
  (`logs/*timing*`).
- In search this matters little: probes happen only with <= 5 pieces, and a Forge node costs ~0.4 us at 2.5M nps.
- The lock exe (trial_w6) has no SyzygyPath at all; the P6 line was gated by the crew (exe 150374ff).

## What this gives the crew
- Forge's own reader is now checked against an independent prober on 50k positions with zero WDL / DTZ mismatches. This
  is evidence for the existing Syzygy line, not a new feature.
- A permissive (MIT) fallback, Fathom or Pyrrhic, if the own reader ever needs replacing. It would be faster per probe
  but is not needed for correctness.
- Reusable harness: generator + two batch probers + compare script. They can re-check any future change to
  `syzygy.inc`, or a 6-piece set once a drive has ~68 GiB free for the WDL files.
