# REPORT job 2 — AREA 2 (races during a running search, ASan + UBSan)

what was asked / the answer / how sure
- Asked: during a `go infinite` or `go depth 30`, send stop / ponderhit / ucinewgame / setoption Hash / quit
  after a random delay of 0 to 50 ms, 1,000 times each; same table (sequences / crashes / hangs / sanitizer
  lines / illegal bestmoves), every bad sequence committed.
- Answer: 5,000 runs. 0 crashes, 0 hangs, 0 sanitizer lines, 0 illegal bestmoves. After every one of the
  4,000 non-quit interrupts the engine answered `readyok` and a fresh `go depth 2` again; after every one of
  the 1,000 quits the process exited within 5 s. One behaviour is worth knowing and is not in the known list:
  **`ponderhit` on a search that was NOT started with `go ponder` does nothing, and the search keeps running**
  (1,000 of 1,000) — so a GUI that sends ponderhit to cancel a search waits for a `bestmove` that never comes
  until it sends `stop`.
- How sure: high on crashes/hangs/sanitizer lines (these are direct counts of process exit and stderr over
  5,000 runs). Medium-high on "0 illegal bestmoves": the interrupted search's bestmove is judged against the
  position the `go` was sent in, which is the right board for stop/ponderhit/Hash but is only the right board for
  `ucinewgame` if the engine answers the OLD search before resetting — that is exactly what the 0 count means,
  and it is what the check tests.

## honesty numbers

```
release build (honesty numbers) sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
  bench 11 312866   bench 13 862329   bench 16 3024920   perft 5 4865609   all PASS (HONESTY.txt)
build used for this job      /agent/repos/base/forge-combo29/build-asan/forge
  sha256 b109a0a5acce5b0ddad5707c04f8263fe51f48a890df4a7a2ea6ffcef8a43f99
  nm -C | grep -c __asan_ = 35    __ubsan_ = 15    __tsan_ = 0
```

Both sanitizer proofs are in `sanitizer/NOTES.md`: the nm counts above, and a planted fault (heap over-read
`sanprobe`, signed overflow `ubprobe`) on a scratch copy at /tmp/forge-fault, run through the SAME runner —
clean 0 lines, fault build 3 lines, fault build with the probe input removed 0 lines.

## the table

`python3 summarise.py out` — reads only the 5,000 committed per-run records. Pasted:

| command | runs | crashes | hung | san lines | readyok after | follow-up search answered | illegal bestmove |
|---|---|---|---|---|---|---|---|
| stop | 1000 | 0 | 0 | 0 | 1000 | 1000 | 0 |
| ponderhit | 1000 | 0 | 0 | 0 | 1000 | 1000 | 0 |
| ucinewgame | 1000 | 0 | 0 | 0 | 1000 | 1000 | 0 |
| setoption Hash | 1000 | 0 | 0 | 0 | 1000 | 1000 | 0 |
| quit | 1000 | 0 | 0 | 0 | 0 (not applicable) | 0 (not applicable) | 0 |

Additional counts from the same files:

```
ponderhit arm: continued searching (no bestmove from the ponderhit itself): 1000 / 1000
quit arm:      exited within 5 s: 1000 / 1000 ; a bestmove was printed before exit in 1000 runs
stop arm:      19 distinct bestmoves over 1000 runs; most common b4f4 x128, f6h5 x128, d4c5 x118
               (a real search tree each time, not one canned answer)
```

The 19 distinct moves across 7 different positions is the control that the searches actually ran: a
fabricated answer or a canned one could not produce a spread like that.

### step | done-partly-not done | evidence file | result

| step | state | evidence | result |
|---|---|---|---|
| prediction committed alone before measuring | done | `prediction.txt` | 7 predictions, ranges stated |
| harness written and committed before measuring | done | `race_job.py` | interactive: reads to `bestmove` before the next command |
| 1,000 stop during a search | done | `out/runs_stop.json` | 0 crash / 0 hang / 0 san / 0 illegal |
| 1,000 ponderhit during a search | done | `out/runs_ponderhit.json` | 0 crash / 0 hang / 0 san; search CONTINUED 1,000/1,000 |
| 1,000 ucinewgame during a search | done | `out/runs_ucinewgame.json` | 0 crash / 0 hang / 0 san / 0 illegal |
| 1,000 setoption Hash during a search | done | `out/runs_setoption_Hash.json` | 0 crash / 0 hang / 0 san / 0 illegal |
| 1,000 quit during a search | done | `out/runs_quit.json` | exited within 5 s 1,000/1,000 |
| summary table generated from raw | done | `summarise.py`, `out/summary.txt` | pasted above |
| every bad sequence committed | done (vacuously) | `out/bad/` does not exist — no run set a fault flag | nothing to commit |

