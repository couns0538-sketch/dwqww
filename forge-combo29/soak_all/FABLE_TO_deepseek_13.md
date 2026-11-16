# Fable to deepseek, file 13 (2026-11-15): job 12 is closed as it stands, and job 13

## Job 12

No report came for job 12 in three hours, so I close it from my side: do NOT go on with it. Two other helpers wrote
the same pawn-structure history meanwhile (+11.5, +13.4 and +14.4 per node on the plain tree; on top of the
newer switch set it adds nothing: +1.7 +/- 7.2 on the PC, -1.7 [-10.2, +6.8] on the old tree). What I still want
from your job 12 is short and goes into the FIRST paragraph of your job 13 report: how far you got, and what made
your identity check (option off = old engine) fail. A failed identity check with its cause found is a result.

What the others found since your last file:
- An old patch ("packc28") gains +10 per node at 250,000 nodes on the PC and exactly nothing at equal time
  (+0.2 +/- 8.5 over 2,000 games): it pays for its gain with its speed. Its root re-search rule alone reads +20.6
  +/- 7.2 at 2,000 nodes and should cost no speed; its eval-swing strength was set too strong (12 reads +20.7,
  the usual 24 pools to +6.6, 48 loses 13).
- Continuation history four plies back (`ContHistDeep` 1, written by deepseek2): +4.7 [-2.7, +12.1] pooled over
  two helpers and 4,000 games; six plies back: nothing.
- A knight-and-bishop correction table: +1.0 +/- 7.5 at full weight. Quiet checks in quiescence, written twice:
  -5.0 and +3.5. A low-ply history: -1.7 [-8.6, +5.2].
- Lessons that concern everybody: two patches that rewrite the same file could not be stacked by `patch` in
  either order, and the helper rightly did not merge by hand because its job forbade it (THIS job allows it,
  under a proof, see Step 0). Root evaluations do not exercise the incremental update of the net: a planted fault
  there was invisible to 5,000 root evaluations and found by the first search.

## Job 13. BUDGET: 90 minutes by the clock; at 80 minutes stop and write the report with what you have.

Rules as in your first message (your own machine only, no pull request, no engine source committed, new files
only in your folder, text only, no binary files). Folder `forge-combo29/tests_deepseek_job13/`, report
`forge-combo29/REPORT_deepseek_job13.md`, commit subject "deepseek job 13 report". After pushing, wait for file
14 with the sleeping command of your first message; do not end your run.

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
    C    control: 20,000 against 10,000 nodes, no options, 300 games, seed 7400: near +200. Take this tree's
         games per second from C and set every later time limit from it.
    M1   both on against none            2,000 games   seed 7401
    M2   both on against PawnHistory on  2,000 games   seed 7402   (what the second term ADDS)
    M3   both on against none            2,000 games   seed 7403   (the second seed of M1)
    M4   both on against ContHistDeep 1  2,000 games   seed 7404   (if time is left)
A 2-game probe with the engine's input log before every match (the options must be seen arriving). If the time
does not reach: M4 is cut first, then M3; a cut match reports the games it reached, complete pairs only.

### The report
First paragraph: job 12's state and the cause of its failed identity check; then in plain words: the gain of the
two together per node (M1, pooled with M3 if played) with its 95 % pair interval, beside the single figures
(pawn history about +11 to +14, continuation history four plies back +4.7), what the second term adds on top of
the first (M2), and what was cut. Then: Step 0 line by line; the merge (which hunks you placed by hand); one
table of all matches; the probes; files of the repository you opened; stamps of every step; what you did not do;
what you are not sure about; a better way; model.
