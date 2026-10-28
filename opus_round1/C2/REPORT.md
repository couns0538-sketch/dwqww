# C2 [Engine Strength + Code Review] Extended correction history (UCI `CorrHistPlus`, default 0) — DONE

Branch `opus-C2` = `opus-O3` (`0d99f02`: AL1 s198 lock tree + O3 no-op refactor) + the `[C2]` commits below.
Engine sources are final at `de2f609`; later commits touch only `opus_round1/C2/` (CI scripts, logs, this report).

**Patches.**
- `patch.diff`: vs the lock tree (`git diff 294dbed HEAD`, engine tree only, as the brief asks).
- `patch_vs_O3_base.diff`: C2's own change vs the O3 base (`git diff 0d99f02 HEAD`, 13 files).

| commit | content |
|---|---|
| e930735 | CorrHistPlus: option, keys, tables, cold twins, hooks in corrected_eval / update_correction |
| a20cf91 | tests/correction_history_tests.cpp extension + `mutation_check.sh` |
| 939caba | evidence tooling: `.github/workflows/opus-c2-smp.yml`, `ci_smp.sh`, `smp_smoke.py`, `bench_pins.py`, `codegen_all.py`, `nps_ab_opts.py` |
| de2f609 | keep the AL1 s198 `.data` addresses of the existing tunables (new tunables defined first) |
| b7c72e9 | CI: the Linux release build must reproduce the PC bench pins (`bench_pins.py --expect`) |
| 49b2b54 | evidence: logs, IDEA_SOURCE, patch.diff, SHA256SUMS |

No Elo claim. All three keys are UNPROVEN until gated.

**Review.** The implementation was done by a sub-agent and reviewed by the main session, which rebuilt
`49b2b54` with the PC lock recipe and re-checked:
- the OFF identity at all 5 depths;
- the ON pins of bits 1, 2 and 4 at d11 and d13;
- the hot-function machine code against the lock;
- the final CI runs.

All match the evidence below (`logs/pc/review_main_session.log`).

## What CorrHistPlus does

New UCI option `option name CorrHistPlus type spin default 0 min 0 max 7` (src/uci.cpp, next to UseNNUE),
stored in `forge::options::corr_hist_plus` (include/forge/search_options.hpp, src/search/options.inc). The
value is a bitmask of extra correction-history keys on top of the lock's pawn and material tables. Each bit
can be gated on its own:

| bit | key | table (per search thread) | test-plan gate |
|---|---|---|---|
| 1 | **continuation**: the previous two moves = (piece type, destination) of our move two plies ago and of the opponent's reply | `[side][our type][to][their type][to]`, 294,912 x int16 (576 KiB), direct index | **G-B1** |
| 2 | **minor piece**: placement of both sides' knights, bishops and kings | `[side][key & 16383]`, int16 (64 KiB) | **G-B2** |
| 4 | **non-pawn**, one key per colour: N, B, R, Q, K of that colour; both read at every node | `[colour][side][key & 16383]`, int16 (128 KiB) | none in the test plan (proposed below) |

- **Keys, without touching Board.** Each key is a hash of the relevant piece bitboards, computed on demand:
  one odd multiplier per piece role, summed, then a SplitMix64 avalanche (`include/forge/correction_plus.hpp`).
  - The continuation key needs the previous two moves. Rather than pass a new argument through the hot
    callers, the search frame is derived from the board history: ply = moves since the root index, frame =
    `stack_[4 + ply]`, confirmed by the frame's own ply.
  - The two moves must be of alternating colours, so there is no key next to the root or after a null move.
