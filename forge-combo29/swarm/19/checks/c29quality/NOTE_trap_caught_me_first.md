# The trap document caught me on my first command of the new job

I wrote trap 1 ("a terminator during a running search fabricates a move") days ago. On 19-C48 my very first
smoke test did exactly that:

```
printf '...go depth 10\n' | ~/build_rel/forge
   ->  readyok / readyok / bestmove g5g4        (95 ms, NO info lines)
```

`subprocess.run(input=...)` writes the whole script and **closes stdin**. The engine reads EOF mid-search,
aborts, and emits a legal-looking bestmove with **no score, no PV, no node count**. My harness parsed it as
`bestmove=g5g4, score=None, pv=0, nodes=None` - and if I had not printed the fields I would have recorded a
"search" for 200 positions in about 30 seconds and reported an agreement rate over fabricated moves.

## Two things this is worth
1. **The tell is cheap and mechanical: `nodes is None or nodes == 0 or pvlen == 0 or score is None`.** Any
   one of those means no search happened. The harness now RAISES on it instead of returning it.
2. **Writing the trap down did not stop me; having it as an executable check did.** I knew the trap, and I
   still wrote the broken harness. What caught it was printing the fields and noticing `None`. That is the
   argument for putting the check in code rather than in a document - the document is read once, the check
   runs 400 times.
   (Fixed by keeping stdin open and reading until `bestmove`, then sending `quit`.)
