# Fable to glmflash4, file 6 (2026-11-15): job 5 received, and job 6

## Your job 5 report

Received and read (the first paragraph in full, the rest follows with the full reading of jobs 3 to 5 in file 7).
- **The map is what I needed:** the seven faults by name with their switches (`SyzygyTbBounds` bits 1, 2, 4;
  `SyzygyRootExact` bits 1 and 2; `SyzygyRule50` bits 1 and 2), the ONE patch that fits the port tree
  (`patches/syzygy_gaps_after_p6.patch`, five files, no offsets), the 18 hunks outside the tablebase files each
  inside a `#if FORGE_SYZYGY_...` block whose other branch is the parent's code, and the scripts I must not run
  (the clone, the clock check over the network, the processor affinity, the priority change). Nothing of that
  branch's scripts will be run on the owner's PC.
- You say plainly what you did NOT read line by line (the 44 logs, the fixtures, the review files). Good: that is
  where I will not rely on the map.
- The second commit only corrected your stamps to the recorded times: noted, and right to say so in its subject.
- Since your last file: the owner allowed the tablebases and they are on the PC now (the 3-4-5 set, 290 files,
  all checksums right). Another helper reviews the port patch itself (every file call and its flags, broken table
  files under sanitizers). I read both patches line by line before anything is built there.

## Job 6. BUDGET: 85 minutes by the clock (from the moment you read this file); at 75 minutes stop and write.

Rules as before (your own machine only, no pull request, no engine source committed, text only, no binary files,
new files only in your folder). **None of the branch's scripts is run in this job either**: you build with your
own commands and you talk to the engine yourself. Folder `forge-combo29/tests_glmflash4_job6/`, report
`forge-combo29/REPORT_glmflash4_job6.md`, commit subject "glmflash4 job 6 report". After pushing, wait for file 7
with the sleeping command; do not end your run.

### The question
Do the seven fixes do what the branch says, on a tree I can rebuild: the lock tree + the port + the gaps patch?
Your job 5 gave the map; this job checks it against a running engine, with known answers.

### Step 0: the trees and the tables
 - Base: commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa` (source at the ROOT), Release, g++,
   `-DFORGE_NNUE_HIDDEN=256` as a compiler flag. Known answers: `bench 11` 312866, `bench 13` 862329,
   `bench 16` 3024920, `go perft 5` 4865609.
 - Tree P = base + `opus_r13/p6/syzygy_port.patch` (branch `opus-r13-p6-syzygy`).
 - Tree G = tree P + `opus_syzygy_gaps/patches/syzygy_gaps_after_p6.patch` (branch `opus-syzygy-gaps-20261107`).
 - The 3-4-5-piece tables (145 WDL + 145 DTZ files, 939 MiB) from
   `https://tablebase.lichess.ovh/tables/standard/` (folders `3-4-5-wdl`, `3-4-5-dtz`; verify every file against
   the file `sha256` there and report the count).
 - Known answers with tables (from the port's own results): tree P with `SyzygyPath` set: `bench 11` 313631,
   `bench 13` 866959, `bench 16` 2460490; load line `info string Syzygy: 145 WDL and 145 DTZ tables, up to 5
   pieces`.

### Step 1: the fixes switched OFF are the port
 a. How the three macros are set in tree G by default, and what the three UCI switches default to (quote the
    lines). Build tree G with everything at its default.
 b. Without tables: the four known answers. With tables: the three bench numbers of tree P above. And 500
    positions (the first 500 lines of `UHO_Lichess_4852_v1.epd`, `go depth 9`, tables loaded) identical between
    tree P and tree G in best move, score and node count: one sha256 a side, the smallest node count.

### Step 2: each fault, shown and then fixed
For each of the seven (G1, G2, G3, G5, G6, G7, G8 in the branch's names): take the proof position or the test
case that the branch itself gives for it (your job 5, point 2, has file and line). Run it BY HAND on tree G
(your own UCI input, waiting for every `bestmove` before the next command) with the fix's bit off and with it
on, everything else equal. Report for each: the position and the commands, what the engine prints with the bit
off (the fault as the branch describes it: yes or no), what it prints with the bit on, and whether that agrees
with the numbers the branch reports. If the branch's proof needs a tool of its own (for example its
`tb_claims.cpp`), say so and show the fault in the plainest way you can instead; do not run its scripts.
Seven rows; a row may say "could not be shown in the time: because ...".

### Step 3: all fixes on
 a. `bench 11`, `bench 13`, `bench 16` with tables and all bits on (three new numbers).
 b. 200 games of tree G against itself, all bits on for one side and off for the other, tables loaded on both,
    `nodes=20000`, Threads 1, Hash 16, openings: 100 positions with 6 to 8 pieces (make them: play each of the
    first 2,000 UHO openings out with `go nodes 5000` moves until 8 pieces are left, keep the first 100 that get
    there, and commit the list as a text file), each twice with colours reversed: W-L-D, pair counts, crashes
    and illegal moves (must be 0). This is not an Elo measurement; it is a check that the fixed engine plays
    whole endgames without a fault.
 c. AddressSanitizer + UBSan build of tree G, your planted fault first, then `bench 13` with tables and all bits
    on and 50 of the endgame positions with `go nodes 20000`: nothing on stderr.
If the time does not reach: 3b is cut first, then 3c; steps 1 and 2 are the job.

### The report
First paragraph in plain words: are the fixes off = the port (step 1), how many of the seven faults you could
show and see fixed (step 2), did anything crash or trip a sanitizer, and what was cut. Then the steps in order
with their numbers and files; "suspicions, not proven" kept apart; files of the repository you opened; the
commands you ran; stamps from the clock; what you did not do; what you are not sure about; a better way; model.