- **Read:** `corrected = raw + (pawn + material x MW/100 + clamp(sum(entry x weight)/100, +-16384)) / 256`.
  - Weights `CorrContWeight`, `CorrMinorWeight` and `CorrNonPawnWeight` are `tune::parameters()` tunables:
    x0.01, default 100 (the pawn table's weight), range 0..300.
  - The blended extra is clamped to +-64 cp; the final eval keeps the lock's mate-range clamp.
- **Update.** The extra entries are learned inside `update_correction`, under exactly the lock's rule. The
  search calls it only when:
  - the side to move is not in check;
  - there is no excluded move and no mate score;
  - the best move is quiet or none;
  - the bound lies on the side of the difference (alphabeta.inc).

  The step uses the pawn table's residual and depth weight:
  `step = clamp((best - eval) x 256, +-2048) x min(depth+1,16) / 256`. A decay is added:
  `entry += step - entry x |step| / 8192`, and the entry is clamped to +-8192 (`corrplus::apply`).
- **Lifetime.** The first update with the option on allocates the tables (zeroed, `new (nothrow)`);
  `Worker::clear()` frees them (ucinewgame, each bench position). With the option off nothing is allocated.
  Tables are per thread, not shared.

### How the default (OFF) build stays the AL1 s198 build
- **The dispatch.** `corrected_eval` and `update_correction` gain one line at the top:
  `if (options::corr_hist_plus != 0) [[unlikely]] return <cold twin>(same arguments);`.
  - In machine code this is a one-byte `cmpb $0, mem` + `jne`. The flag is a `std::uint8_t`, so the test
    needs no register.
  - The jump goes, with the arguments untouched, to `corrected_eval_plus` / `update_correction_plus`
    (src/search/correction_plus.inc). These repeat the lock statements and add the extra keys.
  - Both twins are `[[gnu::cold]]`, so they land in `.text.unlikely`.
- **Why the read twin makes no calls.** GCC's interprocedural register allocation lets `search` and
  `qsearch` keep values in registers that the lock's `corrected_eval` does not touch (`r8`, `xmm0`). A twin
  that called other functions would clobber them and change the callers' code; early versions did, adding
  spills to `search` and `qsearch`.
  - So `corrected_eval_plus` is a call-free leaf: every helper is `always_inline`.
  - Cold code is size-optimised, and GCC then divides by constants with `idiv`. The divisions are therefore
    exact multiply/shift helpers (`corrplus::div100`, `div_pow2`), swept over all 2^32 inputs
    (`logs/pc/div_sweep.log`).
- **`static_evaluate` pin.** `static_evaluate` is pinned with `gnu::aligned(64)` at its lock placement, like
  O3's pin of `MovePicker::next`. The cold worker lifecycle code before it in `.text` grew (the new member's
  construction, destruction and reset); the pin absorbs that, so every hot function after it keeps its lock
  address mod 64.
- **Member and data layout.**
  - The new member `ThreadData::correction_plus_` (a unique_ptr, no initialiser) is the LAST member, so
    every existing member keeps its offset.
  - The new tunables are defined before the existing ones, because GCC emits a translation unit's globals in
    reverse order. This keeps every existing `.data` symbol at its lock address (`logs/pc/data_layout.log`).

## Acceptance

| # | acceptance line | result |
|---|---|---|
| 1 | CorrHistPlus=0 -> bench exact (d11/13/16/20/22), perft, kiwipete | **PASS** (PC recipe and Linux CI; re-checked in review) |
| 2 | search path untouched; diff shows only guarded code | **PASS**: the source diff of the search is 2 guarded lines. Machine code vs the O3 base: 120 of 127 `forge::` functions are identical at the same mod-64 address (incl. search, qsearch, MovePicker, TT, NNUE, Board). `corrected_eval`: +2 instructions on its path. `update_correction`: +3 and a register renaming (section 2) |
| 3 | tests extended: keys stable under make/unmake, clamp holds, index/clamp/decay tests FAIL on a planted off-by-one (demonstrated) | **PASS**: 29,227 checks, 0 failures; 14/14 planted bugs caught |
| 4 | ON bench differs from OFF at d13; recorded as new pins d11/13/16/20/22 per single bit | **PASS** (section 4). Threads=1 repeats are identical; the Linux CI release build reproduces every pin (run 40464660237) |
| 5 | no crash at Threads 1/8 (8 only on CI) | **PASS**: local Threads 1. CI: Threads 1 and 8 on release, ASan+UBSan and TSan builds, values 0/1/2/4/7 |
| 6 | FMA 0 | **PASS** (PC exe and Linux CI exe) |
| 7 | OFF path one well-predicted branch into cold code; codegen_compare.sh shown; NPS OFF vs lock measured | **PASS** (sections 2 and 3); NPS within noise |
| brief §3 | ctest only the 4 known lines; ASan+UBSan and TSan clean; Threads=1 deterministic; no new warnings | **PASS** (local + CI) |

