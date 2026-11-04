# TOOLS - Opus 30-h job (branch opus-30h-20261103; copies under D:\o30\wt\opus_30h)

Every tool is own code. Python = `C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe -I -B` (numpy, torch
CPU, python-chess, psutil). Own processes run at Idle on CPUs 0-1 (lowrun.ps1 / the tools pin themselves). A tool that
does not pin itself runs through `bash opus_30h/tools/idle.sh <mask> <program> [args]` (pins its own bash via
`pin_pid.py`, fail closed exit 78; children inherit Idle + the mask); net_pack.sh and final_checks_o30.sh source it.

## Item A - v2 net path, data, training, packaging (`opus_30h/a/`)
| tool | what it is for | how to verify it |
|---|---|---|
| `v2port.patch` | the engine change: FORGENN2 v2 nets on the lock (UCI EvalFileV2, empty = off) | `pin_check.ps1 -Exe <exe> -Full` = lock pins; lock net as v2 (`o30_v2net.py from-lock`) + `-Expect` lock pins = PASS |
| `o30_v2net.py` | read / write / check FORGENN2 files; `from-lock` writes the lock net as a v2 file (same function); `random` writes test nets | `info <file>` exits 1 on any header / size / checksum problem |
| `v2_eval_o30.cpp` + `build_harness_o30.sh` | engine-side eval printer and accumulator walk (AVX2 / SSE / scalar builds) | `--walk <net> <seed> <games> <plies>` prints 0 mismatches |
| `o30_v2ref.py` + `parity_o30.sh` | independent float32 reference + exact comparison with the three engine builds, planted bug | `parity_o30.sh` prints PARITY PASS and "planted bug caught" |
| `o30_score.cpp` -> `D:\o30\tools_bin\o30_score_v2.exe` | the crew's S31 holdout metric with the engine's own v2 code; `--check-hce` compares the lock's HCE with the FHCE file | lock net as v2 on `holdout_013_014_s16` = b0.6 0.014310027 / b1.0 0.004572428 (the crew's AL1 numbers), hce_differs 0 |
| `o30_data.py` | data audit and training-set preparation (skip lists, jobA overrides, jobA val holdout, evidence JSON) | exit 0 only if jobA aligns 0 mismatches and Astra's mate list = the score rule; AUDIT.json totals |
| `o30_fit.py` | CPU fine-tune of a v2 net (torch, 1 thread): warm start from the lock net, residual target, resumable checkpoints, holdout scores per checkpoint, `stop` via a named event, `selfcheck` | `selfcheck` = the scorer's numbers on the S31 subset |
| `run_fit.sh`, `fit_bg.sh` | launchers (disk / RAM / supervisor checks; Idle + CPU mask; forward-slash paths) | log line with the checks; `fit_bg` prints the trainer's exit code |
| `net_pack.sh` | one step from a trained net to its evidence folder (copy, sha256, parity, holdout scores with per-row dumps, paired diff + z vs the lock net on S31 and jobA val, the offline rule's verdict, OFF / ON pins, RESULT.json) | exit 0 = every check passed (the rule verdict is recorded, not an exit condition) |
| `sanity_match.py` | fixed-length match candidate vs lock with fastchess (sanity only) | RUN_INFO.json + `gate_summary.py <dir>` |
| `net_final_checks.sh` | play-side checks of a packed net: 300 s smoke, NPS ABBA vs the lock, 400-game sanity match + gate_summary -> FINAL_CHECKS.json | exit 0 = smoke PASS and fastchess exit 0 |
| `make_net_index.py` | `D:\o30\nets\INDEX.md` for the crew queue from the per-net RESULT / FINAL_CHECKS / TRAINING json: a summary table (S31 / jobA paired diff and z, offline rule PASS / FAIL, pack checks, sanity line) + one section per net | final_checks_o30.sh check 12 re-hashes every cited file; render test `a/test_make_index.py` |
| `o30_paired.py` (+ `o30_score_v3.exe --dump`) | paired holdout comparison of two nets: mean difference, its standard error (measurement error of the row set), z | S31 SE ~1.5e-6, jobA SE ~1.6e-5 on the job's nets |
| `o30_breakdown.py <dump net> <dump lock> [--out new.md]` | where a net's holdout gain comes from: paired per-row differences grouped by output bucket, both kings' rank buckets, label size, game result (rows, mean, SE, z, share) | groups sum to the total (shares add to 100 %) |
| `o30_joba_old.py` | the jobA val positions with their ORIGINAL 5k-node labels (separates label-fitting from a position shift) | boards equal to jobA_val.pos (printed) |
| `prove_resume_fit.sh`, `fit_resume.sh` | trainer resume proof (interrupted + resumed run = uninterrupted run, bit for bit) / resume launcher | RESUME PROOF PASS (2026-11-03 19:01) |
| `forge_v2_bullet_o30/` + `build_bullet_o30.bat` + `bullet_residual.patch` | GPU path: R14's trainer with a residual `r` mode on a private copy of the trainer library (D:\o30\bullet) | mock + ROCm builds 0 errors; `rfeatures` + `check_rfeatures.py` = 0 mismatches vs o30_fit.py features |
| `export_v2r.py` | trainer-library checkpoint -> FORGENN2 residual net (KB map, mirror, OB8); `--make-test` writes a synthetic checkpoint | synthetic checkpoint -> engine parity 10000/10000 |
| `check_kbmap.sh <map> [mask]` | the proofs a king map needs before training with it (maps: one, rank4, rank4x2 = rank4 x board half, 8 buckets): lock net as that map = lock pins d11-d22, random net parity x 3 + planted bug, walk, trainer selfcheck | prints KBMAP <map> PASS |
| `o30_data_npy.py` | jobA overrides as plain .npy for the Rust reader | 988,336 rows written |
| `o30_runs.py` | one table of every CPU fine-tune run (config, last / best holdout losses vs the lock net, rate) | - |

## Item B - SPSA (`opus_30h/b/`)
| tool | what it is for | how to verify it |
|---|---|---|
| `o30_expose.py` -> `expose22.patch` | 22 more search constants as tune:: options, defaults = the lock's literals | pin_check -Full = lock pins; each option LIVE |
| `tune_spsa.py` + `tune_spsa.ps1` | the SPSA tuner (params CSV, fastchess pairs, per-iteration CSV, resume, thread cap / CPU mask / gate check, deadline, stop event, stop at the C: 30 GB / D: 51 GB floors) | `selftest_10min.ps1 -Out <new dir>` prints SELFTEST PASS; `b/test_disk_low.py` = DISK FLOOR CHECK PASS |
| `sim/test_spsa_sim.py [--cpus N]` (+ `sim/fake_fastchess.bat` / `.py`) | end-to-end simulation: the real tuner against a fake fastchess with a known optimum; checks direction (sign of W - L), option passing, PGN parsing, schedule, resume | SPSA SIM PASS (2026-11-03: A 100 -> 148 of 160, B 60 -> 21.1 of 20 in 1,000 pairs); run it on CPUs without another fastchess |
| `option_inventory.py <exe> [--depth --pin --only]` | every advertised search constant: bench moves when changed, = the pin at its default | INVENTORY PASS on the lock (41 / 41 at default; all live, 4 only deeper / with their feature / in piece-value steps) |
| `build_o30tuned.sh <TUNED_OPTIONS.txt> <run dir> <tag>` | from the session report to the checked one-switch exe (clone, patch, lint, kit pc1 = pc2, test_o30tuned) | last line O30TUNED EXE ... |
| `o30_tuned_patch.py` + `test_o30tuned.sh` | one UCI check `O30Tuned` (default false) that sets a whole tuned set (true) or the lock values (false) on an expose22 tree | `test_o30tuned.sh <exe> <TUNED_OPTIONS.txt>` prints O30TUNED PASS (OFF pins, switch = explicit list, true then false = lock, invalid value rejected) |
| `spsa_report.py` | report of a run: null-gradient sigma and z per parameter, convergence table at 10-100 %, SVG plot, TUNED_OPTIONS.txt / gate_options.txt | ran on selftest_2 |

## Shared (`opus_30h/tools/`, copies of R13-R15 tools with D:\o30 paths)
fresh_lock.sh, export_src.sh, kit_build_o30.sh (kit v2.3), kit24_build_o30.sh (kit v2.4 -PartialTraining; both honour
KIT_MAXMYCPU), plain_build_o30.sh, pin_check.ps1, smoke2m.py, selfplay_smoke.py, cleanroom_lint.py, pc_gate.ps1,
cpu_users.ps1, lowrun.ps1, run_pinned.py, gate_summary.py, abba.py, commit_span.py, doc_lint.py, hash_sweep.py.
Own additions: `idle.sh` + `pin_pid.py` (pin a shell and its children to Idle on a CPU mask, fail closed),
`publish_o30.sh` (copies TOOLS.md / FINAL_REPORT.md to `D:\o30\` with a provenance line, regenerates
`D:\o30\nets\INDEX.md`), `uci_conformance_o30.py` (below), `index_check_o30.py` (every INDEX.md net section: net
sha256 + md5 and exe sha256; a missing row fails), `path_sweep.py <docs> [--allow P]` (every cited Windows / branch
path exists).

## Kit v2.5 (`opus_30h/kit25/`, working copy `D:\o30\kit25`)
QA's kit v2.3 + R12's v2.4 + workload v2n (the training workload also benches the lock net written as a v2 file, so the
EvalFileV2 code gets a PGO profile). Wrapper `tools/kit25_build_o30.sh <repo> <tag>`; verify: pc1 = pc2 and the training
log's v2 benches = the v1 node counts. Gate exe of this job: ff856ba8 (v2 path ~1.0x the lock, advisory).

## Does it work in Forge like a GUI / the gate runner uses it?
| tool | what it is for | how to verify it |
|---|---|---|
| `tools/uci_conformance_o30.py <exe> [--opt N=V]... [--expect-info text] [--mask 0x2]` | one engine process through uci / setoption / isready / ucinewgame / go depth, movetime, wtime+btime, nodes, infinite + stop (no bestmove before stop), mate in 1, one legal move, checkmate and stalemate (0000), Threads 2, quit; legality by python-chess, time limits, empty stderr; OwnBook off as the gates (the book-on `go infinite` case is reported as an observation) | 2026-11-03 20:1x: gate exe ff856ba8 + o30_kb4ob8_n2e 20 / 20, lock exe 18 / 18 |
| `a/loader_fuzz_o30.py <exe> <valid net> <new dir> [--mask]` | 18 kinds of damaged FORGENN2 files (sizes, magic, version, header, feature set, inputs, hidden, bucket counts, flags, scale, map entries, reserved bytes, checksum) must each be refused with their reason and leave the compiled-in net playing; plus load-then-damaged and load-then-empty sequences | LOADER FUZZ PASS 21 / 21 (2026-11-03 20:45) |

## Speed in game conditions (the bench can hide a path's cost: it clears the hash per position)
| tool | what it is for | how to verify it |
|---|---|---|
| `a/depth_probe_o30.py <pgn> <exe A> <exe B> [--opt-b N=V] [--n 200] [--movetime 200]` | positions from a match PGN, `go movetime` in one long-lived process per engine (hash kept, as in a game), A-B / B-A rounds; prints mean depth and the paired nodes-per-second ratio (identical trees -> the speed ratio) with a 95 % CI | lock exe vs itself ~1.0; found the v2 path's 0.887 -> 0.980 after the root fix |
| `a/o30_v2stats.py <repo>` + `a/stats_run_o30.py <exe> <pgn> [--opt]` | TEST builds only (-DFORGE_NNUE_V2_STATS=1): per-path counters (evaluations, walk-backs, plies, updates, columns, cached / full refreshes, evaluations without a valid ancestor) printed at exit; the driver runs N game positions at a fixed depth, one `go` at a time | v1 vs v2 on identical trees: the counters named the lazy-root bug (777k no-ancestor evaluations) |
| `a/o30_v2rootfix.py <repo>` | the fix: refresh the v2 root accumulator at search start | in v2port.patch md5 926ada2c; nodes unchanged, verify build clean |
| `a/o30_evalcmp.py`, `a/o30_bucketcmp.py` | two nets' per-position outputs on the same FENs: scale, rms distance, sign flips; per-bucket mean offsets (seams) | - |

## One-command re-check
`bash opus_30h/tools/final_checks_o30.sh`: 16 checks in ~10 minutes (pins of the three exes, identity, parity, walk,
scorer control, trainer selfcheck, MCP self-test, clean-room lint of patches + commit messages, doc_lint, INDEX hashes,
cited paths, loader fuzz, cited hashes with `tools/hash_allow_o30.txt` for the hand-checked ones, all-or-nothing patch
scripts).

## MCP server forge-o30 (`opus_30h/mcp/`)
net_info, net_score, runs_table, spsa_status, v2_bench; `setup_o30_mcp.sh` registers it at user scope (re-runnable,
never rewrites an entry); `test_forge_o30_mcp.py` = 8 checks over the real stdio transport.
