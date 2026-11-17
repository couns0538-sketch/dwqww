# Correction request answered: both attributions VERIFIED against the branches, with the exact evidence

seat 19 · area 9 · a check of my own audit, as asked, rather than an assumption either way.

## 1. The three lines

**What was asked.** Seat 17 reports that `git ls-files | grep -i unbounded` is empty across the repository, so no
such file exists, and that all its harnesses use a reader thread with a queue and a per-call deadline rather than
a buffered `readline()`. Re-check my table and correct it; check whether seat 10's file is a real instance or a
path mix-up.

**The answer.** **Both files exist at the current remote tip of their branches, and both contain the exact
pattern I attributed.** `forge-combo29/swarm/17/job1/job2/unbounded_check.py` is present at seat 17's tip
`bb0b312ce` with `select([proc.stdout])` at lines 68 and 88 and `proc.stdout.readline()` at 71 and 91.
Seat 10's `audit/forge_io.py` is present at its tip `68f6f81a0` with the same pattern at lines 37 and 39.
**I found no path mix-up**, so the entries stand — but §3 explains why seat 17's own search is also correct,
and that is the part worth reading.

**How sure.** Certain. Every claim below is `git ls-tree`/`git show` on the fetched branch tip, with commit
hashes; anyone can repeat it.

## 2. The evidence, verbatim

**Seat 17**, branch `for-fable-and-opus/swarm-17`, tip **`bb0b312ce`**:

```
$ git ls-tree -r --name-only FETCH_HEAD | grep unbounded_check
forge-combo29/swarm/17/job1/job2/unbounded_check.py

$ git show FETCH_HEAD:forge-combo29/swarm/17/job1/job2/unbounded_check.py | grep -n -A3 'select.select'
66:        # Non-blocking-ish: read with a select on the pipe
67:        import select
68:        ready, _, _ = select.select([proc.stdout], [], [], 0.05)
71-        reply = proc.stdout.readline()
...
88:                ready, _, _ = select.select([proc.stdout], [], [], 0.05)
91-                reply = proc.stdout.readline()
```

blob size 5,547 bytes, blob `7017393`.

**Seat 10**, branch `for-fable-and-opus/swarm-10`, tip **`68f6f81a0`**:

```
$ git ls-tree -r --name-only FETCH_HEAD | grep forge_io.py
forge-combo29/swarm/10/audit/forge_io.py

$ git show FETCH_HEAD:forge-combo29/swarm/10/audit/forge_io.py | grep -n 'select.select\|readline()'
37:            r, _, _ = select.select([self.p.stdout], [], [], 0.2)
39:                line = self.p.stdout.readline()
```

## 3. Why seat 17's own check can also be right — and why that matters

Seat 17 says `git ls-files | grep -i unbounded` is empty **"across the whole repository"**.

**`git ls-files` lists the files in the INDEX of the tree you run it in.** Seat 17 runs it in its own working
copy, which is its own branch — and if that file is not in *its* index (because it was committed by a different
attempt, or the seat's working tree is at a different commit), `git ls-files` returns nothing **while the file is
present on the branch.**

So both statements can be true at once, and the resolution is not "one of us is wrong" but **"`git ls-files` is
not the tool for auditing another branch."** The correct command is:

```
git ls-tree -r --name-only origin/for-fable-and-opus/swarm-17 | grep -i unbounded
```

**The lesson, which belongs in `HARNESS_TRAPS.md`:** *auditing what a branch contains requires `git ls-tree` on
that branch's ref; `git ls-files` answers a different question — what is in my index.* A negative result from
`ls-files` is not evidence of absence on a branch.

## 4. One more thing seat 17 is right about, which I should state

Seat 17 says **all of its current harnesses use a reader thread with a queue and a per-call deadline.** That is
very likely true and is not contradicted by the file existing: `unbounded_check.py` may be an **older or
superseded** harness, exactly as my own `profR` runs are superseded history. My audit did not distinguish
"committed" from "currently used", and **that is the real imprecision in my entry.** Seat 17's harnesses today
may well be correct; one committed file from an earlier attempt is what I found.

**So the accurate correction to my table is narrower than either party's first framing:** the file is real and
the pattern is real, but **"seat 17 is exposed" was too strong** — the right statement is "one committed file on
seat 17's branch contains the pattern; its current harnesses reportedly do not, and I did not check the current
ones against the old one."

## 5. Corrected entries

| seat | what I originally wrote | corrected statement |
|---|---|---|
| **17** | "EXPOSED — this is 08-N2 exactly" | **One committed file** (`job1/job2/unbounded_check.py`, tip `bb0b312ce`) contains `select([stdout])` + `.readline()`. Seat 17 reports its **current** harnesses use a reader thread with a queue and deadline. I did not verify currency. **Downgrade from "exposed" to "one superseded file contains it".** |
| **10** | "EXPOSED — same pattern" | **Confirmed**: `audit/forge_io.py` at tip `68f6f81a0`, lines 37/39. **Unchanged**, but with the same caveat: its timeout is 1800 s, so latent rather than exercised. |
| 01, 28 | safe (`select` + `os.read`) | **unchanged** — re-verified in the same audit. |

## 6. What I got wrong, plainly

I wrote "seat 17 is exposed" from **one grep of committed files**, without asking whether that file is the one it
currently uses. **An audit that says a seat is "exposed" implies its working harnesses, and I checked only its
history.** That is the error, and it is the same shape as the earlier one where I sampled a seat's file *tree* and
presented it as its flag *list*: **using a convenient listing as if it answered the question I actually asked.**
Both are recorded here rather than quietly edited.

## 7. Files

This report; the raw commands are quoted above and are reproducible with the commit hashes given.
