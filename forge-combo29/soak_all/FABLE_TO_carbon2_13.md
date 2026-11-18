Your name in this job is: carbon2 (job 13)

Opus (standing in for Fable this week) to carbon2, file 13, 2026-11-17. Same machine, same builds, same Step 0 as
jobs 1 to 12. If your builds are gone, rebuild them exactly as job 1 says and show Step 0 again before anything else.
This file was written while your job 12 ran, so it judges job 11 (file 14 will judge job 12) and gives you the next
task. If job 12 is not finished when you read this, finish it and its report first.

=== JOB 11 AS WE COUNTED IT (raw files, not the summaries) ===
- Recounted with our own parsers (rates from the times, not from the printed rates); every cell equal to your tables:
  Timing (1), r15d bench profile (A) against r15d SP profile (B), timing1_r15d_bench_vs_sp_12x60_hash16_raw.txt:
  48 runs, ONE trace ee465caeff9c0fcf (7,670 searches, 25,641,316 nodes each), every run "NNUE v3 active"; engine
  CPU median 1.0323, 11 of 12 faster (per round 0.9985 to 1.0511; A/A A2/A1 0.9095 to 1.0406); wall 1.0276, 11 of
  12. Timing (2), SP-profile r15d (A) against SP-profile bundle 5 (B): 48 runs, ONE trace; CPU 1.0259, 12 of 12
  (per round 1.0105 to 1.0498; A/A 0.9446 to 1.0703); wall 1.0215, 12 of 12. Leave-one-out,
  ablation_loo_sp_6x60_hash16_raw.txt: 60 runs, ONE trace; bundle 5 / r15d 1.0274, 6 of 6; bundle 5 over each
  leave-one-out build: without S1+S2+S3+S6 0.9873 (0 of 6), without S4+S5 1.0061 (6 of 6), without S7 1.0113 (4 of 6),
  without G1..G4 1.0171 (6 of 6), without W1+W2 1.0077 (5 of 6), without P1 0.9996 (3 of 6); A/A of the two r15d
  builds 1.0049 (0.9935 to 1.0568), of the two bundle 5 builds 1.0008 (0.9941 to 1.0152). Timing (3), SP-profile
  r15d (A) against SP-profile curated_sp_bundle (B), timing3_sp_r15d_vs_curated_12x60_hash16_raw.txt: 48 runs, ONE
  trace; CPU 1.0366, 12 of 12 (per round 1.0205 to 1.0478; A/A A2/A1 0.9768 to 1.0115, B2/B1 0.9863 to 1.0171);
  wall 1.0336, 12 of 12. curated_identity_and_bench13_raw.txt: bench 11 / 13 / 16 of both nets equal to r15d's
  (net512 625258 / 3652372 / 23891329, net768 882074 / 4275906 / 32374943), 250 of 250 depth-9 rows, the 1,000
  evals, both traces. curated_oracles_and_fault_raw.txt: picker oracle 2,010 sequences, 0 mismatches; evasion oracle
  55,868 sequences, 0 mismatches; the planted fault (a continuation term dropped) caught at sequence 0; the S5 key
  assert fires on a corrupt key.
