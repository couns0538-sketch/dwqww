# Opus round report (Forge, AL1 s198) — status as of this branch

Work brief: `OPUS_PROMPT.md` + `OPUS_TEST_PLAN.md` (repo main). Job table: `opus_round1/SUMMARY.md`.

## Done
- **00_baseline**: lock reproduced on the Windows PC before any job — bench 312866/862329/3024920/12389307/34048354,
  perft 4865609, kiwipete 193690690, FMA 0, ctest 13/14 with exactly the 4 known lines; the rebuilt exe is
  byte-identical to the PC lock exe except the PE timestamp/checksum (`opus_round1/00_baseline/`).
- **O3** (`opus-O3`): search.cpp split into 14 modules + 6 headers, `ThreadData` struct, 3 new unit tests;
  bench/perft/depth-18x50 identical; NPS within 1%. Hot code was instruction-identical to the lock in the PC
  recipe build (a measured property of that build, see opus_round1/O3/REPORT.md); since the code review,
  Worker::search, qsearch and TT probe/store are pinned to 64 bytes (speed-neutral on a quiet runner).

## In progress / left (in order)
O1, C3, O2, C6, C2 (G-B1/G-B2 split), C1, C4, C5, O1-LTT, O5, O8, O4, O6, O7.

## Environment notes (read before re-using numbers)
- This PC was running a fastchess gate, self-play datagen and NNUE training the whole time. With the owner's OK all
  work ran at BelowNormal priority with at most 3 threads; speed numbers are noisy and must be re-measured on an idle
  machine before any speed claim.
- No Linux/TSan locally (WSL2 needs the Virtual Machine Platform feature + a reboot, not done; TSan has no Windows
  port; MinGW has no ASan; the VS 2026 STL rejects the installed clang 18). Linux release identity, ASan+UBSan and
  TSan evidence comes from `.github/workflows/opus-ci.yml` on each pushed `opus-*` branch.
- `C:\Users\Administrator\.wslconfig` was created during the attempted WSL install (caps WSL2 at 2 CPUs / 6 GB);
  delete it if you enable WSL2 and do not want the cap.
