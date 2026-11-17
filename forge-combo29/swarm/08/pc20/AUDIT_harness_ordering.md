# Audit: does any harness of this seat send a `setoption` between `go` and `bestmove`?

08-C17 established that a mid-search `setoption` **silently stops the search**, exactly like `stop`. Every timing and
score number this seat has produced depends on no harness doing that. I had asserted the ordering from reading
(08-C17); this is the mechanical check.

## Result: 0 violations across 57 harnesses

| quantity | value |
|---|---|
| Python/shell harnesses scanned | 57 |
| files with a `setoption` between `go` and the `bestmove` wait | **0** |
| shell files needing manual review (ordering not provable statically) | 0 |

So the assertion in 08-C17 holds, and it is now checked rather than claimed.

## The audit was wrong twice before it was right — recorded, because the errors are instructive

**False positive 1.** The first run flagged `pc20/check_s03f22.py`. Investigation showed every `setoption` there is
followed by a `sync()`, and the `go` comes much later — correctly ordered. The first bug: my test counted any
`setoption` appearing between a `go` and the next `bestmove` line **anywhere in the file**, including a `setoption`
that PRECEDES the go (which is safe, because the engine consumes stdin in order).

**False positive 2.** After fixing that, the same file was still flagged. The cause was subtler: my "bestmove wait"
detector matched the string `startswith("bestmove")` inside a **reader helper function**, not an actual wait after
this `go`. So the window from the `go` at line 85 stretched past the end of its own function into the next function's
`setoption` at line 147, and reported a violation that does not exist.

**The fix** was to count only real waits — `read_until("bestmove")` or `done.wait(...)` — which is what a search
actually blocks on.

**Why this matters beyond the fix.** Both false positives were produced by a static analyser of my own writing, and
both would have been published as "a violation in my harness" had I not checked the flagged file by hand. The audit
is worth having, but **it is a heuristic and its output needs the same scepticism as prose.** That is the same shape
as the `select()` timeout bug (08-N2): a tool that reports something about code, whose report is only as good as its
model of the code.

## What the audit does NOT prove
- It does not prove the ordering for **shell pipelines** (`printf 'uci\nsetoption …\ngo …' | engine`), where ordering
  is a property of the pipeline, not of line order. No shell harness of this seat both sets an option and sends `go`
  in one pipeline, so the count is 0 rather than "reviewed and passed".
- It does not catch a harness that sends `stop`, `ponderhit`, `ucinewgame` or `quit` mid-search. Those are different
  commands with their own effects; 08-C17 is about `setoption` only.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 audit_harness_ordering.py /tmp/a.txt
