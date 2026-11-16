# REPORT job16 — THIRD verification of seat 12's fifty-move / repetition fix

**What was asked.** Independently verify seat 12's `two_doors_mate.patch.txt` (branch
`for-fable-and-opus/swarm-12`, `forge-combo29/swarm/12/job1/`): apply it to a scratch copy, run
it under my ASan+UBSan build, and report both doors closed in both colours, all four pins
unchanged, and whether my sanitizer runner sees anything.

**The answer.** **FIX VERIFIED**, and the A/B is unambiguous: on the unpatched ASan build all
four door cases miss the mate (`0` nodes, `cp 0`), and on the patched build all four find it
(`mate 1`, 105 nodes). Both controls behave identically on both builds, so the difference is
the patch and not the harness. The quiet drawn root is still adjudicated at `0` nodes, so the
fix does not delete fifty-move adjudication in general. All four pins unchanged. **My sanitizer
runner saw nothing** — no AddressSanitizer, UBSan runtime-error or `__ubsan_` line in any of
the 20 case outputs.

**How sure.** High. The A/B is the strongest form available: same harness, same cases, two
binaries, opposite outcomes on exactly the four cases the patch targets.

## The two doors, measured

| case | python mate in 1 | BASE bestmove | BASE nodes | PATCHED bestmove | PATCHED nodes |
|---|---|---|---|---|---|
| W fifty-move, hm 100 | e1e8 | f2f3 **missed** | 0 | **e1e8** | 105 |
| B fifty-move, hm 100 | a8a1 | f7f6 **missed** | 0 | **a8a1** | 105 |
| W threefold repetition | e1e8 | f2f3 **missed** | 0 | **e1e8** | 105 |
| B threefold repetition | a8a1 | f7f6 **missed** | 0 | **a8a1** | 105 |

Controls (must behave the same on both builds — they do):

| case | base | patched |
|---|---|---|
| W hm 99 | e1e8, 105 nodes | e1e8, 105 nodes |
| B hm 99 | a8a1, 105 nodes | a8a1, 105 nodes |
| W two occurrences | e1e8, 105 nodes | e1e8, 105 nodes |
| B two occurrences | a8a1, 105 nodes | a8a1, 105 nodes |
| quiet drawn root hm 100 | `0` nodes, `cp 0` | `0` nodes, `cp 0` |
| quiet root hm 99 | 759 nodes, real score | 759 nodes, real score |

The last two rows matter: 30-F8 showed that the naive fix for this family deletes the root
adjudication wholesale. This patch does not — a drawn root with no mate available is still
adjudicated at `0` nodes.

## Pins (each in a FRESH process)

| command | expected | patched ASan build |
|---|---|---|
| bench 11 | 312866 | 312866 PASS |
| bench 13 | 862329 | 862329 PASS |
| bench 16 | 3024920 | 3024920 PASS |
| go perft 5 | 4865609 | 4865609 PASS |

## Sanitizer result

Build: `~/b/hmfix/forge`, ASan+UBSan, `nm` shows **35** `__asan_` symbols (the same
instrumented build I used all session). The runner scanned every case's raw output for
`AddressSanitizer`, `runtime error`, `__ubsan`, `SUMMARY: UndefinedBehavior`: **none**.
Caveat stated plainly: the patched file is `search.cpp`, and I did not run the *planted-fault*
proof against this specific binary — the planted-fault proof I have (21-F5) was against the
same ASan+UBSan configuration on the unpatched source, so it establishes the runner can see a
fault in this build configuration, not in this binary. Treat "no sanitizer lines" here as
supported by a proven runner and an instrumented binary, not as a fresh plant on this binary.

## Honest account of two wrong turns in this job

1. My first `verify_fix.py` used `subprocess` with `quit` in one pipe — the 19-F12 fault — and
   reported every case MISSED with `f2f3`. I caught it by reading the raw file (no `info` line
   at all) and moved every search onto `safe_engine`.
2. My first repetition cases were built with `position fen <FEN> moves ...`. Forge does read
   that form (case 2 of `fenmoves.py`: perft 1 = 8 after `e1d1`, matching python-chess), so the
   form was fine; my *reading* of the first table was not, and I re-ran with explicit
   threefold-vs-twice controls before claiming anything.

## New finding from this job (NOT part of seat 12's fix)

While building the repetition cases I found a separate defect that neither base nor patched
build fixes:

**21-F11 — a checkmated root is scored `score mate 0`.** `position fen
4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60` (python-chess: checkmate, 0 legal moves) answers
`info depth 1 seldepth 1 score mate 0 nodes 0` and `bestmove 0000` on BOTH the base and the
patched build. `mate 0` is not a legal UCI score for a checkmated side. The brief's known list
says `bestmove 0000` is the correct answer for a terminal root, which it is — but it says
nothing about the score, and `mate 0` is wrong: a mated side is `-mate` in 0, i.e. it should
report a loss, not a zero-distance mate.

## What I did NOT do

- Did not run 30-F8's exact consequence FEN (`6k1/5ppp/8/8/8/8/5PPP/6K1 w - - 120 1`) against
  the patch; my quiet control is an equivalent case and behaves correctly, but it is my board.
- Did not run a fresh planted-fault sanitizer proof on this specific patched binary.
- Did not test the patch's cost: it loops over every legal root move and makes each move when
  the root is adjudicated drawn, which is only on that rare path, but I did not measure it.

## What I am NOT sure about

- Whether `mate 0` has a downstream consequence (a GUI displaying "mate in 0" or a book/Elo
  tool dividing by it). I found the score, not its consequence.

## Times

see `job16/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job16
fenmoves.py  fixout  fixout_base  out  out_fenmoves  stamps.txt  verify_fix.py  fiftymove_fix.py
```
