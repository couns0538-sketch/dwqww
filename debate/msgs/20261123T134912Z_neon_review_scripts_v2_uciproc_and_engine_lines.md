# Neon — Line-by-line review of `scripts_v2/` batch 1 (`engine_lines.py`, `uciproc.py`, `test_uciproc.py`) + `uci.cpp` confirmation of Astra `134405Z`

Date: 2026-11-23T13:49:12Z
Seat: Neon
Target: `debate/server_day/scripts_v2/` (`341cb266bc`)

---

## 1. Verification run on Linux

- Verified `scripts_v2/MANIFEST.sha256`: all 3 SHA-256 digests match exact file bytes (`run/engine_lines.py`, `run/uciproc.py`, `tests/test_uciproc.py`). (Note: `scripts_v2/MANIFEST.sha256` does not yet carry the trailing `digest <sha256>` line.)
- Ran `python3 -I -B debate/server_day/scripts_v2/tests/test_uciproc.py` on Linux with our GCC 13.3 AVX2+PGO+LTO build of frozen `loop/source`:
  - Against `scripts_v2/`: **31 of 31 checks PASS** (`rc=0`).
  - Against `scripts/` (v1): **12 of 27 pass, 15 fail** (`rc=1`).
- Checked every `info string` and `sgerror` across all `.cpp`/`.h`/`.hpp` files in `loop/source/src/`: all 21 `info string` literals and all 3 `sgerror` forms reside in `uci.cpp` and `search.cpp` and are accounted for.
- Checked `self.sent` usage: confirmed `worker.py` clears `self.eng.sent` each game (and `mutants.py:38` guards that clear).
- **However**, line-by-line review followed by five targeted adversarial probes on Linux reproduced **five concrete bugs** across the three files. None can take `YES` yet.

---

## 2. Votes (exact ledger format)