### 1. OFF identity (`logs/pc/identity_off.log`)
PC recipe `build_pc.sh` (MSYS2 g++ 15.2, exact lock flags):
```
built forge_c2.exe sha256 62a9e36b93996f1672d548d12cd3d07d453167eed51f749526ea7b08a7b60ffb   (tree de2f609)
FMA (vfmadd/vfmsub/vfnmadd) count: 0
$ python 2_build/uci_check.py forge_c2.exe --full
bench d11 nodes 312866 ref 312866 OK
bench d13 nodes 862329 ref 862329 OK
bench d16 nodes 3024920 ref 3024920 OK
bench d20 nodes 12389307 ref 12389307 OK
bench d22 nodes 34048354 ref 34048354 OK
perft5 startpos 4865609 ref 4865609 OK
perft5 kiwipete 193690690 ref 193690690 OK
ALL OK
```
- **Linux** (CI release, g++-14.2, box flags): the same 7 lines + `ALL OK`, FMA 0, forge sha256 82e4b87d…
  (`logs/ci/*/opus-ci-release/identity.log`).
- **Extra identity:** with every key on and all three weights at 0, the search visits exactly the OFF tree
  at all five depths (the `all weights 0` row in section 4), i.e. the cold twins reproduce the lock
  statements bit for bit.

### 2. Machine code (`logs/pc/codegen_compare_lock.log`, `codegen_all.log`, `hot_diff.log`)
```
$ bash opus_round1/O3/codegen_compare.sh forge_h256_s198.exe(A: AL1 s198 lock) forge_c2.exe(B: C2 de2f609)
function                                          insns_A  insns_B differing  mod64_A  mod64_B
forge::Worker::search(forge::Board&                  2413     2413         0       32       32
forge::Worker::qsearch(                               810      810         0       48       48
forge::MovePicker::next(                             1822     1854        32        0        0   (O3 pin: padding only)
forge::Worker::static_evaluate(                       349      349         0        0        0
forge::TranspositionTable::probe(                     200      200         0       48       48
forge::TranspositionTable::store(                     129      129         0       16       16
forge::Worker::should_stop(                            73       73         0       32       32
forge::Worker::is_draw(                                31       31         0       48       48
forge::Worker::corrected_eval(                         99      106         7       32       32
forge::Worker::update_correction(                      81       86        93       32        0
forge::Worker::quiet_history(                          36       36         0       48       48
forge::Worker::capture_history_value(                  37       37         0       48       48
forge::Worker::update_quiet_stats(                    302      302         0        0        0
forge::Worker::update_capture_stats(                  160      160         0        0        0
forge::Worker::update_continuation(                    97       97         0       48       48
forge::Worker::record_move(                            32       32         0       48       48
forge::Worker::search(forge::Board,                  2119     2119       372       48       48   (same 372 as the O3 base)
forge::nnue::update/evaluate/refresh, Board::make_move/unmake_move/see_ge: 0 differing, same mod 64
```
- **`corrected_eval` vs the lock:** `+cmpb $0x0,flag(%rip)`, `+jne`, and the cold stub
  `pop %rbx; pop %rsi; jmp corrected_eval_plus` after the `ret`. Everything else is identical; two
  RIP-relative displacements differ because data and code moved.
- **`update_correction`:** the same compare, branch and stub, but GCC moves `this` to `rbx` for the tail call
  and renames the scratch registers of the unchanged statements. That is +3 instructions on the executed path,
  and the function starts at 0 instead of 32 mod 64. Five source variants of the dispatch were compiled; all
  give this renaming. `update_correction` runs at most once per interior node, after the move loop.
