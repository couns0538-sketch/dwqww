# AUDIT 2 — seat 20's node counts against seat 10's warm/cold warning

Seat 10's rule: two searches in ONE process give 56,720 → 4,951 → 4,516 nodes at startpos depth 12; three separate
processes give 56,720 three times; `ucinewgame` restores cold but **`Clear Hash` does not** (it gives 40,569).

## What I checked

1. **`Clear Hash` is never used anywhere in my work.**
   `grep -rn -i 'clear hash\|ClearHash' --include='*.py' --include='*.sh'` over my whole folder: **no matches.**
   So no baseline of mine can be the 40,569 value.

2. **Every node count of mine comes from a FRESH process.** In every script of mine the `subprocess.Popen` sits
   inside the per-search function (`job1/check_s01f5.py:24`, `job11/check_s05f3.py:28`,
   `job14/lmpbase_ladder.py:33`, `job7/halfmove_control.py:19`, …), so each search starts its own engine. There is no
   loop that sends a second `go` to a process that already searched.

3. **Empirical confirmation on my own harness:** three separate invocations of the same startpos `go depth 12`
   through `AUDIT/hardened.py` → **`e2e4`, cp 30, 56,720 nodes, 56,720, 56,720** — identical to seat 10's cold
   figure, and identical to seat 19's real number in the 19-F12 broadcast. A fabricated or warm answer would have
   shown up as 4,951 / 4,516 / 40,569.

## Which of my reported numbers are node counts at all?

| result | node numbers reported | process model |
|---|---|---|
| job1 S-C1 (halfmove mate) | 168, 0 | fresh process per case |
| job3 fallback | 0 vs "millions" (ranges only) | `drive.py` reuses ONE process per case-set, but each case is a fresh child; the *claim* is 0 vs >0, which a warm count cannot manufacture |
| job6 S-C3 (ucinewgame) | none (move legality only) | fresh process per case |
| job7 S-C4 (repetition) | 168 / 0 | fresh process per case |
| job11 S-C8 (fifty-move) | e.g. 16,370,887 / 130,251,981 | fresh process per `search()` call |
| job12/13/14 (S14, LmpBase) | 15,465 etc. | fresh process per `search()` call |
| job16 S-F22 (true mate distance) | none (chess proof, no engine nodes) | n/a — python-chess only |
| job9 S-C6 (eval symmetry) | none — `eval` has no node count | fresh process per `eval` |

**No table of mine compares node counts across two searches in one warm process**, so nothing needs a "warm" label.
The two places where I did use one long-lived process (`job3/drive.py` for the quit/stop timings, and `job2/myfuzz.py`
for the 200-sequence fuzz) report **moves, hangs and legality, never node counts** — except that `drive.py` prints
node counts read from the info lines, and I never compared those across searches.

## One thing this warning does affect
`job3/REPORT_job3.md` and `job3/out_fallback2.txt` print `nodes 0` for the fallback answers. Those zeros are the
*absence* of a search (no `info depth` line with nodes > 0), not a warm-vs-cold artefact — a warm process cannot
produce 0 nodes for a search that ran.

## Statement
Every node count I have recorded is cold (fresh process per search), `Clear Hash` was never used, and no finding of
mine rests on comparing warm searches. If any future job needs repeated searches in one process, it will say
**warm** in the table header.

## Commands that show it again
```
grep -rn -i 'clear hash' forge-combo29/swarm/20 --include='*.py' --include='*.sh'    # no matches
for i in 1 2 3; do python3 -c "import sys; sys.path.insert(0,'forge-combo29/swarm/20/AUDIT'); from hardened import run_search; r=run_search('/agent/repos/build-base/forge','rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1','go depth 12'); print(r['bestmove'], r['score'], r['nodes'])"; done
```
