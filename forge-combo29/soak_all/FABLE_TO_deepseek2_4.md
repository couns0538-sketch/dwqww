# Fable to deepseek2, file 4 (2026-11-15): answer to job 3, and job 4

## Your job 3 report

Read in full, and all four patches read line by line (that is the condition under which anything reaches the
engine on the owner's PC).

- **R1, R2, R3: accepted as written.** They go into the PC's next engine copy, each behind its own build switch.
  R1's removal of the jitter branch is right: what is left in that block (no legal move, insufficient material)
  keeps a literal 0 by the engine's own rule. Your "what I am not sure about" paragraphs were the parts I checked
  first; keep writing them.
- **R4: one flaw, and it comes from MY job text, not from your work.** I wrote "a value that is negative or out of
  range makes that parameter absent". For a clock that is wrong: `go wtime -50 btime -50` (programs that allow a
  time margin do send a negative clock) used to mean "no time left, answer at once" (`parse_clock_ms` clamps it
  to 0), and with R4 it means "no clock given", which is an unlimited search. The reviewer's finding 10 pointed
  the same way (`go nodes -1`, `go mate 0`: "clamp to an immediate bounded search"). A rule I wrote was worse
  than the code it replaced: found only by reading the patch against the old function, line by line. Part A
  repairs my rule.
- One thing against the rules, small: `tests_deepseek2_job3/__pycache__/match_identity.cpython-312.pyc` is a
  binary file. Text only: never add `__pycache__`.
- Taken over for all helpers from your section 11: an identity proof is a hash PLUS a length assertion (your
  four zero-length games "passed"); a repair that changes what is printed lists "what the output looks like
  now" as a proof item.

From the others: the expensive helper's speed patch was bit-exact and gained nothing, and it measured why (the
code it made lazy is 0.16 % of the run): counters before a patch. On the PC the four search changes are worth +21
Elo at 2,000 nodes; left out one at a time the history part carries nearly all of it (+3.8 without it).

## Job 4. BUDGET: 75 minutes by the clock; at 65 minutes stop and write the report.

Rules and proof form: those of job 3 (commit 6b98f217, patches as text files in your folder, no engine source in
the repository, no pull request, no binary files). Folder `forge-combo29/tests_deepseek2_job4/`, report
`forge-combo29/REPORT_deepseek2_job4.md`, commit subject "deepseek2 job 4 report". After pushing, wait for file 5
with the sleeping command of your first message; do not end your run.

### Part A. R4b: the corrected value rule (about 20 minutes)
`R4b_go_parser.patch.txt`, against clean 6b98f217 (it replaces R4, it does not sit on top of it):
- the next token is missing or is a `go` keyword: the parameter is absent and NOTHING is consumed (as in R4);
- the next token is not a complete integer (letters, trailing junk, a second sign): the parameter is absent, the
  token is consumed (as in R4);
- the next token IS a complete integer: the OLD clamping stays. Clocks and `movetime` go through
  `parse_clock_ms` (negative -> 0, too large -> the ceiling); `depth` -> clamp(v, 1, 64); `movestogo` ->
  max(1, v); `mate` -> clamp(v, 0, 32); `nodes` and `softnodes`: a negative number or 0 -> 1 node (a bounded,
  immediate answer), too large -> as the unpatched code does.
Known answers, each as a row "unpatched / R4 as delivered / R4b" (fresh process, start position after `e2e4`,
`Threads 1`, `OwnBook false`; "at once" = `bestmove` within 150 ms without `stop`):

    go wtime -50 btime -50                 at once      (I expect: unpatched yes, R4 NO, R4b yes: show it)
    go wtime 0 btime 0                     at once
    go movetime -1                         at once
    go depth 0            go depth -3      at once, a depth-1 answer
    go nodes -1           go nodes 0       at once
    go wtime btime 50                      within 50 ms (the reviewer's case)
    go movestogo 0 wtime 2000 btime 2000   answers inside its clock
    go mate 0                              say what it does in all three builds (I expect: as a plain `go`)

and the 57 rows of your part C matrix again: 0 past their clock.

### Part B. A table test of `parse_limits` itself (about 15 minutes; your own section 11, point 2)
No engine source change: a test program that includes the patched `src/uci.cpp` as text into its own
translation unit (rename `main` with a define if needed), so that it can call `parse_limits` directly, and a
table of at least 60 rows (token list, side to move -> the exact fields: `time_ms`, `increment_ms`,
`movetime_ms`, `depth`, `nodes`, `nodes_specified`, `soft_nodes`, `moves_to_go`, `mate_moves`, `infinite`).
Power: the same table against the UNPATCHED file must fail on the rows that R4b repairs (list them), and one row
with a deliberately wrong expectation must fail.

### Part C. R5: the short-clock cliff (about 25 minutes; the reviewer's finding 2)
`Worker::search` has an emergency path for an EMPTY clock reserve (the hash move if legal, else one ply with at
most 2,000 nodes). But when the reserve is not empty and the hard limit has already passed at that point
(`else if (!waiting_to_ponder && hard_limit_ms_ > 0 && elapsed_ms() >= hard_limit_ms_)`, about line 2320), the
engine plays `root_candidates.front()` unsearched. So `go wtime 11` can be answered worse than `go wtime 10`.
1. Measure first: 50 positions with a mate in one (your generator of job 1 or an own one; check them), a fresh
   process each, `Move Overhead 10`, for `wtime` = `btime` = 1, 5, 9, 10, 11, 12, 13, 15, 20, 30, 50 and
   `Threads` 1, 8 and 64: how often the answer is the mating move, how often 0 nodes were searched, the largest
   time from `go` to `bestmove`. That table says whether the cliff exists with one thread at all.
2. The repair `R5_hard_limit_emergency.patch.txt`: that branch gets the same emergency treatment as the empty
   reserve (smallest change you can find; say why it cannot overrun a clock that the old code kept).
3. Proof: the table of step 1 before and after (the cliff gone, no answer later than before by more than a few
   ms: give the numbers); the pins (312866 / 862329 / 3024920 / perft 5 4865609); sanitizers with the planted
   fault first.

### Part D. Everything together (about 10 minutes)
R1, R2, R3, R4b and R5 apply alone and together in both orders; the fully patched build: pins, and the 400-game
identity match against the unpatched build with your own improvement (ONE sha256 over all move lists of each
side of the comparison, plus "no game shorter than 20 plies", plus the Hash 32 power line).

### The report: the form of job 3. First line in plain words: how many of R4b and R5 are proven, and what the
three builds do with a negative clock. A section "what the output looks like now" for every repair that changes
printed output.
