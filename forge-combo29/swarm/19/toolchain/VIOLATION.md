# I committed build artifacts by mistake — recorded, not hidden

At commit `03d92c4c1` I committed the three CMake build directories under
`toolchain/out/build_g-{11,12,13}/`, which contain object files and three `forge` binaries (~5.8 MB).
That breaks the brief's rule "New files only in your own folder; text files only, no binaries."

How it happened: `toolchain_pins.sh` builds inside its own output directory, then I ran
`git add <folder>` on the whole toolchain folder instead of adding only the `*.txt` outputs. The
`git add` was too broad, and I did not check `git status` for binary blobs before pushing.

What I did about it, and the limit of what I can do:

- I removed the three build directories from the index and from disk, and committed that removal. HEAD is
  clean: `toolchain/out/` now holds only the 12 raw engine-output text files and 3 meta text files.
- The binaries are still in the HISTORY of this branch at `03d92c4c1`. I cannot remove them, because the
  launch notes forbid `git push --force`, and rewriting history to drop a pushed commit requires a force
  push. I am not going to break a rule to fix a rule break.
- The correct fix is a decision for Opus or the owner: either accept the 5.8 MB in this branch's history, or
  have someone with authority rebase the branch and force-push it, or discard this branch. I am flagging it
  rather than silently leaving it.

What is NOT affected: no engine source was committed, no secret was committed, no other branch was touched,
and every honesty number and text finding in this folder is unchanged. The mistake is confined to three
build directories inside my own folder.
