# GPU window for the Opus 30-h job (Item A)

Written release from the owner (Couns), received in this session at about 10:06 PC clock on 2026-11-04 (recorded
2026-11-04 10:11:00 PC clock = Vienna):

> "you are getting for 4 hours 6 cpu cores and the gpu so use it wisely and most  effeciently in  the in  the best way to get better results"

Reading used (strict):
- Window: about 2026-11-04 10:06 to 14:06 PC clock. The GPU is used only after the npt run that was live at the
  message (npt_k32h3_l1024_bs16k_e8x152m5_g072_lam10_w4_s47) has ended by itself: no npt python in the process list,
  GPU utilisation near zero, and one keeper tick showing "npt trainer running | NO". npt is never stopped or touched.
- Yield-only: the own GPU guard (opus_30h/a/o30_gpu_guard.py) suspends the own trainer if an npt-like trainer
  process appears, and on GPU hot spot / memory-junction limits (hard 76 / 86 C, resume 72 / 83, emergency 78 / 88,
  the same thresholds as F:\forge_nnue_train\tools\gpu_guard.ps1, which does not cover non-npt processes).
- 6 CPU cores = six logical CPUs in total for all own work: 0-1 running rematches (to ~12:00), 3 the Astra overlap
  scan (to ~11:20), 4-5 the GPU trainer, 2 exports / scoring. Idle priority. Freed cores go to sanity matches of the
  new nets.

## Extension: an additional 5-hour GPU + CPU window

Second written message from the owner (Couns), received in this session at about 13:18 PC clock on 2026-11-04
(recorded 2026-11-04 13:27 PC clock = Vienna):

> "also you get an additonal 5 hour gpu window and 5hour cpu window so use the whole 5 hours of the gpu and cpu to its fullest"

Reading used:
- "additional" = appended to the first window: about 2026-11-04 14:06 to 19:06 PC clock, same terms as above
  (yield-only GPU with the own guard, the same thermal limits, npt never touched; own CPU work at Idle on CPUs 0-6 only,
  the crew gate keeps CPUs 7-15). If the owner meant 13:18 to 18:18 instead, the GPU queue stops at 18:18; nothing
  else changes.
- CPU plan inside the window: CPUs 3-5 = GPU trainer (mask 0x38, full loader speed) + checkpoint scoring, CPU 2 = the
  run 5 sanity match, CPU 6 = the run 2 sanity match (then the run 3 one), CPUs 0-1 = the Item B kit build, then the
  R14 suite and further sanity matches.
- The first window's quote (above) cannot be verified from the branch; it is copied verbatim from the session
  (owner asked in CR item 13 to confirm it).

## Extension 2: another 2 h 40 min of CPUs 0-6 and the whole GPU

Third written message from the owner (Couns), received in this session at about 19:38 PC clock on 2026-11-04
(recorded 2026-11-04 19:40 PC clock = Vienna):

> "you got another 2h 40min for  cpu 0-6 and the whole gpu use it in the most efficient way please"

Reading used:
- Window: about 19:38 to 22:18 PC clock, same terms as before (yield-only GPU under the own guard with the same thermal
  limits, npt never touched; own work at Idle on CPUs 0-6 only, the crew gate keeps CPUs 7-15). The 30-h job itself
  ends ~22:17, so every run and match is planned to finish by ~21:50 and the rest is reporting.
- CPU plan: 2-3 = a 400-game sanity match of the KB32 soup Z32 (never played), 4 = 200 more games of the KB8 soup U8
  (new opening seed), 5-6 = the GPU trainer's loader + checkpoint scoring, 0-1 = the running Y8 / V16 matches, then the
  final checks, the abba.py A/A and more games.
