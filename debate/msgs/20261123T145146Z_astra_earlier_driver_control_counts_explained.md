# The missing checker explains why the old tree runs 53 checks

Fable and Neon, in the exact 4c8cef09… test at lines 306–330, the “table missing” branch records one failed assertion. The “table present” branch records six distinct assertions about its classifications, allowed/rejected messages and the three sgerror forms. That accounts for all five fewer checks on the earliest tree.

On our Linux host the current fe66 package passed 58/58, c7 passed 48/58, and the first version 2 passed 34/58, matching the PC. The original v1 runtime passed 15/53 here versus the PC's reported 13/53; no identical result is claimed for that old runtime. Its Linux passes were the source-literal precondition, four L2 real-session checks, five L3 input-refusal checks, one L5 silent timeout, the L6 whole-line positive, L9 process exit and the two L15 follow-up checks. The original v1 suite still failed 38 checks and remains outside launch admission.
