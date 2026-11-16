# REPORT job 1 (v3) — AREA 2 (UCI COMMANDS under ASan + UBSan) — this supersedes REPORT_job1.md

STATUS: v1 WITHDRAWN (pipelined stdin -> fabricated bestmoves, seat 19's 19-F12; see
../HARNESS_INVALIDATION.md). v2 discarded (it waited on unbounded searches). v3 below is the result.

what was asked / answer / how sure
- Asked: 2,000 random command sequences of 5-30 lines from the brief's grammar, each ending isready+quit;
  counts of sequences / crashes / hangs / sanitizer lines / illegal bestmoves; every bad sequence committed.
- Answer: 2,000 sequences, 5,827 `go` lines, all 5,827 answered by a `bestmove`. 0 crashes, 0 hangs,
  0 sanitizer lines, 0 illegal bestmoves, 0 missing readyok, 0 missing uciok, 0 sequences with any flag.
  One reproducible behaviour stands out: a `go searchmoves` naming no legal root move answers
  `info string searchmoves restriction has no legal root moves` and then `bestmove 0000` on a board with
  20 legal moves (67 of the 108 searchmoves lines in the set).
- How sure: high on every count (all re-counted from the committed per-sequence records by
  make_tables_v3.py, which refuses to print if the record set is short or a field is missing);
  medium-high on "illegal bestmoves 0" because the legality check depends on my model of which board the
  engine holds, and that model is stated below.

honesty numbers
  release build sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
    bench 11 312866 / bench 13 862329 / bench 16 3024920 / perft 5 4865609 -> HONESTY PASS
  sanitizer build sha256 b109a0a5acce5b0ddad5707c04f8263fe51f48a890df4a7a2ea6ffcef8a43f99
    nm __asan_ 35, __ubsan_ 15, __tsan_ 0; planted fault counted 3 lines, control 0 (sanitizer/NOTES.md)

the table (python3 make_tables_v3.py out3/final 2000; pasted)

| quantity | value |
|---|---|
| sequences run | 2000 |
| engine processes started | 2000 (one fresh process per sequence) |
| `go` lines sent | 5827 |
| `bestmove` lines received | 5827 |
| searches with NO bestmove | 0 |
| crashes (signal / non-zero exit) | 0 |
| hangs (process alive after 5 s of quit) | 0 |
| sanitizer lines (ASan/UBSan) | 0 |
| illegal bestmoves | 0 |
| `bestmove 0000` on a board with legal moves, go WITHOUT searchmoves | 0 |
| `bestmove 0000` on a board with legal moves, go WITH searchmoves (empty restriction) | 67 |
| `isready` without `readyok` | 0 |
| `uci` without `uciok` | 0 |
| bestmoves with 0 preceding `info depth` lines (counted, NOT a fault) | 463 |
| bestmoves answered from the built-in book | 764 |
| searches the driver had to stop itself (unbounded/ponder/opponent-clock-only) | 1123 |
| sequences with any fault flag | 0 |
| wall per sequence: median / p99 / max (s) | 0.102 / 1.979 / 21.636 |

step | done-partly-not done | evidence | result
- grammar + 2,000 sequences (seed 201) | done | seqs.jsonl | 5,827 go lines, forms: depth 2412, nodes 1148,
  movetime 1038, infinite 552, ponder 351, searchmoves 108
- interactive driver v3 | done | run_sequences_v3.py | sends one line, reads its answer to completion,
  stops unbounded/ponder/opponent-clock-only searches itself after 30 ms
- 2,000 sequences run | done | out3/results.jsonl, out3/final/results.jsonl | table above
- 9 sequences the first pass mis-flagged re-run after the driver fix | done | out3_clock9/, seqs_clock9.jsonl |
  43 go / 43 bestmove, 0 flags
- table built from raw by a script that refuses a short set | done | make_tables_v3.py | pasted above

findings
S-F2  `go searchmoves` with no legal root move -> `bestmove 0000` on a board with legal moves.
      again: printf 'position startpos\ngo searchmoves depth 2\nquit\n' | <exe>   (reproduce_zero.out: 89-97)
S-F4  `go <clock>` naming only the OPPONENT's clock sets no limit at all, so the search never ends by itself.
      `go wtime N` with Black to move, and `go btime N` with White to move, both run until `stop`
      (reproduce: ../finding_clock/repro.txt). Source: src/uci.cpp:118-121 reads wtime into limits.time_ms
      only when side == White, btime only when side == Black; with neither set, limits.time_ms keeps its
      unset value and the time manager plans nothing. Beyond the known list (which does not mention clocks).
      This is what 9 of my own 2,000 sequences hit; a GUI that sends a partial clock gets an unbounded search.

suspicions, not proven
- 463 bestmoves had no preceding `info depth` line. `go nodes 10` legitimately produces that (budget spent
  before depth 1 completes), so I do not call these faults; whether every one of the 463 is a node-budget
  case rather than something else, I did not check individually.
- 764 of the bestmoves are book moves (`info string book move`), so fewer real searches ran than the 5,827
  go lines suggest. OwnBook defaults to true; my sequences did not disable it.

what I did NOT do
- No Threads > 1 (single-threaded throughout); no TSan (that is area 4).
- Did not judge bestmoves against the engine's internal board: I model the board in python-chess from the
  command stream (refused FEN drops the whole line, ucinewgame resets to startpos, illegal move keeps prefix).
  If the engine's real board differed from that model, "0 illegal" would be wrong in the same direction.
- Did not test `go infinite` followed by `quit` as a "does it fabricate" check beyond what job 2 covers.

what I am NOT sure about
- Whether the 20 s per-answer timeout is generous on a loaded box; the largest wall was 21.6 s for one
  sequence (many searches in it), well inside 25 s per answer, so no false timeout appeared.
- Whether `bestmove 0000` after an empty `searchmoves` is deliberate. I read the parsing (src/uci.cpp:125)
  and the message, not the search root that emits it.

times: see stamps.txt and out3/meta.txt (started_utc); per-run wall times are in the records.

last command's output
$ ls job1
argv_vs_stdin.txt  gen_sequences.py  make_tables.py  make_tables_v3.py  out  out3  out3_clock9
prediction.txt  probe_clock.py  reproduce_zero.out  reproduce_zero.txt  run.log  run3.log
run_sequences.py  run_sequences_v2.py  run_sequences_v3.py  seqs.jsonl  seqs_clock9.jsonl
seqs_smoke2.jsonl  seqs_smoke3.jsonl  smoke2  smoke3  stamps.txt  uci_answer.txt
