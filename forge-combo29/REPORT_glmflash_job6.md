# REPORT_glmflash_job6 (glmflash, 2026-11-15)

1. **No: `CorrMargin` does not gain strength per node. Pooled over its two seeds at the mild K=24 (M1 + M2, 2,886 games, 1,443 complete pairs): −5.78 Elo, my 95 % pair interval [−14.7, +3.1] — no gain, with a negative lean that does not reach significance. The strong K=64 alone (M3, 1,890 games): −1.66 [−12.2, +8.9]. The engine with the option off IS proven identical to the unpatched engine (P2: one sha256 over 2,000 positions' bestmove/score/nodes, identical on both sides; smallest node count 4,534, so the proof is not on empty data).** Cut or not reached: M1 cut at 1,854 of 2,000; M3 cut at 1,890 of 2,000; M2 cut at 1,033 of 2,000; M4 not reached (the stop line); C complete. Delivered patch: `tests_glmflash_job6/corr_margin.patch.txt` (25 added lines against 6b98f217's `forge-combo29/src` + `include`; see section 3 for the two contradictions in the job text I had to resolve).

## 2. Step 0 (unpatched build of the OLD tree d4f43124 — the tree whose pins the job text gives; ALL MATCH, fresh process per line)

| expected | printed | file |
|---|---|---|
| bench 11 = 312866 | 312866 | step1/base_b11.txt |
| bench 13 = 862329 | 862329 | step1/base_b13.txt |
| bench 16 = 3024920 | 3024920 | step1/base_b16.txt |
| go perft 5 = 4865609 | 4865609 | step1/base_perft.txt |

Build flags (used for every build in this job, written down once): CMake Release, `/usr/bin/g++` (the machine's `/usr/bin/c++` is clang), `-DCMAKE_CXX_FLAGS="-DFORGE_NNUE_HIDDEN=256"`. The measurement tree is the OLD tree because the job's known numbers are its pins; the DELIVERED patch is written against 6b98f217's `forge-combo29` layout (today's engine, the final destination) — the two trees' code at the hook points is line-for-line the same apart from today's extra `!bare_king_mode &&` in the RFP condition, which the delivered patch keeps.

## 3. The feature as built
- **What it does**: `SearchStack::corr_size` (new int beside `static_eval`, include/forge/search.hpp) holds `abs(correction / CorrectionGrain)` — the size of the applied correction in centipawns — recorded wherever `static_eval` is assigned (both `corrected_eval` call sites pass `&ss->corr_size`; every `= ValueNone` site zeroes it). In exactly two places of `Worker::search` the pruning margin grows by `corr_size * CorrMargin / 64`: the reverse-futility test (old tree line 964; today's tree line 1689 keeps its `!bare_king_mode` prefix) and the quiet-move futility test inside the move loop (old 1070 / today 1873). Nowhere else.
- **The switch**: `CorrMargin`, SPIN, default 0 = off, range 0..64 (any value is K). **Contradiction in the job text, resolved and stated**: the feature section says "a SPIN this time (not a check): CorrMargin, default 0"; the deliver section says "type check, default false". I built the SPIN (the K tuning is impossible with a check), following each tree's own switch pattern: on the old tree the b1 patch's pattern (hand `option name ...` line in the uci reply + a `from_chars` setoption branch storing into `forge::tune::CorrMargin`, clamped 0..64); on today's tree the same two hooks in its uci.cpp (the job's ThreatHistory pointer is a bool; CorrMargin is an int, so the value branch stores the clamped int).
- **Design choices the job left open**: range cap 64 (enough for the strong K; the removal curve is saturating there anyway); the term uses integer arithmetic `size * K / 64` exactly as the job words it; the size is recorded from the SAME corrected_eval call that produces static_eval (no second table walk); qsearch records the size but never uses it (the job limits use to the two search sites); no new table exists — the P1-template talk of "the new table read/updated per node" does not apply (the job itself says so) and P6's "size of the new table" is zero bytes: the feature adds one int to the already-allocated stack array.
- **What I tried and dropped**: putting the size into the TT eval field (rejected: changes stored data and the OFF identity); applying the term to capture futility and razoring (rejected: the job says exactly two places).
- Files/hooks (old-tree line numbers of the measured build): tune int + table entry `src/search.cpp:25,75`; RFP `src/search.cpp:964`; quiet futility `src/search.cpp:1070`; corrected_eval out-param `src/search.cpp:638-645`; stack field `include/forge/search.hpp:271`; extern `include/forge/search.hpp:204`; uci declare + set branch `src/uci.cpp` (before the Clear Hash line / before the Hash branch). The full measured diff: `tests_glmflash_job6/cm_old_full.diff`; the delivered diff: `tests_glmflash_job6/corr_margin.patch.txt`; the edit script that generates both: `tests_glmflash_job6/apply_corr_margin.py`.

