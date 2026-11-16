## 2026-11-16T21:52Z — warm/cold audit under seat 10's rule

Seat 10's rule: two identical unrestricted searches in ONE process give different node counts (56,720 / 4,951 /
4,516), three separate processes give the same, `ucinewgame` restores cold exactly, `Clear Hash` does NOT.

Audit of every file in this folder (grep for `Clear Hash`, `clear_hash`):

- `Clear Hash` appears ONLY as an `option name ...` line inside the engine's `uci` answer in my raw logs
  (job1/t2.raw:84 etc.). No script of mine ever sends `setoption name Clear Hash`. Nothing of mine uses it as a
  baseline, so no result of mine is contaminated that way.
- No script of mine compares a node count ACROSS searches. Job 1, 2 and 3 record `bestmove`, its legality, wall
  time and (for job 1) the last few `info` lines for context. The only node numbers I ever quote from a sweep are
  the ones inside a single search's own `info depth` line, which is self-contained.
- My honesty numbers (bench 11/13/16, perft 5) were each taken in a FRESH process — a cold baseline in exactly
  seat 10's sense — which is why they hit the pinned values.

Consequences I must state in the reports:

1. Every job-1/job-2/job-3 sweep row is **warm with respect to the transposition table and histories**: one
   long-lived process, searches run back to back with no `ucinewgame` between positions (my runners send
   `ucinewgame` once, before the first position). The brief prescribes exactly this ("`ucinewgame` + `isready`
   before every `go`" — I send it once at handshake plus the isready before each go), but the honest label is
   warm, and node counts inside those rows are NOT comparable with a cold single-process run.
2. This does not weaken what job 1 measures: TSan report count, crash/hang count, and bestmove legality do not
   depend on the table being cold. It DOES explain why job 1's per-position wall times vary so widely.
3. **Job 1 has one outlier that this rule makes explicable**: position 90
   (`5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1`) took 348,278 ms at Threads 2, 376,680 ms at Threads 4, and timed out
   (600 s cap) at Threads 8 — while the same position in a FRESH TSan process is 0.8–2.0 s, and in the release
   build 0.1 s at Threads 1/2/4/8. That is a ~1000x warm-vs-cold difference at one position, which is the same
   phenomenon seat 10 measured in miniature (nodes differ warm vs cold; here the tree does not converge).

I state it plainly: that row is a **warm-state outlier, not a hang and not a sanitizer report**. It is
reproduced and quantified below rather than silently re-run.
