# Harness invalidation — job 1 (v1) numbers WITHDRAWN

Coordinator broadcast (from seat 19, finding 19-F12): if a harness pipes `quit` or closes stdin while a
search is running, this build answers a FABRICATED `bestmove` with zero `info` lines.

I reproduced it on my own build before acting (/agent/repos/base/forge-combo29/build/forge,
sha256 e06310ec...); raw in `harness_check/fabrication_quantified.txt`:

```
$ printf 'uci\nposition startpos\ngo depth 12\nquit\n' | forge
info lines: 0      bestmove a2a3
$ interactive: go depth 12, 2 s, then quit
info lines: 12     last: info depth 12 ... nodes 56720 ... pv e2e4 ...
bestmove: e2e4
```

## what this breaks, in my own work

**job 1 v1 (`run_sequences.py`, `out/`, `REPORT_job1.md`) — INVALID, WITHDRAWN.**
That runner wrote a whole sequence to stdin and closed it, so every one of its 5,827 `bestmove` lines was
produced through the fabrication path. 1,779 of its 2,000 sequences had a command after their last `go`.
Its "0 illegal bestmoves" and its "5,827 go = 5,827 bestmove" are therefore NOT results: a fabricated
`bestmove a2a3` on startpos happens to be legal, which is exactly why the check passed and why the check
could not catch this. The sequence *generation* (`seqs.jsonl`, seed 201) is unaffected and is reused.
Re-run: `run_sequences_v2.py`, an interactive driver that sends one line, reads its answer to completion
(`bestmove` / `readyok` / `uciok`), then sends the next; stdin is closed only after the last answer.

**job 2 (`race_job.py`) — VALID, no re-run.** It was already an interactive driver: it waits for `bestmove`
before continuing (median 94 output lines per run) and never closes stdin mid-search. One arm sends `quit`
during a search ON PURPOSE (that is the thing being tested); its 1,000 runs each printed a `bestmove` before
exit, which I record as observed behaviour, not as a search result.

**check08f2 (S-C1, CONFIRMS 08-F2) — VALID.** That harness reads to `bestmove` before the next command.

## lesson recorded for my own harnesses from now on
Every `go` must be followed by a read of stdout up to and including `bestmove` before the next byte is
written, and the process is only sent `quit` after the last answer arrived. A harness that checks only
"did a legal bestmove come back" cannot detect this build's fabrication, because the fabricated move is
legal; the detector is the number of `info depth` lines before the `bestmove` (0 = fabricated).
