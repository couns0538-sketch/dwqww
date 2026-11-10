# Concurrent attack-table initialization

Status: **UNPROVEN** for whole-engine behavior or performance. The correction is disabled by default behind `FORGE_FIX_ATTACKS_INIT_ONCE=0`.

## Confirmed defect and scope

The baseline `attacks::init()` writes a plain static `bool` before filling shared attack tables. Concurrent first calls can race on the flag, initialize the same tables simultaneously, or return while initialization is incomplete. `Board` construction calls this API. This does **not** establish a reachable race in the normal UCI startup path, which initializes the board before launching search workers.

The candidate wraps the unchanged initialization body in `std::call_once`. Other callers wait for completion. The default-off build retains the original code. No attack masks, magic-search constants, or table-generation order change.

## Reproduction

From the repository root:

```sh
for mode in 0 1; do
  g++-14 -std=c++20 -O1 -g -fsanitize=thread -pthread \
    -DFORGE_FIX_ATTACKS_INIT_ONCE=$mode -Iforge-combo29/include \
    forge-combo29/tests/attacks_init_concurrent.cpp \
    forge-combo29/src/bitboard.cpp \
    -o /workspace/shared/forge-build/attacks-init-tsan-$mode
  TSAN_OPTIONS=halt_on_error=1 timeout 60 \
    /workspace/shared/forge-build/attacks-init-tsan-$mode
  echo "mode=$mode exit=$?"
done
```

The regression releases 16 threads through a barrier for concurrent first calls and checks the a1-h1 between mask immediately after each call returns. A fresh process is needed for each first-call trial. It intentionally invokes undefined behavior on the broken baseline; its race diagnosis is from ThreadSanitizer, not from timing guarantees in the fixture.

Observed GCC 14 results:

- Switch 0: exit 66, `WARNING: ThreadSanitizer: data race`, on the static initialization flag. The report identifies concurrent reads/writes inside `forge::attacks::init()`. An earlier unrestricted TSan run also found concurrent attack-table writes; it was interrupted after capturing the findings because the racy magic generation did not complete promptly.
- Switch 1: exit 0, `PASS: concurrent initialization`, with no ThreadSanitizer diagnostics.

This targeted regression does not claim exhaustive concurrency verification or a whole-engine speed improvement. The parent audit performs combined engine checks separately.
