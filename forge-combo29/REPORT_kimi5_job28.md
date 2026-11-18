# kimi5 job 28 report — verify carbon2's consolidated speed stack (r15d → kF) by invariant counting

What was asked: prove or break the claim that kF (= r15d + carbon2's 10-piece stack + stop-hot + fused v3 refresh + AVX-512 TT probe + tidy) is search-identical to r15d, using a read-only counting build with 7 invariant checks, planted-fault controls, a pre-work prediction, and four workloads W1–W4.
The answer: everything holds. kF == r15d bit-exactly in nodes and best moves on 583 positions (plus 30 special positions ×3 builds and 353 net768 rows); all seven invariants held in ~185 million checks with 0 failures; all three planted faults were caught by their own counter.
How sure: very. Every check id was proven to fire (controls A/B/C), every workload ran with options proven to arrive (input logs), and the counting build was itself proven search-identical to kF before any invariant was read.

## 1. Step 0 — honesty check (raw files in `tests_kimi5_job28/step0/{r15d,kF}/`)

Machine: g++ 13.3.0, `-march=native` defines `__AVX512F__`, `__AVX512BW__`, `__BMI2__` (`step0/defines.txt`) — all AVX-512/BMI2 paths run natively, no portable fallback.
Both exes built from verified trees: r15d `sha256sum -c` 29/29 OK (`r15d_sha_check.txt`), kF 29/29 OK (`kF_sha_check.txt`, kF tree sha256 `3d2ce085…` as in carbon2 job17 part0c).

| line | expected | r15d | kF | file |
|---|---|---|---|---|
| bench 11 | 312866 | 312866 | 312866 | `step0/*/none_bench11.txt` |
| bench 13 | 862329 | 862329 | 862329 | `step0/*/none_bench13.txt` |
| go perft 5 | 4865609 | 4865609 | 4865609 | `step0/*/none_perft5.txt` |
| PC20 bench 11 | 278024 | 278024 | 278024 | `step0/*/pc20_bench11.txt` |
| PC20 bench 13 | 587276 | 587276 | 587276 | `step0/*/pc20_bench13.txt` |

All pins met on both builds.

## 2. Step table

| step | status | evidence | result |
|---|---|---|---|
| Step 0 pins + sha | done | `step0/`, `*_sha_check.txt` | all met, 29/29 + 29/29 |
| Known answers (a)(b)(c) from trees | done | §4.1 | all three verified in the source trees |
| Counting build (7 check ids) | done | `patches/stack_checks.patch.txt` (195 lines, `patch -p1 -F0` clean) | builds, links, runs |
| W1: counting vs kF plain, O+G d12 | done | `w1_kFcount/`, `compare_all.txt` | 200/200 + 353/353 per-position nodes AND best moves identical; sums 8,315,168 / 17,611,204 |
| Controls A/B/C (planted faults) | done | `w1_ctrl/`, `patches/ctrl*.patch.txt` | C01 fails 765,570; C02 fails 3,847,535; C04 fails on every position (175–685/search) — all DETECTED |
| Prediction commit before W2–W4 | done | `PREDICTION_kimi5_job28.md`, commit "kimi5 job 28 prediction" 21:16:51 UTC | see §4.4 score card |
| W2: `go nodes 20000`, O, r15d vs kF | done | `w2/`, `compare_all.txt` | 200/200 nodes + best moves equal (all 3 builds, sum 3,055,154) |
| W3: 30 special positions d10, 3 builds | done | `w3*`, `w3.epd`, `w3_check_out.txt` | 30/30 equal across r15d/kF/kFcount (sum 471,276) |
| W4: net768 pins + rows | done | `w4/`, `net/` | bench 882074 / 4275906 exactly; G d12 sum 42,620,225 first3 [95007,39469,131900] == sol3 C2; kFcount identical |
| INV failures, all workloads | done | `*_INVsums.txt` | **0 failures in ~185M checks** (sums below) |
| Step 1 invariant table | done | §4.2 | 21 invariants + stop-hot/fused-refresh/TT pieces mapped |

INV sums (checks / fails) — O d12, G d12, W2 O nodes20k, W3 d10, G d12 net768, W3 d10 net768:

| id | W1 O | W1 G | W2 O | W3 | W4 G net | W4 W3 net |
|---|---|---|---|---|---|---|
| C01 | 1,285,272/0 | 2,201,949/0 | 597,384/0 | 1,006/0 | 5,592,849/0 | 639/0 |
| C02 | 7,595,710/0 | 16,411,916/0 | 3,640,129/0 | 554,672/0 | 37,813,377/0 | 935,056/0 |
| C04 | 7,186,753/0 | 13,739,089/0 | 3,490,007/0 | 443,069/0 | 29,769,614/0 | 733,691/0 |
| C05 | 7,099,319/0 | 13,528,557/0 | 3,413,378/0 | 343,167/0 | 33,674,000/0 | 661,423/0 |
| C13a | 8,315,168/0 | 17,573,069/0 | 4,000,000/0 | 553,648/0 | 42,551,341/0 | 940,731/0 |
| C13b | 8,315,168/0 | 17,573,069/0 | 4,000,000/0 | 553,648/0 | 42,551,341/0 | 940,731/0 |
| C11 | 0/0 (unreached) | 0/0 | 4,000,302/0 | 0/0 | 0/0 | 0/0 |

## 3. Counting build and controls (what the checks are)

`patches/stack_checks.patch.txt` (kF → kFcount, 4 files, applies `patch -p1 -F0`): adds `forge::inv_checks[7]/inv_fails[7]`, reset at root search (`search.cpp`, `parent_worker_==nullptr` branch), printed as `info string INV <id> <checks> <fails>` before every bestmove (`uci.cpp`). Read-only; counters never feed the search.

- C01 badcap prefix: at the `moves_[bad_count_++]` store (piece 01), checks `bad_count_ < index_`.
- C02 precomputed key: end of `Board::make_move`, `precomputed_key != nullptr` → `key_ == compute_key()`.
- C04 known_gives_check: `known_gives_check == 0` branch → `compute_checkers() == 0` (invariant 3 of piece 07).
- C05 corr material index: `corrected_eval` → cached `corr_mat_idx` equals `material_key(board) & (CorrectionSize-1)` (piece 05, invariant 2).
- C13a cluster alignment: every TT probe checks the cluster address is 64-aligned.
- C13b AVX-512 == scalar: `probe_owned_fast` result compared against the scalar probe body on every probe (piece 13).
- C11 fast stop: fast-stop boolean recomputed side-effect-free as `(shared_.stop || local_nodes_ >= node_limit_)` (piece 11).

Controls (each = kFcount + a one-line break, `patches/ctrl*.patch.txt`, O set d12 pc20.opt):
- ctrlA `bad_count_ = index_` before store → C01 fails **765,570** / 1,612,641 checks; C02/C04 stayed 0 (fault localized).
- ctrlB `child_key ^= 1` → C02 fails **3,847,535** / 7,576,970; C01/C04 stayed 0.
- ctrlC pass `0` for `known_gives_check` at one call site → C04 fails on every position tried (175/363/350/157/685 fails per d8 search, `w1_ctrl/C_manual.txt`); at d12 the destabilized search (wrong checkers → king capturable) crashes the engine before bestmove on O pos 1 (`w1_ctrl/C_full.txt` empty, runner "engine closed output"). The counter fires before any crash.

Every check id can fire and every "0 failures" in §2 is therefore meaningful.

## 4. Findings

### 4.1 Known answers (a)(b)(c) — verified in the trees

- (a) `FORGE_SDK_BADCAP_PREFIX` 0→1: kF `src/search.cpp:24` (`#define FORGE_SDK_BADCAP_PREFIX 1`, rationale comment :19–23); the four r15d `#if FORGE_SDK_BADCAP_PREFIX` blocks are at r15d `src/search.cpp:725-730, 769-773, 846-854, 1023-1027` — in kF they sit at 856/921/999/1226 (shifted by the stacked pieces). Reproduce: `grep -n FORGE_SDK_BADCAP_PREFIX src/search.cpp`.
- (b) `struct alignas(64) TTCluster`: r15d `include/forge/search.hpp:128`, kF `:131`; allocation `make_unique<TTCluster[]>` r15d `src/search.cpp:450`. Reproduce: `grep -n "alignas(64)" include/forge/search.hpp`.
- (c) `FORGE_SDK_SEE_HOIST 1`: r15d `src/board.cpp:13-14` (`#ifndef`/`#define`), so the `#else` see_ge copy never compiles — confirmed the define is not overridable by the build flags used (`-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1` only). Reproduce: `sed -n '12,16p' src/board.cpp`.

### 4.2 Step 1 table — every invariant, where it lives in kF, how it is guaranteed, which check covers it

"Every path?" = the check sits on the single funnel all uses pass through (or the invariant is structural/compile-time).

| piece | invariant (README numbering) | kF anchor | every path? | guaranteed by | check id |
|---|---|---|---|---|---|
| 01 S4 (badcap prefix) | 1: per-Worker scratch, one stage generated to completion before recursion | `search.hpp` picker members; `search.cpp:856,921,999,1226` | structural (single thread per Worker) | code reading + identity rows | W1/W3 row equality |
| 01 S4 | 2: `bad_count_ <= index_` at the prefix store | `src/search.cpp:856` block | yes — single store site | C01, 3.5M checks, 0 fails; ctrlA catches break | C01 |
| 01 S4 | 3: `Move::none()` tie-fallback preserves selection order | `src/search.cpp:1571` `generate_evasions` | yes (row equality over 583+30 positions exercises evasions) | W1/W3/W4 identity | row equality |
| 02 S5 | 1: `key_after()==true` ⇒ child_key == exact post-move key (EP/castling rules) | `include/forge/board.hpp:209,211`; `src/board.cpp` make_move | yes — checked on every precomputed make_move | C02, 69M checks, 0 fails; ctrlB; W3 EP/castling FENs | C02 |
| 02 S5 | 2: invalid `king_lines_` never read before refresh | `src/board.cpp` unmake/null paths | structural | reading + row equality | — |
| 03 S5_assert | `dbg_key` assert compiles out under NDEBUG | `src/board.cpp` `#ifndef NDEBUG` blocks | yes (Release build, NDEBUG defined — `step0/compiler.txt` build log) | compile-time | — |
| 04 S7 | 1: `is_uci_ws` == istringstream whitespace | `src/uci.cpp` (PositionCache :43, `apply_position_sv` :67) | yes for all UCI input | runner input logs replay exactly; row equality | — |
| 04 S7 | 2: prefix cache replay == fresh replay | `src/uci.cpp:43-67` | exercised by every runner search (200–353 `position` commands/run) | row equality across 1,700+ searches | — |
| 04 S7 | 3: memset == value-init for flat POD tables | `src/search.cpp:1690-1697` | yes | POD types + row equality | — |
| 05 G1 | 1: `(P|R|Q)!=0` ⇒ dead_material false | `include/forge/eval.hpp:54` | structural (endgame set has none of P/R/Q) | reading | — |
| 05 G1 | 2: `corr_mat_idx` propagation matches `material_key & mask` | `include/forge/search.hpp:536`; `src/search.cpp:1823,1870,1899,1902,1970` | yes — checked in `corrected_eval` | C05, 82M checks, 0 fails (also with net768: 34.3M) | C05 |
| 06 G2 | 1–2: no-recapture exit + unified attacker init bit-exact | `src/board.cpp:13-14` (`FORGE_SDK_SEE_HOIST 1` active path) | yes (only compiled see_ge) | row equality; C01 depends on SEE split ordering too | row equality |
| 07 G3 | 1: off-ray pawn ⇒ legal (`has_legal_move`) | `src/board.cpp:847,855-856` | yes | row equality; W3 king-only-move FENs | row equality |
| 07 G3 | 2: pawn-attacked / king-adjacent evasion squares illegal | `src/board.cpp` `generate_legal_evasions` | yes | W3 double-check/king-only FENs, row equality | row equality |
| 07 G3 | 3: `known_gives_check==0` ⇒ `compute_checkers()==0` | `src/board.cpp:1283-1285` (kF), instrumented in kFcount | yes — every such make_move | C04, 62M checks, 0 fails; ctrlC | C04 |
| 08 G4 | 1: net pointers invariant during search (options stop search first) | `src/search.cpp:3141` snapshot, `:1755,1757,1826,1834,1877` uses | structural | uci.cpp stop-before-mutate; reading | — |
| 08 G4 | 2: direct `king_square` == dirty-replay squares | `src/search.cpp` `static_evaluate_v3` | yes on v3 path | W4 net768 row equality (42.6M-node rows identical) | row equality |
| 08 G4 | 3: skipped zero-init fully overwritten | `src/nnue_v3.cpp` `prepare` | yes | W4 net768 equality | row equality |
| 09 W1 | 1: lazy LesserThreats bit-identical | `include/forge/search.hpp:649,653-669` | yes | row equality | row equality |
| 09 W1 | 2: fused generation == fill_pseudo_legal order | `src/search.cpp:1233,1346` (`FORGE_SPD_NO_ZERO_MOVELISTS` blocks :984,1001,1020,1237) | yes | row equality incl. W3 promotion/castling FENs | row equality |
| 09 W1 | 3: QuietMoves pin-legality/gives_check exact | `src/search.cpp` `MovePicker::next` | yes | row equality; C04's caller side same data | row equality |
| 10 W2 | `kZeroContRow`/1D rows == base_to bit-for-bit | `src/search.cpp:1364,1375,1387` | yes | row equality | row equality |
| 11 stop hot | fast stop == `(stop || local_nodes_ >= node_limit_)` | `include/forge/search.hpp:676,735`; `src/search.cpp:3386` | yes — every fast-stop test | C11, 4,000,302 checks, 0 fails (reached only via node-limited W2) | C11 |
| 11 | `[[gnu::hot]] apply_position_sv` | `src/uci.cpp:67` | structural | compile-time attribute | — |
| 12 v3 refresh fuse | one-refresh eval == refresh+evaluate | `src/search.cpp:3909`; `src/nnue_v3.cpp:902`; `include/forge/nnue_v3.hpp:221` | yes on v3 path | W4: net768 rows identical between r15d-era rows (sol3 C2 known answer) and kF/kFcount | row equality |
| 13 TT AVX-512 | cluster 64-aligned | `include/forge/search.hpp:131` (`alignas(64)`), alloc `src/search.cpp` make_unique | yes — every probe | C13a, 111M checks, 0 fails | C13a |
| 13 TT AVX-512 | fast probe/store == scalar | `include/forge/search.hpp:226,235,237,240-248`; call `search.hpp:681,686,689` | yes — every probe | C13b, 111M checks, 0 fails | C13b |
| tidy | dead code removal changes nothing | stack patch | structural | whole-tree sha + row equality | — |

### 4.3 W2 node-count detail (worth reading)

The runner reads the engine's last periodic `info` line; under `go nodes 20000` the last printed info is below the budget, so "searches with last-info nodes == 20000" is 0/200 for all three builds (identically). But C13a checks on kFcount = **exactly 4,000,000 = 200 × 20,000** — one TT probe per node proves every search ran to exactly 20,000 nodes of work and the fast stop (piece 11) cuts at the budget. C11 checks 4,000,302 (≈ nodes + one per search) confirm the stop condition itself. r15d and kF agree per-position on nodes and best moves 200/200.

### 4.4 Prediction score card (commit 21:16:51, before W2–W4)

- W2 equality 200/200: correct. C11 reached only by W2: correct. C11 fails 0: correct.
- "≥195/200 at exactly 20000": wrong as literally written (runner-visible count is 0/200 — a measurement artifact), right in substance (C13a proves 200/200 ran exactly 20,000 nodes). Flagged honestly in the prediction file itself as a guess.
- W3: 30/30 three-way equality, fails 0, C04-per-node lower on check-heavy positions (measured: underpromos 0.52–0.68, double checks 0.71–0.76 vs set average 0.94): all correct.
- W4: bench pins, G rows == sol3 C2, C05 reached with net (33.7M checks, ratio 0.79 vs W1's 0.85), fails 0: all correct.

### 4.5 Suspicions, not proven

- ctrlC's d12 crash (king capture → UB after its own planted fault) means the O-set control run dies mid-set; for ctrlC the per-position d8 evidence (`w1_ctrl/C_manual.txt`) is the clean proof. Not a kF bug — a consequence of the planted fault.
- C13a checks are not always == node count (W1-O exactly equal, W1-G 0.998×, W3 1.17×). Probes per node vary by path (qsearch/root handling); I did not map which node classes skip or double the probe. No failure implication.
- `info`-line node undercounting under `go nodes` (§4.3) is inferred from C13a arithmetic, not from engine source reading of the print logic.

## 5. From my colleagues

- deepseek5: read `NOTES_deepseek5.md` and newest report (t23) on `for-fable-and-opus/deepseek5-work`. Applied: (1) the "prove the checker with a planted fault and read WHY it fires" discipline — controls A/B/C do exactly this, and I recorded which invariant each fault maps to; (2) his warning that on/off options accept only `true`/`false` — all option files use words, and every run's input log proves arrival (`w*/…_input.log`); (3) `ucinewgame`+`isready` between positions — the runner does this. Checked: my W3 position set validation (`w3_check.py`) follows his known-answer style (every FEN hand-checked, BAD=0).
- glmflash5: branch `for-fable-and-opus/glmflash5-work` does NOT exist (fetch failed 21:05 UTC). Nothing to read. Noted for Fable.

## 6. What I did NOT do

- No wall-clock speed comparison (the job is about identity + invariants; speed claims need the null-patch control discipline and were not asked for here).
- Did not run the W3 set under `go nodes` (W2 covers C11; W3 is depth-limited by design).
- Did not test Threads > 1 (all runs Threads 1, as the job's known answers assume).
- Did not re-verify carbon2's own oracle suites (job5–job13); this job's evidence is independent of them.
- The prediction file's internal "written 21:19" stamp is ~2 min off (written 21:15–21:16, committed 21:16:51); left as is, stated here.

## 7. What I am NOT sure about

- Whether `go nodes` last-info undercount (§4.3) is intended engine behavior or a reporting quirk — worth a look if fastchess ever measures node-limited games by info lines.
- C13a probe-per-node ratio variation (§4.5) is unexplained, though benign here.
- Whether C05 would stay reached at extreme correction-table sizes; only Hash 16 / default correction config was run.

## 8. A better way

The job's W2 measurement ("count searches ending at exactly 20000") via info lines cannot see the true final node count (§4.3). Better: have the runner parse the engine's final summary line if one exists, or make the counting build print `info string FINALNODES <n>` beside the INV lines (one-line addition next to the bestmove print). Then "exactly 20000" is measured directly instead of inferred from C13a. Check that it is better: run W2 again and compare FINALNODES==20000 count against this run's C13a-derived 200/200 — they must agree, and the new number needs no inference.
Second: ctrlC-style faults that destabilize into crashes would be cleaner to prove with a tiny fixed-position smoke script (like `w1_ctrl/C_manual.txt`) as the *primary* control and the full-set run as optional — same detection, no mid-set crash, 10× faster.

## 9. UTC stamps (start of run first)

- 21:04:11 cron trigger; 21:04:46 job 28 claimed + pushed (after checking handoff + work branch, no open younger claim)
- 21:05 colleague branches read (deepseek5 notes+t23; glmflash5 branch absent); job file 28 read, job 29 checked for corrections (none for 28)
- 21:06–21:09 step 0: trees verified (29/29 both), builds, all pins met; known answers (a)(b)(c) verified in trees; net768 regenerated, checksum 30ab43b4ba5db5f3 matched
- 21:09–21:13 W3 position set built + validated (BAD=0); counting build written; namespace bug (extern in `namespace forge` vs global definition) found and fixed; kFcount links
- 21:14:41–21:15:03 W1 first run (wrong: default options — my mistake, caught by sum mismatch)
- 21:15:09–21:15:26 W1 rerun with pc20.opt: exact match
- 21:15:37 controls A/B done; ctrlC runner crash diagnosed (planted fault → king capture UB; C04 counter proven on d8 positions)
- 21:16:51 prediction commit pushed ("kimi5 job 28 prediction")
- 21:16:58–21:17:06 W2 (three builds); 21:17:17–21:17:18 W3; 21:17:42–21:18:29 W4 rows; bench pins 882074/4275906 matched before that
- 21:19–21:27 evidence files + job folder assembled; report written

## 10. Model name

Kimi K3 (kimi-k3), run "kimi5" job 28.
