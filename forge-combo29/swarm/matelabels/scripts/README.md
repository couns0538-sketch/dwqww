# scripts — mate-label corpus measurement

Run order is not optional; each step depends on the one before it.

| # | script | what it does |
|---|---|---|
| 1 | `mate_oracle.cpp` | The oracle. Independent mailbox board, own move generator, own negamax mate search. Shares **no code with forge**. |
| 2 | `perft_check.py` | Validates the oracle's move generator against published perft values **and** python-chess. Nothing downstream is trustworthy until this prints `ALL PERFT MATCH`. |
| 3 | `pysolve_independent.py` | A second, slower oracle on python-chess. Used to establish fixture distances so the C++ oracle is never checked against a recalled answer. |
| 4 | `oracle_selftest.py` | Known-answer suite (expectations computed by step 3) **plus** a planted-wrong oracle that must fail. |
| 5 | `mate_oracle_planted_wrong.cpp` | The planted fault: returns the requested depth as "exact" whenever any mate exists. Built by `oracle_selftest.py`'s sibling recipe; the fault is chosen because it would fake a clean result. |
| 6 | `harvest_labels.py` | Samples 300 mate-labelled positions from the repo's own search corpus at a fixed recorded configuration. |
| 7 | `add_seldepth.py` | Re-runs the engine on every harvested FEN to record `seldepth`, and doubles as a determinism check. |
| 8 | `verify_two_halves.py` | The two-halves verifier (S4). Half (A) pinned to the engine's move, half (B) the cheaper "no shorter mate" search. |
| 9 | `run_verify_parallel.py` | Runs step 8 over the corpus, 4 workers, one fresh process per query, global deadline. |
| 10 | `e2e_label_test.py` | End-to-end test of the **verifier**: plants honest, overstated, and understated labels and requires correct classification in both directions. |
| 11 | `analyze.py` | Produces the reported rates, every one with its denominator, and quotes `seldepth` beside every wrong label. |
| — | `paths.py` | Path handling. Every script reads and writes through it, so no script hard-codes a world-writable directory and no caller-supplied path is opened without being confined to the work directory. |

## Where files go

Nothing writes to a fixed absolute path. The work directory is, in order of
precedence:

1. `$MATELABELS_WORK`, if set;
2. otherwise `tempfile.mkdtemp(prefix="matelabels-")` — a private `0700`
   directory with a random name.

`paths.checked_input()` / `paths.checked_output()` resolve any path given on the
command line and refuse it unless it lies inside the work directory. The guard is
tested: `/etc/passwd`, `../../etc/shadow`, a `..`-laden variant, and
`../escape` are all refused, while a legitimate name is accepted.

Inputs the pipeline needs from the repo are overridable by environment variable:
`$FORGE_ENGINE` (the engine binary) and `$FORGE_CORPUS` (the sampling frame);
both default to the paths inside `forge-combo29/`.

## Build

```bash
g++ -O2 -std=c++20 -o oracle mate_oracle.cpp
g++ -O2 -std=c++20 -o oracle_broken mate_oracle_planted_wrong.cpp
```

The engine under test is built separately, from the audit base, with the brief's recipe:

```bash
cmake -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 ..
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 make -j4
```

## Why the oracle is not just "python-chess"

`python-chess` is used for **fixture validity and as a second opinion**, never as
the primary oracle, for two reasons recorded in the brief:

* its `Board.fen()` silently drops the ep square when no legal ep capture
  exists, so it is not a neutral round-trip;
* its repetition logic can be stricter than the engine's.

The C++ oracle is validated against published perft (which pins castling, ep,
promotion and pin handling all at once) *and* cross-checked against
python-chess perft. Both must agree before any mate answer is used.
