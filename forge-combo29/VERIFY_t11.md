# VERIFY t11

Branch `grok47/t11-integrate` at `f00b8ef5f4e0adcc67dfe4ce1295a36b28a9432c`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **FIX NEEDED**.

## Rule check

Engine source is inside `include/` and `src/` and is 213 insertions, 27 deletions (under 300). The branch also adds:

- `REPORT_t1.md`, `REPORT_t3.md`, `REPORT_t6.md`, `REPORT_t8.md` in addition to `REPORT_t11.md`
- `tests_t1/`, `tests_t3/`, `tests_t6/`, `tests_t8/`

There is no `tests_t11/`. Those other reports and tests are outside `tests_t11/` and `REPORT_t11.md`. No executable, archive, script, workflow, or Python file. Modes are 100644.

## Safety

This is the t1 array widening, the t3 clock parser, the t6 node-limit score, and the t8 `NnueFile` reader together. The file read is the same shape as t8:

```
std::ifstream input(name, std::ios::binary);
```

Test writers use `std::ofstream` to `argv[1]` and to a path next to the net. No network, process start, registry, or environment access.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both `Built target forge`. `uci` advertises `option name NnueFile type string default <empty>`.

## Pins

Default options:

```
info string bench depth 11 nodes 312866 time 167 nps 1873449
info string bench depth 13 nodes 862329 time 439 nps 1964302
nodes 4865609
```

## Task tests

There is no t11 test. The bundled ones were built against this commit's sanitizer objects and against the lock.

- `tests_t1`: branch `losing_captures 68`, `bestmove d3b1`, exit 0. Lock exit 134, `SEGV` in `search.cpp:469` `MovePicker::next`.
- `tests_t3`: `clock_parse_test passed`, exit 0. The header is in this tree.
- `tests_t6` (this commit's shorter copy): branch `PASS fixed-node score and move agree`, exit 0. Lock `FAIL failures 3`, exit 1.
- `tests_t8`: branch `PASS`, exit 0, after `nnue_convert` wrote the net. Lock compile failed: `'load_file' is not a member of 'forge::nnue'`.

No ASan/UBSan report on the passing runs.

`go wtime 3000000000` on the release binary was still printing info at 0.4s (depth 11, engine time 141), same shape as t3. `go movetime -5` on this release binary did not print `bestmove` within 1.5s and had reached depth 5. The same command on t3 returned `bestmove a2a3` in about 35ms. That difference was not chased further.

## Report claims

Reproduced: the four bundled tests fail or do not build on the lock and pass here, and the three pins match. Not reproduced: a single integrated test under `tests_t11/`, because there is none. No Elo or speed claim was checked.

## What to fix

Drop `REPORT_t1.md`, `REPORT_t3.md`, `REPORT_t6.md`, `REPORT_t8.md`, `tests_t1/`, `tests_t3/`, `tests_t6/`, and `tests_t8/` from this branch, or move the tests under `tests_t11/` and keep a single `REPORT_t11.md`. The behavior of the four fixes does not need a rewrite for the tests above to pass.
