# INTEGRITY AUDIT — seat 13, after the coordinator's 19-F12 and parser warnings

Both warnings were well aimed at me: I hit three separate integrity faults in my own tooling, and
two of them would have produced a confident-looking wrong result. This file records each one, how
it was caught, and what changed. It is the honest part of my record.

## 1. Pipelined `quit` vs async search (19-F12) — reproduced, does NOT affect my results

I reproduced seat 19's finding on my own build before doing anything else:

```
printf 'uci\nisready\nposition startpos\ngo depth 12\nquit\n' | forge
  -> bestmove a2a3            (no info lines at all)
```
The same search read to `bestmove` before sending `quit` gives
`bestmove e2e4` at `nodes 56720`.

**Audit of my harnesses.** `job1/engine_perft.py` and `job2/engine_perft.py` are interactive: they
send one command, read stdout until the expected token (`readyok`, `nodes`), and only send `quit`
at the very end. They never close stdin mid-command. `job2/divide_check.py` and
`checks/check_21f1.py` DO pipeline via `subprocess.run(input=...)`.

**Why that does not invalidate those two:** the fabrication is a property of the *asynchronous
search* path. Perft is synchronous on this build, shown by direct comparison:

| form | command | result |
|---|---|---|
| pipelined | `printf '...go perft 6\nquit\n'` | `nodes 119060324` |
| interactive | read to `nodes` before `quit` | `nodes 119060324` |
| pipelined | `go perft 5` (honesty pin) | `nodes 4865609` |
| pipelined | `bench 13` | `nodes 862329` |
| pipelined async control | `go nodes 1000000` + `quit` | `bestmove a2a3` (fabricated) |

So every *perft* number I have recorded stands, and the honesty pins were re-run interactively
anyway (`honesty/recheck_interactive.py`, output `honesty/honesty_recheck.txt`): all four MATCH.

I do **not** report 19-F12 as my own finding; it is seat 19's. My `S-C1` (check of 21-F1) used a
pipelined harness, but every number in it is a perft node count, which the table above shows is
unaffected — and case D and case B in it are controls that would have failed if the engine had not
actually responded.

## 2. A parser that would have confirmed without measuring — found and fixed

My first `job1/compare.py` skipped any `(position, depth)` pair missing from either file:

```python
if e is None or r is None:
    continue          # <-- a truncated or empty reference file reports "0 differing"
```

That is precisely the fault the coordinator warned about. An empty reference file would have
produced `TOTAL differing pairs: 0` and looked like a clean pass.

`compare.py` is now hardened. It raises on: an empty file, a missing record for any pair asked
for, a non-integer node count under an `OK` marker, a position-count mismatch, and — separately —
it refuses to declare a pass if zero pairs were actually compared. Proof that it fails when it
should, run on my real job 1 data:

| planted fault | what the hardened checker did |
|---|---|
| empty reference file | `FAIL reference: no records at all (empty file) - nothing was measured` |
| reference truncated to 100 records | `FAIL depth 1 position 25: NO REFERENCE RECORD` |
| a node count replaced by `nan` | `FAIL reference line 2: marker OK but node count 'nan' is not an integer` |
| the real files, untouched | `pairs in scope 20000, compared 20000 / differing pairs 0` |

Only the last line is a pass, and it states how many pairs were compared.

## 3. A stale-file merge that invented 1,929 differences — found and fixed

My `ref_par.py` wrote its per-shard output to fixed paths `/tmp/refpart<k>.txt`. After I rebuilt
the job 2 position set (500 -> 494 positions, different FENs), a re-run silently merged **stale
shard files from the previous run**, so half the reference numbers belonged to different boards.
The hardened `compare.py` immediately surfaced it as 1,929 differing pairs instead of the
"0 differences" the old silent-skipping version would have reported.

I checked ground truth directly rather than trusting either file:

| position | FEN | python-chess perft 1 | engine | stale ref file |
|---|---|---|---|---|
| 16 | `1rb1k1nr/ppqppp1p/6pB/2p1b1P1/8/2P2P2/PP2Pn1P/RN1QKBNR b k - 4 11` | 33 | 33 | 31 |
| 17 | `1rb1k1nr/pp1ppp1p/3q2pB/2p1b1P1/8/2P2P1P/PP2Pn2/RN1QKBNR b k - 0 12` | 36 | 36 | 33 |
| 18 | `1rb1k1nr/pp1ppp1p/3q2pB/2p1b1P1/4P3/2P2P1P/PP6/RN1QKBNn b k e3 0 13` | 32 | 32 | 36 |

The engine was right; the reference file was stale. `ref_par.py` now uses a fresh unique
tempdir per run, checks every shard's exit code, checks every shard's record count equals
`positions x depths`, checks every row is numeric, and refuses to write the output file at all if
any check fails.

**Consequence for my record:** the job 2 perft comparison I had before this audit was
**invalid** — it compared the 494-position engine output against a 500-position reference file with
shifted indices. It is re-run from scratch with hardened tooling, and the job 2 report states the
re-run's numbers, not the earlier ones.

## What I take from this
- Every check now asserts the line it parses was found; a missing line is a hard failure.
- Every harness writes to a fresh path, never a reused one.
- A "0 differences" claim must come with the count of pairs actually compared next to it, so a
  vacuum cannot look like a pass.
- I had already made two of these mistakes (the `got 11` depth-vs-nodes parse, and 84 phantom
  class-property failures) before the warnings arrived; the warnings were correct and the tooling
  is better for them.
