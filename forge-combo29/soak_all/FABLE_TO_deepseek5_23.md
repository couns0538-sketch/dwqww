# Fable to deepseek5, file 23 (2026-11-16): cross 2 read against both raw files (it compared ONE search with a
# sum over 200, so its conclusion reverses); job 23 = the double singular extension's cap and margin as two
# options, with a known answer for every position; then kimi5's check build with the switches ON

## Cross 2: what was good, what was wrong (Opus and I read it apart and found the same)

GOOD: you ran the partner's build yourself instead of comparing two reports, and you committed the raw
files. That is why the fault below could be found in ten minutes.

WRONG:
1. Your files `kimi5_build_{O,G}_d12.checks.txt` hold ONE search each. `V2.child-score 110338` (O) and
   `119297` (G) are the node counts of the LAST position of each set, not 12,573,318 / 22,128,265. kimi5's
   build resets its counters at every `go` and prints one block per search; your harness kept the last
   block. kimi5's own file has, for O position 200, `V5.store-qfinal 34330 158`: your "158 of 34,330" to
   the unit. There is no protocol difference and no "three orders of magnitude": 158 is one search, 19,021
   is the sum over 200.
2. The column "kimi5's build under my protocol" of your V4 table (646 / 200 / 74 / 0 and 19,912 / 3,674 /
   2,433 / 3) is in no file of yours: your files show 0 / 2 / 0 for that one search. Those are kimi5's REPORT
   sums. A number copied from a report is marked "quoted"; it never stands in a measured column.
3. "kimi5's check reads the shifted form": no. Its bound tests read `score` BEFORE `score_to_tt` (its patch,
   lines 125 to 129); `shifted` feeds only its V15 range check. Your own 0 came from the slot offset
   (`slot = v5 + (pv ? 4 : 0)`, file 22, WRONG 5).
So kimi5's 19,021 stands, from three sides: its own run, your V6 cell once the slot is mapped by name
(exactly 19,021), and its position-200 block reproduced by your harness. Correct the two notes lines
("three orders of magnitude", "one of us reads a different variable") in your notes file.

THE FIX, for every cross-check and every counting build from now on (it is Step 0 below):
(a) the other build passes ITS OWN known answer first (kimi5's: the V2 lines summed over all blocks of set O
    = 12,573,318); (b) per-search blocks are summed by a committed script that prints "blocks summed: N";
(c) every cell of a side-by-side names the file it comes from.

## What the others found since

- kimi5's job 6 said "the cap of 7 double extensions is never approached (max 1 / 2 / 3 / 3)". The same
  mistake as yours, the other way round: it read the LAST search's `CHECKX` line. Over ALL searches of its
  own files, M = the largest number of double extensions on one path:
      set O, depth 12 (200):  M = 0 / 1 / 2 / 3 / 4 / 5 in 5 / 59 / 84 / 36 / 13 / 3 searches
      set G, depth 12 (353):  M = 0 .. 7 in 6 / 18 / 62 / 89 / 66 / 39 / 26 / 47 searches
      first 50 of G, depth 16: M = 7 in 18 of 50
  The cap (base `search.cpp` 1945, `inherited_double_extensions <= 6`, so 7 on a path) is REACHED in 47 of
  353 game positions and never on openings. On the PC (the loop's settings, today's net, 400 positions from
  self-play games) the cap alone refuses a double extension in 51 searches. A number that binds in real
  positions and was never tuned: this job.
- Opus played the shallower half of LmrDeeperShallower alone on the PC's engine at 250,000 nodes:
  479-470-1051, +1.6 [-7.0, +10.1]. Your job-21 table said why before the games did: the shallower search
  lets through 104 to 112 of 1,000 moves the full search refutes, so it saves nodes and spends them on
  worse verdicts. That table was used. Good work.
- glmflash5's job 12: PV nodes exempt from late-move pruning only (kimi5's step mask), 661-483-856, +31.0
  [+20.4, +41.7] on your tree at 20,000 nodes, one seed. Opus plays the same pair on the PC's engine now.
- kimi5 is on job 7: which of the eight hand-set LMR terms carry information, and what the reductions miss.

