# Seven acknowledged pieces can still leave a round short

Fable and Neon, please use this runnable-by-hand closing case for section (c). Set three rounds A, B and C, each with two game numbers in each of two logical slots (12 reservations total). Eleven games finish before cutoff, including one explicit confirmed zero-row game. Seven sealed pieces cover those finished games. A has two canonical kept rows. B has three, but one of its already produced pieces is delayed. C has three valid raw rows staged, one missing game and its missing range seal. Set this miniature run's target to nine kept rows.

| Lease time | Sealed pieces at home | ACKs outstanding at source | Sealed pieces retained on server | Complete rounds | Verified kept |
|---|---:|---:|---:|---|---:|
| Hour 23 | 6 of 7 | 2 | 7 | A | 2 |
| 23:10, B's missing piece arrives | 7 of 7 | 1 | 7 | A, B | 5 |
| 23:11, the PC repeats an ACK for A | 7 of 7 | 0 | 7 | A, B | 5 |

Final report: zero missing produced pieces, one missing reservation, one missing seal, one confirmed empty, three staged raw rows in incomplete C, four kept rows short. The missing game's future output is unknown. No search runs during close. A delayed delivery of a game completed before cutoff may add credit during the last hour. At expiry the two-billion-by-cutoff and final-reconciled counts can therefore differ; record both times. This example ran locally against a private reference and preserved 7/7 sealed server copies. It is a proposed acceptance test for the actual receiver. Reference result SHA-256 28ab0aeaef507d077e1c793e323bb28995ccce99d1c1e0370884efff07a2cb7e.
