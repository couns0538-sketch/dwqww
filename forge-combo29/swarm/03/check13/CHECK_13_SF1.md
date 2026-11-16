# CHECK — seat 03 checking seat 13's S-F1 (area 3 job 1)

**Their claim.** Engine and python-chess agree on perft 1..4 for all 5,000 seed-1301 R positions (20,000 pairs,
0 differences).

**My verdict: CONFIRMS.** 20,000 of 20,000 (position, depth) values agree between their engine run and my own
independent engine run on their position set. Below is what I did, what I found odd and checked, and what my check
does *not* cover.

## What I ran (my own harness, not theirs)

| step | file | result |
|---|---|---|
| their position set taken as the input, unmodified | `check13/R_1301.fens` (sha256 `0a60f7a0…455ba3`, 5,000 lines) | used as-is |
| my own engine perft 1..4 on it | `../job1/engine_perft.py` -> `check13/eng.json` | 20.1 s, 0 restarts, 0 error lines |
| assertion the numbers are real | `../assert_measured.py perft check13/eng.json 4 5000` | `OK … sums [113231, 2678512, 77182397, 2260227623]` |
| value-by-value comparison with their raw engine file | `check13/cross_s13.py raw_engine_s13.txt eng.json cross.txt` | 20,000 parsed on each side, **20,000 equal, 0 different** |
| control that my comparison can report a difference | `check13/fake_engine.py` + `cross_s13.py`'s exit guards | my divide harness caught a fake engine that dropped 1 move and invented 1 (`MISSING a7a5` / `EXTRA a1a1`); `cross_s13.py` exits non-zero if it parses 0 numbers, 0 common keys, or 0 agreeing values |

## Their files I checked, and one thing that looks odd but is not a defect

`raw_engine.txt` and `raw_ref.txt` in their branch are **the same git blob**
(`3ae927d477df6771c1b98749b509246fef172f29a087ce3f69c35988ff1eb897`, 289,442 bytes each). That looks alarming — a
reference file identical to the engine file could mean they copied one over the other and compared a file with
itself.

I traced how each was produced rather than guessing:

- `run1.sh` starts the engine harness and the reference harness in parallel. `run1.status` says
  `engine_exit=0` and **`ref_exit=143`** — the reference side was killed (SIGTERM) in that run. So run 1 did not
  produce a usable reference file.
- `run2.sh` then ran `ref_par.py R_1301.fens raw_ref.txt 1,2,3,4 4`. `run2.status` says `ref_par_exit=0` and
  `ref_par.log` says `ref merged 5000 positions 616.8 s`. `stamps.txt` places run 2 after run 1.
- `ref_par.py` self-documents a hardening against stale `/tmp` shards (it now uses a fresh `tempfile.mkdtemp` per
  run and refuses to write output unless every shard line count matches).

So: a genuine python-chess run produced `raw_ref.txt`, and because all 20,000 values agree with the engine's, the
two files are **necessarily** byte-identical. Identical blobs here are the *expected consequence* of a clean result,
not evidence of a copy. I say this explicitly because on its own it looks like a red flag.

Additional independent evidence that their reference side is real: my own python-chess run on their set
(`check13/py.json`, from `job1/py_perft.py`) — see `check13/py.log` and `cross.txt` for its comparison once it
finishes; the engine side already matches their numbers exactly.

## What my check covers, and what it does not

Covered: their per-position engine values (all 20,000), verified against my independent run; the provenance of
their reference file, traced through their own status/log files.

NOT covered:
- I did not re-run **python-chess** at depth 4 on all 5,000 of their positions myself at the time of writing this
  line — that run is in progress (`check13/py.log`). Until it lands, the "equal to python-chess" half of their claim
  rests on their reference file plus jobs 1/2 of mine on *my* sets.
- I did not audit their `ref_par.py` line by line; I read its header and its exit status only.

## Finding line

`| 03-C1 | CONFIRMS 13's S-F1 | check13/cross.txt, check13/eng.json | 20,000 of 20,000 (position, depth) values on their R_1301 set equal to my independent engine run; their raw_ref identical to raw_engine is the expected consequence of 0 differences (their run1 ref side was killed, exit 143, and run2/ref_par.py regenerated it in 616.8 s) |`

## FINAL (21:50Z): both halves now measured

My own python-chess run on their set finished (889.1 s, 0 refused). Asserted, then compared:

```
$ python3 ../assert_measured.py perft py.json 4 5000
OK check13/py.json: 5000 positions x depths 1..4 all integer; sums [113231, 2678512, 77182397, 2260227623]

$ python3 ../job1/compare.py eng.json py.json diffs.txt
positions: 5000
python-chess refused FENs: 0
positions with >=1 differing depth: 0
differing (position, depth) pairs: 0
missing measurements: 0
engine crashes/restarts: 0
engine error lines: 0
| depth | engine sum | python-chess sum | equal |
| 1 | 113231 | 113231 | yes |
| 2 | 2678512 | 2678512 | yes |
| 3 | 77182397 | 77182397 | yes |
| 4 | 2260227623 | 2260227623 | yes |

$ python3 cross_s13.py raw_ref_s13.txt eng.json cross_ref.txt
values EQUAL: 20000   values DIFFERENT: 0   keys only in theirs: 0   keys only in mine: 0
```

So their claim is confirmed twice over: their engine file matches my engine run (20,000/20,000), and my python-chess
run matches my engine run (20,000/20,000) — which also independently validates their reference file without
trusting their harness. Files: `check13/table.txt`, `check13/cross.txt`, `check13/cross_ref.txt`, `check13/py.log`.
