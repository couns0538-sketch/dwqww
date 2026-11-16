# APPLY SHEET — `fullmove 0` refused while python-chess accepts it (21-F8)

One page. Everything a person applying this patch needs, without reading a report.

## The fault

A FEN whose sixth field is `0` is refused:

```
$ printf 'position fen 4k3/8/8/8/8/8/8/4K2R w K - 0 0\nisready\ngo perft 1\nquit\n' | forge
info string invalid FEN: invalid FEN fields
readyok
nodes 20            <-- 20 is START POSITION perft 1: the refused command left the old board
```

The same board with `fullmove 1` is accepted and gives `nodes 15`. python-chess treats
`fullmove 0` as a valid FEN (`Board(fen).status() == 0`) and gives 15 legal moves.

Consequence: because a refused `position fen` keeps the previous position and still answers
`readyok` (21-F2), a GUI that loads such a FEN gets moves for the wrong game with no error it
can see — not merely a refusal.

## The change — two lines of `forge-combo29/src/board.cpp`

```diff
@@ -264,7 +264,7 @@
     if (rank != 0 || file != 8 || kings[White] != 1 || kings[Black] != 1 ||
-        (side != "w" && side != "b") || halfmove < 0 || fullmove < 1) {
+        (side != "w" && side != "b") || halfmove < 0 || fullmove < 0) {
@@ -349,7 +349,8 @@
-    candidate.fullmove_ = static_cast<std::uint16_t>(std::min<long long>(fullmove, 65535));
+    candidate.fullmove_ = static_cast<std::uint16_t>(
+        std::min<long long>(std::max<long long>(fullmove, 1), 65535));
```

Read it as: accept `0`, still refuse anything negative, and store a floor of 1 so the engine
never records a fullmove number of 0 internally.

## Apply

```
cd <repo root containing forge-combo29/>
patch -p1 < fullmove0_accept.patch.txt
```

Dry run first if you like — it applies with no fuzz:

```
patch -p1 --dry-run < fullmove0_accept.patch.txt
```

## The four commands, before and after

Run each in a FRESH process (a cold baseline is a fresh process or `ucinewgame`, never
`Clear Hash`).

| command | base | patched |
|---|---|---|
| `bench 11` | 312866 | 312866 |
| `bench 13` | 862329 | 862329 |
| `bench 16` | 3024920 | 3024920 |
| `go perft 5` | 4865609 | 4865609 |

Identical, so the patch changes no node count.

## The fault, before and after

| check | base | patched | python-chess |
|---|---|---|---|
| `4k3/8/8/8/8/8/8/4K2R w K - 0 0`, perft 1 | refused, `nodes 20` (stale) | accepted, `nodes 15` | 15 legal moves |
| `r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 0`, perft 1 | refused, `nodes 20` (stale) | accepted, `nodes 30` | 30 legal moves |
| the same boards with `fullmove 1` | accepted, same numbers | accepted, same numbers | — |

## Six negative controls — all still refused by the patched build

| FEN | answer |
|---|---|
| `4k3/8/8/8/8/8/8/4K2R w K - 0 -1` (fullmove −1) | `info string invalid FEN: invalid FEN fields` |
| `4k3/8/8/8/8/8/8/4K2R w K - -1 1` (halfmove −1) | `info string invalid FEN: invalid FEN fields` |
| `8/8/8/8/8/8/8/8` (three fields) | `info string invalid FEN: FEN must contain six fields` |
| `r9/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1` (9 in a rank) | `info string invalid FEN: invalid FEN placement` |
| `4k3/8/8/8/8/8/8/4K1KR w K - 0 1` (two white kings) | `info string invalid FEN: invalid FEN fields` |
| `4k3/8/8/8/8/4P3/8/4K2R w K - e3 0 1` (ep on a wrong rank) | `info string invalid FEN: inconsistent en-passant square` |

The first row is the one that matters: my FIRST version of this patch dropped the
`fullmove < 1` test outright and accepted `fullmove -1`. That is why the final patch tests
`fullmove < 0` instead.

## Regression: 6,073 real positions

All 353 positions of set G and all 5,720 of set R2 are accepted by the patched build —
0 refusals, identical to the base build. And `go perft 2` on the first 200 of G matches
python-chess on all 200 (0 mismatches). So the patch does not make the parser stricter or
change move generation.

## Suites and files

| what | path |
|---|---|
| the patch | `forge-combo29/swarm/21/job12/fullmove0_accept.patch.txt` |
| verification script | `forge-combo29/swarm/21/job12/verify_patch.py` |
| its output | `forge-combo29/swarm/21/job12/out/summary.md` |
| honesty, base | `forge-combo29/swarm/21/job12/honesty_base.txt` |
| honesty, patched | `forge-combo29/swarm/21/job12/honesty_patched.txt` |
| full report | `forge-combo29/swarm/21/REPORT_job12.md` |

Reproduce the whole check with:

```
python3 forge-combo29/swarm/21/job12/verify_patch.py <patched-exe> <base-exe> <outdir>
```

It prints `PATCH VERIFIED` or `PATCH NOT VERIFIED` as its last line.

## Caveats

- The patch assumes the owner WANTS `fullmove 0` accepted, on the grounds that python-chess
  accepts it and FEN writers emit it. If strict refusal is preferred, do not apply it; the
  finding stands either way.
- The patched build was not run under ASan+UBSan for this change (two-line parser edit, no
  ownership change).
- It does not touch 21-F9 (the halfmove ≥ 100 root shortcut) or 21-F2 (the stale board after a
  refusal). Those are separate defects; a related fix for 21-F9 is seat 12's
  `two_doors_mate.patch.txt`, which I verified separately in `REPORT_job16.md`.
