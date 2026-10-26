# S09 static ASan/UBSan — closed 2026-10-26

PASS on the exact private default-onehead Lprime and B sources. This is native
correctness evidence, not speed, playing strength, Windows or adoption evidence.
Release already supplies the five deep bench references and both perft5 counts;
these separate sanitizer runs deliberately use bench11 and both perft4 fixtures.
No accepted source/net or original Release controller was changed.

| Check | Lprime | B |
|---|---|---|
| Complete CTest | PASS 16/16 | PASS 17/17 |
| Known/new failure lines | 4 KNOWN /0 FAIL | 4 KNOWN /0 FAIL |
| FIRST new main beforeUCI | PASS barebench11=308972 | PASS barebench11=308972 |
| FULL bench11 | 308972 | 308972 |
| Startposperft4 | 197281 | 197281 |
| Kiwipeteperft4 | 4085603 | 4085603 |
| Typed unchangedUCI /T1/T2 legal /EOF | PASS | PASS |
| NNUE object /ELF scope /wholeELF FMA | 0 /0 /0 | 0 /0 /0 |
| Source files /artifact bindings | 84 /16 unchanged | 85 /17 unchanged |
| Owned protocol groups | 5 closed | 5 closed |
| Max sampled runtime ownedRSS bytes | 451129344 | 451043328 |

Both complete configured CTest inventories match the unchanged source and contain
all passing, unskipped JUnit cases. Exactly the four documented source-known
net-horizon diagnostics remain (WAC score661 and mirrored promotion scores642).
There are no new failure lines or sanitizer diagnostics; native runtime stderr
files are empty. This does not prove absence of every possible engine bug.

The profile is RelWithDebInfo, static core, O2/g/DNDEBUG, C++20, H256,
x86-64-v3/znver5 tuning, fno-fast-math and ffp-contract=off. Every generated
translation unit is address+undefined instrumented with frame pointers; both
original native helper drivers are manually compiled with the same recipe.
No PGO, LTO, FMA, narrowing or source changes were introduced by the sanitizer
configuration. GCC14.2 compiler SHA6b3696e4dcb85e1c949c732a02befa50e3983ecf94ce7e8e58d9d503b954b79d.

The builds use one compiler job at nice19 (LprimeCPU3/B_CPU1) with per-process
4GiB address limit and sampled aggregate ownedRSS guard. Actual max observed
build RSS:494465024/495161344 bytes. Runtime explicitly checks UNLIMITED virtual
address space and never sets an AS limit: ASan needs its large virtual shadow.
Runtime guards sampled owned-subtree physical RSS at4GiB. Canonical child env
is ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 and
UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1. No leak suppression or disabling
was used. All native sanitizer invocations used the authorized escaped tool
execution because prior evidence established sandbox LeakSanitizer restrictions.
Both FIRST and FULL source/artifact inventories are unchanged, every owned
protocol group has a reaping receipt, and owned command groups are closed.

Build elapsed731.352174085/517.193880738 seconds; FIRST18.922414506/11.377846162;
FULL83.936258989/49.424386300. These are engineering-budget observations only;
no NPS comparison is claimed. All original build/stdout/stderr/UCI/JUnit/FMA and
assembly logs remain in the six dated /tmp run directories. Build-only frozen
engine_executions=0 metadata describes the build phase; separate actual native
FIRST/FULL raw streams and receipts establish subsequent execution.

Lprime engine SHA256: `71275a8c7489b59457a9773d69e7b7716a2621a44929f1040f500bbdcebcf228`.

build result: `0a4b79a7c431e2c620accdbf30dfd44795826341fb0de6779e57cf4cb4f1760f`.

first result: `f1897e3168631404909511c16fb58162a486091a9e0d6f854aef969aefc37e47`.

full result: `1ea7ac26ed891e084cf2b6ff41c557eae313a87c50674ac787057f79ae1f1a6e`.

B engine SHA256: `406c7be69e5fd11242115b0bd0988d0b2dc4594653a56a3458c4ad9f61e477fb`.

build result: `998f0bda1464e8a808432a64bd1a97c2a2531f74ee1342f87a3f4ffb091da383`.

first result: `5015a0cae9fe9aaec1f8973943d0cd7596079fe91d8c6919dffd89d8062b89ca`.

full result: `2d59f35b92c14bbd3c3f2fa1ecd0b91693cbf6fecbfaddcadc8ef35a90599500`.

The full21MB assembly streams are retained unchanged locally and additionally
provided as exact deterministic gzip transports, each round-tripped with both
Python and GNU gzip. Transport manifest:
6e42eae7370bd87fd219dca0cb0ff1356afb399d66d5b1a3b61c819f6c496c08.
The two compressed payloads total5612952 bytes. All other original raw evidence
is761471 bytes, plus its manifests. Copying the uncompressed full43MB into the
nearly-full workspace is unnecessary; transport bindings preserve exact original
hashes/lengths and their sealed full-packet manifests. No raw input was removed.
Recipe snapshots copy only exact cache/compile-command/flags/link/CTest metadata;
ELFs, objects, archives and private source trees are retained but not duplicated.

