# Fable to deepseek3, file 6 (2026-11-15): job 5 received, and job 6

## Your job 5 report

Received and read (first reading; the full reading of jobs 4 and 5 and of your patch follows in file 7).
- **`CorrMargin`, your version: mild K = 20 pooled -0.7 [-8.1, +6.7] on 4,000 games, strong K = 64 pooled -1.4
  [-10.0, +7.2] on 3,038 games.** The other helper's version, written without seeing yours: -5.8 [-14.7, +3.1]
  and -1.7 [-12.2, +8.9]. Two authors, the same answer: nothing. Recorded as "nothing alone on the plain tree at
  20,000 nodes"; it is not ported.
- **You found the same contradiction in my job text as the other helper** (the feature part said "a spin", the
  template still said "type check") and resolved it the same way, with the reason written down in a file. The
  template is corrected since 19:42.
- Since your last file: your find about the eval-swing strength was tested on the PC on top of today's switch set
  at 2,000 nodes: strength 12 reads +13.9 +/- 7.1 there, 24 reads +20.1 +/- 7.1, so on that tree and depth 12 is
  NOT better; another helper measures both at 80,000 nodes on the plain tree. The four options of that old patch
  together are worth exactly nothing at EQUAL TIME (+0.2 +/- 8.5): the gain per node is paid back in speed. Its
  root re-search rule alone reads +20.6 +/- 7.2 and costs no speed: it is the candidate now. A knight-and-bishop
  correction table, two authors, 16,000 games: +2.9 [-0.8, +6.6], the nearest thing to a small real gain today.
- NOTE: the PC that gives you jobs may be restarted tonight and both sessions sleep until about 02:00 UTC. If no
  file 7 comes after your report, keep waiting with the sleeping command as long as your run allows; the owner
  restarts you in the morning with your restart line, and it finds the newest job by itself.

## Job 6. BUDGET: 90 minutes by the clock (from the moment you read this file); at 80 minutes stop and write.

Rules as in your first message (your own machine only, no pull request, no engine source committed, new files
only in your folder, text only, no binary files). Folder `forge-combo29/tests_deepseek3_job6/`, report
`forge-combo29/REPORT_deepseek3_job6.md`, commit subject "deepseek3 job 6 report". After pushing, wait for file 7
with the sleeping command of your first message; do not end your run.

### The question
The owner's rule: a small lean is tested TOGETHER with what belongs to it before it is put aside. Today's
correction-history ideas, each alone: your `CorrMargin` (nothing), the knight-and-bishop table `MinorCorrection`
(about +3, weight 50 a little better than 100). The first uses the SIZE of the correction; the second makes the
correction itself better informed. Does the size carry more once the correction is better? One tree with both.

### Step 0: one tree with both, proven by known answers
Base: commit `6b98f217` (`forge-combo29/src` and `include`; Release, g++, the flags of your job 5). Known answers
on the unpatched build: `bench 11` 312866, `bench 13` 862329, `bench 16` 3024920, `go perft 5` 4865609.
 C = your own `tests_deepseek3_job5/corr_margin.patch.txt` (your known numbers with K = 20 and K = 64 are in
     your job 5 report: use them as the check).
 M = `forge-combo29/tests_deepseek2_job8/minor_correction.patch.txt` on branch `for-fable-and-opus/deepseek2-work`
     (option `MinorCorrection`, a spin, the weight in percent; fetch the branch by name and read only that
     folder and `forge-combo29/REPORT_deepseek2_job8.md`, which gives its `bench` numbers with weight 100).
 a. List the files each patch touches (`grep '^+++ '`) and try `patch` in both orders on fresh copies.
 b. If neither order applies cleanly, MERGE BY HAND: this job allows it. The merged tree counts as right only if
    ALL of these hold, each reported as a line: both options off = the four known answers AND 2,000 positions
    (the first 2,000 lines of `UHO_Lichess_4852_v1.epd`, `go depth 9`) identical to the unpatched build in best
    move, score and nodes (one sha256 a side, smallest node count); `CorrMargin` alone at K = 20 and at K = 64 =
    your job 5 bench numbers; `MinorCorrection` 100 alone = the other helper's bench numbers. If one differs,
    the merge is wrong: fix it or stop and say which line differs.
 c. One design point that only the merged tree has, and you decide it and say why: does the SIZE that
    `CorrMargin` uses include the minor table's term (I expect yes: it is the size of the whole correction
    that is applied)? Report `bench 13` with both on (K = 20, weight 50) for the choice you made.
 d. Deliver the tree as ONE unified diff against 6b98f217: `correction_bundle.patch.txt` (text, your folder).
 e. Sanitizers (AddressSanitizer + UBSan, a planted fault first): `bench 13` with both on and 200 of the
    positions: nothing on stderr.

### The matches (20,000 nodes, `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings each twice with
### colours reversed, `order=random` with `-srand <seed>`, no adjudication; the same exe on both sides)
    C    control: 20,000 against 10,000 nodes, no options, 300 games, seed 7930: near +200. Take this tree's
         games per second from C and set every later time limit from it.
    M1   MinorCorrection 50 + CorrMargin 20   against none                 2,000 games   seed 7931
    M2   MinorCorrection 50 + CorrMargin 20   against MinorCorrection 50   2,000 games   seed 7932
         (what the size term ADDS once the minor table is there)
    M3   MinorCorrection 50 + CorrMargin 20   against none                 2,000 games   seed 7933   (second seed)
    M4   MinorCorrection 50 + CorrMargin 64   against MinorCorrection 50   2,000 games   seed 7934   (if time is left)
A 2-game probe with the engine's input log before every match (both options must be seen arriving). If the time
does not reach: M4 is cut first, then M3; a cut match reports the games it reached, complete pairs only.

### The report
First paragraph in plain words: the gain of the two together per node (M1, pooled with M3 if played) with its
95 % pair interval, beside the single figures (minor table about +3, size term 0), what the size term adds on
top of the minor table (M2), and what was cut. Then: Step 0 line by line; the merge (which hunks you placed by
hand) and your decision in c; one table of all matches; the probes; files of the repository you opened; stamps
of every step; what you did not do; what you are not sure about; a better way; model.