- **All functions** (`codegen_all.py`: every `forge::` symbol, padding ignored), C2 vs its O3 base built with
  the same recipe: 120 of 127 are identical at the same mod-64 address. The 7 others are:
  - the cold lifecycle functions (`~ThreadData`, `~Worker`, `clear`, `Worker()`);
  - `corrected_eval` and `update_correction`;
  - the UCI parser `parse_limits` (moved only).

  The two new cold twins live in `.text.unlikely`. Against the lock exe, the list also contains what O3
  already changed (`set_threads`, the iterative driver, `Searcher::search` placement, `uci_output_mutex`).
- **Data** (`data_layout.log`): of 79 `forge::` data symbols, 77 are at their lock address. Two `.bss` ints
  (`FailLowContinuationBonus`, `CaptureFutilityBase`) moved by 4 bytes within the same 64-byte line. The new
  symbols lie after the existing blocks.

### 3. NPS (PC busy with gates, datagen and training: load 12-17 on 16 logical CPUs; all runs at nice 19)
`nps_ab.py` (QA's script): ABBA-interleaved fresh processes, bench, Threads 1, Hash 16, 10 runs per side.

| A vs B | depth | wall B/A (95% CI of the difference) | cpu B/A | log |
|---|---|---|---|---|
| **lock vs C2 final (OFF)** | 16 | **+0.39%** (−1.85 .. +2.63) | **−1.01%** (−2.40 .. +0.38) | `logs/pc/nps_off_vs_lock.log` |
| **lock vs C2 final (OFF)** | 20 | **−0.09%** (−2.71 .. +2.53) | **−1.34%** (−3.57 .. +0.89) | same |
| lock vs C2 939caba (before the .data fix), first run | 16 / 20 | −2.82% (−3.86 .. −1.78) / −3.01% (−3.98 .. −2.03) | −2.72% / −2.75% | `nps_history/1_*` |
| A/A control: lock vs a byte copy of the lock | 20 | +1.55% (−2.88 .. +5.98) | +1.56% | `nps_history/2_*` |
| control: lock vs O3 base | 20 | −0.40% (−0.98 .. +0.18) | −0.39% | `nps_history/3_*` |
| O3 base vs C2 939caba | 20 | −0.92% (−3.95 .. +2.11) | −0.56% | `nps_history/4_*` |
| lock vs C2 with the .data fix | 16 / 20 | −0.57% (−1.28 .. +0.15) / +1.36% (−1.96 .. +4.68) | −0.38% / +1.60% | `nps_history/5_*` |
| d16 replication, back to back (lock vs 939caba, lock vs .data fix; 2 rounds) | 16 | −0.08% / +0.07%, then −0.93% / −0.87% | −0.30% / −0.19%, then −1.01% / −0.18% | `nps_history/6_*` |

**How the numbers developed.**
- The first measurement of 939caba showed −3% with a tight interval. That led to the data-layout check, which
  found the 49 existing tunables shifted by 12 bytes (fixed in de2f609).
- Back-to-back replications then put both builds within about 1% of the lock, so most of the −3% was session
  noise. The fix is kept because it restores the lock's data addresses.
- The final OFF numbers are within noise at both depths. Differences below about 2% cannot be resolved on
  this machine; QA should repeat `nps_ab.py` on an idle machine.

**ON-path cost** (`nps_ab_opts.py`). The same exe runs OFF against one bit with its weight at 0. That
searches the identical tree (node counts checked), so the difference is the cost of the ON code alone: key
hashing, table traffic and cold code. 10 runs per side:

| ON line (weight 0) | d16 wall / cpu | d20 wall / cpu |
|---|---|---|
| bit 1 (G-B1) | −2.44% / −1.32% | −1.41% / −1.09% |
| bit 2 (G-B2) | −0.75% / −2.62% | −1.55% / −1.03% |
| bit 4 | −2.97% / −2.39% | — |
| all three | −3.58% / −6.96% | — |

The 95% intervals are 3-12 points wide (`nps_on_cost_d16.log`, `nps_on_cost_d20.log`); the cost is roughly
1-3% per bit. The first cold twins used `idiv` (size-optimised code); the division-free version measured
+2.17% cpu against it on the same tree.

### 4. ON bench pins
PC recipe exe de2f609; Threads 1, Hash 16, OwnBook false; each line was run twice in fresh processes, with
identical results (`logs/pc/bench_pins_*.log`). The Linux CI release build reproduces every value. In review,
`49b2b54` reproduced the d11 and d13 values of bits 1, 2 and 4.

| line | option | d11 | d13 | d16 | d20 | d22 |
|---|---|---|---|---|---|---|
| OFF (= lock) | CorrHistPlus=0 | 312866 | 862329 | 3024920 | 12389307 | 34048354 |
| **G-B1** continuation | CorrHistPlus=1 | **318363** (+1.8%) | **915778** (+6.2%) | **2347193** (−22.4%) | **9687762** (−21.8%) | **19269711** (−43.4%) |
| **G-B2** minor piece | CorrHistPlus=2 | **296553** (−5.2%) | **824640** (−4.4%) | **2914749** (−3.6%) | **13945117** (+12.6%) | **40489211** (+18.9%) |
| non-pawn | CorrHistPlus=4 | 340927 (+9.0%) | 734347 (−14.8%) | 2794671 (−7.6%) | 12132495 (−2.1%) | 37005405 (+8.7%) |
| all keys | CorrHistPlus=7 | 317529 (+1.5%) | 866764 (+0.5%) | 2715911 (−10.2%) | 8754177 (−29.3%) | 26756688 (−21.4%) |
| all keys, weights 0 | 7 + CorrContWeight=CorrMinorWeight=CorrNonPawnWeight=0 | 312866 | 862329 | 3024920 | 12389307 | 34048354 |

Every single bit differs from OFF at d13. On the crew node screen (+10% at d13/d16), all three bits pass. G-B2
is above +10% at d20 (+12.6%) and d22 (+18.9%), the flag the crew used for a longer-TC confirm.

### 5. Tests (`tests/correction_history_tests.cpp`, ctest `forge_correction_history_tests`; `logs/pc/correction_history_tests.log`)
All existing checks are unchanged. Each new section prints one PASS/FAIL line, and failures print individually:
```
PASS corrplus keys: make/unmake, null move, FEN round trip, change iff hashed pieces change checks=29112
PASS corrplus continuation index: exact value, in range, bijective checks=6
PASS corrplus division helpers: div_pow2<8>, div_pow2<13>, div100 equal the / operator checks=3
PASS corrplus update rules: step, decay, clamp, blend (exhaustive entry x step domain) checks=10
PASS corrplus worker glue: OFF untouched, one entry per key, read formula, frame and null-move rules, clamps, clear checks=32
PASS corrplus search: Threads 1 determinism, ON differs from OFF, tables filled during search checks=10
SUMMARY checks=29227 failures=0
```
- **Keys:** 36 random walks over 9 positions (including en passant, castling and under-promotion), up to 120
  plies. Keys are unchanged by a null move, restored by unmake, equal after a FEN round trip and for a
  transposition, and change exactly when the hashed pieces change. The reference is mailbox signatures, not
  bitboards.
- **Index:** all 294,912 continuation slots are hit exactly once, and each value equals the reference formula.
- **Update:**
  - `apply` matches a reference over the whole domain (16,385 entries x 257 steps), and the clamp is never
    left;
  - the decay anchors hold, decay is monotone under alternating steps, and a constant step converges to
    exactly +8192;
  - `step` and `blend` match their references, and the division helpers match `/`.
- **Glue** (through `SearcherTestProbe`):
  - OFF allocates nothing; each bit writes exactly its entries with the pawn table's step.
  - The read formula is checked with seeded entries and weights 33/70/130.
  - Frame derivation: ply 1 gives no key; ply 2 gives the (White, P-e4, P-e5) slot. A wrong ply, a null
    move, a same-colour pair and a board outside a search all give no key.
  - The blend clamp (±64 cp) and the entry clamp (±8192, reached exactly) hold through the Worker, and
    `clear()` frees the tables.
  - The twins equal the lock's update and corrected eval over 3 x 3000 random updates
    (MaterialCorrectionWeight 100/33/0).
- **Search:** depth 9 on 2 positions for each value 0/1/2/4/7. Two runs are identical, every ON value differs
  from OFF, and more than 200 continuation entries are learned in a real search.

Planted bugs (`mutation_check.sh`, `logs/pc/mutation_check.log`), one bug at a time in a scratch copy:
```
BASELINE (unmutated): 0 SUMMARY checks=29227 failures=0
MUTATION index_stride_63 -> caught        MUTATION index_type_offset -> caught       (index off-by-one)
MUTATION clamp_limit_minus1 -> caught     MUTATION total_limit_minus1 -> caught      (clamp off-by-one)
MUTATION decay_shift_minus1 -> caught     MUTATION decay_shift_plus1 -> caught       (decay divisor)
MUTATION div_pow2_bias_plus1 -> caught    MUTATION div_pow2_floor -> caught    MUTATION div100_rounding -> caught
MUTATION step_depth_weight -> caught      MUTATION minor_key_no_white_king -> caught
MUTATION frame_offset -> caught           MUTATION twin_depth_cap -> caught    MUTATION clear_keeps_tables -> caught
mutation_check status=0
```
A twin divisor of 255 instead of 256 was tried first and turned out to be an equivalent mutant: `diff` is a
multiple of 256 clipped to +-2048, so both divisors give the same quotient for every reachable input.

### 6. Threads 1 / 8, sanitizers (CI; local runs are Threads 1 only)
`.github/workflows/opus-c2-smp.yml` calls `ci_smp.sh`. It builds the engine three ways (release, ASan+UBSan
with recover off, TSan) and runs `smp_smoke.py` for CorrHistPlus 0/1/2/4/7:
- **Searches:** `go depth` on 10 positions (ucinewgame before every second one), `go movetime 300`,
  `go infinite` + stop, `go ponder` + ponderhit.
- **Checks:** each search must give exactly one legal bestmove (the engine checks legality), and the process
  must exit cleanly.
- **Threads:** Threads 1 runs twice per value, and the node counts must match; then Threads 8.
- **Pins:** release mode also checks the PC bench pins.

Result on release, ASan and TSan: 260 PASS, 0 FAIL each; 0 sanitizer reports; all pins equal. The local
Threads 1 run is in `logs/pc/smp_smoke_threads1_local.log` (175 PASS).

### 7. Other section-3 checks
- **ctest** (CMake Release, MSYS2 g++ 15.2, tree de2f609): 16/17, only `forge_tests` with exactly the 4 known
  lines (`logs/pc/ctest_release.log`, `ctest_release_known_failures.log`). CI shows the same on release,
  ASan+UBSan and TSan (TSan 0 reports).
- **Compiler warnings** (-Wall -Wextra -Wpedantic -Wconversion -Wshadow): the same 6 pre-existing
  `-Wconversion` lines as the lock and O3; no new warning (`logs/pc/compiler_warnings.log`).
- **`tools/check_nnue_simd.py`** prints "FAIL: NNUE output has no 256-bit vmaxps" for this exe and for the lock
  exe alike. This is pre-existing with the znver5 recipe: nnue.cpp is untouched and `nnue::evaluate` is
  machine-code identical. The FMA count by objdump is 0.

## CI runs (GitHub Actions, couns0538-sketch/dwqww, branch opus-C2)

| head | workflow | run id | result |
|---|---|---|---|
| 939caba | opus-ci (release identity, ctest release/ASan+UBSan/TSan) | 40410939194 | success: identity ALL OK, FMA 0; 16/17 + 4 known lines x3; TSan 0 reports |
| 939caba | opus-c2-smp (Threads 1/8, release/ASan/TSan) | 40410939229 | success: 260/260 PASS x3, 0 sanitizer reports |
| de2f609 | opus-ci | 40462176469 | success, as above (Linux forge sha256 82e4b87d…) |
| de2f609 | opus-c2-smp | 40462176446 | success, as above |
| b7c72e9 | opus-ci | 40464660204 | success: identity ALL OK, FMA 0 (same Linux exe hash); 16/17 + 4 known lines x3; TSan 0 reports (re-checked in review) |
| b7c72e9 | opus-c2-smp (+ Linux bench pins vs PC pins) | 40464660237 | success: 260/260 PASS x3, 0 sanitizer reports; the Linux release build reproduces OFF and CorrHistPlus 1/2/4/7 pins at d11-d22 (re-checked in review) |
| 49b2b54 and later | (logs/docs only; paths-ignore) | — | no run |

Downloaded logs: `logs/ci/<head>_run<id>_<workflow>/`.

## Proposed gate specs (one option per gate; QA runs them and assigns the srand)

**Candidate exe:** a PC recipe build (`build_pc.sh` = the 2_build/build_windows.ps1 flags) of `opus-C2`.
Before a gate:
- its OFF bench must equal the lock pins, and its ON bench the pins below;
- `uci` must list `option name CorrHistPlus type spin default 0 min 0 max 7`.

Options go on the candidate only.

- **G-B1 (continuation correction)**
  - Line: candidate `option.CorrHistPlus=1` (weights at defaults) vs the AL1 s198 lock exe.
  - Settings: fastchess 10+0.1, Threads=1, Hash=16, OwnBook=false, 8moves_v3 order=random, -repeat -games 2,
    SPRT [0,10] normalized, alpha=beta=0.05, cap 1500.
  - srand: the G-B1 seed of the test plan (QA).
  - Pre-gate identity: bench d11/13/16/20/22 = 318363 / 915778 / 2347193 / 9687762 / 19269711.
  - Per the test plan, an H1 at 10+0.1 needs a 40+0.4 confirm (EVAL change).
- **G-B2 (minor-piece correction)**
  - Line: the same settings with `option.CorrHistPlus=2`; srand: the G-B2 seed of the test plan (QA).
  - Pre-gate identity: 296553 / 824640 / 2914749 / 13945117 / 40489211.
  - d20/d22 nodes are +12.6% / +18.9%, so a longer-TC confirm is advisable on H1 (the test plan requires one
    anyway).
- **Non-pawn correction (no test-plan ID)**
  - Line: if QA wants it gated, `option.CorrHistPlus=4`, the same settings, and a new gate ID and srand from QA.
  - Pre-gate identity: 340927 / 734347 / 2794671 / 12132495 / 37005405.
- **Not proposed:** `CorrHistPlus=7` (three changes in one gate). The weights are tunables, for a later SPSA if
  a bit passes.
- **When reading the gates,** keep the ON speed cost in mind: roughly 1-3% per bit on this machine (section 3).

## Files (`opus_round1/C2/`)
- **Report files:** `REPORT.md`, `IDEA_SOURCE.md`, `patch.diff`, `patch_vs_O3_base.diff`, `SHA256SUMS`.
- **Scripts:** `bench_pins.py`, `codegen_all.py`, `nps_ab_opts.py`, `mutation_check.sh`, `smp_smoke.py`,
  `ci_smp.sh` (workflow `.github/workflows/opus-c2-smp.yml`).
- **Logs:** `logs/pc/` (final exe evidence, incl. `review_main_session.log`), `logs/pc/nps_history/` (every NPS
  run of this job), `logs/ci/` (downloaded CI artifacts).

## Notes / open items
- **Not verified:** the Linux machine-code layout (the codegen claims are for the PC recipe build, which the
  gates use), and NPS on an idle machine (QA).
- **Register renaming:** `update_correction` keeps the renaming from section 2. This is accepted because it is
  not per-node code.
- **Merge note:** the O1 branch also creates `include/forge/search_options.hpp` and `src/search/options.inc`
  (its SMP options) and edits the same advertise/parse spot in uci.cpp. The merge is a union of both. Keep the
  `std::uint8_t` type of `corr_hist_plus`, and keep the CorrHistPlus tunables defined first in tune.inc.
- **Memory:** `ThreadData` grew by 8 bytes (the new last member). Tables are per thread, 768 KiB each when on,
  so memory is threads x 768 KiB.
