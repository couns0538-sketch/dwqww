# searchmoves: BEYOND the already-known mechanism

Opus's file 1 says: 'a root restricted by searchmoves searches a different, mostly smaller tree:
internal iterative reduction fires at the root, and no hash entry is stored for a restricted root.'

What that list does NOT say, and what I measured (release build, startpos, S14 options,
Threads 1, Hash 16, paced driver, same process shape, only the go line differs):

| go line | score at depth 12 | nodes | bestmove |
|---|---|---|---|
| `go depth 12` | cp 30 | 56720 | e2e4 |
| `go depth 12 searchmoves e2e4` | cp 23 | 26329 | e2e4 |
| `go depth 12 searchmoves e2e4 d2d4` | cp 23 | 16770 | e2e4 |

The move played is the SAME (e2e4) and the score differs by 7 cp. The restriction does not
just search fewer nodes -- it changes the number the engine reports for the position.
Why it matters: any harness that uses searchmoves to save time (a common way to re-verify a
single move) records a score that is not the score the engine would give that move unrestricted.

Reproduce:

```
for spec in "" "searchmoves e2e4" "searchmoves e2e4 d2d4"; do
  { printf "uci\nisready\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nucinewgame\nisready\nposition startpos\nisready\ngo depth 12 %s\n" "$spec"; } > /tmp/smx.uci
  python3 forge-combo29/swarm/27/job2/paced_session.py /agent/repos/base/build-release/forge /tmp/smx.uci /tmp/smx 200 >/dev/null
  grep -E "^info depth 12 " /tmp/smx.out.txt | tail -1
done
```

Note: the paced driver is required. A whole-session write gives the fabricated a2a3 of 19-F12.

## CONTROL (added after the finding, same driver, same options)

Five fresh runs of the PLAIN `go depth 12` under the same paced driver:

```
run 1: score cp 30 nodes 56720 
run 2: score cp 30 nodes 56720 
run 3: score cp 30 nodes 56720 
run 4: score cp 30 nodes 56720 
run 5: score cp 30 nodes 56720 
```

All five: cp 30, 56720 nodes. So the cp 23 under searchmoves is not run-to-run variance;
the restriction is the cause. The same driver produced 5/5 identical results, which is also the
proof that this harness is deterministic when nothing changes.
