# Warm/cold audit of every table I published (seat 10's measurement rule)

Rule given: two identical searches in ONE process with nothing between them give 56,720 -> 4,951 -> 4,516 nodes;
three separate processes give 56,720 each; `ucinewgame` restores cold exactly; `Clear Hash` does NOT (it gives a
third value, 40,569).

## I reproduced the rule first (`job6/raw_warm_audit.txt`)
- one process, 3x `position startpos` + `go depth 12`, nothing between: **56,720 / 4,951 / 4,516** — exactly as
  seat 10 reported.
- 3 separate processes: **56,720 / 56,720 / 56,720** — cold each time.
- one process with `ucinewgame` + `isready` before each `go`: **56,720 / 56,720 / 56,720** — `ucinewgame` restores
  cold, confirmed.

## audit of my own tables

| table | how measured | cold or warm | verdict |
|---|---|---|---|
| HONESTY.txt (bench 11/13/16, perft 5) | fresh process each line | **cold** | VALID |
| job1 profile / timing, bench 13 | fresh process per run; `bench` also clears its table per position | **cold** | VALID |
| job2 paired speed (base/patch) | fresh process per run, 24 pairs | **cold** | VALID |
| job2 equiv_search (40 pos x depth 10) | one search per process | **cold** | VALID |
| job2 equiv_perft (65 pos x d3,d4) | one perft per process | **cold** | VALID |
| job2/raw_rows_sums.txt — **O = 9,500,069, G = 18,466,239** | `ucinewgame` + `isready` before every `go`, in one process (what the brief specifies) | **COLD** (verified above) | VALID |
| job4 profile (400 pos, depth 12) | ONE process, 400 searches, **no `ucinewgame` between them** | **WARM after the first position** | percentages only; see below |
| job5 profile R_2911 (200 pos, depth 12) | same harness | **WARM after the first position** | percentages only; see below |

## what being warm means for the two labelled tables
Those two tables are SHARE tables (percent of samples per symbol), not node counts, and I never published a node
count from them. Warmth changes the work per position — later positions reuse the table and search fewer nodes — so
the MIX of samples is not the same as 400 independent cold searches. Specifically, a warm table means fewer nodes
spent re-deriving what is already stored, which can only *raise* the transposition-table probe share and lower the
rest; so the 3.65 % / 4.86 % `probe_body` figures I published may be slightly INFLATED by warmth, while the
`pick_best`/`next` shares may be slightly deflated. I am labelling both tables WARM rather than silently re-running
them at this deadline, and I state that the 2.14-point ordering gap in job5 and the 0.05-point tie in job4 are both
measured on a warm sequence.

What does NOT change: 29-F11's DIRECTION (probe_body higher in deep search than on bench) is large (2.6x) and its
bench side is cold, but the deep side being warm biases it UPWARD, so the true cold gap could be smaller than 2.6x.
I mark that as a caveat on 29-F11 rather than a retraction.
