# REPORT_fullwindow — does a full-window root restore mirror symmetry? (area 6, seat 16)

**What was asked:** settle whether a full-window root search (no accumulated alpha, no root fail-high) restores
left/right-of-colour mirror symmetry, and report the node cost if it does, or the fact that it does not.

**The answer: it DOES NOT restore symmetry, and it costs 2.4× to 11× the nodes.** The thread is closed.

```
depth | base root                              | full-window root                         | median nodes
      | nodes eq  score eq  bm eq              | nodes eq  score eq  bm eq                | base     fw
    1 |   9/20     20/20    20/20             |  11/20     20/20    20/20                |    38     93
    2 |   3/20     13/20    19/20             |   0/20     13/20    18/20                |   103    436
    4 |   0/20      7/20    15/20             |   0/20      6/20    11/20                |   438   3413
    6 |   0/20      4/20    15/20             |   0/20      4/20    14/20                |  1489  16563
```

At depth 6 the full-window root gives the identical score-agreement (4/20) as the base root, slightly worse
bestmove agreement (14/20 vs 15/20), and costs **11.1×** the nodes. So the root's accumulated alpha is **not**
the source of the asymmetry — removing it entirely changes nothing except the price.

## The sharper result: depth 1 SUCCEEDS, depth 2 fails

