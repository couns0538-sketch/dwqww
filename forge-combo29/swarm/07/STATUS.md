# STATUS — seat 07

## 2026-11-16T21:06:28Z (date -u)

seat 07
area 7 (READING THE CODE for faults) — job order: search, move picker+histories, position/move making, transposition table, UCI loop, time manager, evaluation, move generator
branch for-fable-and-opus/swarm-07
seed 701

Done: seat claimed (SEAT.txt pushed by take_seat.sh), area/seed computed.
Runs: nothing yet.
Next: build base worktree 6b98f217 and run the honesty check (bench 11/13/16, perft 5).

Next command:
`cd /agent/repos/dwqww && git worktree add ../base 6b98f2170a3210e71beed04bbd2553972c253ed7 && cd ../base/forge-combo29 && cmake -S . -B build-rel -DCMAKE_BUILD_TYPE=Release && cmake --build build-rel -j$(nproc)`