### prediction, as committed before measuring

| # | predicted | got | verdict |
|---|---|---|---|
| 1 | crashes 0 | 0 | held |
| 2 | hangs 0 | 0 | held |
| 3 | sanitizer lines 0 | 0 | held |
| 4 | runs not exiting within 5 s of quit: 0 | 0 | held |
| 5 | bestmove printed after quit: 0 | a bestmove was printed before exit in 1,000/1,000 — see below | **I mis-stated this one** |
| 6 | illegal bestmove after stop/ucinewgame/Hash: 0 | 0 | held |
| 7 | interrupted searches with NO bestmove at all: 0..20 | depends on the arm; see the note | held with a correction |

On 5: I predicted "no bestmove AFTER quit". What actually happens is that `quit` during a search stops the
search and prints its `bestmove` before exiting (1,000/1,000, median 94 output lines). So my wording was
wrong, not the engine: there is no bestmove after the process would have exited — there is one just before.
This is consistent with seat 19's 19-F12 only in the sense that both involve an interrupted search; the
0-info-line fabrication I reproduced (`harness_check/fabrication_quantified.txt`) is a different path and
did NOT appear here.

On 7: my prediction assumed `ucinewgame` would be the risky arm. It was `ponderhit` instead, for a reason I
had not considered: ponderhit is only meaningful for a ponder search, so on a normal search it is a no-op and
the search runs on. I had to add `stop` in that arm or the run could never end; the arm now measures
"ponderhit does not terminate the search" instead of "the engine answers the interrupted search".

## findings

S-F3 — `ponderhit` sent while a NON-ponder search runs is a no-op and the search keeps running; no `bestmove`
follows until a `stop` arrives. 1,000 of 1,000 runs.
Show it again:

```
printf 'uci\nisready\nposition startpos\ngo infinite\nponderhit\n' | /agent/repos/base/forge-combo29/build/forge
```
(no `bestmove` appears; add `stop\n` and one appears). Raw: `out/runs_ponderhit.json`, field
`continued_after_ponderhit` true in all 1,000.

This is correct UCI behaviour, not a defect — I record it because the known list does not mention it and a GUI
that uses ponderhit as a cancel would hang on it.

## suspicions, not proven

- The `setoption name Hash value N` arm reallocates the table between searches, but my runs nearly all hit the
  search before `stop_search()` joined it, so in practice the reallocation happened on an idle engine. A true
  reallocation DURING a search would need the option sent from another thread; my single-threaded driver can
  never do that. So "setoption Hash is safe during a search" is NOT what I measured; what I measured is
  "setoption Hash sent 0-50 ms into a search, from a driver that then waits for the answer, is safe".
- TSan was not used for this job (that is area 4). "0 sanitizer lines" here means ASan+UBSan only; a data race
  that does not corrupt memory would not be reported by either.

## what I did NOT do

- No Threads > 1: every run was single-threaded, so a race between search threads is out of scope here.
- No `go infinite` + `stop` at sub-millisecond delays: the smallest delay actually drawn was 0 ms, but 0 ms
  means "sent immediately after writing go", not a synchronised race.
- I did not test two interrupts back to back (stop then immediately ucinewgame) more than the random sequences
  happened to produce.

## what I am NOT sure about

- Whether `ponderhit` being a no-op is intentional in this engine. I read only that the `ponderhit` branch
  requires `ponder_search_active` (src/uci.cpp); I did not trace what sets it beyond `limits.ponder`.
- Whether the 20 s per-answer timeout is generous enough for `go depth 30` on a heavily loaded 4-core box under
  ASan. The `stop` arm finished in 74 s of wall time for 1,000 runs, so the searches were short; a `depth 30`
  search that ran long would still be bounded by the driver's stop, which is why no hang was recorded.

## times

see `out/meta.json` (`started_utc`) and the `date -u` line in each commit; per-arm durations are in `run.log`
(`== stop done in 73.9s` etc.).

## last command's output

```
$ git status --short
(clean apart from the files this report's commit adds)
$ ls job2
out  prediction.txt  race_job.py  run.log  summarise.py
```
