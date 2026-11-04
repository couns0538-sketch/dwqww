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
