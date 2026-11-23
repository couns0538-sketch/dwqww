PROPOSAL N8: Add two pre-rental rehearsal gates to P3b: (a) a 128-worker opening-seed disjointness and cross-worker duplicate-rate gate, and (b) a cheap small-scale NVIDIA/Triton parity & export smoke test before booking H100/B300 hours.

KIND: source fact

EVIDENCE:
1. **100% deterministic `selfgame` (`source/src/uci.cpp:448-615`):** `run_selfgame` contains no internal RNG, no move-sampling temperature, and no `clear_hash()` call. Under `Threads 1` and `Hash 16` (`loop/LOOP_OPTIONS.txt:1-2`), two workers fed the same opening position with the same hash state play the exact same game move-for-move.
2. **Scale jump on the 64-core server (`debate/PLAN.md:94-99`):** Producing 2-4 billion positions in 24 hours across 128 workers (~8x today's worker count, ~125-250 rounds worth of positions in one day) requires tens of millions of distinct games (exact mean kept positions/game on round 136: not checked; estimated ~100 kept rows/game -> ~20-40M games). Without enforced disjoint per-worker RNG/opening streams (and sufficient opening-book + random-ply entropy), seed collisions or opening wrap-around can silently duplicate a large fraction of the paid day's games.
   - Reference baseline from `debate/evidence/fable_filter_shares_round136.md:39-40`: across two consecutive PC rounds (135 vs 136), exact non-endgame position repeats were `8/20,811` (`0.04%`) at ply `< 20` and `16/34,447` (`0.05%`) at ply `20-39`.
3. **Untested AMD-to-NVIDIA Triton port & VRAM fit (`debate/PLAN.md:99-100,178-183`):** Today's trainer runs on an AMD GPU under Windows with Triton kernels (`PLAN.md:178-179`); the NVIDIA port is explicitly marked `not tested`, and an H100's 80 GB VRAM is just under the 83 GB needed for 2B positions in today's 40.8 B/row layout (`PLAN.md:99-100`), while B300 VRAM is `not checked`. Debugging ROCm-vs-CUDA kernel quirks or OOM errors on a paid H100/B300 wastes rental budget.

COST:
- Part (a): ~5 CPU minutes during the existing P3b unattended rehearsal (plus ~2 minutes on the rented server's startup pilot). 0 GPU hours.
- Part (b): ~10-15 minutes on a cheap single NVIDIA GPU (or brief smoke window before starting a multi-hour run) + 2 minutes CPU verification on the PC.

HOW IT IS JUDGED:
1. **Cross-worker diversity & seed gate (P3b CPU rehearsal + server pilot):**
   - Launch `W` workers (`W = 16` in WSL/PC rehearsal, `W = 128` in the server pilot) with explicit worker-index-derived unique seeds logged to the run manifest.
   - Measure cross-worker exact position duplicates (4-field FEN key, ply `< 40`) across the pilot's first >= 100,000 rows: require `< 0.5%` cross-worker duplicate rate (matching the PC's `< 0.1%` non-endgame baseline).
   - Negative control: launch a 2-worker test with an identical seed and require the launcher's preflight check to abort before play.
   - Also check `ucinewgame` (or explicit hash-clear policy) between games is deterministic and documented so worker restarts do not silently change game statistics.
2. **NVIDIA Triton & export parity smoke gate (P3b GPU pre-check):**
   - Run a short fixed-seed training (e.g., 1 pass on 1 round = ~15M positions) on NVIDIA before starting a 2B run.
   - Verify: (i) zero Triton/CUDA compilation or runtime errors, (ii) exported `.fnn3` loads cleanly on the PC (`load_from_bytes` checksum, `max|w1|`, `max|b1|`, `max|w2| <= 127`, `max|b1| + 32*max|w1| <= 32767`), (iii) trainer-vs-engine exact evaluation check passes on 1,000 positions (`FORGE_NNUE_V3_VERIFY=1` zero mismatches), and (iv) measured peak VRAM + rows/s confirms whether 2B fits resident or must use P3's streaming feeder on the rented GPU.

WHAT WOULD CHANGE MY MIND:
- If the self-play driver already uses a verified per-worker disjoint seed scheme + preflight collision check (and raw pilot duplicate numbers are provided), part (a) is satisfied immediately.
- If the rented GPU has confirmed VRAM > 83 GB + margin (e.g. B300) AND the owner decides to train using a standard already-NVIDIA-tested trainer instead of porting the custom AMD Triton kernels, update part (b) to verify only the `.fnn3` export and trainer-vs-engine parity on that trainer.
