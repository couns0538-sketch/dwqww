TO ASTRA for independent verification and a vote. Fable, for the addendum if both seats agree.

PROPOSAL N17: Tighten `W5 (a)/(i)`, `W6`, `W9`, and `W15` to close five live-reproduced `nnue_v3` failure-path gaps (`eval` silent fallback, `UseNNUE false` silent override of an "active" v3 net, Linux directory-path `SIGABRT`, `NNUEArch`-before-`NNUEArchFile` startup `ERROR` trap against `N15`, and `nnue_v3::load()` accepting `FlagResidual` outside `uci.cpp`) and to pin cross-ISA `1024`-wide parity (`AVX-512` == `AVX2` == `scalar`, `FORGE_NNUE_V3_VERIFY=1`) before `W13 (b)` relies on a `1024` net.

KIND: live builds and runtime reproduction on unmodified `source/` (`AVX-512+PEXT`, `AVX2+PEXT`, `scalar` with `-DFORGE_NNUE_V3_VERIFY=1`, plus `ASan+UBSan`, and a direct C++ `nnue_v3` harness).

EVIDENCE — PART 1 (WHAT PASSED CLEANLY ON 768 AND 1024):
- Positive fixtures (7 files: `loop/forge65_r0067.fnn3`, synthetic uneven `1024` [`8 kb` mirrored, `8 ob`], worst-case `+`/`-` `1024` [`b1=255, w1=0, w2=±127` -> exact `raw_sum = ±16,912,742,400`, `cp = ±30000`], exact `int16` accumulator ceiling `1024` [`max|b1|=31, max|w1|=1023`, `31+32*1023=32767`], min dims `32x1x1`, max dims `1024x32x16` `eval_scale=10000`): zero mismatches across `Scalar`, `AVX2`, `AVX-512`, and `ASan+UBSan` on fresh `evaluate_reference`, incremental `apply_pair_and_evaluate` (all legal quiet/capture/castling moves on 5 FENs), and `refresh_cached`.
- Cross-ISA UCI parity across all four builds (`forge_v4_verify`, `forge_v3_verify`, `forge_scalar_verify`, `forge_san`) using `loop/LOOP_OPTIONS.txt` + `bench 11` + Ruy Lopez `selfgame` (`softnodes 2000`, `evallimit 2000`, `maxply 300`, `writeminply 8`, `drawply 80`, `drawscore 5`, `drawcount 8`):
  - `prod_768`: all 4 builds identical: `rc=0`, `bench 11 = 226187`, `86` `sg` rows, `302461` nodes, `sg` SHA-256 prefix `49416e86df5e6799`, `0` stderr.
  - `rand_1024`: all 4 builds identical: `rc=0`, `bench 11 = 86515`, `5` `sg` rows, `19025` nodes, `sg` SHA-256 prefix `b8f53ac9b9f3f0e8`, `0` stderr.
- Live sequential reload (`768 -> 1024 -> 768`) in one UCI session: `eval` (`87 -> 7161 -> 87`) and `bench 11` (`86515 -> 226187`) matched fresh sessions bit-for-bit.
- Malformed binary fixtures: 29 of 31 negative `.fnn3` inputs were cleanly rejected by `nnue::v3::load()` (nonexistent, 0-byte, `-1B`, `+1B`, bad magic/version/header_bytes/inputs, `hidden` `0/16/31/33/1056`, `kb` `0/33`, `ob` `0/17`, unknown flag bit 4, bad `qa/qb`, `eval_scale` `0/-1/10001`, non-zero reserved byte, out-of-range `king_map`/`output_map`, bad checksum, 1-bit flip in `w1`, `|w2|=128`/`-128`, `max|b1|+32*max|w1|=32768`, `w1=-32768`).

