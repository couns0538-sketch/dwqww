seat 62, area 2 (UCI commands; reassigned by brief to the one-ply-down draw rule), seed 6201
branch for-fable-and-opus/swarm-62
base commit 6b98f2170a3210e71beed04bbd2553972c253ed7
folder forge-combo29/swarm/62/

## 2026-11-17T03:51Z
Done: seat, honesty 4/4 on base and on both patched builds (/tmp/build-seat12, /tmp/build-seat27).
Reproduced the defect: hm=99 -> cp 0 / 36 nodes / bm g8f8; hm=97,98 -> mate -1 / 63 nodes.
Depth sweep 1,2,6,12,24,32 at hm=99: cp 0 at every depth, nodes exactly 3*depth.
Neither seat 12's two_doors_mate nor seat 27's drawn_root_reporting changes hm=99 (still cp 0, 36 nodes).
Next: diagnostic build printing is_draw clause/ply, then blast-radius position set.

## 2026-11-17T05:25Z
Done since last block:
- Code path PROVEN by instrumented build (not inferred): root guard root_drawn=0 at hm=98 AND 99;
  leaf rule at 1302-1304 fires at hm=99 with "clause=halfmove>=100 ply=1 ... returns=1" (24x), and at
  hm=98 with "ply=2 in_check=1 has_legal=0 returns=0" (23x). job2/CODE_PATH.md, job2/diag/.
- Independent oracle (matedist.py) self-tested against the engine's own mate scores AND a plain
  minimax. Planted-fault proof that it can fail: job3/oracle_fault_proof.txt.
- BAND: 80 (position,clock) pairs measured, prediction 80/80. p=2 misses from H=99, p=4 from H=97.
  The band is H > 100-p, NOT "98-99". job3/BAND_TABLE.md.
- Both named patches measured: seat12 and seat27 are NODE-FOR-NODE identical to base on 18 cells.
  Harness proven live with --plant-fault (caught 9 planted errors, exit 1). job2/PATCH_TEST.md.
- Control class: bare-king cp 0 is the ROOT GUARD (0 nodes), not this defect. Real control with a
  reset available searches 23k-99k nodes and returns real scores. job3/CONTROL_CLASS.md.
- Real play: 5689 games / 792081 plies / 798 band plies -> 1 band position with a forced mate,
  and it is the FOUND cell. 0 EXPOSED. job4/REAL_PLAY.md.
Running: scan_pgn_wide.py over all 13 PGNs firing on H > 100-p for p=2,4,6 (tmux swarm62-wide).
Next: record wide-band funnel, then FINDINGS.md + final report.
