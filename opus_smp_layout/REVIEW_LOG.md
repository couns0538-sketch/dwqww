# opus_smp_layout — REVIEW_LOG

Policy: AGENTS.md (recovered verbatim with `git show 3e900941:AGENTS.md`, md5 94169aefef79ccb69c21f8f2c86298f0; absent from d4f4312). One focused reviewer subagent per milestone. The main agent assesses every finding, fixes the confirmed ones, has substantive fixes rechecked, keeps the reviewed hashes frozen, and records findings, dispositions and rechecks here. Independence: the reviewer is a `fable` subagent (claude-fable-5-1, max effort) in a separate context. It reads only the frozen commit through git and gets no conclusions from the main agent. It is the same vendor family, so the review is recorded as **partially independent**, not an independent human review.

| round | Vienna | reviewer | frozen scope | report | outcome |
|---|---|---|---|---|---|
| R1 | 19:25-19:39 | fable `smp-reviewer` (read-only, nothing built) | `7ce10a05..893b78d` (engine, tests, CMake, CI) + SPEC/INVENTORY/tools | `logs/review/R1_smp.md` | **no BLOCKER, no MAJOR**; 3 MINOR, 4 NIT |
| R1-recheck | 19:49 start, not finished | same agent (SendMessage) | fix commit `0599271` | none: the fable subagent became unreachable after its start (`fable`/`opus-max` agent types disappeared from this session; "failed to write to smp-reviewer's inbox"). The user's CLAUDE.md allows only those two types, so no substitute reviewer was spawned. WORKER_BOARD line 20:22 records this | replaced by **SR1, a structured self-review, NOT independent** (below) |
| SR1 | 20:22-20:30 | main session (Opus 5.5), **NOT independent** | `893b78d..0599271` (+ the CI hardening after it) | this file | the fixes hold; 1 new NIT in my own CI addition, fixed |
| R2 (bug hunt) | 21:12 start | fable bug hunter (see note), read-only, nothing built. **Partially independent**: it read the code through git and derived its own checks | `7ce10a05..0599271`, then `527a696` (enc2), then the enc3/enc4 working tree, then commit `a675c04` | `logs/review/R2_bughunt_FINDINGS.md` (copy of `out\hunt_agent\FINDINGS.md`) | **no BLOCKER, no MAJOR, no MINOR**; 6 NIT, all fixed in `a675c04`; identity of enc2/enc3/enc4 confirmed line by line; the tag census reproduced independently (F47) |

Note on R2's agent type: on 2026-11-09 the user asked for "a fable subagent that hunts for bugs". The `fable` agent type was not available in this session, so the hunter runs as a general-purpose agent with model **fable** (claude-fable-5-1). That keeps the user's rule of fable-only subagents, at one bug hunter at a time. Its WORKER_BOARD start line says 20:12; that is GMT, i.e. 21:12 Vienna, as the board's 21:31 line notes.

## R2 findings (fable bug hunt) and dispositions
| id | severity | finding | disposition (`a675c04`) |
|---|---|---|---|
| NIT-1 | NIT | CI's `--opt TtLockless=true` pins cannot tell an applied option from an ignored one (an unknown setoption name is silently ignored) | **FIXED**: `opus_round1/opus2_smp/liveness_check.py` (port of `tools/liveness_check.ps1`) runs in release CI. The toggle must empty the table exactly as Clear Hash does, lockless = legacy cold and warm, and both engines must exit 0. Negative control: on the parent exe (option unknown) it FAILs (b3 = 3,373 warm nodes instead of 35,964); on the gate exe it PASSes with the PS tool's numbers |
| NIT-2 | NIT | `check_known_failures.py` would stay green if the pack tests were never built | **FIXED**: `require_pack_tests` in `run_ci.sh` (release, asan, tsan) requires `forge_tt_lockless_tests` and `forge_smp_lifecycle_tests` to show `Passed`. While fixing it, my first version ran the function inside a `\| tee` pipeline, a subshell where `status=1` is lost. It now tees inside and is called without a pipe. Regex checked on a real ctest log |
| NIT-3 | NIT | `uci_check.py` ignored the engine exit code | **FIXED**: `ok &= returncode == 0`, printed |
| NIT-4 | NIT | `tt_microbench` without NDEBUG would trip `assert(has_exclusive_access())` on the owned legacy path | **FIXED**: `#error` unless NDEBUG, with the reason in the source |
| NIT-5 | NIT | "P[collision] ≤ 2^-31 per pair" is the random-multiplier bound, not a per-pair bound for the fixed multiplier | **FIXED**: exact rule in search.hpp and SPEC 3.3 (2^33 − 2 bad deltas, density 2^-31, `c(delta)`); `tag_scan` part 4 implements the suggested combined-delta census (BENCH §9) |
| NIT-6 | NIT | `identity_check.ps1`'s hashed body leaves out the engine exit state | **FIXED**: the summary line prints `engine exit ok=…` and the tool exits 1 if the engine did not exit. Body hashes unchanged, so the references stay comparable |
| NIT-7 (on `a675c04`) | NIT | `tag_scan` part 4 counts (score, eval) field-difference labels, not distinct deltas: through the uint16 wrap one stored delta can carry two labels. The minima and the density are unaffected | **FIXED** after `a675c04` (tool output and BENCH §9 now say "labels"; re-run log `logs/enc4/tag_scan.txt`). Code only in the tool, not in the engine |

