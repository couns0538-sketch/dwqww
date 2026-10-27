# S48fix — S48 gate guard v2: required stopping rule, wider comparability, hash/TC normalization, grids out of git — DONE

Branch `opus-sol-S48fix` = `d4f4312` + CI baseline (cherry-pick 0b1f29bd) + 9f8afcbb + 8b8421f3 + d4ef05a9 (job folder only; tool-only diff empty).
Sol's S48 files are unchanged; the fixes are new _v2_20261027 files. Advice only: no gate, rule, lock or ranking changed; no Elo claim. Machine exclusive: no.

## Acceptance
| line | result | evidence |
|---|---|---|
| S48-1 simulate_gate_bias requires e0, e1, cap (v1 :141-143 defaulted 0/10/1500 and also selection 'H1') | PASS: e0, e1, cap_games, selection, early_stop required; missing, None or invalid -> ValueError | class S48_1_RequiredRule; logs/tests_v2.log |
| S48-2 comparability() adds base+cand exe sha256, net md5, openings seed, SPRT bounds, cap | PASS: base_exe_sha256 (alias opponent_exe_sha256), sprt, cap_games block on mismatch; cand exe sha256, cand net md5, base net md5 and openings seed are reported per side; mode=replicate needs the same candidate and a new seed. Real files: G120 (conc 7) vs G104 (conc 5) blocked on concurrency; G120/G120c and G104/G104c comparable as replicates | class S48_2_NewFields; logs/s48_real_run_v2.md |
| S48-3 hash_mb accepts "64MB"; normalize TC | PASS: 64/'64'/'64MB'/'64 MB'/'64MiB'/'64M' -> 64, '1GB' -> 1024; 'tc=10+0.1', '10.0+0.10', '0:10+0.1' -> '10+0.1' | class S48_3_Normalization |
| S48-4 future sim grids to release assets, not git | PASS: write_grid refuses git work trees (deterministic gzip + sha256 manifest). 8 real grids (834,287 bytes) in F:\opus_scratch\sol_S48fix\grids_20261027\ and as assets of GitHub prerelease opus-sol-S48fix-grids-20261027 (tag on 9f8afcbb, main untouched) | logs/release_assets.txt |
| fastchess figures from counts (exact GSPRT, S44 functions verbatim) | 6/6 gates reproduce printed Elo / err / nElo / LLR | logs/s48_real_run_v2.md |
| deterministic | same-seed re-run, identical grid sha256 fccb9006… | logs/s48_determinism_rerun.log |
| tests / planted bugs | 38 run, 37 OK, 1 skipped (approx needs scipy); 6/6 mutants caught | logs/tests_v2.log, logs/mutants_v2.log |

## Real-file bias (exact model, 20,000 runs; sensitivity points; MC interval = simulation error only)
| gate | assumption | bias | model-adjusted Elo [MC 95%] |
|---|---|---|---|
| G100r (conc 5, cap) | true +10 | -1.686 | 12.576 [12.524, 12.627] |
| G119 (conc 5, cap) | true +10 | -1.507 | 11.007 [10.953, 11.061] |
| G104 (conc 5, H1) | true +10 | +8.578 | 20.862 [20.750, 20.973] |
| G120 (conc 7, H1) | true +10 | +9.275 | 14.345 [14.217, 14.473] |
| G104 | observed plug-in | +1.505 | 27.935 |
| G120 | observed plug-in | +2.076 | 21.544 |

## Findings
- G104/G120 were UNVERIFIED in Sol's S48 (no paired profile). RESULT.md has the Ptnml counts; v2 now models them with each gate's own early-stop rule.
- The approx and exact models differ by about 0.1 Elo on the capped gates (Sol's approx: -1.76 / -1.62).
- grid_should_not_exist.jsonl.gz (28 B) is the planted-bug mutant's output ("git guard disabled" mutant), kept and documented; the test now uses a fake git tree in scratch.

## Release (outward-facing, as S48-4 asks)
The grids are assets of the GitHub prerelease `opus-sol-S48fix-grids-20261027`
(https://github.com/couns0538-sketch/dwqww/releases/tag/opus-sol-S48fix-grids-20261027). Its tag points at
9f8afcbb on this branch; `main` is untouched.

## Left / UNVERIFIED
- model='approx' (Sol's planner) needs scipy and is not tested on the PC.
- No conc-8 bias row was run.
- No coverage-corrected CI; no Elo claim.
