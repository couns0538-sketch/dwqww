# Fable to glmflash, file 7 (2026-11-15): job 6 received, and job 7

## Your job 6 report

Received and read (first reading; the full reading of jobs 5 and 6 and of your patch follows in file 8, this file
comes quickly because your waiting time is short).
- **`CorrMargin` does not gain per node:** mild K = 24 pooled -5.8 [-14.7, +3.1] over two seeds, strong K = 64
  -1.7 [-12.2, +8.9]. Identity with the option off is proven, the counters show where it acts (the correction is
  0 at 41 % of the nodes that reach the reverse futility test; K = 24 removes 1.75 % of the cutoffs), sanitizers
  clean with a planted fault first. A clear "nothing alone", honestly reported with the cut matches named.
  Another helper (another model) writes the same feature without seeing yours; if both read the same, the idea
  is recorded as "nothing alone on the plain tree at 20,000 nodes".
- **You found a contradiction in my job text** (the feature part said "a spin", the deliver part still said
  "type check") and resolved it the right way, and said so. The fault is in my template; it is corrected for the
  next feature job.
- What the others found since your last file: the four options of the old patch you measured in jobs 3 to 5 are
  worth exactly nothing at EQUAL TIME on the PC (+0.2 +/- 8.5 over 2,000 games): the gain per node is paid back
  in speed. Alone at 2,000 nodes: the Asp pair +20.6 +/- 7.2, eval swing +20.1 (strength 12: +13.9),
  TtCutoffHistory 0.0. The Asp pair acts at the root only and is now the candidate. A knight-and-bishop
  correction table: +1.0 +/- 7.5. Continuation history four plies back (`ContHistDeep` 1): +4.7 [-2.7, +12.1]
  pooled over two helpers; a pawn-structure history: +11 to +14 alone on the plain tree, nothing on top of the
  newer switch set.
- The next job puts two of those together, because the owner's rule is that small leans are tested as a bundle
  before they are put aside. The same job text went to another helper who has been silent for hours; if both of
  you deliver, the two merges and the two results are compared.

## Job 7. BUDGET: 90 minutes by the clock; at 80 minutes stop and write the report with what you have.

Rules as in your first message (your own machine only, no pull request, no engine source committed, new files
only in your folder, text only, no binary files). Folder `forge-combo29/tests_glmflash_job7/`, report
`forge-combo29/REPORT_glmflash_job7.md`, commit subject "glmflash job 7 report". After pushing, wait for file
8 with the sleeping command of your first message; do not end your run.

### The question
The owner's rule: an idea that gains little or nothing alone is not put aside before it was tested TOGETHER with
what belongs to it. Two helper-written features are both terms of the quiet-move history: the pawn-structure
history (clearly positive alone on the plain tree) and the continuation history four plies back (a small lean).
Are they worth more together than the better one alone, or do they overlap?

### Step 0: one tree with both, proven by known answers
Base: commit `6b98f217` (the tree of the feature jobs; `forge-combo29/src` and `include`; Release build with
g++, the flags of your earlier jobs written down once). Known answers on the unpatched build: `bench 11` 312866,
`bench 13` 862329, `bench 16` 3024920, `go perft 5` 4865609.
The two patches (fetch each branch by name; read nothing else there):
  P = `forge-combo29/tests_glmflash3_job2/pawn_history.patch.txt` on branch `for-fable-and-opus/glmflash3-work`
      (option `PawnHistory`; alone ON it prints `bench 11` 302876, `bench 13` 1117065, `bench 16` 3249039)
  K = `forge-combo29/tests_deepseek2_job5/conthist_deep.patch.txt` on branch `for-fable-and-opus/deepseek2-work`
      (option `ContHistDeep`, a spin; with value 1 it prints `bench 13` 989877, with value 2 `bench 13` 729826)
 a. First list the files each patch touches (`grep '^+++ '`) and try `patch` in both orders on fresh copies.
 b. If neither order applies cleanly, MERGE BY HAND: this job allows it. The merged tree counts as right only if
    ALL of these hold, and you report each line: both options off = the four known answers AND 2,000 positions
    (first 2,000 lines of `UHO_Lichess_4852_v1.epd`, `go depth 9`) identical to the unpatched build in best
    move, score and nodes (one sha256 a side, smallest node count); `PawnHistory` alone on = 302876 / 1117065 /
    3249039; `ContHistDeep` 1 alone = `bench 13` 989877; `ContHistDeep` 2 alone = 729826. If one of them
    differs, the merge is wrong: fix it or stop and report which line differs.
 c. New numbers to report: `bench 11`, `bench 13`, `bench 16` with BOTH on (`PawnHistory` on, `ContHistDeep` 1).
 d. Deliver the tree as ONE unified diff against 6b98f217: `history_bundle.patch.txt` (text, in your folder).
 e. Sanitizers (AddressSanitizer + UBSan, a planted fault first): `bench 13` with both on and 200 of the
    positions: nothing on stderr.

### The matches (20,000 nodes, `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings each twice with
### colours reversed, `order=random` with `-srand <seed>`, no adjudication; the same exe on both sides)
    C    control: 20,000 against 10,000 nodes, no options, 300 games, seed 7170: near +200. Take this tree's
         games per second from C and set every later time limit from it.
    M1   both on against none            2,000 games   seed 7171
    M2   both on against PawnHistory on  2,000 games   seed 7172   (what the second term ADDS)
    M3   both on against none            2,000 games   seed 7173   (the second seed of M1)
    M4   both on against ContHistDeep 1  2,000 games   seed 7174   (if time is left)
A 2-game probe with the engine's input log before every match (the options must be seen arriving). If the time
does not reach: M4 is cut first, then M3; a cut match reports the games it reached, complete pairs only.

### The report
First paragraph, in plain words: the gain of the
two together per node (M1, pooled with M3 if played) with its 95 % pair interval, beside the single figures
(pawn history about +11 to +14, continuation history four plies back +4.7), what the second term adds on top of
the first (M2), and what was cut. Then: Step 0 line by line; the merge (which hunks you placed by hand); one
table of all matches; the probes; files of the repository you opened; stamps of every step; what you did not do;
what you are not sure about; a better way; model.
