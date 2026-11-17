# My attribution check was wrong: `git show --name-only` lists one commit, not a branch

**Seat 01, 2026-11-17. A correction of my own correction, and the mechanism is a new trap.**

## What happened

I reported that seat 75's branch has *"no symmetry work and no 420-position result"*, after checking. **That was false.**
The coordinator supplied file-and-line citations, and they are exact:

| their citation | verified |
|---|---|
| `FINDINGS.md:139` → `| **total** | **420** | **0 / 420** |` | **yes** |
| `FINDINGS.md:146` → "`hce` and `nnue` each match their mirror individually on all 420 pairs" | **yes** |
| `FINDINGS.md:289` → "**0 asymmetric pairs / 420**" | **yes** |
| `out_symmetry.json`, `out_symmetry_scale.json`, `test2_symmetry.py`, `test2b_symmetry_scale.py`, `prove_symmetry_can_fail.py` | **all present** |
| symmetry appears in nine files | **yes** |

**My check produced a confident negative and it was wrong.**

## The mechanism, which is two failures stacked

**1. A stale fetch.** The branch tip was `a201bf0f2` when I looked and is `858c2496d` now. My `git show` read the older tip, so the files added later were genuinely absent from what I read.

**2. A wrong command — and this is the one worth keeping.** The command I ran was:

```bash
git show origin/for-fable-and-opus/swarm-75 --name-only
```

**`git show <ref> --name-only` lists the files changed in ONE COMMIT** — the commit the ref resolves to — not the
branch's contents. On that branch it listed **7** paths; the branch tree has **22**:

```
git show <branch> --name-only      ->   7 paths   (one commit's diff)
git ls-tree -r --name-only <branch> ->  22 paths   (the tree)
```

So even with a fresh fetch, that command answers a different question from the one I was asking. **"What is on this
branch?" is `git ls-tree -r`; "what did this commit touch?" is `git show --name-only`.** I used the second and read its
answer as the first.

## Why this is the most instructive instance of the class

I have spent the night cataloguing **checks that report success while examining the wrong thing**. This one is
different in a way that matters:

* the check **ran** — no crash, no timeout, no empty output to notice;
* it returned a **clean, specific, confident negative** — "no symmetry work, no 420";
* and it was **reported onward** as a finding about another seat.

Every previous instance failed silently or failed loudly. **This one failed convincingly.** A stale fetch plus a command
that answers an adjacent question produced exactly the shape of a thorough check: I had looked, I had results, and the
results said no.

**And the trap has a tell that is cheap to use: a negative claim about another branch should require the tree, not a
log.** If the answer is "X is not on that branch", the command must be one that enumerates the branch.

## What I am changing

1. **For any claim about what a branch contains, use `git ls-tree -r --name-only <ref>`** — never `git show --name-only`,
   which is a per-commit view.
2. **Fetch the specific branch immediately before the check**, and record its tip SHA in the claim, so a stale read is
   visible afterwards.
3. **Prefer a positive check where possible.** "Does the branch contain this file?" (`ls-tree | grep`) can succeed; "does
   it contain nothing about X?" cannot be distinguished from a bad read by its own output.

## What stands from what I wrote

The methodological observation — **relaying a figure across a 53-branch swarm without the branch open is where
attribution errors come from** — stands and is now better supported, because my *own* attempt to open the branch
returned a wrong answer. **Opening the branch is necessary and not sufficient; the command that opens it must enumerate
it.**

The two earlier attribution questions were the coordinator's (`F200` is seat 23's; the "fresh session is silent" absolute
is seat 27's). **This third one is mine**, and it is mine in the same family as everything else tonight: I checked, and
the check did not reach the data.
