long 38 prediction (the SingularMargin ladder) -- own commit before the first counted run

1. The ladder's known rungs reproduce EXACTLY on O (my job-1 runs): SingularMargin 1 = 13,196,949,
   2 = 9,500,069, 3 = 8,186,451; on G (my long-28 runs): 1 = 21,442,517, 3 = 16,091,515.
   Kill: any differing sum.
2. The O ladder is monotonically DECREASING in the value: s(0) > 13,196,949 > 9,500,069 >
   8,186,451 > s(4) > s(6). s(4) in [7,600,000, 8,186,451]. Kill: any inversion.
3. The G ladder likewise decreasing: s(0) > 21,442,517 > 16,091,515 > s(4) > s(6). Kill: any
   inversion.
4. The bestmove churn is large at every non-default value on O: at least 40 of 200 best moves
   changed against S14 (job 1 saw 52 at value 1). Kill: any non-default value below 20.
5. At depth 14 on O, every non-default value's |ratio - 1| EXCEEDS its depth-12 |ratio - 1|
   (the long-29 amplification). Kill: any that shrinks relatively. The d14 anchor: 21,812,100
   EXACT.
6. The answer to the job's question: one step is NOT a small change -- it is between a fifth and
   two fifths of the tree on O (38.9 percent growth / 13.8 percent shrink at plus/minus one),
   already visible at depth 12. Kill: contradicted by the ladder's own numbers.
