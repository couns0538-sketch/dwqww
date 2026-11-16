# REPORT job 3 — area 1 (FEN input) — seat 01

## 1. What was asked / the answer / how sure

**What was asked.** `position startpos moves` with 1,000 legal plies of a random game (the driver must never
let the game end: take back to the last position that still had moves), then the same list with one illegal
move at ply 1, 10 and 500: the answer lines and which position the engine keeps (`go perft 1`). Known: an
illegal move keeps the legal prefix (perft 1 = 29 after `e2e4 e7e5 e1e3`).

**The answer.** All four cases behave exactly as the known behaviour says. The 1,000-ply list is accepted with
no error line and the engine's `perft 1` (16) equals python-chess's legal-move count for the same final
board. With one illegal move at ply 1 / 10 / 500 the engine answers exactly `info string illegal move e1e3`
and keeps the legal prefix: perft 1 = 20 / 32 / 6, each equal to python-chess's count for the prefix.
0 crashes, 0 ASan/UBSan lines in every case. Setup for a 1,000-ply list takes 0.03 s.

**How sure.** High. The kept position is not inferred from the log: `go perft 1` prints one line per legal
move plus `nodes N`, and N is compared with python-chess's count for the prefix I constructed. Setup time is
small enough that a quadratic cost in the move list would have shown at 1,000 plies (0.03 s).

## 2. Honesty numbers

ASan+UBSan build, sha256 `37c0d256accc64b90aaccaf14e421f26607b4982adf976546d769351a0b50770`,
`nm -C | grep -c __asan_` = 35, `__ubsan_` = 15 (`asan/meta.txt`). The two sanitizer proofs are in
`job1/sanitizer_proof/`. The four engine pins PASS on this build (`honesty/asan/summary.txt`).

## 3. Table

Pasted output of `runner_moves.py` (reads `plies.txt`, which `gen_plies.py` wrote and verified):

```
case	plies_sent	answer_lines	perft1_engine	python_chess_perft1	match	setup_s	sanitizer
full_list	1000	(none)	16	16	True	0.03	0
illegal_ply_1	1001	info string illegal move e1e3	20	20	True	0.02	0
illegal_ply_10	1001	info string illegal move e1e3	32	32	True	0.02	0
illegal_ply_500	1001	info string illegal move e1e3	6	6	True	0.03	0
```

Expected FENs of the kept positions: `asan/expected_fens.txt`.
The ply list itself: `plies.txt` (1,000 plies, final FEN `4k3/2K2N2/8/6N1/8/8/8/8 w - - 646 501`).

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| 1,000-ply random legal list, game never ended | done | `gen_plies.py`, `plies.txt` | 1,000 plies; generator asserts every intermediate position is non-terminal and every ply legal |
| full list through `position startpos moves` | done | `asan/table.txt` | accepted, no info string, perft 1 = 16 = python-chess |
| illegal move at ply 1 | done | `asan/table.txt` | `info string illegal move e1e3`, perft 1 = 20 = start position |
| illegal move at ply 10 | done | `asan/table.txt` | prefix of 10 plies kept, perft 1 = 32 = python-chess |
| illegal move at ply 500 | done | `asan/table.txt` | prefix of 500 plies kept, perft 1 = 6 = python-chess |
| sanitizer lines | done | `asan/results.json`, `asan/meta.txt` | 0 in all four cases, with the two proofs |
| extra: list ending in checkmate, with a move after it | done | `asan/probe_edges.txt` | refused at the post-mate move; keeps the mate, perft 1 = 0 |
| extra: list ending in stalemate | done | `asan/probe_edges.txt` | accepted, perft 1 = 0 = python-chess |
| extra: list through a threefold repetition and on | done | `asan/probe_edges.txt` | accepted, perft 1 = 20 = python-chess (a claim is not a legality block) |

## 4. Findings

| id | area | one sentence | file with the exact command that shows it again | status |
|---|---|---|---|---|
| S-F9 | 1 | A 1,000-ply `position startpos moves` list is applied with no error line and no measurable setup cost (0.03 s on an ASan build), and the kept position's perft 1 equals python-chess's, so nothing overflows or degrades at four-digit ply counts. | `job3/asan/table.txt`; again: `python3 job3/runner_moves.py ~/builds/asan/forge job3/plies.txt /tmp/o` | NEW |
| S-F10 | 1 | An illegal move at ply 1, 10 or 500 keeps exactly the legal prefix (perft 1 = 20 / 32 / 6, each equal to python-chess) and answers exactly one line, `info string illegal move <token>`, with no other error text. | `job3/asan/table.txt` | NEW (confirms and quantifies the brief's known case at three depths) |
| S-F11 | 1 | A move list that walks *through* a threefold repetition is accepted and continues (perft 1 = 20 = python-chess): repetition is treated as a claim, not a legality wall, which is the correct UCI behaviour. | `job3/asan/probe_edges.txt` (case `after_repetition`) | NEW |
| S-F12 | 1 | A move list with a move after checkmate is refused at that move and keeps the mated position (perft 1 = 0), i.e. the same prefix rule applies to terminal positions, not just to unparsable tokens. | `job3/asan/probe_edges.txt` (case `after_checkmate`) | NEW |

## 5. Suspicions, not proven

- The engine's `position startpos moves` path parses each token with `Board::parse_uci` (uci.cpp:60). I did not
  test a promotion written WITHOUT the piece letter (`a7a8` instead of `a7a8q`); reaching a promotion inside a
  `startpos moves` list needs a long list, and I chose not to spend the run on it. It is listed here rather
  than reported as a result.
- My `after_stalemate` probe turned out to be a list that ENDS in stalemate (19 plies, no continuation is
  legal there), not a list that continues past one. The engine accepts it and reports perft 1 = 0, which is
  right, but the case does not prove anything about continuing past stalemate; only `after_checkmate` does.

## 6. What I did NOT do

- No promotion-in-move-list case (see suspicions).
- No move list longer than 1,000 plies.
- No `position fen ... moves` variant here (job 1 and job 2 cover FEN input; the move tail through a FEN root
  was covered by my S11-F1 check).
- The first version of the generator (`runner_moves.py` before I split it) hung in its take-back fallback and
  was killed by `timeout 600` with no output. I replaced it with `gen_plies.py` (committed) and
  `runner_moves.py` (committed) and did not reuse the hung version's output — there was none.

## 7. What I am NOT sure about

- P1–P7 all held. P1 (1,000-ply list accepted, perft 1 equals python-chess) held at 16 = 16. P2 (illegal at
  ply 1 keeps the start position, perft 1 = 20) held. P3 (ply 10) held at 32. P4 (ply 500) held at 6. P5
  (0 sanitizer lines) held. P6 (no crash) held. P7 (exactly one error line, before readyok) held.
- The brief's known number (perft 1 = 29 after `e2e4 e7e5 e1e3`) is a different prefix from mine; I did not
  re-run that exact line, because my three injected cases already cover plies 1/10/500 with the same rule.

## 8. Times

see `stamps.txt`.

## 9. Last command output

```
$ ls
asan  gen_plies.py  plies.txt  prediction.txt  probe_edges.py  runner_moves.py  stamps.txt
```
