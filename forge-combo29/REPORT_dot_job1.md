# dot Job 1: baseline gate

Clock start: 2026-11-18 10:47:15 UTC (`date -u`). Case A: native commands and GitHub text publication work. Model identifier unavailable to this task; not inferred.

Lock source: 16833ecc03b425586f91f4c8834dea8807bf4c22. Plain CMake Release, default x86-64-v4 and PEXT/ZMM switches, unchanged source, -j2. CMake 4.4.5; GNU C++ 14.2.0 (Debian 14.2.0-19); glibc 2.41 (Debian GLIBC 2.41-12+deb13u4); dynamically linked libstdc++.so.6/libgcc_s.so.1. Exact libstdc++ package version not yet established (package database unavailable). Binary SHA256 1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6. Embedded AL1 s198 net SHA256 a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638.

Commands:
```
cmake -S forge-combo29 -B /tmp/forge-dot-lock-build -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/forge-dot-lock-build -j2
```
CMake was absent initially, installed PyPI CMake 4.4.5 in a temporary task directory. Configuration selected /usr/bin/c++ GNU 14.2.0 without compiler override.

Fresh process for each bench, sent Threads 1, Hash 16, OwnBook false, bench depth, quit. Bench uses its own 16 MiB single-thread searcher. UseNNUE true default. Perft uses startpos. Raw stdout:
```
info string bench depth 11 nodes 312866 time 198 nps 1580131
info string bench depth 13 nodes 862329 time 551 nps 1565025
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```
All three required pins MATCH. NPS here is raw output only, not a speed result or Elo claim. `git diff --exit-code` passed before leaving the lock checkout.

Read LOCK.md, README.md and CMakeLists.txt on lock. Read latest NOTES_sol3.md at 58b6ef8f6999200ef9023509f7dbdd27a498a912 (through Job 6) and latest NOTES_kimi5.md at c04ba44b662d701e8bdc74e48fbfcbbc98338421 (through Job 24). Useful prior mechanisms: final node count differs from completed-iteration labels, reset semantics, clock gates, and source-only suspicion is not a native defect proof. Will deduplicate against these notes.

The helper base 6b98f2170a3210e71beed04bbd2553972c253ed7 is NOT source-identical to the lock: source/include diff contains substantial changes. The pin gate applies only to the lock binary above; upcoming line references and review target the requested helper base, not the lock. No claim of base-build pin equivalence.

FABLE_TO_dot_1.md absent in handoff snapshot e122d5c163b0d831762db954c8adbc1e57d838a8; user's first job is the governing assignment. Code review next; no candidate findings or repairs claimed yet.

## First review checkpoint (2026-11-18 10:53:54 UTC)

### Build and inspection attribution
All findings below refer to helper base **6b98f2170a3210e71beed04bbd2553972c253ed7**, not merely to the lock. Built it separately with the same default CMake Release recipe and GNU 14.2.0 / libstdc++.so.6.0.33 / glibc 2.41 / CMake 4.4.5. Base binary SHA256 **2f545495d4e3e2b59af49fbb18212ec2ed8ae297d801e58647cfea37cd18e785**. Its own bench 11/13 also matched 312866/862329 (raw lines in dot_job1_native_raw.txt). Embedded net is the same SHA256 recorded above. Repository source remained unchanged; git diff --exit-code passed.

Read UCI command handling (src/uci.cpp 1–654), clock_plan.hpp, uci_clock.hpp, tm_finish.hpp, tm_node_share.hpp, search limits and timing/driver/facade code. An internal independent reader covered search.cpp 1–2110 plus remaining driver/facade portions; combined reading covered the complete search file. This is inspection, not a proof of all branches or a full regression suite.

Native probes use fresh processes, UCI handshake, Threads 1, Hash 16, OwnBook false, UseNNUE true, embedded AL1 s198, otherwise defaults. They wait for bestmove before quit. Spin-only probes search zero nodes. Raw transcripts: [dot_job1_native_raw.txt](dot_job1_native_raw.txt).

### 1. uci-node-mode-sticky — reproduced parser inconsistency; precedence decision required
**Files opened:** src/uci.cpp:104–113; include/forge/search.hpp:32–34; src/search.cpp:2174–2180. Existing behavior docs REPORT_r3_12.md say go nodes remains a hard bound.

**Fact:** Both tokens overwrite the same numeric node budget, but only softnodes sets the mode flag. A later nodes token does not clear it.
- Base startpos, go nodes 1000: final completed iteration depth 4, 404 reported nodes, bestmove e2e4. The 404 is NOT the consumed hard budget; no final-total label exists for normal nodes.
- Base startpos, go softnodes 1 nodes 1000: depth 5, final softnodes total **1001**, bestmove c2c4, identical non-time fields to go softnodes 1000.
- Reverse order go nodes 1 softnodes 1000 also selects soft mode.

**Expectation/suspicion:** If duplicate budget selectors follow the last accepted selector, as their numeric assignment suggests, the trailing nodes must restore hard mode. Mixed-selector semantics are not explicitly documented, so this is not a claim that a UCI standard defines this custom extension.

**Deciding test:** Compare the mixed command with plain go nodes 1000 in fresh identical processes. With [dot_softnodes_last_mode.patch.txt](dot_softnodes_last_mode.patch.txt), the mixed command ends at the same depth 4 / 404 completed-iteration label / e2e4 and prints no softnodes marker. Before patch it exceeds the requested hard budget and selects c2c4. Choosing instead to reject mixed selectors is another defensible policy.

