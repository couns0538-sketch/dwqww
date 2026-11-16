long 28 prediction (SENSITIVITY B: the 22 default-anchored settings, plus/minus one step) -- own commit before the first counted run

1. The harness check reproduced: QsSeeMargin 100 on O sums EXACTLY 9,768,507 (kimi5's job 13,
   my own job-1 control). Kill: any difference.
2. All 44 O sums equal my job-1 Part-1 table EXACTLY (the same plus/minus-one-step moves on the
   same base; the table's 22 non-S14 settings). Kill: any differing sum.
3. Four settings are EXACT identities on BOTH sets (job 1 proved them on O; G now too):
   QsSeeMargin -c and +c, CaptureFutilityMultiplier -c and +c, CaptureFutilityDepth -c and +c --
   six runs with 353/353 nodes AND moves equal to S14 on G and 200/200 on O. Kill: any changed
   row in those six runs.
4. Direction agreement O/G: at least one SIGN FLIP exists among the remaining pairs (the long-27
   pattern says the two sets disagree somewhere; these 22 are the "other" half of the tuner's
   list). Kill: zero sign flips across all non-identity pairs.
5. No clamping: every run value lies inside its option's min..max (checked against the plain
   build's uci list before the runs). Kill: any clamp needed.
