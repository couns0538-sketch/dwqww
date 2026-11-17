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
