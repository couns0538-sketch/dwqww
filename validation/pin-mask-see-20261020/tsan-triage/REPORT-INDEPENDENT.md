# Independent candidate16 TSan failure triage

The original full TSan CTest attempt **FAILED**. The proximate failure is the initial Python UCI-handshake deadline in test9, `ownbook_regression`; the underlying delay is **unresolved**. No source/strength gate passes from this triage. This initial read-only triage ran no engines, reruns or builds and changed no Git state, original evidence, production, protocol or other documentation. Only this report was written. Root subsequently authorized one separately recorded diagnostic pair; that does not alter this original-failure analysis.

## Exact retained failure

Frozen source is `553caef144ae2e1b696ba35d7a0eb1a50a03fde9`. The failed JSON records engine SHA256 `0dfa0b4c81d8ba4deea4b7c835133b7ec0aa2b31e5c536a5ca8ae937e8b4319f`; the current preserved executable hashes identically. That is a post-failure identity check, not a recovered before/after execution proof: the driver raises on CTest failure before attaching its local `binary_before` map or computing final binary/source hashes to summary.json.

CTest reports tests1–8 passed and test9 `ownbook_regression` failed after16.76s. Suite output reports92.49s total; the outer driver records93.541845164s and exit8. This is not the driver's1200s outer CTest-process deadline. The test command in LastTest.log:235 is the frozen Python `tools/ownbook_regression.py`, exact TSan engine, and build-local `ownbook-regression.json` output. The actual signature is:

```text
RuntimeError: AssertionError('UCI response deadline exceeded')
```

`tsan-driver.stderr` adds only the outer `RuntimeError: ctest failed with exit 8`. There is no captured `WARNING: ThreadSanitizer`, `FATAL: ThreadSanitizer`, data-race, lock-order or deadlock report in the requested raw logs, LastTest.log or OwnBook transcript. TSan options remained `halt_on_error=1:exitcode=66`, with no disabled deadlock detector recorded. Absence of a captured sanitizer report does not turn the failed suite into a pass.

## Stage and last captured exchange

The failed OwnBook JSON has `checks: []` and this ordering:

```text
> uci
> quit
< id name Chess Engine Forge 6.4.16 candidate
< id author OpenAI
< option name Hash type spin default 32 min 1 max 2048
... normal advertised options ...
< uciok
```

There is no `> isready`, external book path, OwnBook change, position or `go` command. `ownbook_regression.py:18–20` sends `uci`, waits for `uciok`, then sends readiness. Therefore the first `Engine.until` at line19 exceeded its default15s monotonic deadline (`uci_regression.py:36–46`), before any book behavior or search assertion. The final captured line is `< uciok`.

The helper appends sent commands **before** writing/flushing stdin, and its daemon reader appends received lines to the transcript before enqueuing them (`uci_regression.py:24–34`). Cleanup sends `quit`, waits up to5s, then joins the reader up to2s and checks child exit0 (`:104–114`); it does not assert that the reader joined. The OwnBook JSON is written after cleanup (`ownbook_regression.py:49–59`). No `; close:` error is recorded, so that close path reported no failure and its child-returncode assertion passed. The transcript orders Python append events, not engine write timestamps. It cannot distinguish delayed engine startup/handling/output from reader/consumer scheduling, nor prove byte-level capture completeness. The shell-read latency separately observed in this session does not establish a cause.

## Focused counterpart and source context

The existing candidate15 TSan OwnBook run passed all five toggle checks with `error: null`; its full CTest9/9 passed and OwnBook took3.41s. The two frozen source exports have byte-identical OwnBook scripts and imported UCI helper:

- `tools/ownbook_regression.py`: `2ebd2c43ba7d05caee77a10fc823214f16e46f3a4cee2c5dd8e21550b8d2f801`.
- `tools/uci_regression.py`: `0ecfbdd3b04bf0ef4f6669ed43581d124e75ff3224926874da98c451649ee4cc`.