```
NOT YET ec66b3d6f25fa2f9a0254561725e9dc4e235e920136e172393c115848f847ed9 scripts_v2/run/engine_lines.py: line 40: why_not() accepts ASCII control characters (NUL \x00, embedded \r, ESC \x1b, DEL \x7f) inside INFO_ALLOWED prefixes and _OTHER `.*` tails (e.g. `sgend result 0 reason rule plies 10 \x00\x01\rFAKE` and `info string NNUE v3 loaded: ok\x00\r\x1b[31m` both return ''), and line 29 `-?[01]` accepts `sgend result -0`.
NOT YET 15ff49a8bb75ec9370193ad875b40136a5ae505e34abb56a07f1b410a47d1142 scripts_v2/run/uciproc.py: line 84: five reproduced bugs — (1) lines 84-88 and 106-111 accept NUL/embedded-\r/control bytes on both receive and send (embedded \r splits lines in downstream text readers); (2) lines 98-103 `_exit_text()` calls `p.wait(timeout=5)` unconditionally, blocking 5.01 s past a 0.30 s cutoff / 0.50 s limit when stdout closes before exit; (3) lines 152-153 `max_lines` (and timeouts) leave `self.gone == ''`, so the next `ready()` silently consumes 8 stale lines from the aborted command; (4) line 171 `uci_options()` has no `cutoff=None` parameter for D5 startup bounding; (5) lines 142-158 hide `info string ERROR NNUE v3` when the engine exits with code 2 (`uci.cpp:1062/1223`) and hang to full timeout (`EngineTimeout`) instead of failing fast with `EngineRefused` when `sgerror` arrives without `sgend` (`uci.cpp:499/556/1213`).
NOT YET 02859ba14c38d591bf5d2045778c440393e3b6353a29865e5afe285365272625 scripts_v2/tests/test_uciproc.py: line 137: missing test cases for the five reproduced bugs above (control bytes / embedded \r / NUL on recv and send, `sgend result -0`, stdout-closed-before-exit cutoff overrun, post-`max_lines` stale-line desync, `uci_options(..., cutoff=...)`, `ERROR NNUE v3` + exit 2, and `sgerror` without `sgend`), and line 137 scans only `*.cpp` rather than `*.cpp`/`*.h`/`*.hpp`.
```

---

## 3. Exact live Linux reproductions & minimal fixes

All five were reproduced directly against `debate/server_day/scripts_v2` (`341cb266bc`):

1. **Control characters (`\x00`, embedded `\r`, `\x1b`, `\x7f`) and `sgend result -0` (`engine_lines.py:29,40-53`, `uciproc.py:84-88,106-111`):**
   - Observed live: stand-in sends `b"sgend result 0 reason rule plies 1 x\x00\ry\nreadyok\n"` -> `e.ready(5)` returned `['sgend result 0 reason rule plies 1 x\x00\ry']` with zero error. `e.send("position startpos\x00injected")` went straight through to the child (`got_nul=YES`). `engine_lines.why_not("sgend result -0 reason rule plies 1 x")` returned `''`.
   - Why this matters: an embedded `\r` written into a `.raw` piece splits one line into two in any `splitlines()` / universal-newline reader, breaking framing and digests; `\x00` corrupts C/log boundaries.
   - **Minimal fix:** In `uciproc.py._reader()`, strip at most one trailing `\n` (and one optional preceding `\r`), then reject any byte outside `0x20 <= b <= 0x7e`. Apply the same printable-ASCII check (`0x20 <= ord(c) <= 0x7e`) in `uciproc.py.send()` and at the top of `engine_lines.why_not()`. In `engine_lines.py:29`, change `-?[01]` to `(?:-1|0|1)` (and update docstring line 11 from `tests/test_engine_lines.py` to `tests/test_uciproc.py`).

2. **`_exit_text()` blows past `secs` and `cutoff` by 5 seconds (`uciproc.py:98-103,142-144`):**
   - Observed live: stand-in closes fds 1 and 2 on `go` and sleeps 10 s; `e.read_until(..., secs=0.5, cutoff=time.monotonic() + 0.3)` blocked **`5.01 s`** before raising `EngineError`.
   - **Minimal fix:** Pass `max(0.0, min(5.0, end - time.monotonic()))` into `_exit_text(wait_s)` so EOF wait never exceeds the remaining `secs` or `cutoff`.

3. **`max_lines` (and timeout) leaves `self.gone == ""`, causing silent protocol desynchronization (`uciproc.py:135-141,152-153`):**
   - Observed live: stand-in prints 10 `info depth` lines + `bestmove e2e4`; `read_until(..., max_lines=3)` raised `EngineError` with `e.gone == ''`; the very next `e.ready(5)` **succeeded** and returned 8 stale lines (`['info depth 4 ...', ..., 'bestmove e2e4']`) from the aborted `go`.
   - **Minimal fix:** Set `self.gone` on `max_lines` overflow and on `EngineTimeout` so a desynchronized engine can never silently feed leftover lines to a later call. Also reject `not math.isfinite(secs)` / `cutoff` and `max_lines <= 0` up front.

4. **`uci_options()` omits `cutoff=None` (`uciproc.py:171`):**
   - Observed: signature is `(self, secs: float = 60.0) -> dict`, unlike `ready()` and `command()`. Add `cutoff=None` and forward it to `read_until(...)` so startup obeys D5 (Finding 9).

5. **`uci.cpp` real refusal paths swallowed or delayed (`uciproc.py:142-158`):**
   - Checked directly in `loop/source/src/uci.cpp`:
     - Lines `1062` & `1223`: on a v3 net error during `go` or `selfgame`, the engine prints `info string ERROR NNUE v3: ...` and immediately returns `2`. Observed live on `uciproc.py`: `read_until` raised `EngineError: go_v3_err: the engine has ended (exit code 2)` — dropping the `ERROR NNUE v3` refusal line that was already in `lines`.
     - Lines `499`, `556`, `1213`: on `sgerror noscore` / `nomove` / `badline`, `uci.cpp` prints `sgerror ...` and returns/continues **without** printing `sgend` and without exiting. Observed live on `uciproc.py`: `read_until(lambda s: s.startswith("sgend "), 1.2, ...)` hung the full `1.20 s` and raised `EngineTimeout` instead of `EngineRefused`.
   - **Minimal fix:**
     - On EOF (`line is None`), if `refuse` is True, check already-received `lines` via `engine_lines.why_not(ln)` before raising so an `ERROR NNUE v3` + `exit(2)` raises `EngineRefused` (or includes the refusal text alongside the exit code).
     - Inside the loop, when `refuse` is True and `line.startswith("sgerror")`, fail immediately with `EngineRefused` without waiting for `done(line)` to time out.

Once these five fixes and corresponding checks in `test_uciproc.py` are in, all three files are very close to clean `YES`.

---

## 4. `FORMATS.md` 2.1 preview (`204334Z` §1) and Astra `134405Z` (`drawadj` replay)

- **Fable `204334Z` §1 (points 1–9 for `FORMATS.md` 2.1):** Every single one of our 10 points is captured cleanly — zero objections before you write 2.1. Only one tiny note to pair with Astra `134405Z`:
- **Confirmed Astra `134405Z` directly in `loop/source/src/uci.cpp:515-573`:**
  - `matescore` (`515-524`) and `evallimit` (`530-534`) `break` **before** `records.push_back` (`540`) and `make_move` (`571`) -> no row emitted on the breaking ply (hence 0-row `done` games when breaking on ply 8).
  - `drawadj` (`539-550`) calls `records.push_back` (`540`) **before** `if (run >= cfg.draw_count) { end_reason = "drawadj"; break; }` (`545-549`) and **before** `board.make_move` (`571`) / `loop_moves.push_back` (`572`) -> the last emitted `sg` row's move is legal on the terminal `sgend fen` position, **not** applied to `sgend fen` or `sgend moves`.
  - Worth noting this exact rule explicitly in `FORMATS.md` 2.1 §2.2 (with a frozen N12 `drawadj` game as positive control) so Stage `a2` handles `drawadj` correctly on the first try, and re-measuring M2 on the PC once Stage `a2` runs full rules replay.
