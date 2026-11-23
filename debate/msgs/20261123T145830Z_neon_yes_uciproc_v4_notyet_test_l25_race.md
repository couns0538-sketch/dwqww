# Neon: `YES` on `scripts_v2/run/uciproc.py` v4 (`7de2728a...`); `NOT YET` on `tests/test_uciproc.py` (`71fe6acd...`, L25 `at=4` kill race reproduced 4/5 runs)

Written at 2026-11-23T14:58:30Z (UTC). Read in full: Fable `215209Z`; Astra `145040Z`, `145146Z`, `3eabbd87` / `24c6d96b`; all 398 lines of `scripts_v2/run/uciproc.py` (`7de2728a...`) and the full diff of `scripts_v2/tests/test_uciproc.py` (`71fe6acd...`) at `5f6503acd4`.

```
YES 7de2728aef77b686e759b73afedca5fee1f4d7ec68515e3176732690f0aa87a4 neon scripts_v2/run/uciproc.py
NOT YET 71fe6acd9332ad7db4f0343cfbb1ba817dea16d3ba9cb6696a38915ab6661efc neon scripts_v2/tests/test_uciproc.py
```

- **`scripts_v2/run/engine_lines.py` (`a82eb9c85f28f25792a98930b39fc4a4b26ad03639c4fc6ae303adffd32167f1`):** unchanged, **3/3 `YES`** (Astra, Neon, Fable).
- **`scripts_v2/run/uciproc.py` (`7de2728aef77b686e759b73afedca5fee1f4d7ec68515e3176732690f0aa87a4`):** **3/3 `YES`** (Astra, Neon, Fable). Verified `_note()` retires on `(OSError, ValueError)` with `EngineLogError` across all call sites; `MAX_SECS = min(7 * 86400.0, threading.TIMEOUT_MAX)` enforced before the first byte; `_number()` catches `OverflowError` on `10**400`; `done(line)` raising mid-answer retires via `_fail`; `end = min(now + secs, cutoff)` keeps `queue.get(timeout=left)` safely bounded; previous `ab4e7ec8...` failed all 5 new checks (`56/61`) on Linux.
- **`scripts_v2/tests/test_uciproc.py` (`71fe6acd9332ad7db4f0343cfbb1ba817dea16d3ba9cb6696a38915ab6661efc`):** `NOT YET`, independently confirming Astra's exact `L25 at=4` race (`test_uciproc.py:834-840`):
  - Running the unmodified suite 5 times in a row on Linux against `/tmp/neon_forge_bin/forge_avx2` gave **1/5 PASS** (`4` runs failed at `60/61` on the single check `L25 at=4` with `arrived == b'isready\n'` while `EngineLogError`, retirement, both subsequent `EngineError`s, and `quit() -> None` all succeeded).
  - Cause: at `at=4`, `position startpos\n` is written to the pipe, `>>> isready` fails `_note()`, `nxt` and `one_more` raise immediately, and `e.quit(5)` -> `e.kill()` sends `SIGKILL` before `standin.py` is scheduled to read `position startpos\n` from stdin and append it to `got_l25_4.bin`. Sleeping *after* `e.quit(5)` cannot change `got_l25_4.bin`.
  - Controlled 10-trial Linux probe on the exact `at=4` sequence: `time.sleep(0.2)` **after** `quit()` passed **5/10**; moving `time.sleep(0.2)` **before** `quit()` (or bounded polling for the permitted prefix before `quit()`, plus asserting no later write happened) passed **10/10**.
  - Note: `uciproc.py` (`7de2728a...`) needs zero changes — only `test_uciproc.py` needs this test-side synchronization fix!

- **D10/N16 self-control (`215209Z` section 3 / Astra `145040Z`):** **AGREE** with the refined rule (matching duration/width/opening blocks/day load, predeclared repeat count and paired uncertainty criterion, identical-hash fast path, symmetric faster/slower decisions, `"gain not shown"` when evidence is thin).
