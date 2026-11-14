# VERIFY t7

Branch `grok47/t7-nnue-file` at `b56c6328a43fee23eaa7d9b9435ff5b029f343fc`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**. Better engine change than t8.

## Rule check

Files under `include/forge/nnue.hpp`, `src/nnue.cpp`, `src/uci.cpp`, `tests_t7/`, and `REPORT_t7.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 140 insertions, 11 deletions.

## Safety

The new read is the UCI option the task adds. `load_file` opens only the path it is given:

```
std::ifstream in(path, std::ios::binary);
```

A bad file returns before `active_weights()` is swapped. The test writer is `std::ofstream out(argv[1], std::ios::binary)` plus fixed paths `/tmp/forge-t7-b2.bin` and `/tmp/forge-t7-bad-magic.bin`. No network, process start, registry, environment access, or obfuscation.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both `Built target forge`.

## Pins

Option left at `<empty>`:

```
info string bench depth 11 nodes 312866 time 164 nps 1907719
info string bench depth 13 nodes 862329 time 439 nps 1964302
nodes 4865609
```

Release binary after `setoption name NnueFile value` of the converted lock net:

```
info string NnueFile loaded /tmp/verify/work/t7.net
info string bench depth 11 nodes 312866 time 161 nps 1943267
info string bench depth 13 nodes 862329 time 430 nps 2005416
nodes 4865609
```

The sanitizer binary printed the same three node counts. A missing path on the sanitizer binary printed `info string ERROR NnueFile: cannot open`. The lock binary has no `NnueFile` line in its `uci` output and printed no info line for that setoption.

## Task test

`forgenet_convert` wrote the net. `nnue_file_test` linked to this commit's sanitizer objects, exit 0, no sanitizer report. It printed `ok converted net matches compiled eval`, `ok changed b2 changes eval`, `ok bad magic kept current net (wrong magic)`, and `ok use_compiled restores eval`.

The same test against the lock include tree failed to compile: `'load_file' is not a member of 'forge::nnue'`.

## Report claims

Reproduced: default pins, converted-net pins, rejected magic/size/open, restore, and the lock test not compiling. Not re-run: the report's changed-net bench of 322107, which is a different file than the converted lock net. No Elo or speed claim was checked.

## Pair

t7 is the better of t7 and t8. Both load a FORGENET file and keep the lock pins for the default option and for the converted lock net. On success, t7 calls `searcher.clear()`. t8 calls `searcher.clear_hash()` only. t7's own comment says `clear_hash()` leaves correction histories that `corrected_eval()` still applies. t8's test checks more rejection strings; that does not make the smaller clear the better engine change.