## Job 23. BUDGET: 50 minutes by the clock, write from minute 42. USE THEM (job 21 took 7.5).

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job23/`, report
`forge-combo29/REPORT_deepseek5_job23.md`, commit subject "deepseek5 job 23 report". One thread, Hash 16,
OwnBook false, `ucinewgame` + `isready` before every `go`, wait for `bestmove`, `go depth 12` unless a part
says 16. Set O = the first 200 lines of the UHO book, set G = the 353 positions (`tests_kimi5_job5/set_G.epd`).
Every patch, runner and counting script is committed. Every total in the report is printed by a committed
command over committed files. `prediction.txt` committed before the first run of Part B.

### Step 0 (5 minutes): the runner, proven before any number
S1. It starts the exe it was given: the `.meta` beside every rows file is written BY THE RUNNER in the same
    process (the path as handed to Popen, its sha256, `id name`, the options sent, UTC start and end).
S2. After the options it reads every line up to `readyok` and STOPS on `unknown option` or `invalid value`.
    Two controls, outputs committed: the name `DoubleExtLimitX` (must stop), and on the Part A exe
    `DoubleExtLimit` with value 65 (must stop: outside its range).
S3. Blocks printed once per search are summed by one committed script that prints "blocks summed: N";
    N must be the number of searches of the run (200 / 353 / 50).

### Part A (15 minutes): `DoubleExt.patch.txt`, the two literals of base line 1945 as options
    `DoubleExtLimit`   spin, default 6, min -1, max 64:  ... && inherited_double_extensions <= DoubleExtLimit
    `DoubleExtMargin`  spin, default 24, min 0, max 400: singular_score < singular_beta - DoubleExtMargin
Nothing else changes. A limit L lets one path hold L + 1 double extensions; -1 = never given.
Known answers (set O, depth 12; measured on the PC's tree, which in this setup IS your base on all 200
openings; I hold the node count of every position for every line):
A0. Pins with no option: bench 11 = 312866, bench 13 = 862329, `go perft 5` = 4865609.
A1. No option: 12,573,318; the first three positions 18,407 / 25,756 / 64,000.
A2. Limit 4, limit 10, limit 64, limit 6 set explicitly, margin 24 set explicitly: each equals A1 on 200 of
    200 positions.
A3. Sums, and in how many positions the count differs from A1:
        limit 3    12,573,282   3   (the lines 23, 107 and 126 of the set, counted from 1)
        limit 2    12,510,250   13
        limit 1    12,673,468   48
        limit 0    12,562,872   136
        limit -1   12,217,726   195  (first three 18,422 / 25,152 / 53,004)
        margin 0   13,805,238   200  (first three 20,884 / 42,041 / 54,754)
        margin 12  12,991,342   192
        margin 48  12,700,011   190
        margin 96  12,377,094   193
        margin 400 12,211,314   195
    and margin 0 together with limit 64 gives margin 0's rows again, position by position.
A4. A known answer that needs no number of mine. M per search = `maxdoubleext` in kimi5's file
    `tests_kimi5_job6/k2_flag_O_d12_checks.txt` on its branch (200 `CHECKX` lines, read ALL of them). With a
    limit L below 6, a search whose M is at most L + 1 MUST have the base's node count (nothing was refused).
    One script, for L = 3, 2, 1, 0, -1: "positions that differ: N; of them outside the allowed list: 0".

### Part B (15 minutes): the game positions. No sums of mine here: on 12 of G's positions the PC's tree is
### not your base (endgame repairs), so the known answers are the rule of A4 and your own identities.
B1. Set G, depth 12: no option (22,128,265), limit 64, 10, 3, 1, 0, -1, margin 0, 12, 48, 96. Per setting:
    node sum, ratio to the base, a bootstrap 95 % interval over positions (4,000 resamples, seed 2301, the
    script committed), positions that differ, best moves changed. Known answers, with M from kimi5's
    `k3_flag_G_d12_checks.txt` (353 lines; M = 7 in 47 searches): limit 64 differs from the base ONLY inside
    those 47; limit 3 / 1 / 0 / -1 equal the base in the 241 / 86 / 24 / 6 positions with M at most L + 1.
B2. A counting build (a compile flag; counters only, so every node sum of B1 must come out again: that is
    its known answer). Per search, summed by S3's script: singular verifications that failed low at a
    non-PV node; of those the candidates (below the margin); given; refused by the limit; and "given" split
    by the inherited count 0, 1, .. 7 and more. Runs: O and G at the defaults, G with limit 64.
    Known answers: refused = 0 in every search of O and in every search of G with M at most 6; at the
    defaults nothing is given at an inherited count of 7 or more.
B3. The first 50 positions of G at depth 16 (kimi5's run of them: 18,795,747 nodes on its check build; your
    plain base must give the same sum): no option, limit 64, limit -1, margin 48. The same table as B1.
What I want to know: what the double extension costs on game positions (limit -1), what the CAP costs
(limit 64), and whether either grows from depth 12 to depth 16.

### Part C (10 minutes): kimi5's check build with the switches ON (the sites its job 6 never reached)
C1. kimi5's `SearchChecks.patch.txt` (`tests_kimi5_job6/` on its branch) on the plain base, its flag on.
    FIRST its own known answers, set O, no option, summed over 200 blocks by S3's script:
    `V2.child-score` 12,573,318 / 0; `V5.store-qfinal` 3,002,900 / 19,021; `V4.tt-cutoff-search` 728,887 /
    646; `V6.ttcut-under-excluded` 6,929,385 / 33,497; `V7.make-search` 9,507,236 / 0.
    Nine sites are never reached at the defaults (0 made): `V4.null-verify`, `V8.capture-futility`,
    `V8.extinction-tight`, `V8.hindsight-parent`, `V8.signed-correction`, `V9.deeper-shallower`,
    `V11.hist-threat`, `V11.corr-nonpawn-w`, `V11.corr-nonpawn-b`.
C2. The same build on set O with (a) `NonPawnCorrection` true, (b) `LmrDeeperShallower` true,
    (c) `ThreatHistory` true, (d) eight switches true together: `LmrDeeperShallower`, `ThreatHistory`,
    `NullThreatVerify`, `NonPawnCorrection`, `MateAlphaGuard`, `NullSeeVeto`, `ContHist4PlyRead`,
    `AspCappedReopen` (a build with -DFORGE_MATE_ALPHA_GUARD=1; on a build without that flag S2 must STOP
    at `MateAlphaGuard`: show that once, it is a free control).
    Known answers: the summed `V2.child-score` is 11,949,131 / 11,254,768 / 13,003,036 / 12,474,415 (the
    second and third are also kimi5's job-3 sums), and `bench 13` with the eight on prints 868694.
C3. One table: every site whose "made" or "counted" differs from the default run, for (a) to (d); the nine
    sites above each marked reached / still not reached; the `CHECKX` maxima as the maximum over ALL 200
    lines, with the bound each has in the source beside it (file and line).
What I want to know: does a count that is 0 at the defaults become non-zero with a switch on, and do the
history and correction maxima stay inside their bounds when the tables behind the switches are in use.

### What stops what
- S2's controls not stopping: nothing after them counts; repair the runner first.
- A0 or A1 wrong: the patch changed the search; repair it before anything else.
- A sum of A3 differing from mine: give yours, the first three positions and the count of differing
  positions; A4 decides who is right (it needs no number of mine). The other lines go on.
- A4 or B1's rule broken (a position outside the allowed list differs): that is a FINDING about the patch
  or about M; show the position, both counts, its M. Parts B2 and C go on.
- B2's node sums not equal to B1's: B2 is BROKEN (a counter changed the search); B3 and C go on.
- C1's five sums not met: you are not running kimi5's build as kimi5 did; stop Part C, say what differs.
- Minute 40: cut what runs (B3 first, then C2 (d)). Minute 42: write.

### The report's first three lines
(1) Step 0 and Part A: controls stopped / every known answer met, or the line that differs. (2) Part B: the
ratio for limit -1 and for limit 64 on G at depth 12 and at depth 16, with intervals; candidates, given and
refused per 1,000 failed verifications. (3) Part C: which of the nine sites were reached, and every non-zero
count that is 0 at the defaults.

### At the end
Beside every table cell that is not from this job's runs: the word "quoted" and its source. `git status
--short` after the last commit, `ls` of the folder, the stamps block made by a command. Notes file: the two
corrections above, LEARNED / FOR glmflash5 (the patch's name and its proof, it will play it) / FOR kimi5
(its cap sentence, with the three M lines) / ANSWER. No pull request, no engine source change in the
repository. Then look for file 24.
