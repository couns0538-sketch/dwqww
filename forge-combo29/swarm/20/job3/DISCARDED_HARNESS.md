# seat 19's harness sweep — what it found in my branch, and what it did and did not move

Seat 19 swept all 49 seat branches for committed UCI input files whose last `go` has only `quit`/EOF after it:
251 files total, **20 → 222**, 27 → 25, 19 → 3, 17 → 1. The serious case is mine. This is the audit and the outcome.

## Confirmed: the 222 files are real, and they are from the harness I discarded
I verified it myself:
```
$ ls job3/*.out.txt job3/out/*.out.txt | wc -l
222
$ for f in ...; do grep -q 'info depth' "$f" && c++ || z++; done
with info depth: 0
without: 222
```
**All 222 contain zero `info depth` lines** — every bestmove in them is the fabricated first-generated-move answer.
They come from `job3/fallback.sh`, the **first** harness I wrote for that job, which piped `position`/`go`/`quit`
together.

## What did NOT move, and why — verified, not asserted
1. **I discarded that harness before drawing any conclusion.** `REPORT_job3.md`'s step table opens with
   *"first, a WRONG measurement | done and discarded | out/fallback.out.txt | piping `go` + `quit` together means quit
   always wins; every case 'unsearched'. My criterion, not the engine, was at fault."* The replacement,
   `job3/drive.py`, waits for `bestmove` before writing anything else and produced **26 `info depth` lines** in
   `out_drive1.txt`.
2. **No finding or report ever cited those 222 files as evidence.** Checked:
   `grep -rn 'job3/out/|out/case_' FINDINGS.md REPORT_*.md` returns only `../job3/out/planted.meta` and
   `out/clean.meta` — the **sanitizer proofs**, which are `.meta` files, not search transcripts, and are unaffected.
   `out_fallback.out.txt` is cited nowhere.
3. **`go perft` is synchronous**, so the honesty perft numbers are unaffected (seat 19 says this explicitly and I
   confirmed the `perft5` run completes before `quit` is read).
4. **Every job after job3 used the proper driver.** From job24 onward, `AUDIT/hardened.py` reads to `bestmove` before
   `quit` and raises if no `readyok` arrives.

## The one thing that IS affected, and it is a label rather than a number
`out_clockcut.txt`, `out_clockcut_bookoff.txt` and `out_fallback2.txt` also contain **zero `info depth` lines** — but
for a different reason: they are **my script's own summarised tables** (the header line `exe=... runs unsearched moves
seen ref(depth12)` is visible), not engine transcripts. So the absence is expected there. I state it because a
mechanical sweep like seat 19's cannot tell the two apart, and a reader should know which is which.

## So what moved: nothing numeric. What I am changing anyway
1. **The 222 files stay on the branch but are now labelled** — a `job3/DISCARDED_HARNESS.md` beside them says they
   come from the piped harness, contain no search, and support nothing.
2. **The driver rule goes into METHOD as a hard rule**, with the abort condition spelled out: read stdout until
   `bestmove` before sending anything else, and **abort any row whose search produced zero `info depth` lines**.
3. **FINDINGS gains a line naming the jobs that used the old driver**, so a reader knows which numbers were
   re-produced on a correct driver.

## Honest assessment of the report
Seat 19's sweep is a good check and it found a real defect in my folder — a discarded harness whose output sat
committed and unlabelled for hours, 222 files of fabricated bestmoves that *look* like evidence to a scanner. The
conclusion does not change, but **leaving that much zero-value output in an evidence directory is itself a fault**,
and the labelling fix is the right response rather than deleting it (deleting would hide that it happened).
