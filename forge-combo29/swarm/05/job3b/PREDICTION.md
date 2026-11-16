# PREDICTION — seat 05 job3 REPEAT (fresh roots, seed 521) — pushed BEFORE any measuring command

The brief's cycle step (c) applied to job 3: new checkmated/stalemated root sets from `random.Random(521)`
(the first job3 set used seed 501), same three `go` commands, same ASan+UBSan build.

| # | what | predicted | killed if |
|---|------|-----------|-----------|
| 1 | every run answers exactly `bestmove 0000` | 60 of 60 | any other bestmove |
| 2 | checkmate roots score `mate 0`, stalemate roots score `cp 0` | 30/30 and 30/30 | any other score |
| 3 | nodes reported | 0 in all 60 | any non-zero node count |
| 4 | `go depth 5` stops at depth 5 | 5 info lines | more or fewer |
| 5 | `go nodes 100` and `go movetime 50` iterate past their limit to depth 64 (S-F7 reproduces on fresh positions) | 64 info lines each | stopping at 5, or a different number |
| 6 | crashes / hangs / sanitizer lines | 0 / 0 / 0 | any |
| 7 | the same seeds produce the same roots as seed 501 did (i.e. I did not silently reuse the old set) | 0 positions in common | any overlap |

#7 is the control that matters: if my "fresh" sets overlap the first ones, the repeat measures nothing new.