R2 on `a675c04` (hunted 21:45-22:05 Vienna):
- The raw-word store equals `store_body`, including the padding byte and the no-rewrite path.
- tag_scan part 4's two-residue derivation and its decomposition are exact (its output matches a uniform-density estimate of about 102,900).
- The new CI bash (`require_pack_tests` status propagation, regex) and `liveness_check.py` are sound.
- NITs 1-6 are verified closed.

## R1 findings and dispositions
| id | severity | finding (file:line in 893b78d) | disposition |
|---|---|---|---|
| MINOR-1 | MINOR | `Worker::tt_lockless_` (search.hpp:493) is set only in `Searcher::search` (search.cpp:1956) and survives a mode toggle. A direct `Worker::search` (the `SearcherTestProbe::run` pattern of rule50_tests) after `set_tt_lockless(false)` would call `probe_lockless` on a null array. Latent: no shipped path does this | **FIXED**: the per-worker flag is removed; `probe_tt`/`store_tt` read the table's own `lockless_` (quiescent-only writes). Regression test `direct_worker_after_toggle()` in `smp_lifecycle_tests.cpp` (both toggle directions, result = a fresh legacy searcher) |
| MINOR-2 | MINOR | the positive control prints INCONCLUSIVE but never fails (tt_lockless_tests.cpp:345-351), so a blind fixture would stay green | **FIXED**: with ≥ 2 hardware threads, `control_hits > 100000 && control_bad == 0` is now a failing check. On 1 hardware thread it is still INCONCLUSIVE (tearing can legitimately be absent there) |
| MINOR-3 | MINOR | `set_lockless` frees the old array before allocating the new one (search.cpp:476-477). An allocation failure would leave a null array in the active mode | **FIXED**: allocate first (local), then move-assign, then release the old array, as in P's `resize` |
| NIT-1 | NIT | CI builds only macro 1 (run_ci.sh:21), so a macro-0 typo would be caught only by the kit | **FIXED**: release mode also builds the default configuration (`FORGE_SMP_LAYOUT` OFF), checks its pins with `uci_check --full` and checks that it does not advertise `TtLockless` |
| NIT-2 | NIT | no Linux UCI evidence of the ON path | **FIXED**: `uci_check.py` takes an optional `--opt Name=Value` (absent = old behaviour). Release mode runs `--full --opt TtLockless=true` on the macro-1 exe and checks that it advertises `TtLockless type check default false` |
| NIT-3 | NIT | double dispatch in the gate build with the option off (`lockless_` tested in probe_tt and again in probe) | **acknowledged, not changed**: correct and predictable. Speed belongs to QA's timing, and the advisory numbers are in BENCH §7 |
| NIT-4 | NIT | STATUS.md at 893b78d said "no code yet" | **already fixed** in later commits (1a43ba9 onward) |

## SR1 structured self-review of the fix commit `0599271` (NOT independent)
| check | evidence | result |
|---|---|---|
| MINOR-1 gone everywhere | `git grep tt_lockless_ 0599271 -- include src tests tools`: only the test file's name. `lockless_` is assigned only in `set_lockless` (search.cpp:485, quiescent) and by its default member initialiser. probe_tt/store_tt read `shared_.tt.lockless_` (friend access) | OK |
| MINOR-1 regression | `direct_worker_after_toggle()`: both toggle directions, direct `Worker::search` result and visited nodes = a fresh legacy searcher; PASS natively, and under TSan in CI 42677341394 | OK |
| MINOR-2 gate | tt_lockless_tests.cpp:355-360: fails only for ≥ 2 hardware threads, > 100k hits and 0 incoherent. Observed incoherent counts: 500,206 (CI TSan) and 0.84M-2.46M (native, 4 runs), far from the threshold | OK, not flaky on these machines |
| MINOR-3 order | set_lockless: `make_unique` into a local, move-assign, then reset the other array; `lockless_`, `generation_` and `epoch_` change only after both succeed | OK |
| NIT-1/2 in CI | run 42677341394 release `identity.log`: macro-1 pins ALL OK; `--opt TtLockless=true` pins ALL OK; macro-0 build pins ALL OK, no TtLockless option; macro-1 advertises `TtLockless type check default false` | OK |
| new: uci_check.py `--opt` | backward compatible: no `--opt` means the old behaviour, and the exe stays argv[1]. The `--full` test uses `in sys.argv`, unaffected | OK |
| **new NIT (own CI addition)** | the advertisement checks piped `forge` into `grep -q` under `pipefail`. An early grep exit could let the engine's SIGPIPE decide the pipeline status (harmless here because the output is tiny, but fragile) | **FIXED** after 0599271: the uci output is captured into variables first, a non-zero engine exit is a FAIL of its own, then grep runs on the variable |
| test-binary ODR | `forge::SearcherTestProbe` is defined in each test executable separately (rule50, tests, smp_lifecycle); every CTest target is its own executable linking `forge_core` | OK |
| macro 0 after the fixes | `pp_identity.ps1` (fix1_macro0): all 8 units IDENTICAL. Kit s0c = s0d = 4181a589 | OK |

Reviewer notes taken over into the evidence:
- This branch is the **first Linux CI / TSan run of the trial_w6 tree** (trial_w6's own defaults cannot build at x86-64-v3 because of the `NNUE_ZMM` `#error`). A TSan report there could have come from trial_w6 itself: there was none.
- CI release with `-DFORGE_SPD_NNUE_ZMM=0` hit all pins (bench d11-22, perft), so that CI-only override is node-identical where measured.
