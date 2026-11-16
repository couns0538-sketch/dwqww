# REPORT job 1 — AREA 2 (UCI COMMANDS under ASan + UBSan)

what was asked / the answer / how sure
- Asked: 2,000 random command sequences of 5 to 30 lines from the brief's grammar, every sequence ending
  `isready` + `quit`; count sequences / crashes / hangs / sanitizer lines / illegal bestmoves; commit every
  bad sequence.
- Answer: 2,000 sequences run in 2,000 fresh engine processes. 0 crashes, 0 hangs, 0 sanitizer lines,
  0 illegal bestmoves, 0 missing `readyok`/`uciok`. One behaviour worth knowing was found and is reproducible
  in isolation: a `go searchmoves` that names no legal root move answers `info string searchmoves restriction
  has no legal root moves` and then `bestmove 0000` on a board that HAS legal moves (67 of the 108
  `go searchmoves` lines in the set were of this empty form).
- How sure: high on the counts (every one is a re-count of committed raw output by `make_tables.py`);
  medium-high on "no illegal bestmove", because the legality check pairs the k-th `bestmove` with the k-th
  `go` line, and that pairing is only exact when the engine answers searches in order (it did: 5,827 `go`
  and 5,827 `bestmove` lines, 0 sequences with differing counts).

## honesty numbers (build under test)

```
exe     /agent/repos/base/forge-combo29/build-asan/forge
sha256  b109a0a5acce5b0ddad5707c04f8263fe51f48a890df4a7a2ea6ffcef8a43f99
nm -C | grep -c __asan_ = 35        __ubsan_ = 15        __tsan_ = 0
release build used for the honesty numbers: sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 = 312866   bench 13 = 862329   bench 16 = 3024920   go perft 5 = 4865609   (all PASS, see HONESTY.txt)
```

Sanitizer claim proofs (both required ones, see `sanitizer/NOTES.md` and `sanitizer/meta.txt`):
`nm` counts above 0, and a planted fault (heap over-read `sanprobe`, signed overflow `ubprobe`) on a scratch
copy of the engine at /tmp/forge-fault, run through the SAME runner: clean engine 0 sanitizer lines, fault
build 3 sanitizer lines, fault build with the probe lines removed from the input 0 lines.

## the table

Produced by `python3 make_tables.py out` from `out/results.jsonl`; pasted, not typed.

| quantity | value |
|---|---|
| sequences run | 2000 |
| engine processes started | 2000 (one fresh process per sequence) |
| crashes (non-zero exit, not a timeout) | 0 |
| hangs (no exit within 25 s -> SIGKILL) | 0 |
| sanitizer lines (ASan/UBSan) | 0 |
| `go` lines sent | 5827 |
| `bestmove` lines seen | 5827 |
| sequences where go/bestmove counts differ | 0 |
| sequences where at least one search was judged | 1779 |
| illegal bestmoves | 0 |
| `bestmove 0000` on a board WITH legal moves, go without searchmoves | 0 |
| `bestmove 0000` on a board WITH legal moves, go WITH searchmoves | 67 |
| `isready` answered late/missing (`readyok` absent) | 0 |
| `uci` answered without `uciok` | 0 |
| sequences with any flag set | 0 |
| wall time per sequence: median / p99 / max (s) | 0.044 / 1.832 / 4.691 |
| sum of all wall times (s) | 393.4 |

go forms exercised: depth 2412, nodes 1148, movetime 1038, infinite 552, ponder 351, searchmoves 108,
bare/other 218 (full list in `out/tables.md`).

### step | done-partly-not done | evidence file | result

| step | state | evidence | result |
|---|---|---|---|
| grammar generator written and committed | done | `gen_sequences.py`, `seqs.jsonl` (2,000 lines of JSON) | seed 201, 5-30 lines each, last two always isready+quit |
| runner written and committed | done | `run_sequences.py` | one fresh process per sequence, 25 s deadline, env cleared of ASAN/UBSAN/TSAN_OPTIONS |
| sanitizer build proven | done | `sanitizer/verify_san.sh`, `sanitizer/planted_proof.sh`, `sanitizer/meta.txt` | nm counts 35/15, planted fault counted 3 lines, control 0 |
| 2,000 sequences run | done | `out/results.jsonl`, `out/summary.txt` | 2000/2000, table above |
| every bad sequence committed | done (vacuously) | `out/bad/` is empty; `out/tables.md` says `count 0` | no sequence set a flag |
| the empty-`searchmoves` behaviour reproduced alone | done | `reproduce_zero.txt`, `reproduce_zero.out` | see finding S-F2 |
| prediction checked against the result | done | `prediction.txt` vs table | all seven predictions held (see below) |