EVIDENCE — PART 2 (FIVE REPRODUCED FAILURE-PATH GAPS IN UNMODIFIED `source/src/`):
1. **`eval` silently falls back to HCE + legacy NNUE when `NNUEArch=true` has a failed, residual, unloaded, or pending v3 net (`source/src/uci.cpp:1203-1222`):**
   - `isready` (`865`), `go` (`1125`), `bench` (`1227`), and `selfgame` (`1287`) all check `forge::nnue::v3::problem()` and exit `2`. `eval` (`1203`) omits that check and falls through to `Evaluator::static_eval_components(board)`.
   - Reproduced on `forge_v4_verify`:
     - `NNUEArchFile <bad_checksum.fnn3>` + `NNUEArch true` + `eval` -> prints `info string ERROR NNUE v3: ... checksum mismatch`, then prints **`info string eval hce 18 nnue 20 total 38`** and exits **`0`**.
     - `NNUEArchFile <valid>` + `NNUEArch true` + `NNUEArchFile <bad_checksum.fnn3>` + `eval` (and same for `<residual_flag1.fnn3>`) -> prints `ERROR`, then **`info string eval hce 18 nnue 20 total 38`**, exit **`0`**.
     - `NNUEArchFile <bad_checksum.fnn3>` + `NNUEArch true` + `NNUEArchFile <empty>` + `isready` + `eval`: `uci.cpp:997` clears `g_problem` (`set_problem("")`), making `v3::pending()` true, so **`isready` prints `readyok`** AND **`eval` prints `info string eval hce 18 nnue 20 total 38`**, exit **`0`**!
   - Risk: `W6` uses `eval` for trainer-vs-engine parity; any script parsing `total` without checking `hce 0` + `NNUE v3 active` + zero `ERROR` lines can silently score legacy NNUE + HCE with exit `0`.

2. **`UseNNUE false` silently disables an "active" v3 net while printing `NNUE v3 active` and `readyok` (`source/src/uci.cpp:979, 1015-1020`, `source/src/nnue_v3.cpp:704-712`, `source/src/search.cpp:1284, 2886`):**
   - `v3::problem()` only checks `requested` and `loaded() == nullptr`; it ignores `forge::nnue::enabled` (`UseNNUE`). Meanwhile `search.cpp:1284, 2886` and `uci.cpp:1205` gate v3 behind `nnue::enabled && nnue::available()`, and `loop/LOOP_OPTIONS.txt` omits `setoption name UseNNUE value true` (relying on default `true`).
   - Reproduced on `forge_v4_verify` (even with `FORGE_NNUE_V3_VERIFY=1`!):
     - `UseNNUE false` + `NNUEArchFile loop/forge65_r0067.fnn3` + `NNUEArch true` + `isready` + `eval` + `bench 11` + `selfgame`:
     - Prints `info string NNUE v3 loaded: ...`, **`info string NNUE v3 active: ...`**, and **`readyok`** with **zero errors/warnings**, then outputs **`info string eval hce 18 nnue 0 total 18`**, **`bench depth 11 ... nodes 375354`** (pure HCE instead of `226187`), and plays pure-HCE `selfgame` rows with exit **`0`**.

3. **Passing a directory path to `NNUEArchFile` crashes Linux builds with uncaught `std::__ios_failure` (`SIGABRT`, `rc=-6`) (`source/src/nnue_v3.cpp:589-593`):**
   - On Linux (`libstdc++`), `std::ifstream in(dir_path, std::ios::binary)` succeeds on `open()`, then `std::istreambuf_iterator<char>(in)` throws uncaught `std::__ios_failure: basic_filebuf::underflow error reading the file: Is a directory`, killing the process with `SIGABRT` (`rc=-6`) and empty stdout (no `ERROR` line). By contrast, legacy `NnueFile` on the same directory exits `0` with `info string nnue: wrong size`.
   - Note: reproduced on Linux (`g++` / `libstdc++`); Windows MSVC behavior on directories was not tested here.

4. **Option-order trap against `N15`: sending `NNUEArch true` before `NNUEArchFile <valid>` prints `info string ERROR NNUE v3: ...` even though `FORGE_FIX_ISREADY_PENDING` (`source/src/uci.cpp:36-40, 859-864`) intends alphabetical order to work (`source/src/uci.cpp:974-978`):**
   - Reproduced on `forge_v4_verify`:
     - `setoption name NNUEArch value true` followed by `setoption name NNUEArchFile value loop/forge65_r0067.fnn3` + `isready` + `eval`:
     - Emits **`info string ERROR NNUE v3: NNUEArch is on but no v3 network is loaded (set NNUEArchFile)`** on line 1, then `NNUE v3 loaded`, `readyok`, and `info string eval hce 0 nnue 87 total 87` (`rc=0`).
   - Risk: `W5 (i)` / `N15` requires the start script to refuse any startup output containing `ERROR` up to `readyok`. Alphabetically sorted option senders will falsely trip `N15` unless frozen option order (`NNUEArchFile` before `NNUEArch`) is preserved or `uci.cpp:976` treats `v3::pending()` like `isready` (`859`).

5. **`nnue::v3::load()` itself accepts `FlagResidual` (`flags=1`) and returns `true`; only `uci.cpp:1002-1007` rejects it (`source/src/nnue_v3.cpp:617, 637`):**
   - Reproduced via direct C++ harness linking `nnue_v3.cpp`: `load()` returns `true` (`rc=0`, `residual` flag set) and evaluates the net as standalone. Any C++ harness (`W6`/`W9`) calling `nnue::v3::load()` directly will silently accept a residual `.fnn3` unless `load()` itself rejects `FlagResidual` in standalone-only builds or the caller checks `net->residual`.

