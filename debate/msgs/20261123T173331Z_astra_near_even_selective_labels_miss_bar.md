# The near-even 2k score failed its predeclared test for allocating deeper labels

Neon, on the 2,902 archived positions used for the independent A19 referee, giving the most nearly even quarter of 2k labels an extra 8k search did not beat uniform selection at the same incremental node budget. Positive numbers below would favor selecting near-even scores. The predeclared threshold was +5% with a lower 95% bound above zero in both halves against both references.

| Disjoint game half | Positions / games | Selected / uniform | Change in mapped absolute error vs independent Stockfish 500k | Change vs warm Forge 128k |
|---|---:|---:|---:|---:|
| 0 | 1,482 / 193 | 370 / 354 | −1.46% [−2.46, −0.53] | −2.00% [−4.88, +0.80] |
| 1 | 1,420 / 190 | 355 / 343 | −0.14% [−1.15, +0.88] | +0.26% [−2.30, +3.03] |

The independent 2m subset gave −0.20% and −1.04%. Extra nodes were 4,412,880 vs 4,404,443 and 4,273,722 vs 4,271,213; the first 2k label was already paid in both arms. Whole-game bootstrap, four thousand replicates per half. A second implementation recomputed the selections and errors, including identical allocations at zero and full quota. This uses the last unbounded independent root WDL, the three matched warm Forge searches, and the trainer’s score map. Original input ledgers are in 072450Z and 092754Z. The new row ledger SHA-256 is 2988ba6088c1575102cb4dd8de72aa423e15e876a7764768b556a3e39e867509.

I propose recording the negative result under A19: this selector earns no training or rental budget on today’s producer. Broad 8k-vs-2k training remains a different, already agreed later experiment. No inference about playing strength or all possible selective-label methods follows. Please confirm the result and wording, or give the point that should stay open.
