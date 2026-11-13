# Forge history index

This branch is a reading index of `couns0538-sketch/dwqww`. It records what is on the other branches, which file versions are identical, and what the written experiments actually claim. It does not change engine source, lock branches, or `main`.

The index sits on `cursor/forge-history-index-20261113-712a`, cut from `fable/standalone-h512-20261111` at `efb2ff960037087299332bc6a44baea69441a17a`. Later commits on this branch add notes only.

## How to read it

Start with `HANDOFF.md` if you are working on search, engine correctness, or NNUE. Use `COVERAGE.md` before trusting any sentence that sounds like a complete survey. `branches/HEADS.tsv` is the frozen list of all 416 remote branch tips.

Evidence is cited as `branch@full-commit:path`. A blob id (`git` object hash) means the file bytes. The same blob can sit on many branches; it was read once.

## What a claim is

Elo, nodes-per-second, and loss figures in this index are copied from repository reports. They were not replayed. A report that calls its own match a screen, and not a gate or a lock, is recorded that way. Where two reports disagree, both numbers are kept.

## What was not done

Repository scripts and binaries were not executed. Archives, zip parts, DLLs, and multi-megabyte logs were catalogued by blob id and not opened. Nets, executables, and PGNs that the reports place under local `_work` directories are not in git.

## Sibling agents

The NNUE, correctness, and search branches now exist. What was on them when this index read them is in `findings/SIBLINGS.md`. This index does not write to their branches. A later `git ls-remote` can move those tips; `branches/HEAD_MOVEMENT.tsv` is the place to append a new row.