ASAN build controller SHA523bc1954cee0b0451722e095695df42641c2922b24de988ec82011eb34e0109.
Runtime SHA162da3119d09a63e1152ca855dfe14940e91225feaa1f9bc420f59061d914b39.
Closed raw auditor SHA9ef7bfe5d8436560bd8b511eeae4d5e3c76375a6ab8cc74dbe2e846f54d66a30.
Ten meaningful profile/guard/inherited tests passed before native execution.
Original Release scripts remain de17f7ac.../f7265049... byte-identical. Original
CPU3 preregister e3a7c9af... is preserved; B_CPU1 addendum1d6485f3... records the
fresh root CPU allocation after BRelease FULL passed. No failed native ASAN
attempt occurred; no budget was increased after a failing run.

Exact executed commands (new output names are mandatory for any future run):

```sh
taskset -c 3 nice -n 19 python -B /workspace/forge-pack24-20261026/S09_ASAN_PREP_20261026/forge_sol_S09_build_ASAN_20261026.py --execute --authorization-reference root-S09-LP-Release-PASS-ASAN-build-CPU3-20261026 --role candidate --source /workspace/forge-pack24-20261026/S09_NATIVE_20261026/Lprime_default_source_once_20261026 --source-receipt /workspace/forge-pack24-20261026/S09_NATIVE_20261026/Lprime_default_source_once_20261026/S09_source_view.json --stored-heads 1 --out /tmp/forge_sol_S09_native_20261026/Lprime_ASAN_static_once_20261026 --cpu 3 --max-seconds 900
taskset -c 3 nice -n 19 python -B /workspace/forge-pack24-20261026/S09_ASAN_PREP_20261026/forge_sol_S09_qualify_ASAN_20261026.py --execute --authorization-reference root-S09-LP-Release-PASS-ASAN-native-leaks-on-20261026 --mode FIRST --build-receipt /tmp/forge_sol_S09_native_20261026/Lprime_ASAN_static_once_20261026/forge_sol_S09_build_result_20261026.json --out /tmp/forge_sol_S09_native_20261026/Lprime_ASAN_FIRST_once_20261026 --max-seconds 600
taskset -c 3 nice -n 19 python -B /workspace/forge-pack24-20261026/S09_ASAN_PREP_20261026/forge_sol_S09_qualify_ASAN_20261026.py --execute --authorization-reference root-S09-LP-Release-PASS-ASAN-native-leaks-on-20261026 --mode FULL --build-receipt /tmp/forge_sol_S09_native_20261026/Lprime_ASAN_static_once_20261026/forge_sol_S09_build_result_20261026.json --first-runtime-receipt /tmp/forge_sol_S09_native_20261026/Lprime_ASAN_FIRST_once_20261026/forge_sol_S09_runtime_result_20261026.json --out /tmp/forge_sol_S09_native_20261026/Lprime_ASAN_FULL_once_20261026 --max-seconds 600
```

```sh
taskset -c 1 nice -n 19 python -B /workspace/forge-pack24-20261026/S09_ASAN_PREP_20261026/forge_sol_S09_build_ASAN_20261026.py --execute --authorization-reference root-S09-B-Release-PASS-ASAN-build-CPU1-20261026 --role candidate --source /workspace/forge-pack24-20261026/S09_NATIVE_20261026/B_default_source_once_20261026 --source-receipt /workspace/forge-pack24-20261026/S09_NATIVE_20261026/B_default_source_once_20261026/S09_source_view.json --stored-heads 1 --out /tmp/forge_sol_S09_native_20261026/B_ASAN_static_once_20261026 --cpu 1 --max-seconds 900
taskset -c 1 nice -n 19 python -B /workspace/forge-pack24-20261026/S09_ASAN_PREP_20261026/forge_sol_S09_qualify_ASAN_20261026.py --execute --authorization-reference root-S09-B-Release-PASS-ASAN-native-leaks-on-CPU1-20261026 --mode FIRST --build-receipt /tmp/forge_sol_S09_native_20261026/B_ASAN_static_once_20261026/forge_sol_S09_build_result_20261026.json --out /tmp/forge_sol_S09_native_20261026/B_ASAN_FIRST_once_20261026 --max-seconds 600
taskset -c 1 nice -n 19 python -B /workspace/forge-pack24-20261026/S09_ASAN_PREP_20261026/forge_sol_S09_qualify_ASAN_20261026.py --execute --authorization-reference root-S09-B-Release-PASS-ASAN-native-leaks-on-CPU1-20261026 --mode FULL --build-receipt /tmp/forge_sol_S09_native_20261026/B_ASAN_static_once_20261026/forge_sol_S09_build_result_20261026.json --first-runtime-receipt /tmp/forge_sol_S09_native_20261026/B_ASAN_FIRST_once_20261026/forge_sol_S09_runtime_result_20261026.json --out /tmp/forge_sol_S09_native_20261026/B_ASAN_FULL_once_20261026 --max-seconds 600
```

Next: parent integrates these closed source/metadata/raw transports with the
separately completed Release and native parity results, verifies publication,
and continues the remaining job queue. No Git write was performed by this task.
Windows/owner-PC execution, authentic held-out training quality, playing strength
and promotion remain UNVERIFIED by these sanitizer results.