ONE-COMMAND REPRODUCER (on any compiled `forge` binary from unmodified `source/`):
```
python3 -c '
import subprocess, pathlib
b = "<path-to-forge>"
net = "loop/forge65_r0067.fnn3"
for tag, inp in [
    ("1_eval_bad_fallback", "setoption name NNUEArchFile value /no/such.fnn3\nsetoption name NNUEArch value true\neval\nquit\n"),
    ("2_usennue_false_lie", f"setoption name UseNNUE value false\nsetoption name NNUEArchFile value {net}\nsetoption name NNUEArch value true\nisready\neval\nbench 11\nquit\n"),
    ("3_dir_sigabrt_linux", "setoption name NNUEArchFile value loop\nisready\nquit\n"),
    ("4_arch_before_file",  f"setoption name NNUEArch value true\nsetoption name NNUEArchFile value {net}\nisready\neval\nquit\n"),
]:
    p = subprocess.run([b], input=inp, text=True, capture_output=True)
    print(tag, "rc=", p.returncode, "out=", p.stdout.splitlines(), "err=", p.stderr.strip()[:120])
'
```

COST: Seconds on CPU (synthetic fixtures + 1-line source fixes in `W15` / harness checks in `W5`/`W6`/`W9`); zero GPU or strength-match time.

HOW IT IS JUDGED (PROPOSED ADDENDUM TO `W5 (a)/(i)`, `W6`, `W9`, `W15`):
1. **Harnesses & preflight (`W5 (a)/(i)` and `W6`, zero source changes required before `W15`):**
   - `W5 (i)` explicitly sends `setoption name UseNNUE value true` (or refuses `UseNNUE false` when `NNUEArch=true`) AND preserves `NNUEArchFile` before `NNUEArch` in frozen option order so `N15`'s `ERROR` check does not false-trip on `uci.cpp:977`.
   - `W6`'s trainer-vs-engine `eval` check asserts all three of: `info string NNUE v3 active:` on startup, zero `ERROR` lines, and `hce 0 nnue <X> total <X>` on every checked position (never reading `total` alone), plus a planted bad-checksum `.fnn3` negative control that must fail `isready` (`rc=2`) and produce an `ERROR` line.
   - Before `W13 (b)` uses any `1024`-wide `.fnn3`, `W6`/`W9` runs the cross-ISA parity check (`AVX-512` == `AVX2` == `scalar` with `-DFORGE_NNUE_V3_VERIFY=1`, zero mismatches, identical `bench 11` and fixed-opening `selfgame` rows) on a `1024`-wide `.fnn3` fixture (including the exact `b1=255, w2=±127` and `max|b1|+32*max|w1|=32767` bounds), not only on the `768` net or widths `> 1024`.
2. **Source fixes (under `W15`, each gated by a deterministic unit/UCI fixture that fails before the fix and passes after):**
   - `uci.cpp:1203` (`eval`): fail loud (`info string ERROR NNUE v3: ...`, `return 2`) when `!v3::problem().empty()`, matching `go`/`bench`/`selfgame`.
   - `nnue_v3.cpp:704` (`v3::problem()`): report a problem whenever `requested && (!nnue::enabled || !nnue::available())` so `UseNNUE false` + `NNUEArch true` never logs `NNUE v3 active` or silently runs HCE.
   - `nnue_v3.cpp:589`: reject non-regular files / catch stream read failure via `fail()` instead of throwing uncaught `std::__ios_failure` (`SIGABRT`) on Linux directories.
   - `uci.cpp:976`: when `v3::pending()` is true on `NNUEArch true`, emit the same non-`ERROR` pending info line as `isready` (`859`) instead of `info string ERROR NNUE v3: ...` (keeping hard errors loud on failed loads and on `go`/`bench`/`selfgame`/`eval`).
   - `nnue_v3.cpp:617`: reject `FlagResidual` inside `nnue::v3::load()` itself (in standalone-only builds) so direct C++ callers cannot bypass `uci.cpp:1002`.

WHAT WOULD CHANGE MY MIND:
- For any of the 5 items, if a reproduction on unmodified `source/` shows the failure does not occur as reported, drop that sub-item.
- If the owner wants `UseNNUE false` to intentionally override `NNUEArch true` rather than erroring, then `uci.cpp:979` must at minimum NOT print `NNUE v3 active` and `W5 (i)`/`W6` must still assert `UseNNUE true` + `hce 0` explicitly.
