long 21 prediction (the LmrRoundF sweep on B_FINE) -- own commit before the first counted run

The fine reduction r = (f + LmrRoundF) >> 10 is pointwise non-decreasing in LmrRoundF (same f,
larger addend, arithmetic shift): a bigger RoundF rounds more sites UP, i.e. reduces more. My
primary hypothesis: the node sums respond monotonically (decreasing sums as RoundF grows), with
T2 (RoundF 0, O 11,915,365 / G 22,952,032) and T1 (RoundF 512, O 10,170,054 / G 19,269,858) as
the two anchors.

1. The six sums on O are strictly decreasing in RoundF and each of 128/256/384 lies strictly
   between T2's and T1's sums; 640/768/896 lie strictly below T1's sum. Same shape on G.
   Kill: any inversion among the six on either set, or 128/256/384 not between the anchors, or
   640/768/896 not below T1.
2. The response is STEEP at the bottom: s(128) is within 15 percent of T2's sum (most of the
   T2-to-T1 drop happens by RoundF 128), and s(896) is within 12 percent of T1's sum or below it.
   Kill: s(128) below 0.85 x T2's sum, or s(896) above 1.12 x T1's sum.
3. The bestmove churn stays modest: at every swept value, bestmove-equal counts against the T1
   rows are at least 100 of 200 on O. Kill: below 100.