The frozen15→16 runtime diff changes only the version in CMakeLists.txt/src/uci.cpp and the mask implementation inside `Board::see_ge` in src/board.cpp. The UCI identification branch still emits `uciok` with `std::endl` (`src/uci.cpp:161–183`), and unchanged startup constructs Board/Searcher and loads the embedded book before reading commands (`:125–155`). No search was requested in this failed exchange. This locates the useful diagnostic boundary; it does not exonerate candidate16 or establish an environmental cause. Release/ASan/Windows passes and the older15 pass do not clear this failed16 TSan gate.

## Minimal next probe, if root authorizes it

First preserve the original build-local OwnBook JSON and LastTest.log, exact engine/core bytes and all original profile logs in an immutable failure archive. A subsequent CTest/OwnBook invocation must not overwrite those originals.

One fresh, bounded diagnostic should exercise only the frozen16 binary's `spawn → uci → uciok → quit` boundary under the same TSan options, retaining the original15s handshake deadline and a separate outer cleanup guard. Record monotonic process-create/send/flush/first-byte/parsed-uciok/quit/exit events, separate raw stdout/stderr, reader-join state, exit status and before/after executable hashes in a new directory. If the delay recurs, time-stamped child writes and parent reads plus process/thread wait-state samples are the next discriminating evidence. No book fixture, search, match, source patch, timeout widening or sanitizer suppression is justified by the current record. A diagnostic pass would mean only that the stall was not reproduced; it would not erase this original failure or establish its root cause.

## Original evidence hashes at independent read

| Original path | SHA256 |
|---|---|
| `/workspace/dwqww/validation/pin-mask-see-20261020/native/frozen-tsan-attempt1/ctest.stdout` | `a918799b20111af731a69cc7aeb60648aa592d80d1d3f19fac1928c8c9f2c521` |
| `/workspace/dwqww/validation/pin-mask-see-20261020/native/frozen-tsan-attempt1/ctest.stderr` | `18e00877dc1071c85cd4f479d451bebeef8309022e46cf8c63b0bed5151984a4` |
| `/workspace/dwqww/validation/pin-mask-see-20261020/native/frozen-tsan-attempt1/summary.json` | `85714d763146eb0d353771910de31e435ef2513105e006129e799b7dcea544c6` |
| `/workspace/dwqww/validation/pin-mask-see-20261020/native/tsan-driver.stderr` | `24c127805b50e527669a3d18b756f5920c6bf2fc1c3fadcfcf0c50b92200496c` |
| `/workspace/.cloud-setup/forge-pin-mask-tsan/Testing/Temporary/LastTest.log` | `acdf6f835768bb9443bc9fb2cb55bfd560ffced9cac31f298b95821545206e5e` |
| `/workspace/.cloud-setup/forge-pin-mask-tsan/ownbook-regression.json` | `788e1df181df10bf0870dda0a35f3f1a624dc6a9816a89b81da30bd82e66f8d5` |
| `/workspace/.cloud-setup/forge-pin-mask-source/tools/ownbook_regression.py` | `2ebd2c43ba7d05caee77a10fc823214f16e46f3a4cee2c5dd8e21550b8d2f801` |
| `/workspace/.cloud-setup/forge-pin-mask-source/tools/uci_regression.py` | `0ecfbdd3b04bf0ef4f6669ed43581d124e75ff3224926874da98c451649ee4cc` |
| `/workspace/.cloud-setup/forge-pin-see-tsan/ownbook-regression.json` | `c7c580dd6ad2e29a4da87b57747f41b5dba36db73666388c8526c40e6110f4b6` |
| `/workspace/dwqww/validation/pin-aware-see-20261020/native/frozen-tsan-attempt1/ctest.stdout` | `fb1b60ef4ba5684d269ac34d734f80f561a049af2d99f3f55ba06f58c996ca80` |
