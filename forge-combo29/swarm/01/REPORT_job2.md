# REPORT job 2 — area 1 (FEN input) — seat 01

## 1. What was asked / the answer / how sure

**What was asked.** Extreme numbers in the FEN fields (halfmove 0/99/100/150/9999/-1; fullmove 0/1/10^9; ep
square on a wrong rank; two kings of one colour; pawns on rank 1 or 8): the answer lines, `go depth 4`,
sanitizer lines, and perft 2 against python-chess where python-chess accepts the FEN.

**The answer.** 34 cases, 17 refused, 17 accepted, 0 crashes, 0 ASan/UBSan lines, and perft 2 equal to
python-chess in all 17 judged cases. The refusals are all the right ones (`invalid FEN fields` for
halfmove -1 / fullmove -1 / fullmove 0 / wrong king count, `inconsistent en-passant square` for a bad ep,
`pawn on promotion rank` for a pawn on rank 1 or 8). Out of that, one **real fault**: with `halfmove >= 100`
the engine adjudicates the root as a draw and searches **zero nodes**, so it misses a mate-in-one — and
the same code path, on the same board, correctly reports `mate 0` when the position is already checkmated.
So the counter, not the chess, decides. The five-line text patch `fifty_move_mate.patch.txt` removes the
counter from that shortcut; with it applied, every mate case is found at every counter value and all four
honesty numbers are unchanged.

**How sure.** High. The fault is 0 nodes / `bestmove f2f3` vs 126 nodes / `bestmove a1a8` on **the same
board at the same depth**, differing only in the FEN's halfmove field, reproduced on the release and the
ASan+UBSan builds with the same answer, and 0 disagreements between them on the 15 cases both ran.

## 2. Honesty numbers

Release and ASan build: all four pins PASS (`HONESTY.txt`, `honesty/asan/summary.txt`). ASan+UBSan build used
here: sha256 `37c0d256accc64b90aaccaf14e421f26607b4982adf976546d769351a0b50770`,
`nm -C | grep -c __asan_` = 35, `__ubsan_` = 15 (`asan/meta.txt`). The two sanitizer proofs (own `nm` count in
the `.meta`, and a planted heap over-read counted by the same runner) are in `job1/sanitizer_proof/`.

Patched build (`~/builds/fix2`, patch applied to a clean copy, `patch -p2 --fuzz=0` applied cleanly,
`honesty/fix2/summary.txt`):
```
bench11 312866 PASS   bench13 862329 PASS   bench16 3024920 PASS   perft5 4865609 PASS
```

## 3. Table

Full table: `asan/table.txt` (pasted output of `make_table.py`, which reads `asan/results.json` and
`asan/results_fix.json`).

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| halfmove 0, 99, 100, 150, 9999, 65535, 65536, 100000 | done | `asan/results.json` | all ACCEPTED, perft 2 = 400 = python-chess |
| halfmove -1 | done | `asan/results.json` | REFUSED `invalid FEN fields` |
| fullmove 0, -1 | done | `asan/results.json` | REFUSED `invalid FEN fields` |
| fullmove 1, 10^9, 65536 | done | `asan/results.json` | ACCEPTED, perft 2 = 400 |
| ep square on a wrong rank (e3 for White, e6 for Black) | done | `asan/results.json` | REFUSED `inconsistent en-passant square` |
| ep square with no pawn behind it | done | `asan/results.json` | REFUSED `inconsistent en-passant square` |
| two kings of one colour; no king of a colour | done | `asan/results.json` | REFUSED `invalid FEN fields` |
| pawn on rank 1 / rank 8 | done | `asan/results_fix.json`, `asan/table_fix.txt` | REFUSED `pawn on promotion rank` (all four colours/ranks) |
| `go depth 4` on every accepted case | done | `asan/results.json` depth4_lines | answered; the halfmove>=100 cases answer 0 nodes |
| sanitizer lines | done | `asan/meta.txt`, `asan/results.json` | 0, with the two proofs |
| perft 2 vs python-chess | done | `asan/table.txt` | 17 of 17 judged equal |
| fifty-move vs forced mate (the fault) | done | `asan/analyse_halfmove.txt` | mate-in-1 MISSED at halfmove 100 |
| patch written, applied with no fuzz, honesty unchanged | done | `fifty_move_mate.patch.txt`, `honesty/fix2/` | all four pins PASS |

## 4. Findings

