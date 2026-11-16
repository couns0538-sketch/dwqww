# Audit of MY results against seat 10's warm-search rule

Seat 10's rule: a cold baseline is a fresh process or `ucinewgame`, NEVER `Clear Hash`; several searches in
one process with nothing between them are warm and give different node counts.

I verified the claim on my own build first — `warm_check.py`, interactive, raw in `out/rows.json`:

```
== startpos
   three separate processes      : [56720, 56720, 56720]
   one process, nothing between  : [56720, 4951, 4516]
   one process, ucinewgame       : [56720, 56720, 56720]
   one process, Clear Hash       : [56720, 40569, 35808]
== middlegame (r2q1rk1/... depth 12)
   three separate processes      : [68210, 68210, 68210]
   one process, nothing between  : [68210, 5497, 4437]
   one process, ucinewgame       : [68210, 68210, 68210]
   one process, Clear Hash       : [68210, 51196, 43605]
```

The startpos row reproduces seat 10's numbers EXACTLY (56,720 / 4,951 / 4,516 and Clear Hash 40,569), so the
claim holds on this build, not just on theirs.

## every result of mine that touches node counts, classified

| result | does it compare node counts? | measured how | status |
|---|---|---|---|
| HONESTY.txt — bench 11/13/16, perft 5 | yes, against four fixed numbers | each in a FRESH process, one command per process (`run_honesty.sh`) | **COLD, valid**. Separately re-tested: three bench 12 in one process, with `ucinewgame`, and with `Clear Hash` all give the identical 467,411 — `bench` clears its own state per position (it calls `bench_searcher.clear()` per FEN), so bench is immune to this effect. |
| S-C1 / check08f2 — movetime latency | no node counts at all; wall-clock only | one process per (movetime, overhead) cell, 72 searches per cell | **unaffected** (time, not nodes). The cells are warm within themselves — 72 searches in one process — but every cell is warm the SAME way, so the comparison between cells is still like-for-like. I state this rather than leave it implied. |
| S-C2 / check_s11f8 — `UseNNUE` on/off | YES: bench 13 862,329 vs 907,205 | each `bench` in its OWN fresh process (`bench_nodes()` starts a new subprocess) | **COLD, valid**, and bench is self-clearing anyway (see above). |
| REPORT_job1 (v3) — 2,000 sequences | no node counts compared; only legality and counts of answers | one fresh process per sequence | **unaffected**. Within a sequence, later searches are warm, which is why I never compared node counts inside one sequence. |
| REPORT_job2 — race arms | no node counts | one process per run | **unaffected**. |
| REPORT_job3 — options | no node counts compared; I checked answer lines and that the next search was legal | one process per case | **unaffected**. |
| finding_button / nnuefile_probe | YES: `eval` values (not node counts) before/after `NnueFile` | one process each, but three separate `printf | forge` runs | **COLD**: three separate processes. `eval` is a static evaluation with no search state, so warm/cold does not apply, but the runs were cold regardless. |

## what this changes
Nothing in my filed numbers: I never used `Clear Hash` as a baseline and I never compared node counts across
searches in one process. The one place I came close is S-C1's "72 searches in one process", which is a
latency measurement per cell and warm identically in all four cells — now labelled explicitly in RESULT.md
rather than left for a reader to notice.

## what I did NOT do
- Did not re-run the job-3 option sweep with `ucinewgame` between cases. Its node-free nature means the
  warm effect cannot bite it, but I am saying so instead of implying I re-measured.
- Did not determine WHY a warm search is cheaper (histories/cont-hist survive `ucinewgame`? no — ucinewgame
  restores cold exactly, so it is the histories in the SEARCHER that `ucinewgame` clears and `Clear Hash`
  does not). That mechanism belongs to whoever owns the searcher; seat 17's S-C6 measured the same thing from
  another angle.