### prediction, as committed before measuring (`prediction.txt`)

| # | predicted | got | verdict |
|---|---|---|---|
| 1 | crashes 0 | 0 | held |
| 2 | hangs 0 | 0 | held |
| 3 | sanitizer lines 0 | 0 | held |
| 4 | illegal bestmoves 0 | 0 | held |
| 5 | searches with no bestmove, no hang: 0 to 3 | 0 (every `go` got a `bestmove`) | held |
| 6 | quit during a search leaves the process alive: 0 | 0 (no sequence outlived its 25 s deadline) | held |
| 7 | missing readyok/uciok: 0 | 0 | held |

## findings

S-F2 — a `go searchmoves` that names no legal root move answers `bestmove 0000` on a board that has
legal moves, after the line `info string searchmoves restriction has no legal root moves`.
Show it again:

```
printf 'position startpos\ngo searchmoves depth 2\nquit\n' | /agent/repos/base/forge-combo29/build/forge
```

Raw output: `reproduce_zero.out` lines 89-91 (`info string searchmoves restriction has no legal root moves`,
`info depth 1 ... nodes 0 ... pv`, `bestmove 0000`), while line 97 shows the same board answering
`bestmove a2a3` for a plain `go depth 2`. Beyond the known list: the known list says `bestmove 0000` is the
answer on a position WITHOUT legal moves; here the position HAS 20 legal moves and the empty restriction is
what produces `0000`. A GUI that trusts `bestmove` without checking the restriction will treat this as a
resignation/loss.

Also from this job (not a NEW finding, a confirmation of the known list): `position ... moves` keeps the legal
prefix and prints `info string illegal move <token>`; an illegal `e2e4e4` is refused.

## suspicions, not proven

- The empty-`searchmoves` path prints `info depth 1 ... nodes 0 ... pv` with an EMPTY pv and score cp 0.
  I did not check whether a `searchmoves` restriction naming only ILLEGAL moves behaves the same as one naming
  no move at all (`go searchmoves e2e5 depth 2` was not in the generated set in a way I isolated). That is
  job 3's territory (searchmoves/option values) and I left it there rather than guess now.
- `setoption name NnueFile value x` prints `info string nnue: cannot open file` and the next search answers
  normally. I did not check whether the net is then DISABLED or the built-in net is kept — a search whose
  node count I could compare would settle it, and I have not run that.

## what I did NOT do

- I did not test concurrency/races: the grammar never sends `stop`/`setoption` while a search is genuinely
  running for long, so job 2's subject is untouched here.
- I did not judge the legality of a bestmove for sequences where the go/bestmove counts could differ; there
  were none, so nothing was skipped in practice, but the method is stated.
- I did not compare node counts or scores between the release and sanitizer builds.
- I did not investigate the book: `OwnBook` is true by default and several `bestmove` lines are preceded by
  `info string book move ...`, so a share of the "searched" positions were answered from the book. That does
  not affect the counts above (a legal book move is still a legal bestmove) but it does mean fewer real
  searches ran than `go` lines suggest.

## what I am NOT sure about

- Whether the 25 s deadline is generous enough on a loaded machine. The largest wall time seen was 4.7 s, so
  there is margin, but a 16-thread `setoption name Threads value 256` followed by `go infinite` is the case
  that came closest.
- Whether `bestmove 0000` after an empty `searchmoves` is deliberate (a "no move to play" signal) or an
  accident of the same code path that handles a mated root. The source path is in `search.cpp`'s root
  restriction; I read only `uci.cpp`'s parsing (`src/uci.cpp:125`) and did not trace the search root.

## times

see `stamps.txt` and the `date -u` line in each commit; `out/meta.txt` also carries `started_utc`.

## last command's output

```
$ git status --short
(clean at the time of writing this report; the report itself is the next commit)
$ ls job1
gen_sequences.py  make_tables.py  out  prediction.txt  reproduce_zero.out  reproduce_zero.txt
run_sequences.py  run.log  seqs.jsonl  seqs_smoke.jsonl  smoke  stamps.txt  uci_answer.txt
```
