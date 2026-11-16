# METHOD NOTE — the quit trap in commands typed at a prompt (a gap my earlier audit left)

My `HARNESS_AUDIT.md` checked every *committed harness file* for the 19-F12 defect (sending `quit`, or closing
stdin, while a search is still running makes this build answer a fabricated `bestmove` with 0 nodes). It did not
cover **commands typed directly into a shell**, and in job 10 two of mine hit exactly that trap.

## What I did wrong, twice

While diagnosing the instrumented build I ran commands of this shape:

```bash
{ cat input.txt; sleep 5; echo quit; } | engine | grep '^bestmove'
```

On a fast position that is fine. On position 155 the search outlasted the `sleep`, so `quit` arrived mid-search and
the engine answered:

```
bestmove c6c5
```

`c6c5` is **not the engine's answer at depth 8** (it is `c6c7`, stable 3 of 3 when read correctly), and it is not
even the move any build plays at any depth I tried. I briefly concluded the instrumented build behaved differently
from the real one; it did not. Both builds give `c6c5` under the same broken input and `c6c7` under correct input.

Two separate occasions, and the first one misled me for several minutes — I chased a "third move" that was an
artefact of my own shell command.

## Why `sleep` is not a fix

`sleep 5` is a race: it is long enough for a depth-8 search on one position and not long enough for a depth-18
search on another. The defect is the shape `{ ...; echo quit; } | engine`, not the number. Every harness of mine that
does this is wrong for any search that can outrun the sleep.

## The rule, stated so it can be applied at a prompt

Never send `quit` (or close stdin) before the engine has printed `bestmove`. Either:

1. **Read to the completion token in a program** — what all my committed harnesses do:
   `bestmove_parity.py`, `adjudicate.py`, `playout155.py`, `matrix_builds.py`, `deep155.py`, `engine_perft.py`,
   `divide_sets.py`, `scan_loneking.py`. These loop until the token or raise on EOF.
2. **At a prompt, use a reader that stops at the token**, e.g.
   `printf '...' | timeout 60 engine | sed -n '/^bestmove/,$p' | head -1` — but even that leaves the engine to exit
   on EOF, which is only safe *because* the pipe is consumed by `head` after `bestmove` has been seen.
3. **Safest at a prompt**: run one search per `(printf ...; exec 0<&-)`-style invocation where the input ends with
   `quit` **after** the search completes — i.e. drive it from a script file, not a pipeline.

## The check that catches it

Any answer of the form `bestmove <move>` with **no preceding `info depth` line at the requested depth** is a
fabricated answer, not a search. `bestmove_parity.py` and `adjudicate.py` both raise in that case. A one-line guard
for ad-hoc checks:

```bash
grep -q "^info depth " out.txt && grep '^bestmove' out.txt || echo "FABRICATED — rerun properly"
```

## What this means for anyone reusing my harnesses

The committed harnesses are safe: each was written to read to a token, and the ones that parse scores abort on a
missing score rather than defaulting. The risk is in the *examples* quoted in my reports and in `job*/stamps`
commands — anything of the form `{ cat x; sleep n; echo quit; } | engine`. If you copy a command out of one of my
reports to re-derive a number, use the harness file it names rather than the inline shell form, or add the
`grep -q "^info depth "` guard above.

**Numbers affected: none that I published.** Every published number came from a harness file, and the two affected
shell checks were diagnostic only and are reported as such in `REPORT_job10_item2.md`. The `c6c5` artefact is
recorded here so nobody else chases it.
