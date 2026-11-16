# Branch audit — checking a report that my commit corrupted STATUS with an 84,000-line diff

A report reached me that one of my commits had corrupted STATUS.md with an ~84,000-line diff and that a repair had
been pushed as its own commit. **I have no record of making such a repair**, so before accepting or denying it I
checked the repository. The findings, with the exact commands:

## what is actually on my branch
```
$ git diff --quiet 6b98f2170a3210e71beed04bbd2553972c253ed7 HEAD -- . ':(exclude)forge-combo29/swarm/02'
YES - no change anywhere outside my folder
```
**My branch tip `11fd90700` differs from base commit `6b98f217` ONLY inside `forge-combo29/swarm/02/`.** Nothing
outside my folder is added, modified or deleted by any of my commits.

```
$ git diff --stat 6b98f217 HEAD -- forge-combo29/swarm/02 | tail -1
282 files changed, 53967 insertions(+)
```
282 files, ~54k lines — all of it my own reports, scripts and raw output.

## STATUS.md is healthy
```
$ wc -l forge-combo29/swarm/02/STATUS.md
228 forge-combo29/swarm/02/STATUS.md
```
228 lines. It has been touched by exactly ONE commit in my history
(`git log --format=%h -- forge-combo29/swarm/02/STATUS.md` returns a single hash), with a 228-line addition.

## where the "25 million lines" impression comes from
`git show --numstat 80883aba3` DOES report 13,540 files and 25,336,784 insertions. But that commit has **no parent**
in this clone:

```
$ git rev-list --parents -n 1 80883aba3
80883aba387b04b034afa4dd96d0bc9213ea7bb2          # no parent hash follows
```

This checkout is a SHALLOW clone (`--depth 1`), so the first commit I made is recorded as a ROOT commit and
`git show` prints the ENTIRE tree as "added". Every one of those files, checked individually, was already present
in base commit `6b98f217`:

```
$ git cat-file -e 6b98f217:"chess-engine-forge-5.31.0(2).zip"     -> present (pre-existing)
$ git cat-file -e 6b98f217:replay-work.js                        -> present (pre-existing)
$ git cat-file -e 6b98f217:verify.py                             -> present (pre-existing)
$ git cat-file -e 6b98f217:forge-combo29/include/forge/search.hpp -> present (pre-existing)
```

So the 25M-line figure is an artefact of the shallow clone's root commit, not content I introduced. The same
applies to any `--numstat` on that one commit; `git diff` against the real base commit is the meaningful test, and
that shows zero files outside my folder.

## what I did NOT do
- I did not make a STATUS repair commit, and there is none in the log.
- I did not `git add -A` at any point; every commit was `git add forge-combo29/swarm/02/<specific paths>`.
- I did not modify, force-push or delete any other branch. The remote tip equals my local tip:
  `git ls-remote` gives `11fd90700…` for `refs/heads/for-fable-and-opus/swarm-02`, matching HEAD.

## the lesson worth keeping
**In a shallow clone, `git show <first-commit>` is not a diff — it is the whole tree.** Anyone auditing a swarm
seat's first commit here will "find" tens of thousands of files and millions of lines that were never added. The
correct audit is `git diff <base-commit> <branch-tip> -- . ':(exclude)<seat folder>'`, which answers the real
question: did this seat change anything it should not have?
