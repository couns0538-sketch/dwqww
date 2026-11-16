# HARNESS AUDIT after seat 19's 19-F12 broadcast (done 2026-11-16T21:34:58Z)

## The trap, reproduced on my build
```
$ printf "uci\nisready\nucinewgame\nposition startpos\ngo depth 12\nquit\n" | ./forge
bestmove a2a3            <- FABRICATED, no info line
$ { printf "...go depth 12\n"; sleep 3; printf "quit\n"; } | ./forge
info depth 12 seldepth 23 score cp 30 nodes 56720 ... pv e2e4 ...
bestmove e2e4
```

Bench and perft are SYNCHRONOUS in the UCI loop (uci.cpp:590-598 runs the searches inline),
so a pipelined bench/perft is NOT affected: bench 13 still 862329, perft 5 still 4865609 with an
immediate quit. Only `go` (async worker thread) is affected.

## Every measurement I have recorded, and whether it is affected

| job | script | stdin handling | affected by 19-F12? |
|---|---|---|---|
| honesty (all builds) | honesty.sh | bench/perft synchronous | NO — verified by re-running with immediate quit |
| job1 f1 (MultiPV) | f1_multipv_nodes.sh | cat + sleep + quit (held open) | NO |
| job1 f2 (hashfull) | f2_probe.sh | cat + sleep + quit | NO |
| job1 f3 (drawn root) | f3_root_draw.sh | cat + sleep + quit | NO |
| job1 f4 (node budget) | f4_budget_bestmove.sh | cat + sleep + quit | NO — and re-verified with paced_session.py |
| job1 san/real (600 FEN mutations) | runner.py | WHOLE SESSION AT ONCE | **YES — searches aborted** |
| job1 san/stress (40 sessions) | runner.py | WHOLE SESSION AT ONCE | **YES — superseded by stress_paced** |
| job1 san/stress_paced (8) | paced_runner.py | paced, awaits bestmove | NO |
| job1 san/planted | runner.py | whole session (planted fault fires on position, not go) | NO — the plant fires in apply_position, before any go |
| job2 f1/f2/f3 (histories) | paced_session.py / awaits bestmove | line-by-line | NO |

## What this changes

- The sanitizer claim for the 6 FEN-mutation sessions is WEAKER than written: each session pipelined
  100 positions, so the next `position` aborted the running search and 4 of 6 sessions show 0 info
  lines. Fewer nodes were really executed than the report implies. 0 sanitizer lines is still true,
  but the coverage is smaller than claimed. RE-RUN paced (below), the result replaces the old one.
- S-F2 SURVIVES: re-tested with paced_session.py (awaits bestmove, never closes stdin early),
  `go nodes 20` still answers a2a3 with no info line while `go nodes 26` answers d2d4 WITH an info
  line in the same run. A harness that fabricates cannot produce that split, so S-F2 is the engine.
- S-F1/S-F3/S-F4/S-F5 are unaffected (held-open stdin, or paced).
