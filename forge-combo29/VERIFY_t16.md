# VERIFY t16

Branch `grok47/t16-option-handling` at `c3468fc9262edbd8068d2b9ac5244379e055f756`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

## Rule check

Files: `src/uci.cpp`, `tests_t16/*`, `REPORT_t16.md`. All mode 100644. `tests_t16/start h2h4.book` is 16 bytes of data, not an executable, archive, script, workflow, or Python file. Engine source: 44 insertions, 46 deletions.

## Safety

Out-of-range spins print `info string invalid value for option <name>` and still clamp. Unknown names print `info string unknown option <name>`. A bad token does not change the stored value. Book load is the existing reader. No new network, process start, registry, environment access, obfuscation, or file write. `check_lines.cpp` only reads two files.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both `Built target forge`.

## Pins

```
info string bench depth 11 nodes 312866 time 171 nps 1829625
info string bench depth 13 nodes 862329 time 506 nps 1704207
nodes 4865609
```

## Task test

Sanitizer binaries, cwd `/tmp/verify/t16` so the book path in the script resolves. `check_lines` is the branch's checker.

This commit:

- `options.in.txt` stdout matched `options.expected.txt` exactly (11517 bytes).
- `clamp.in.txt` stdout matched `clamp.expected.txt` exactly (11574 bytes), including the first line `info string invalid value for option LmrQuietBase`.
- `ownbook.in.txt` against `ownbook.spec.txt`: `ok 54 lines`, exit 0.
- `search.in.txt` against `search.spec.txt`: `ok 7 lines`, exit 0.

No ASan/UBSan report.

Lock sanitizer binary, same inputs:

- options transcript is not exact. The diff deletes the `invalid value` lines this branch prints for Hash, Threads, Move Overhead, Book Depth, Book Variety, and the tunables.
- clamp transcript is missing `info string invalid value for option LmrQuietBase`.
- ownbook spec, exit 1: missing `invalid value for option Book Depth` and `Book Variety`.
- search spec, exit 1: missing `invalid value for option Threads` and `unknown option Not During Search`.

## Report claims

Reproduced: the four transcripts pass on this commit and fail on the lock, and the pins match. No Elo or speed claim was checked.
