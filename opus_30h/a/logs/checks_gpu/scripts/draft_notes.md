## Notes and caveats

- Reading of the speed figures: the control of each net is the lock's own evaluation written as v2 replicas with the same
  bucket layout, on the same exe, so the ratio is what the net itself costs beyond its bucket layout. KB4 (vs
  lock_kbrank4_ob8): pooled 0.9997 (CI 0.9923 .. 1.0071), single runs 0.9984 / 0.9987 / 1.0019 and 0.9986 at movetime 500
  - no measurable cost. KB8 (vs lock_kbrank4x2_ob8): pooled 1.0024 (CI 0.9937 .. 1.0112), single runs 1.0232 / 0.9994 /
  0.9850 and 0.9759 at movetime 500 - the single runs scatter by about +-2 to 3 % around 1 (the same run-to-run noise the
  main session noted for this testbed), without a consistent sign; no cost beyond noise is shown, and none excluded below
  about 2 %. The depth differences at equal time are all within about 2 SE of 0 and are not strength statements.
- Smoke: `net_final_checks.sh` step 1 runs Threads 2 on two CPUs; here both engine threads shared the one logical CPU 0
  (mask 0x1), a harder clock test than the gates' own. KB8 had one overrun (game 1, ply 113: 342 ms used with 57 ms left on
  the 2000+20 ms clock, 285 ms over, inside the 1000 ms margin that fastchess gives in the crew's gates) - reported, not
  a time loss; KB4 had none. 49 games each (48 finished, one cut by the 300 s end).
- Load next to the figures: the CPU 0 / CPU 1 busy lines are 3 x 1 s snapshots taken right before each run (not during
  it). The only other process with CPU 0 in its mask (apart from full-mask system processes) was the forge-uci MCP server
  (python pid 10192, Idle, mask 0x3, idle most of the time). The 92.8 % CPU 0 snapshot before KB8's conformance was taken
  while the smoke's engine was still winding down; the 96.9 % CPU 1 snapshot before KB8 rep2 shows the SMT sibling busy
  with somebody else's work at that moment (CPU 1 is not in my mask; its load during the runs is not recorded). No
  forge-v2-bullet process had CPU 0 in its mask at any step (the r3_kb8warm trainer, pid 5948 on mask 0x3, had ended
  before 13:05; later trainers ran on mask 0x38).
- Window: first engine start 13:05:22, last engine end 13:39:30 (PC clock, from `date` in the step logs); nothing was
  started after that, nothing of mine ran after 14:05. Every run went through `opus_lowrun.py --mask 0x1` (Idle +
  affinity read back, fail closed); smoke2m (`--mask 0x1 --idle`), uci_conformance (`--mask 0x1`) and the probe
  (`--mask 0x1`) pinned themselves to the same mask (no tool overrides it with a wider one).
- Not run (not asked, listed for completeness): the normal step 2 of `net_final_checks.sh` (`bench 16` NPS ABBA against
  the lock exe) and its step 3 (the sanity match; KB4's own 400-game sanity match runs on CPU 6, untouched); no probe
  against the lock exe itself. Nothing from the task list is missing.
- Files: everything under `D:/o30/checks_gpu/<net name>/` (step logs *.txt with the command line, clock, sharers and
  busy snapshots; smoke_300s.json / .stderr.txt; uci_conformance.json; depth_probe*.json with per-position depths and
  nps); chains: `D:/o30/checks_gpu/<net name>/chain*.txt`, `D:/o30/checks_gpu/after_kb4.txt`,
  `D:/o30/checks_gpu/after_reps.txt`; helpers in `D:/o30/checks_gpu/scripts/`. Nothing in D:/o30/wt or D:/o30/nets was
  written; the nets were only read. The probe PGN `D:/o30/control/lockkb4_v2p4/lockkb4_v2p4.pgn` (md5
  95a432e46d38c7d30c12eccfb9cc73f3) is the finished control match of this exe (ended 11:49).