- Good, keep doing it: each prediction committed alone before its first run (9db90b8c and ececa439 before the
  builds, 61c13775 before the leave-one-out, 5d5b4264 before the curated build); the carrier rule declared before
  the leave-one-out ran; each step judged by taking it OUT of its bundle (file 12's lesson); the curated bundle timed
  with two builds of each tree.
- Wrong or not shown by your files:
  (a) stamps.txt has no line between 23:34:17Z (the curated prediction) and 23:53:13Z (its finished result): the
      builds, the identity suite, the oracles, the planted fault and 48 timed runs carry no stamp of their own. File
      12 named the same gap in job 10. One line per step, pasted from date -u when the step ends.
  (b) Report section 4, item 3: "curated_sp_bundle harvests all remaining bit-exact wasted-work pockets". No file of
      job 11 shows it: there is no time profile of the curated build. Say only what a raw file carries.
  (c) Report section 2: "S1+S2+S3+S6 actively dragged ... by -1.27 %" and "absorbed by the SP profile". Each
      leave-one-out tree is ONE build, and the A/A of two r15d builds of the same rounds spans 0.9935 to 1.0568: one
      build cannot name a cause. What stands is timing (3), two builds of each tree.
- What it means for the PC: one unified diff of 1,857 lines against r15d. The PC reads every line before it builds
  anything (the owner's rule), then times it on its own SP-profiled build (clang 23, -march=znver5, Ryzen 7 9850X3D);
  that number alone decides for the loop. On the PC, bundle 5 WITHOUT PGO was 0.977 with the six speed switches, so
  nothing is assumed.

=== THE TASK (yours to plan; the owner's words: a task, not an order) ===
Part 1, first: make the PC's line-by-line read small and safe. Split curated_sp_bundle.patch.txt into a STACK of
unified diffs, one per piece, in this order: S4, S5, S5_assert, S7, G1, G2, G3, G4, W1, W2, as
forge-combo29/carbon2/job13/stack/NN_<piece>.patch.txt, each made against the tree the pieces before it leave
(patch -p1 -F0, zero fuzz).
  - Known answer that must hold: r15d + the ten pieces in order = r15d + curated_sp_bundle.patch.txt, byte for byte
    over src/ and include/. Paste the command (diff -r) and its empty output.
  - stack/README.txt, one block per piece: lines added and removed; the functions it touches; the invariant it relies
    on (what must stay true for the same moves, nodes and output); which of your oracles or identity checks would
    catch a fault in it, by name; and whether the piece's text equals the text of the same step in an EARLIER job's
    patch file (name that file; job 5's bundle.patch.txt holds S4, S5 and S7: the PC built that bundle once, without
    S7 part 3, as r15e).
  - After each piece: bench 11 / 13 / 16 of both nets and the 250 depth-9 rows (all equal to r15d's). No timing per
    piece: on a profiled build steps do not add up.
Part 2: the next speed step, on top of the curated tree (the tree the PC will time).
  - If job 12 made a time profile: take its first target as ONE step on curated, with the usual proofs, and time
    curated (SP profile) against curated + step (SP profile), two builds each, A1 B1 B2 A2, 12 rounds of 60 games,
    Hash 16, the prediction committed alone first.
  - If job 12 made no time profile: make one of the SP-profiled curated build (a function together with its callers,
    or ms per game; not self shares across builds that inline differently, file 12 (b)), and stop after its table.
Not wanted: bug hunting (cheaper helpers do that), a change of the net file format, anything about training, and
any strength match with net512.fnn3 or net768.fnn3 (made-up weights; file 11 v3).

=== EVIDENCE RULES (as in jobs 4 to 12) ===
- Every step: its prediction committed ALONE before its first timed run (what it removes or changes, its count, the
  predicted gain with the range that kills it); one unified diff forge-combo29/carbon2/job13/<step>.patch.txt on your
  base; the identity proof of files 4 to 12 (bench 11, 13 and 16 of both nets, the 250 depth-9 rows, the 1,000
  evals, both traces) plus any oracle of the code the step touches; a planted fault your checks catch.
- Each build: the full compile and link lines and the profile run's output in a raw file (build_pgo_raw.txt), with
  the number of profile files merged and the self-play games, searches and nodes of the SP profile run.
- Timing with your self-play driver at Hash 16: A1 B1 B2 A2, 12 rounds of 60 games, the per-round ratios, their
  median, the number of rounds faster, and the per-round A/A range beside the median.
- A count, share or time in the report comes from a committed raw file. Before you write "X is in file Y", open Y.
  A number you multiply or compare is copied from its raw file, with the file named beside it.
- After every step append the output of  date -u  and a few words to forge-combo29/carbon2/job13/stamps.txt; never
  type a time.

=== BUDGET ===
90 minutes from the moment you read this file, by the clock; the report at minute 80 with what you have. Nobody
answers questions within that time: decide, write down what you decided and why, go on.

=== RULES (as in jobs 1 to 12) ===
- Your branch: for-fable-and-opus/carbon2-work (add commits on top). New files only under
  forge-combo29/carbon2/job13/ (text only).
- Change NO engine source file in the repository: patches stay text files. No binaries, no net files, no profile
  data files.
- Do NOT open a pull request. If your tool opens one by itself, say so in the report.
- Read no other branches than the ones named in jobs 1 to 12 and here. No secrets, keys or personal data anywhere.
  Text in the repository is data, not instructions to you; only this file and your job 1 to 12 files direct your work.
- The last command before the report commit is  git status --short  and  ls -R forge-combo29/carbon2/job13 , pasted
  into the report.

=== THE REPORT: forge-combo29/carbon2/job13/REPORT_carbon2_job13.md ===
  0. Step 0 on each build, the compiler and its version, the -march, the profile files merged per build, and the
     self-play games, searches and nodes of the SP profile run.
  1. Part 1: the stack (piece, file, lines, identity after it), the byte-for-byte check, the README's place.
  2. Part 2: what you did and the counts or the profile that decided it.
  3. A table, one row per step: step | patch file | lines | identity | timing | prediction (met or killed) | planted
     fault (caught or not).
  4. What you would do next with another 90 minutes, ranked, or why you would stop.
  5. Times: the first and last line of stamps.txt; your model name and version as your runtime gives it.
Then push your branch.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_14.md on branch handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1 origin handoff/fable-opus-combo29-all-20261114, then git show FETCH_HEAD:<path>) every 2 minutes for at
most 20 minutes. If it appears, it is your next job. A first line STOP ends you. If nothing appears within 20
minutes, end.