### 2. uci-spin-overflow-not-clamped — reproduced mismatch with stated integer-clamping contract
**Files opened:** src/uci.cpp:275–286, REPORT_t16.md. Comment and report distinguish non-integer rejection from out-of-range integer clamping, without stating an int32 limit.

**Fact:** from_chars parses directly to int, and result_out_of_range takes the rejection branch before clamp.
Fresh spin-only process, initial TmSoftDivisor 22, advertised range 5..80:
- value 1000 or 2147483647: diagnostic, stored 80.
- value 2147483648: diagnostic, stored **22**, not 80.
Stored value observed via this engine's repeated uci tunable listing, which REPORT_t16.md explicitly documents as live-value output. No search or node count involved.

**Expectation:** A complete decimal integer outside the range clamps as the comment says. If int32-only rejection is deliberate, documentation should say so.

**Deciding test / candidate:** [dot_spin_integer_clamp.patch.txt](dot_spin_integer_clamp.patch.txt) handles full-token result_out_of_range by assigning the appropriate endpoint. Patched value 2147483648 becomes 80; -2147483649 becomes 5; an arbitrarily long positive digit run becomes 80. Trailing junk, --4, and junk retain 22 and diagnose. This is parser consistency, not a playing-strength change.

### 3. search-negative-history-bonus — source and native-function fact; search-quality consequence unverified
**Files opened:** src/search.cpp:134–136 permits both coefficients to be zero; :242–248 computes/applies bonus; :1374–1393 rewards the chosen move and negates the bonus for other quiets; :2027–2029 says a successful quiet deserves a history boost.

**Fact:** With admitted settings HistoryBonusQuadratic=0 and HistoryBonusLinear=0, history_bonus(depth) is -32 at every depth. Starting from zero history, the chosen move receives -32 and other quiets receive +32. The late-quiet “boost” is -16.

Native function probe included the exact unmodified search.cpp in its translation unit and linked the other base-build objects, GNU 14.2.0, -O2, same feature macros/ISA/strict-FP flags. It called the actual history_bonus and apply_history functions, not a rewritten mathematical model:
```
depth 1 quadratic 0 linear 0 bonus -32 winner -32 other 32 search_nodes 0
```
This is a function-level probe, NOT a whole-engine event trace or Elo experiment.

**Suspicion:** Allowed zero coefficients might be expected to disable rewards rather than reverse them. They may instead intentionally permit signed tuning extremes; no product decision inferred.

**Deciding test:** Instrument the actual winning-quiet update event in an isolated candidate copy, set both coefficients to zero, and use a cold startpos depth-8 search. Record bonus before applying it and pre/post history entries, with a positive event-count control. Compare today's formula with a lower-clamped max(0, formula) candidate. Today any such event has negative bonus; the candidate has zero, and fresh entries stay zero instead of changing with reversed signs. Run default-option lock pins and existing search regressions separately. That full-search event test and any repair are NOT done. No patch proposed for this until signed-tuning intent is settled.

### Important rejected lead: DrawJitter precedence is already intentional
search.cpp:1315 says stalemate and insufficient material keep literal zero. Native DrawJitter 5 / depth 1 / zero-node root probes give cp -5 for stalemate and bare kings at halfmove 100, versus cp 0 at halfmove 0. However **REPORT_r3_14.md:15 explicitly documents fifty-move precedence**, including stalemate at clock 100. Therefore this is an overbroad inline comment, NOT a new correctness bug. An exploratory behavioral patch was generated and built only in a disposable copy, then withdrawn before the final candidate build; it is not published or recommended. Preserve the deliberate semantics; clarify the comment if desired.

### Time-control comment boundary, not promoted to a bug
search.cpp:2395 and :2587–2589 say depth/nodes searches skip clock features. Actual gate is time_managed_, set from supplied clocks at :2194–2199, not from absence of a depth/node bound. TmNodeShare=true with go depth 8 wtime 1000000 btime 1000000 prints node-share adjustments; depth-only does not. Both test arms completed depth 8 / 4099 nodes / d2d4 on the base build. Mixed limits can reasonably obey the clock too. Read this comment as “untimed depth/node searches,” or clarify it, rather than disabling useful time safety.

## Candidate validation
Only the two UCI patches above were present in the FINAL isolated candidate; search.cpp was restored byte-for-byte to helper base. No repository source edits. Candidate binary SHA256 **14d868e06b6d3b2f870ac5669f1d1059f27c4dfb36eb295e03bff412b7b7e5e5**. Same CMake Release/toolchain/default switches/net; raw candidate bench/perft output in dot_job1_native_raw.txt:
- bench 11 = 312866
- bench 13 = 862329
- startpos perft 5 = 4865609
Native discriminating parser probes changed exactly as described. No claim of a full regression pass, performance improvement, or playing-strength improvement.

## What I did not do / uncertainty
No source commit, PR, merge, match, training, standalone-v3 run, owner-PC work, sanitizer run, or long multithread stress test. Not every repository report was audited; dedup searched source-base reports and two latest helper notes. Findings may have counterparts elsewhere. No exact model identifier available to this task. The source review does not establish absence of other defects.

## FOR FABLE AND OPUS
1. Should mixed nodes/softnodes use the last selector, reject ambiguity, or retain documented soft dominance?
2. Should all complete decimal spin integers clamp, or should the contract explicitly stop at int32?
3. Are negative history rewards at legal zero coefficient settings intentional? If not, the next useful task is an event-level regression with a nonzero-event control, not a match.
4. Job 1 is complete. Per the owner's subsequent instruction, I will check FABLE_TO_dot_2.md every two minutes for up to **30 minutes** after this publication, continue on a new job, stop on a first-line STOP, and report no reply through the owner conversation if that window expires. No one-hour global stop is assumed.