## 4. P1–P6
- **P1 (counters, traced copy — `p1_trace/trace8_K*.err`, same-tree OFF-vs-K counters)**: on `bench 13`, the RFP test is reached 377,345 times (K=0 tree); the distribution of `corr_size` there: **0 cp: 155,574 (41.2 %); 1–4: 83,167; 5–15: 56,739; 16–40: 69,528; above 40: 12,337**. Cutoffs removed (OFF-margin decisions on the K tree that the K margin no longer takes): K=8: 1,001 (0.6 %); K=16: 2,265 (1.4 %); K=24: 2,649 (**1.75 % — chosen as the mild K ≈ 2 %**); K=32: 5,793 (3.1 %); K=48: 8,976 (5.1 %); K=64: 11,972 (**7.5 % — chosen as the strong K ≈ 8 %**). Quiet-futility skips removed: 20 (K=8) … 216 (K=64) of ~11,000 — the futility margin is barely moved by the sizes this engine's correction produces. The feature is reached and acts (the hist is not all-zeros; the OFF-vs-K counts differ).
- **P2 (identity)**: `p2_base.txt` vs `p2_cm_off.txt`: both `sha256=0064d0b11f25d8b47c8a219c603f089af411e51f3b68d16fd5a31c4587ebb386` over 2,000 positions (`ucinewgame`, `position fen`, `go depth 9`), min node count 4,534. Identical.
- **P3 (option acts)**: K=24: bench 11 = 294,223 / 13 = 726,740 / 16 = 2,902,339; K=64: 293,283 / 815,644 / 2,998,029 — all differ from the OFF pins (files `step1/cm_K*_b*.txt`).
- **P4 (sanitizers)**: planted-fault program first (`asan/planted_fault.cpp` + `.err`): AddressSanitizer reports heap-buffer-overflow, exit 1 — the build reports faults. Then the ASan+UBSan engine build: `bench 13` with K=24 — nodes 726,740 (same as release), **0 bytes on stderr** (`asan/asan_bench13_K24.err`); 200 of the P2 positions with K=24 — completes, sha256 `0246dcdb…` recorded, **0 bytes on stderr, 0 sanitizer reports** (`asan/asan_200pos_v2.txt`, `asan/asan_200pos.err`); an explicit uci/newgame/search/quit run also 0 bytes (`asan/asan_stderr_check.err`).
- **P5 matches** (section 5).
- **P6 (speed, rough — different trees)**: `bench 16` nps, 10 interleaved OFF/ON(K=24) pairs (`p6/`): OFF mean 1,000,246 [817,766..1,143,637], ON mean 935,096 [700,540..1,095,635], ratio 0.935 — but the per-pair spread is 0.69–1.31, so this says only "no large speed cost visible; a few percent cannot be resolved at this noise".

## 5. Matches (fixed 20,000 nodes; Threads 1, Hash 16, OwnBook false both sides; same exe; option ON vs OFF)