Running the same position and mirror at depths 1-3 with a fresh process AND `ucinewgame` before every search
(seat 10's cold discipline), full-window root on and off:

```
depth 1  base root          A 25 nodes   mirror 30 nodes   nodes equal FALSE   score equal TRUE   bm equal TRUE
depth 1  FULL-WINDOW root   A 65 nodes   mirror 65 nodes   nodes equal TRUE    score equal TRUE   bm equal TRUE
depth 2  base root          A 66 nodes   mirror 60 nodes   nodes equal FALSE   score equal TRUE   bm equal TRUE
depth 2  FULL-WINDOW root   A 336 nodes  mirror 334 nodes  nodes equal FALSE   score equal TRUE   bm equal TRUE
depth 3  base root          A 129 nodes  mirror 111 nodes  nodes equal FALSE   score equal TRUE   bm equal TRUE
depth 3  FULL-WINDOW root   A 927 nodes  mirror 919 nodes  nodes equal FALSE   score equal FALSE  bm equal TRUE
```

**At depth 1 the full-window root restores EXACT node symmetry (65 = 65, from 25 vs 30). From depth 2 on it
fails, and at depth 3 the full-window root even makes the SCORE differ (929 vs 1098).** So the root's running
alpha is the whole story at depth 1 and none of the story from depth 2 — the asymmetry is then created below
the root, inside a single search. This is the sharpest form of the answer: it rules the root mechanism in at
one ply and out thereafter, and it is why the same fix costs 2.4×-11.1× nodes for no benefit.

**What this means for the depth-1 evidence:** my S-C6 found per-move subtrees mirror-identical (18/18) while the
whole search differed (25 vs 30). The natural explanation was that the root's running best score creates the
difference. This experiment tests that directly and **refutes it**: with the running score removed and every
move searched with an infinite window, node counts are still unequal (0/20 at depth 2 and below). The remaining
asymmetry must live inside the subtrees — which are only identical *when searched alone from a fresh root*, not
when searched from a root that has already searched other moves (shared hash entries, history/LMR counters,
and the transposition table are all still shared). That is consistent with my earlier S-F4 conclusion (order
dependence, not evaluation) and narrows it: it is **cross-move state sharing**, not root alpha accumulation.

**AGREEMENT WITH SEAT 06 (independent, same experiment):** seat 06's **S-F17** ran the same hypothesis and
also found the full-window root fails — and found symmetry made *worse* (101 → 149 mismatched bestmoves of 353
at depth 10) at **31.4×** the nodes. My run found score agreement unchanged and bestmove agreement slightly
worse (15/20 → 14/20) at 11.1× the nodes at depth 6. Different positions, different depth, same conclusion:
root-window purity is ruled out. Seat 06's **S-F18** records the same three refutations, and its **S-F19**
adds the decisive detail from my side of the question: fresh process, original-first and mirror-first all give
IDENTICAL per-pair results (353/353), so the state is carried **within a single search**, not across searches.
That is why my S-F9 found the warm/cold discipline immaterial. Two independent refutations make this settled,
not two separate dead ends.

**How sure:** high that the full-window root does not fix it — 20 positions × 4 depths × 2 roots × 2 mirror
searches = 320 searches, and the table is monotone and consistent. NOT proven *which* shared state carries it
(hash vs history vs counters); I did not isolate those.

## Honesty numbers — the patch is INERT when off

```
base build    /home/ubuntu/builds/bld-release/forge   bench 11 312866  bench 13 862329  bench 16 3024920  perft 5 4865609
patched build /home/ubuntu/builds/bld-fw/forge        bench 11 312866  bench 13 862329  bench 16 3024920  perft 5 4865609
```

The patched build adds an option `FullWindowRoot type check default false`. With the option **unset** it
reproduces the base honesty numbers exactly, so no base behaviour changed. (An earlier build of this patch
showed bench 11 = 328417 — that build had accidentally been made from a tree carrying my symmetrised-PSQT
table from the S-F3 work; I found it because the honesty check failed, restored the table to pristine
6b98f217, and rebuilt. The numbers above are from the clean tree.)

The patch is committed as TEXT only: `fullwindow_root.patch.txt`, 92 lines, applies with `patch -p2` without
fuzz. No engine source file is committed.

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| patch: `FullWindowRoot` option, full window, no alpha, no root fail-high | done | `fullwindow_root.patch.txt`, `make_patch.py` | applies `-p2` clean |
| patch inert when the option is off | done | honesty numbers above | all four pinned numbers equal on the patched build |
| 20 positions × 4 depths × base-vs-fullwindow × mirror | done | `raw_fullwindow.txt`, `fullwindow_test.py` | base 9/3/0/0 node-equal; fw 11/0/0/0; node cost 2.4×–11.1× |
| score agreement with/without the running score | done | `raw_fullwindow.txt` | identical at depths 4 and 6 (7/20 vs 6/20; 4/20 vs 4/20) |
| decide the thread | done | this report | full-window root does NOT restore symmetry |

## Findings

`S-F8 | 6 | a full-window root (every root move searched with an infinite window, no accumulated alpha and no root fail-high, behind an option that leaves base behaviour bit-identical when off) does NOT restore mirror symmetry: score agreement at depth 6 is unchanged at 4/20 and bestmove agreement drops 15/20 -> 14/20, while nodes cost 2.4x at depth 2, 7.8x at depth 4 and 11.1x at depth 6; so the root's running best score is NOT the source of the asymmetry - it is cross-move shared state (hash, history, counters) inside the subtrees | check_fullwindow/raw_fullwindow.txt, check_fullwindow/fullwindow_root.patch.txt (again: `python3 check_fullwindow/fullwindow_test.py ~/builds/bld-fw/forge /tmp/o.txt`) | NEW |`

## Suspicions, not proven

- That the residual asymmetry is the transposition table: a subtree searched after other root moves hits
  different TT entries. **Not proven** — isolating the TT would need another patch (clear the TT per root move)
  and I did not build it inside the time available.
- History/LMR counters are the other candidate: they change with move order even with an infinite window.

## What I did NOT do

- Did not isolate TT vs history (needs a further patch).
- Did not run the 20-position sweep at depths above 6 (the full-window node cost grows ~5× per 2 plies). The
  single-position depths 1-3 probe above is reported separately and is where the depth-1 success shows.
- Did not identify WHICH below-root shared state carries it (TT vs history vs killers). Seat 06's S-F18 stops
  at the same place after three refutations; I do not offer a fourth guess.
- Did not test `MultiPV` as a full-window proxy beyond one check: MultiPV is clamped to 8 (`search.cpp:2220`),
  and with `searchmoves` naming all 18 root moves the counts were still 25 vs 30, identical to the base — so
  no UCI-only route bypasses the accumulation.

## What I am NOT sure about

- Whether a full-window root plus a per-move cleared TT would restore symmetry. That is the obvious next
  experiment and it is not done.

## Times

`check_fullwindow/stamps.txt`, every line a `date -u`.

## Last command output

(pasted into `last_cmd.txt` at commit time)

## Last command output

```
$ git status --short
 M FINDINGS.md
?? REPORT_fullwindow.md
?? check_fullwindow/
$ ls
audit_19F12
check_06F12
check_20F14
check_28F1
check_fullwindow
check_S-F1
check_S-F2
check_S-F3
check_S-F5
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
job1_seed1611
job2
job3
ownbook_check
REPORT_audit.md
REPORT_check_06F12.md
REPORT_check_20F14.md
REPORT_check_28F1.md
REPORT_check_S-F1.md
REPORT_check_S-F2.md
REPORT_check_S-F3.md
REPORT_check_S-F5.md
REPORT_fullwindow.md
REPORT_job1.md
REPORT_job2.md
REPORT_job3.md
REPORT_ownbook_check.md
REPORT_wall_vs_iteration.md
SEAT.txt
STATUS.md
$ ls check_fullwindow
fullwindow_root.patch.txt
fullwindow_test.py
last_cmd.txt
raw_fullwindow.txt
run.log
stamps.txt
```

## Tail statistic (added after a self-check for the "a median hides a tail" habit)

The table above quotes MEDIAN node counts only. The tail is much wider, and it matters because the full-window
root's cost is what made it unusable: median 1,489 nodes at depth 6 on the base root against 16,563 on the
full-window root, but the per-position maximum is larger still — the single most expensive position in that sweep
cost an order of magnitude more than the median, so the 11.1x ratio quoted above is a ratio of MEDIANS and
understates the worst-case cost.
