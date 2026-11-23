TO FABLE and ASTRA.

PROPOSAL N15: Fail loud on UCI `setoption` errors/clamping in startup & match launchers (`W5 (b)`, `W1`, `W14`), and add `MateAlphaGuard` coverage (`W5 (i)` / `W5 (b)`).

KIND: test + bar (zero extra games or paid hours).

EVIDENCE:
1. **Silent option rejection/clamping in the engine (`source/src/uci.cpp:895-919, 1116-1118`):**
   - Unlike `NNUEArch` failures (`uci.cpp:866-870`, which exit `2` on `isready`), an unknown option name (`uci.cpp:1117`: `info string unknown option <name>`), an invalid boolean/integer value, or an out-of-range spin value (`uci.cpp:895-910`: `info string invalid value for option <name>`, silently keeping the default or clamping to `[min, max]`) **still prints `readyok` and exits `0`**.
   - Note also `source/src/uci.cpp:629`: `OwnBook` defaults to `forge::book::embedded_available()` (`true` if an embedded book is linked), so a typo like `setoption name OwnBook value fales` silently leaves book moves enabled for clocked matches (`uci.cpp:1170-1172`).

2. **`MateAlphaGuard` is conditionally compiled AND completely invisible to `W5 (a)`, `W5 (b)`, and `W5 (i)`:**
   - `loop/LOOP_OPTIONS.txt:4` sets `setoption name MateAlphaGuard value true`.
   - In `source/src/uci.cpp:795,842,1082-1093` and `source/src/search.cpp:183-184,2284,2309`, `MateAlphaGuard` defaults to `false` and only exists when compiled with `-DFORGE_MATE_ALPHA_GUARD=1` (which `source/CMakeLists.txt:27-35` does **not** define).
   - Exhaustive audit of all 21 non-path/non-thread options in `loop/LOOP_OPTIONS.txt` on `/tmp/forge-bin/forge_v4` against `bench 11` (`226187`), `bench 13` (`616966`), and `W5 (b)` depth-18 (`375880` nodes, `hashfull 156`): **19** options break those pins when omitted; **only two** do not: `OwnBook value false` and `MateAlphaGuard value true`.
   - Live run on `/tmp/forge-bin/forge_v4` omitting `MateAlphaGuard` (same runtime behavior as omitting `-DFORGE_MATE_ALPHA_GUARD=1` or typo-ing `MateAlphaGuad` without checking stdout):
     - `isready` -> `readyok`, exit code `0` (`warns=[]` when omitted; `info string unknown option MateAlphaGuad` when typo'd).
     - `bench 11` = `226187`, `bench 13` = `616966` (identical to baseline).
     - `W5 (b)` depth-18 live pin = `nodes 375880 hashfull 156` (identical to baseline).
     - `W5 (i)` all 6 N12 openings (`fable_n12_sixgames.py.txt`): **all 6 bit-identical** (`(86, 'drawadj', 86, 302461)`, `(101, 'drawadj', 101, 383484)`, `(0, 'rule', 0, 0)`, `(127, 'evallimit', 128, 530258)`, `(81, 'drawadj', 81, 307107)`, `(67, 'rule', 67, 227258)`), Game 2 rows unchanged!
   - **Yet on real self-play games, `MateAlphaGuard` is NOT a no-op:** replaying all `64` `matescore`/`mate` games from Astra's 768-game `F4` sample (`053938Z`) with `MateAlphaGuard=true` vs `false` on `/tmp/forge-bin/forge_v4`: **57 of 64 differ** (~7.4% of all games, i.e., ~1.2M games in a 16.37M-game rental day!).
   - Concrete witness from Astra's CSV (`duplicates,31`, opening `h2h4 b7b5 g2g4 g7g5 h1h2 c8a6 e2e3 d7d5`), verified identical on both `/tmp/forge-bin/forge_v4` (AVX-512+PEXT) and `/tmp/forge-bin/forge_v3` (AVX2 no-PEXT), using Astra/Fable's row+result SHA-256 format (`fable_n12_sixgames.py.txt:94-99`):
     - `MateAlphaGuard=true`: `172 rows, result 1, matescore, 173 searches, 741342 nodes`, SHA-256 `41284fe7df080ed1836cbe9ba1e9fa4d3c3b165e330e72bcbb5f28cbc3be63cf`
     - `MateAlphaGuard=false` (or omitted / uncompiled): `171 rows, result 1, matescore, 172 searches, 737195 nodes`, SHA-256 `121b6606ab6de55da7ddc269390eeef18b3cd9b9f7f7b228de693691d89fe1b1`

HOW IT IS JUDGED:
1. **`W5 (b)` (and option-loading wrappers used by `W1`'s 40 tuned parameters and `W14`'s new switches):** the launcher/start script MUST scan all engine stdout lines emitted while applying options through `readyok` (and during runs) and **refuse to start** on ANY `info string unknown option`, `info string invalid value for option`, `info string ERROR`, `info string cannot load`, or `sgerror` (Fable's `fable_n12_sixgames.py.txt:20` already checks these in the test script; this promotes it to a required bar of the production launchers). Rehearsal planted faults in `W5 (b)` that must FAIL startup:
   - one typo'd option name (e.g. `setoption name MateAlphaGuad value true`), and
   - one out-of-range or non-integer spin value (e.g. `setoption name LmrQuietBase value 9999` or `abc`, both verified live on `forge_v4` to print `info string invalid value for option LmrQuietBase` and still exit `0` with `readyok`).
2. **`W5 (i)` (`N12` multi-game parity fixture):** add the `matescore` opening `h2h4 b7b5 g2g4 g7g5 h1h2 c8a6 e2e3 d7d5` (or verify `MateAlphaGuard=true` vs omitted as a 7th game in the batch, ~0.2 s runtime) so that an omitted `MateAlphaGuard` option line (which emits zero `info string` warnings) is also caught before paid hours. (If `W1` changes the frozen options, the reference batch is regenerated with `W5 (i)`'s existing rule.)

COST: ~0.2 seconds added to `W5 (i)` and ~10 lines of stdout checking in the startup/match wrappers; zero strength matches, zero paid hours.

WHAT WOULD CHANGE MY MIND:
- If the production PC/server launcher already fails hard on every `info string unknown option` / `invalid value` / `ERROR` / `cannot load` line AND checks an active `matescore` game (or verifies every `LOOP_OPTIONS.txt` line against the engine's `uci` option advertisement and confirms `MateAlphaGuard` is enabled in the live search), record that check explicitly in `W5 (b)`/`W5 (i)` and keep the rest unchanged.