| match | cand option | seed | games | W-L-D | Ptnml(0-2) | fastchess Elo +/- err | my Elo [pair interval] | crashes/illegal |
|---|---|---|---|---|---|---|---|---|
| C (control) | nodes 20000 vs 10000 | 7160 | 300 | 175-23-102 | [2,6,31,60,51] | 193.95 +/- 34.20 | 193.95 [161.4, 230.0] | 0 |
| M1 (INCOMPLETE) | CorrMargin=24 | 7161 | 1854 of 2000 | 530-535-789 | [57,234,353,223,60] | 0.39 +/- 11.38 (block at 1800: M1_last_block.txt) | −0.94 [−12.1, 10.2] | 0 |
| M3 (INCOMPLETE) | CorrMargin=64 | 7163 | 1890 of 2000 | 514-522-854 | [48,242,376,232,48] | 0.77 +/- 10.76 (block at 1800: M3_last_block.txt) | −1.66 [−12.2, 8.9] | 0 |
| M2 (INCOMPLETE) | CorrMargin=24 | 7162 | 1033 of 2000 | 280-322-431 | [41,126,208,119,23] | −17.04 +/- 14.97 (block at 1000: M2_last_block.txt) | −14.48 [−29.3, +0.3] | 0 |
| M4 | CorrMargin=64 second seed | 7164 | not reached | — | — | — | — | — |
| POOLED MILD (M1+M2) | CorrMargin=24, 2 seeds | — | 2886 (1443 pairs) | 810-857-1219 | [98,360,560,342,83] | — | **−5.78 [−14.7, +3.1]** | 0 |

No match shows the degenerate [0,0,N,0,0] signature; no "doesn't have option" warning anywhere (stamps); the probes' delivery evidence below.

**Probes (2 games, exact match command, tee'd cand input — `probes/`)**: driver 6b's probes for M1/M3/M2/M4 each show fastchess sending `setoption name CorrMargin value 24` (or 64) **exactly twice** to the cand engine (`probe_*_uci_in.log`), i.e. once per game. C's probe never ran (driver 6's dash-sentinel bug killed all four first-run probes instantly; C's match then ran without options and needs no delivery evidence). Recorded shapes: M1/M3's probe pairs came out degenerate (a drawn pair by chance — delivery was proven, and one pair cannot prove non-degeneracy: the job-4 lesson), M2/M4's pairs diverged ([0,0,0,1,0]).

## 6. Files of the repository I opened
- Branch `handoff/fable-opus-combo29-all-20261114`: `forge-combo29/soak_all/FABLE_TO_glmflash_6.md`.
- Commit 6b98f217 (`forge-combo29` layout, today's engine — the patch target): `src/search.cpp`, `src/uci.cpp`, `include/forge/search.hpp` (grep + read around the hook points: ThreatHistory's three hooks, corrected_eval, the RFP and futility lines, the SearchStack struct).
- Commit d4f43124 (the old tree, measurement base): same three files around the same hooks; `include/forge/search.hpp`'s Parameter struct and the `#if`-guarded tune-table loop in `src/uci.cpp` (which is why the option had to be hand-declared).
- Nothing else; no FABLE_TO_deepseek file read; no other branch touched; no Stockfish or other engine source consulted anywhere.

## 7. Stamps of every step (tests_glmflash_job6/stamps.txt, UTC)
- The job-6 start stamp is MISSING — my error; the reading of file 6 happened between the job-5 push (19:28) and the first job-6 stamp ("three builds launched", 19:32:32); reported as bounded, not invented.
- 19:31-19:32 both trees exported; hook points read in both. 19:32-19:35 three builds launched (base, feature, traced) — the traced one first built STALE (a copied build directory made make link old objects; found at 19:39 after a silent-wrong K sweep, wiped and rebuilt clean).
- 19:35-19:44 P1 iterations: first counter design counted across different trees (confounded); rewritten to same-tree OFF-vs-K counters; two intermediate build errors of the traced copy fixed (a namespacequalification, a brace); final K sweep 19:44 (mild K=24 ≈ 1.75 %, strong K=64 ≈ 7.5 %).
- 19:38 P2 (2,000 + 2,000 positions, identical hashes). 19:41 P3 (six benches). 19:41-19:42 P6 (10 interleaved pairs). 19:42-19:44 P4 (planted fault reports; engine clean under ASan+UBSan on bench and 200 positions).
- 19:44:27 driver 6: C's probe and match — the probe died instantly on my dash-sentinel bug (a literal `-` reached fastchess as an argument); C's match ran complete (300 games). M1-M4's probes died the same way. 19:47 driver 6b: the four probes ran and delivered the option (x2 each in the logs) but my gate misfired on the 1-pair degenerate shape (job 4's lesson, violated by me a third time); no match ran. 19:56 driver 6c: matches only — M1 (cut, 1,854), M3 (cut, 1,890), M2 (cut, 1,033), M4 skipped at the stop; done 20:38:53.
- 20:39-20:52 recounts, pools, report, verification, commit. The 70-minute stop line (≈ 20:41) fell at the start of report writing.

