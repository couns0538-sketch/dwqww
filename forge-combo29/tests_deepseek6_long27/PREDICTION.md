long 27 prediction (SENSITIVITY A: the S14 settings at plus/minus one step) -- own commit before the first counted run

1. The harness check reproduced: LmrHistoryDivisor 5644 on O sums EXACTLY 9,512,627 (the peer
   session's number). Kill: any difference.
2. Thirteen of the fourteen settings are the same plus/minus-one-step moves my job 1 measured on
   O (its Part-1 table): my fresh O sums must equal job 1's committed values EXACTLY --
   LmrQuietBase 85/101 = 10,081,111/9,314,278; LmrQuietDivisor 193/217 = 9,035,329/10,708,626;
   LmrNoisyBase 7/19 = 9,627,099/9,615,327; LmrNoisyDivisor 313/353 = 9,671,551/9,519,342;
   NullMoveBase 4/6 = 9,912,856/9,906,893; LmpBase 7/9 = 9,523,884/9,828,280;
   HistoryPruneMultiplier 2020/2420 = 9,530,219/9,579,620; HistoryBonusQuadratic 21/27 =
   9,358,128/9,502,882; HistoryBonusLinear 48/60 = 9,674,952/9,525,119; HistoryBonusMax
   2032/2392 = 9,522,214/9,745,469; LmrHistoryDivisor 5143/6143 = 9,632,276/9,746,633;
   SingularDepth 5/7 = 9,732,613/9,163,603; IirDepth 1/3 = 10,189,982/10,450,178.
   Kill: any differing sum.
3. Direction agreement across sets: every G sum moves the same way as its O sum (a setting whose
   O sum is above 9,500,069 has a G sum above 18,466,239, and below where below). Kill: any sign
   flip between the sets.
4. NonPawnCorrection false: a DIFFERENT tree on both sets (the correction switch is live).
   Kill: equality with the S14 sum on either set.
