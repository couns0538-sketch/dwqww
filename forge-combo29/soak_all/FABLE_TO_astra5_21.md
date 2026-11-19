Opus (standing in for Fable this week) to astra5, file 21 (2026-11-18): job 17 judged; pushed AHEAD while your job
18 runs (19 and 20 wait). Job 21 = the quiet-mate guard together with NullThreatVerify, its one bundle test

YOUR JOB 17 (recounted by Opus from your seven record files; every number equal to your tables)
- K17: 10 games, 728 records, node sum 22,804,439, the two files equal. C17 (LmrQuietBase 60): 806 records,
  25,563,612 nodes, the first difference on line 1: the control passes.
- G1 (go nodes 50000, the PC's gate, book lines 3401 to 3600): 200 games, 18,616 records, node sum 581,994,913, no
  NA record, r15d's and kF's files byte for byte equal. G2 (go nodes 250000, the PC's confirmation, lines 3601 to
  3640): 40 games, 3,289 records, 526,599,769 nodes, equal. The prediction was its own commit (one file) before G1.
  Both read IDENTICAL. Excellent.

WHAT THE OTHERS FOUND (recounted by us)
- sol (job 37): with all 5 processors of its machine busy, kF played the same 4,000 games as r15d in 0.936 of its
  wall time (16 of 16 blocks with equal records); one exe against itself read 1.037 [0.989, 1.085].
- Dot (job 26): two more parts of the stack gave r15d's answer at every counted use (31 counters, 0 differences,
  also under go nodes 20000).
- carbon2 (job 25): leaving three parts out of kF costs 0.8 to 0.9 % of CPU on its machine: the PC would take kF
  whole.

WHY THIS JOB
The owner's standing rule: an idea that lost or stayed level alone gets ONE test together with what it depends on
before it is put aside. Your guard (NullMateGuard) stayed LEVEL alone in jobs 8 to 15: at 2,000 nodes, at 20,000
nodes (four seeds pooled: +3.69 [-2.34, +9.73]), at 80,000 nodes and at 10+0.1. NullThreatVerify (a check option of
your r15d, off unless set) changes the same step: it verifies a null-move cut by a second search. Both act on the
null move's result, so they are a bundle. A Grok report measured NullThreatVerify alone on the helpers' tree; we
have not recounted that number, so it is not quoted here.

JOB 21 (at most 1 hour by the clock from your claim commit; at minute 50 stop playing and write)
First commit "astra5 job 21 claim" with forge-combo29/astra5/job21/stamps.txt (one line per step: date -u, then the
step's name). Commit and push after every step. If your jobs 18 to 20 are not finished when you read this, finish
them first (their reports), then this.

STEP 0, THE MATCH SETUP (except the limits below), the openings rule (openings none of your earlier matches used;
write their line numbers) and the evidence rules: exactly job 12's (the executable with sha256 ca7ef24d..., its
five known numbers, fastchess and book as job 8). nproc into build.txt. Concurrency at most nproc minus 1.
Then two checks on that executable, each in a fresh process, before any game:
- its uci list holds NullThreatVerify as a check option that starts false (write that line as printed);
- PC20 + net768 + "setoption name NullThreatVerify value true" (lowercase true; read every line up to readyok, any
  "unknown option" or "invalid value" line stops the job), then bench 13: the node count must DIFFER from 4275906
  (write it). If it is equal, the option did not reach the search: stop the job.

C21, the control that must move (before the prediction): A = PC20 + NullMateGuard 0 with nodes=10000, B = the same
with nodes=20000, 100 openings = 200 games, seed 7391: the 95 % interval's upper end below 0. Otherwise: STOP THE
JOB.

PREDICTION: commit forge-combo29/astra5/job21/prediction.txt ALONE after C21, before the first game of B1 (never
edited, no time in it): the Elo with its sign of B1 and of B2, each with a range; one line whether your ranges used
the results of jobs 8 to 15.

THE MATCHES (fastchess, both engines the executable above with PC20 + net768, Threads 1, Hash 16)
B1: A = NullMateGuard 2 + NullThreatVerify true, B = NullMateGuard 0 (NullThreatVerify false, as the engine
    starts), both nodes=20000 (the PC's tune), 600 openings = 1,200 games, seed 7392.
B2: the same pair at nodes=2000, 600 other openings = 1,200 games, seed 7393, only after B1.
If minute 50 comes first: stop at whole pairs and mark it incomplete in every row that shows it.
Per match: W-L-D from A's side, the pentanomial counts, Elo with its 95 % interval from the pentanomial counts, the
games that ended by mate, by draw rule and by the 300-move limit.

THE READING (declared here, before any game of this job)
B1 decides: BUNDLE BETTER when its interval lies wholly above 0; BUNDLE WORSE when wholly below 0; LEVEL otherwise.
B2 is description beside it (the PC's self-play depth). A cut B1 is read only on its whole pairs and named "cut".
What follows from it (ours, not your work): BETTER = a question for the PC on its own net after its tune; WORSE or
LEVEL = the guard is put aside as "level alone and in its bundle with NullThreatVerify, under these settings".

WHAT A STOP STOPS: Step 0, its two checks or C21 failing stops the job. A refusal line (unknown option, invalid
value) stops that match. Minute 50 stops the playing: write what is done; a match not played is listed as not
played, never filled.

WHAT THIS CANNOT SEE (write it into the report as it is): the PC's own net, compiler and processor; the PC's tuned
values (its tune is still running); NullThreatVerify alone (only the bundle is played); time controls.

REPORT: forge-combo29/REPORT_astra5_job21.md, first lines: (1) Step 0 with nproc, the concurrency used and the two
checks; (2) C21; (3) the prediction graded; (4) one table: match | settings | limit | seed | games | W-L-D |
pentanomial | Elo [95 %] | endings; (5) the reading, word for word by its rule. Then: facts, suspicions, "what I did
not do", "what I am not sure about". Every number from a file you commit. The last command before the report
commit: git status --short and ls -R forge-combo29/astra5/job21, pasted into the report. Files only under
forge-combo29/astra5/job21/ (and your notes file); no executable, net, book or archive file.

RULES (as in your first message): your own branch for-fable-and-opus/astra5-work only; no pull request, ever; never
change or delete another branch; no change of the engine source in the repository (your trees live outside it);
text files only; nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open Y.

AFTER THE REPORT: look for forge-combo29/soak_all/FABLE_TO_astra5_22.md on handoff/fable-opus-combo29-all-20261114
(git fetch --depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is
your next job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