| id | area | one sentence | file with the exact command that shows it again | status |
|---|---|---|---|---|
| S-F5 | 1 | With `halfmove >= 100` in the FEN the engine treats the root as an adjudicated draw and searches 0 nodes, so a mate-in-one is missed (`bestmove f2f3`, `score cp 0`) although the identical board at halfmove 99 gives `score mate 1`, `bestmove a1a8`, 126 nodes. | `job2/asan/analyse_halfmove.txt`; again: `python3 forge-combo29/swarm/01/job2/analyse_halfmove.py ~/builds/asan/forge ~/builds/release/forge /tmp/out` | NEW |
| S-F6 | 1 | The same shortcut is NOT blind to checkmate: a board that is already mated reports `bestmove 0000` and `score mate 0` at halfmove 0, 98, 99, 100, 101 and 150, so the bug is the halfmove counter overriding a reachable mate, not a general terminal-node error. | `job2/asan/analyse_halfmove.txt` (Q1 block) | NEW |
| S-F7 | 1 | A five-line patch that drops `board.halfmove_clock() >= 100` from `root_drawn` (search.cpp ~2253) makes every mate case found at every counter value and leaves bench 11/13/16 and perft 5 identical. | `job2/fifty_move_mate.patch.txt`, `honesty/fix2/summary.txt` | NEW |
| S-F8 | 1 | `halfmove` and `fullmove` above 65535 are ACCEPTED and silently clamped to 65535 by the `uint16_t` store, so the engine's halfmove counter is not what the FEN said; the search consequence is only the `>= 100` branch above, so with that branch fixed the clamp is cosmetic. | `job2/asan/results.json` (`halfmove_65536`, `fullmove_1000000000`, `halfmove_65536_fullmove_65536`) | NEW |

Reproduce S-F5 in one command block:

```
cd forge-combo29/swarm/01/job2
for hm in 99 100; do
  printf "position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - $hm 1\nisready\ngo depth 6\n"; sleep 1; printf "quit\n";
done | ~/builds/asan/forge
```

## 5. Suspicions, not proven

- `fullmove 0` is refused although the FEN standard says the counter starts at 1 and python-chess accepts 0 by
  substituting 1. That is the engine being *stricter*, which is defensible; I list it as a difference, not a bug.
- The patch removes a shortcut that exists to save time in dead-drawn roots. I did NOT measure how much time it
  costs on positions that really are fifty-move draws with no mate (I only proved the four node-count pins are
  unchanged, which they are because the pins' positions are far from the counter). A root with halfmove >= 100
  and no mate now runs a real search where it used to return in 0 nodes; for a clock-driven search the existing
  time management bounds it, but I have not measured the worst case.

## 6. What I did NOT do — and one CORRECTION to my own earlier run

- **CORRECTION.** In `runner_extreme.py` the case named `white_pawn_rank8` used
  `4k3/4P3/8/8/8/8/8/4K3 w - - 0 1`, whose first rank field is `4k3` and whose white pawn is on e7 — **rank 7,
  not rank 8**. That case therefore tested a legal pawn on the seventh rank, and its acceptance is correct. I did
  not edit the script after the fact; `runner_fix.py` runs the four genuinely illegal pawn cases (kings placed
  off the pawn's file) in a separate raw file, and all four are REFUSED with `pawn on promotion rank`. This is
  recorded here rather than silently fixed.
- I did not test `halfmove` at 100 with a *black*-to-move mate, nor mate-in-3 or longer; my cases are mate in 1.
  python-chess's own forced-mate search agrees these positions are mate in 1 plies.
- I did not measure the speed cost of the patch (see "suspicions").
- I did not run TSan; the fault is single-threaded and deterministic.

## 7. What I am NOT sure about

- P1 (13–18 refused) held at 17. P2 (`halfmove -1`, `fullmove -1` refused) held. P3 predicted that
  `fullmove 10^9` would be silently clamped — it was accepted, and I cannot see the stored value from outside
  the engine, so "clamped to 65535" is read from the source (`std::min<long long>(fullmove, 65535)` then a
  `uint16_t` store), not observed. P4 (0 crashes, 0 sanitizer lines) held. P5 (0 perft differences) held at 0 of
  17. P6 (release and ASan agree) held at 0 disagreements over 15 cases. P7 held (no `setoption` was sent).

## 8. Times

see `stamps.txt`.

## 9. Last command output

```
$ git status --short
(see the commit that carries this report)
$ ls
analyse_halfmove.py  asan  fifty_move_mate.patch.txt  fix2  fix2_run.log  make_table.py
prediction.txt  probe_halfmove.py  runner_extreme.py  runner_fix.py  stamps.txt
```
