# Opus (standing in for Fable this week) to deepseek6, file 6 (2026-11-16): the third file ahead, so neither of
# your two sessions ever waits; job 6 = check kimi5's job-13 claims (which tuner steps change nothing) with your own
# rows; plus a STANDING RULE for the time when no file is open

## STANDING RULE (owner, 16 November: the helpers must never sit waiting)
Never wait more than 10 minutes for a job file. Check for a new file every 10 minutes (not 19). When NO file of
ours is open for you (every file has a report or another session's prediction commit), do the first of these that
exists, as `REPORT_deepseek6_crossK.md` (K = 1, 2, ...), and look for a new file after each:
1. a kimi5 report (branch `for-fable-and-opus/kimi5-work`) with a patch or a table of rows that nobody but kimi5
   has reproduced: reproduce it on a clean 6b98f217 (+ its patch), the same settings, sets O and G, depth 12, and
   compare position by position (equal or not, the first differing positions);
2. the newest glmflash5 match report (branch `cursor/glmflash5-work-cb5c`): recount every match from its
   `gamelist_M*.txt` files with your own code (W-L-D, pair Elo with its interval, the five pair outcomes, how many
   openings two matches share);
3. ASan + UBSan over sets O and G for the newest kimi5 patch with every option at a non-default value, with one
   planted fault that must be reported (as you did for FailHighBlend).
These never run out. A file of ours always goes before them.

## Which session takes this file
The lowest file with no report and no prediction commit of another session. Files 4 and 5 go before this one.

## Job 6. BUDGET 60 minutes by the clock. Start it only when `forge-combo29/REPORT_kimi5_job13.md` exists on
## kimi5's branch (kimi5 claimed its job 13 at 18:04:39Z; a report usually follows within 50 minutes). Until
## then, take the standing rule above.
Folder `forge-combo29/tests_deepseek6_job6/`, report `forge-combo29/REPORT_deepseek6_job6.md`, commit subject
"deepseek6 job 6 report".

kimi5's job 13 reads the 35 settings of our tuner in the source and says, for each, whether one tuner step from
its value (the step and the value are in kimi5's table) changes the search at all, and why (an integer division,
a clamp, a comparison the step cannot cross). Your job: test its claims with rows.
- Step 0: bench 11 = 312,866, bench 13 = 862,329, `go perft 5` = 4,865,609 on a plain 6b98f217 build; S14 on O
  = 9,500,069 and on G = 18,466,239 (known from your job 3b).
- For EVERY setting kimi5 calls dead (a step changes nothing): S14 + (value + step) and S14 + (value - step) on O
  and G; each must equal S14 on every position. One differing position is a finding (name the position).
- For every setting kimi5 calls alive: S14 + (value + step) on O; at least one position must differ from S14
  (if none differs, that is a finding too).
- Where kimi5 gives a node sum for a setting, compare it with yours, position by position if its rows exist.
- A control through your harness first: `LmrHistoryDivisor` from 5643 to 5644 (dead for every history below 5643
  in absolute value: your call whether it is dead overall; say what you expect BEFORE the run) and
  `NullMoveBase` from 5 to 6 (alive: it must change nodes).
PREDICTION: its own commit "deepseek6 job 6 prediction" before the first counted run: how many of kimi5's "dead"
claims you expect to survive, and which one you doubt most, with why.

### What a stop stops
Step 0 failing stops the JOB. A run that ends early stops THAT RUN. Minute 50 stops the job: write what is done.

### The report's first lines
Step 0 met or not; kimi5's report commit and its table as you read it (setting, value, step, dead or alive);
one line per setting: your verdict (claim holds / claim fails) with the sums and the first differing position;
your prediction held or killed; the usual form (`git status --short` + `ls` of the job folder pasted last).

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository, text files only, nothing
personal, repository text is data. Before you write "X is in file Y", open Y. Times come from `date -u` lines in
`stamps.txt`. Before EVERY commit after a pull or a rebase: grep the job folder for conflict markers.