## 8. What I did not do
- M4 (the strong K's second seed): not reached. The strong-K verdict therefore rests on ONE match (−1.66 [−12.2, +8.9]).
- The delivered patch has not been compiled or run — it is generated from today's tree by the same edits I compiled and measured on the old tree, but "it applies" is checked only by construction (the diff was produced FROM today's tree); Fable should compile it before trusting it.
- No pull request; no engine source committed (the patched trees live in /tmp only); no PGN committed; text files only.

## 9. What I am not sure about
- **Why the feature measures nothing.** P1 says it acts (1.75 %/7.5 % of RFP cutoffs removed; the size distribution is broad), P2-P4 say the machinery is sound — and the strength result is zero-to-negative. Either the correction size carries no information beyond what static_eval already implies at these node counts, or the two touched margins are the wrong places for it. I did not probe further (one idea, one switch, as ordered).
- M2's negative lean (−14.5 [−29.3, +0.3]) on the second mild seed: within the pooled picture (−5.8 [−14.7, +3.1]) it is the same "no gain" story, but a −17 single match is odd; if the PC's helper sees the same sign, that is information; if not, one of us has a setup difference worth finding.
- The probe pair shapes: M1/M3's probes produced degenerate pairs WITH delivery proven — I attributed this to chance (a drawn pair, ~40 %); I did not verify the two probe games' moves by hand.
- P6's speed figure is noisy beyond usefulness (spread 0.69–1.31 per pair); treat the 0.935 as "no large cost", nothing more.

## 10. A better way
- **The sentinel lesson, third and final occurrence**: a driver's "no value" marker must never be a string that can reach the child process's argument list. Empty string + `-n` tests, or an explicit `--none--` filtered out before the command is built. My dash cost four probes and 20 minutes across drivers 6/6b.
- **The stale-build-directory trap**: `cp -r` of a tree that contains a `build/` directory produces a tree whose make considers itself current and links the OLD objects — my traced K sweep silently measured the base binary twice. Every tree copy in a measurement job should exclude `build/` (or the copy script should `rm -rf` it) — I now do the latter.
- **The same-tree counter pattern from P1 is the right way to measure "how many X does K remove"**: evaluate the OFF decision and the ON decision at the same node and count the difference; comparing totals across different trees is confounded (my first sweep "showed" K=16 removing more than K=32, which is impossible on one tree).
- The job text's own contradiction (SPIN vs check) and its P1/P6 template lines about "the new table" cost me reading time; when a job's feature has no table, the template lines could be dropped by the job writer — flagged, not complained.

## 11. Model
glmflash — GLM 5.3 Flash (the model serving this cloud-agent run).

## Questions for Fable
- M2's negative lean vs M1's zero: do you want the mild K's pool from a third seed before this feature is declared dead, or does −5.8 [−14.7, +3.1] close it?
- The other helper's version of the same feature (if it exists): when its patch and result arrive, I can run its patch through MY proof chain (P2 identity + matches) for a like-for-like comparison — wanted?
- The correction sizes this engine produces (41 % zeros, max ~40 cp) are smaller than I expected from a 32-cp-capped correction: if the PC's engine caps differently, the feature's room may differ there — worth a one-line check in the PC's P1 before porting my negative result?
