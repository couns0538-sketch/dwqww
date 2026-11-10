# opus_smp_layout — REVIEW_LOG

Policy: AGENTS.md (recovered verbatim with `git show 3e900941:AGENTS.md`, md5 94169aefef79ccb69c21f8f2c86298f0; absent from d4f4312). One focused reviewer subagent per milestone. The main agent assesses every finding, fixes the confirmed ones, has substantive fixes rechecked, keeps the reviewed hashes frozen, and records findings, dispositions and rechecks here. Independence: the reviewer is a `fable` subagent (claude-fable-5-1, max effort) in a separate context. It reads only the frozen commit through git and gets no conclusions from the main agent. It is the same vendor family, so the review is recorded as **partially independent**, not an independent human review.

| round | Vienna | reviewer | frozen scope | report | outcome |
|---|---|---|---|---|---|
| R1 | 19:25-19:39 | fable `smp-reviewer` (read-only, nothing built) | `7ce10a05..893b78d` (engine, tests, CMake, CI) + SPEC/INVENTORY/tools | `logs/review/R1_smp.md` | **no BLOCKER, no MAJOR**; 3 MINOR, 4 NIT |
| R1-recheck | pending | same agent (SendMessage) | fix commit | pending | pending |

## R1 findings and dispositions
| id | severity | finding (file:line in 893b78d) | disposition |
|---|---|---|---|
| MINOR-1 | MINOR | `Worker::tt_lockless_` (search.hpp:493) is set only in `Searcher::search` (search.cpp:1956) and survives a mode toggle. A direct `Worker::search` (the `SearcherTestProbe::run` pattern of rule50_tests) after `set_tt_lockless(false)` would call `probe_lockless` on a null array. Latent: no shipped path does this | **FIXED**: the per-worker flag is removed; `probe_tt`/`store_tt` read the table's own `lockless_` (quiescent-only writes). Regression test `direct_worker_after_toggle()` in `smp_lifecycle_tests.cpp` (both toggle directions, result = a fresh legacy searcher) |
| MINOR-2 | MINOR | the positive control prints INCONCLUSIVE but never fails (tt_lockless_tests.cpp:345-351), so a blind fixture would stay green | **FIXED**: with ≥ 2 hardware threads, `control_hits > 100000 && control_bad == 0` is now a failing check. On 1 hardware thread it is still INCONCLUSIVE (tearing can legitimately be absent there) |
| MINOR-3 | MINOR | `set_lockless` frees the old array before allocating the new one (search.cpp:476-477). An allocation failure would leave a null array in the active mode | **FIXED**: allocate first (local), then move-assign, then release the old array, as in P's `resize` |
| NIT-1 | NIT | CI builds only macro 1 (run_ci.sh:21), so a macro-0 typo would be caught only by the kit | **FIXED**: release mode also builds the default configuration (`FORGE_SMP_LAYOUT` OFF), checks its pins with `uci_check --full` and checks that it does not advertise `TtLockless` |
| NIT-2 | NIT | no Linux UCI evidence of the ON path | **FIXED**: `uci_check.py` takes an optional `--opt Name=Value` (absent = old behaviour). Release mode runs `--full --opt TtLockless=true` on the macro-1 exe and checks that it advertises `TtLockless type check default false` |
| NIT-3 | NIT | double dispatch in the gate build with the option off (`lockless_` tested in probe_tt and again in probe) | **acknowledged, not changed**: correct and predictable. Speed belongs to QA's timing, and the advisory numbers are in BENCH §6 |
| NIT-4 | NIT | STATUS.md at 893b78d said "no code yet" | **already fixed** in later commits (1a43ba9 onward) |

Reviewer notes taken over into the evidence:
- This branch is the **first Linux CI / TSan run of the trial_w6 tree** (trial_w6's own defaults cannot build at x86-64-v3 because of the `NNUE_ZMM` `#error`). A TSan report there could have come from trial_w6 itself: there was none.
- CI release with `-DFORGE_SPD_NNUE_ZMM=0` hit all pins (bench d11-22, perft), so that CI-only override is node-identical where measured.
