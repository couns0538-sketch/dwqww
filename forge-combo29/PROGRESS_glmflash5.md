# PROGRESS glmflash5 (run A, branch cursor/glmflash5-work-cb5c)

- RUN ANCHOR: this 24-hour run's first stamp 2026-11-16T18:19:37Z (an earlier same-day session
  ran jobs 1-25 from 03:21Z; the 24h clock here is anchored at 18:19:37Z).
- RUNNING NOW: queue item 1 (row 1: five candidates at 20,000 nodes vs S14); matches M101 (V)
  and M102 (C8) finished, M103 (T1) and M104 (T2) next; M105 (P) deferred to item 2 if time.
- FINISHED SINCE THE LAST PUSH (job 27 report, 19:44:42Z): queue-1 prediction commit 81f35741c
  (19:44:54Z); step-0 rows of B10/V, B10/C8, B_FINE/T1, B_FINE/T2 all equal their known sums
  (8565026 / 9015167 / 10170054 / 11915365); pins on both builds exact; four probes exact.
- NUMBERS SO FAR THIS ITEM: M101 V@20000 +0.69 [-9.57, +10.95] (fifth look; the four-look pool
  +1.30 stands); M102 C8@20000 -6.95 [-16.59, +2.69] (third look; pulls the C8@20k pool toward
  -3.3).
- RAW FILES SO FAR: queue-1 folder holds cmd/config/gamelists/last40 for M101, M102; probe logs
  x4; the openings file and its globbing script; prediction.txt; stamps.txt.
- NEXT: M103, M104, then the queue-1 report (item 1's pool rule: pools come at items 4/8/12/16/20).
