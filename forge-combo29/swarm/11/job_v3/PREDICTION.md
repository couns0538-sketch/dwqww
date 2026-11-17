# PREDICTION — v3 profiling job (FABLE_TO_swarm_7 Step 1)

Committed and pushed ALONE before the first measuring command of Step 1. Never edited afterwards.

Build: PC r15 source + `-DFORGE_NNUE_V3=1 -DFORGE_MATE_ALPHA_GUARD=1`, g++ 13.3.0, `-march=x86-64-v4`,
kernel `avx512`. Machine: Intel Xeon, 4 cores. Test net `fdff70de72e4ca82`. Settings PC20, Threads 1.
Step 0 passed all eleven numbers (`job_v3/step0_out.txt`).

1. **Hottest v3 function.** I predict `nnue::v3`'s incremental **refresh/update** path dominates — the
   function that folds the accumulator for the changed features on each make/unmake — with a share of
   `bench 13` time between **35 % and 60 %**.
   KILLED IF: the hottest v3 function is the forward pass (the output/activation evaluation) with a
   share above 30 %, or if no v3 function exceeds 20 %, or if the top v3 share is above 70 %.

2. **Forward pass share.** I predict the forward pass (features → hidden accumulation → output) is
   **15 % to 35 %** of `bench 13` time under PC20 + test net.
   KILLED IF: below 8 % or above 45 %.

3. **Search share drops.** Under the test net, the hand-crafted evaluation is gone (`hce 0` in every
   eval line), so search's own share should RISE relative to PC20-no-net. I predict total `nnue::v3`
   share between **45 % and 70 %** of `bench 13`.
   KILLED IF: under 35 % or over 80 %.

4. **Speed headroom.** I predict the v3 path is at least **1.5x more expensive per node** than the
   built-in net path (comparing `bench 13` nps with the test net against PC20-no-net).
   KILLED IF: the ratio is below 1.1x or above 4x.

5. **Node count identity holds under profiling.** The eight bench numbers must stay exactly as Step 0
   measured them even while profiling (profiling must not change results).
   KILLED IF: any of the eight changes.

6. **Timing noise.** Two builds of the same source will differ by **1 % to 6 %** on `bench 13` nps
   (file 7 quotes 4.2 % for another seat on other machines).
   KILLED IF: the two-build spread is under 0.5 % (suspiciously identical) or over 12 %.
