# swarm 19 — status

seat 19
area 9 (SPEED)
branch for-fable-and-opus/swarm-19
seed 1901

## 2026-11-16T21:10:00Z (written at start, times below come from stamps.txt)

Started. Repository check ok (origin ends couns0538-sketch/dwqww). Seat 19 claimed.
Area = ((19-1) mod 10)+1 = 9 = SPEED. SEED = 19*100+1 = 1901.

Next: STEP 2 — build 6b98f217 in ../base and run the honesty check
(bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609).

## 2026-11-16T21:13:02Z

job 1 (profile bench 13) DONE.
perf: 17K samples task-clock, bench 13 x40 (all 40 nodes 862329).
top: evaluate_position 16.51 %, Worker::search 11.97 %, nnue::apply_and_evaluate 11.84 %,
MovePicker::next 6.69 %, pick_best 6.35 %, see_ge 5.56 %. All evaluation 38.24 %.

files: REPORT_job1.md, FINDINGS.md (19-F1..F5), job1/ (profile.sh, profile_cg.sh, summarize.py, summary.txt, prediction.txt, stamps.txt).

next command: `bash ~/build_rel/forge` nothing — literally:
  cd /agent/repos/dwqww && S=$(cat ~/swarm_seat.txt) && python3 forge-combo29/swarm/$S/job1/summarize.py forge-combo29/swarm/$S/job1/profile > forge-combo29/swarm/$S/job1/summary.txt
then: job 2 written to job2/prediction.txt and committed ALONE before the first speed measurement.

## 2026-11-16T21:25:28Z

job 2 DONE (negative result, stated as such).
patch job2/optimize_material_key.patch.txt: material key cached in Board.
node counts identical (bench 11/13/16 + perft 5 on the patched build). cache proven correct on 4,736 positions.
speed: ratio 1.0059, 95% CI [0.9680, 1.0454] -> NOT shown faster; control pair of two identical builds gave [-5.12%, +5.43%], so this machine cannot resolve <5%.

next command: bash ~/build_rel/forge is NOT next; next is job 3 (the next hot spot), starting with the prediction:
  cd /agent/repos/dwqww && S=$(cat ~/swarm_seat.txt) && printf "%s\n" "job 3 prediction" > forge-combo29/swarm/$S/job3/prediction.txt && git add forge-combo29/swarm/$S/job3/prediction.txt && git commit -m "swarm $S job3: prediction alone" && git push origin HEAD:refs/heads/for-fable-and-opus/swarm-$S
