long 35 prediction (long 17's eleven counters at depth 14 on O under S14) -- own commit before the first counted run

1. The depth-14 node sum = 21,812,100 EXACTLY (the known anchor). Kill: any difference.
2. The tree grows 2.296x from depth 12 (21,812,100 / 9,500,069). The gate ratio (against long
   17's 4,049,383) lands in [2.2, 2.6]. Kill: outside.
3. The depth-sensitive statements outgrow the tree: probcut_enter's ratio in [2.3, 3.2] and
   strictly ABOVE the tree ratio. Kill: outside, or below the tree ratio.
4. iir's ratio in [2.0, 3.0]. Kill: outside.
5. The frontier statement (razor_ret, depth <= 2) grows LEAST: its ratio in [1.5, 2.4], below
   the tree ratio. Kill: outside.
6. The largest ratio among the eleven is probcut_enter or one of the null statements -- NOT
   razor_ret and NOT the gate. Kill: otherwise.
