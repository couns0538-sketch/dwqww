# S15 SPSA harness — DONE (harness v2, PC fixture run, no tune applied)

`SOL_LEFTOVERS_FOR_CLAUDE.md` §2 item 6. Branch `opus-sol-S15` = `d4f4312` + `0d99f02` cherry-picked (`4a710b68`) + `b2649706`. This is a tool job with no engine change: `git diff 294dbed -- src include tests tools bench CMakeLists.txt` is empty. Commits are `[skip ci]`; no CI run.

**Acceptance (QA):** "harness + fixture run with 2 params × few iterations at BelowNormal; no tune applied".
Sol's pass line: deterministic with a seed; parses every tune:: param with its range; the dry run converges on the fake objective; writes only into its own out dir.

| item | result | evidence |
|---|---|---|
| harness | PASS. `forge_sol_S15_spsa_v2.py` keeps Sol's reviewed v1 (sha256 `5f1f5978…`): catalog, demo, plan and observe logic unchanged, every changed line marked `v2:`. v2 adds a `run` driver: UCI capture, application proof, fastchess, owned-checker observe and pentanomial cross-check. | `logs/v1_to_v2_tool.diff` |
| every tune:: param with its range | PASS. 51 parameters on the AL1 lock (`src/search.cpp` sha256 `44680416…`, identical to Sol's L), equal to Sol's catalog. NetScale is absent, so `unsupported_requested: ["NetScale"]`. | `logs/step6_catalog_and_demo.log` |
| dry run converges, deterministic | PASS. 20 iterations over 51 params; synthetic loss 0.08447646447944493 → 0.07216007690858689. Two runs are byte-identical (24 files), and 21/21 iteration/result files are byte-identical to Sol's Linux v1 outputs. | step 6 |
| fixture run: 2 params × few iterations at BelowNormal or lower | PASS. Pre-registered: LmrQuietBase and QsSeeMargin, 4 iterations × 2 pairs (16 games), tc 2+0.02. Settings: Threads=1, Hash 16, OwnBook off, concurrency 1, reversed colours. Priority was Idle: 145/145 samples of the tool, fastchess and engines show base priority 4. Ran 112 s; 16/16 terminations normal. Each iteration's pentanomial equals fastchess's own report, and both probe settings were proven applied in every iteration (`uci`, `setoption`, `uci` re-advertisement). | `logs/step7_*`, `logs/step7_fixture_run.tar.gz` (107,327 B) |
| no tune applied | PASS. `tune_applied: false`, `engine_source_modified: false`. The proposed values (LmrQuietBase 85→149, QsSeeMargin 40→114) come from 16 games, are noise, and are not applied anywhere. | `logs/step7_run_summary.json` |
| writes only its own out dir | PASS. A NEW `--out` is required and all creates are exclusive; inputs are sha256-pinned and re-checked. | tests |
| engine for the games | Exposed build: unchanged lock source + `-DFORGE_EXPOSE_TUNABLES=1`, box recipe `build_pc.sh`, nice 19, sha256 `dccaba91…`, FMA 0. `uci_check.py --full` ALL OK: bench 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690. | `logs/step1_build_exposed.log`, `logs/step2_identity_exposed.log` |
| unit tests | PASS 29/29: Sol's 13 ported (assertions unchanged, paths ported) + 16 v2. No real engine runs in the tests. | `logs/step4_unit_tests.log` |
| planted bugs | PASS: 16/16 mutants caught; the clean copy passes. | `logs/step5_mutation_check.log` |
| README | PASS | `README.md` |

## Findings on the PC (v2 fixes of Sol's v1)
1. **Hidden tunables.** The release lock exe accepts tunables silently but does not advertise them. Fastchess `-strict` then refuses: "Candidate doesn't have option LmrQuietBase", interrupted, rc 1. The exposed build is required, as Sol had planned. (`logs/step3_fastchess_probes.log`)
2. **Adjudication cap.** Sol's planned `-maxmoves 200` makes fastchess tag a capped draw `[Termination "adjudication"]`, which the owned checker `tools/match/pgn_stats.py` rejects. A 252-ply game appeared in a 2-game probe. v2 drops the cap: games end by the rules, and a per-iteration timeout bounds them.
3. **E.p. normalization.** Fastchess writes an e.p. square that no pawn can capture as `-`. v1 compared all four FEN fields and failed closed (reproduced in `e2e_run1_epfail`); 3,209 of the 10,000 book openings carry an e.p. square. v2 matches placement, side and castling exactly, the e.p. field equal or `-`, with exactly one planned opening per played FEN.
4. **Opening reuse.** v1 replayed the same openings every iteration. v2 rotates them with sha256(seed:iteration, fen).
5. **Windows text handling.** Text-mode writes produced CRLF and reads used cp1252. v2 writes LF bytes and reads UTF-8.
6. **Priority.** The PC's gate engines run at BelowNormal and self-play/training at Idle. The fixture therefore ran at Idle; BelowNormal would outrank self-play and training.

## Reproduce
```
nice -n 19 bash b/tools/build_pc.sh <lock tree> F:/opus_scratch/sol_s15/build/forge_s15_exposed.exe -DFORGE_EXPOSE_TUNABLES=1
python -I -B <lock archive>/2_build/uci_check.py F:/opus_scratch/sol_s15/build/forge_s15_exposed.exe --full
FORGE_S15_TEST_ROOT=<new dir> python -I -B test_forge_sol_S15_spsa_v2.py -v
python -I -B mutation_check_v2.py <new dir>
python -I -B forge_sol_S15_spsa_v2.py demo --source <lock tree> --seed 20261027 --iterations 20 --out <new dir>
nice -n 19 python -I -B forge_sol_S15_spsa_v2.py run --source <lock tree> --engine <exposed exe> \
  --fastchess C:/Users/Administrator/grok-pc/tools/fastchess/fastchess.exe --openings <lock tree>/tools/openings/forge-10000.epd \
  --select LmrQuietBase,QsSeeMargin --iterations 4 --pairs 2 --tc 2+0.02 --seed 20261027 --gain 0.05 --perturbation 0.1 \
  --priority idle --iteration-timeout 120 --max-wall-seconds 540 --min-free-ram-gib 6 --out <new dir>
```
Environment:
- Python: Windows CPython 3.14.7, standard library only.
- fastchess: the PC binary alpha 1.8.2 (f618e34, sha256 `c6d7e445…`), used read-only.
- Machine exclusive: no; gates, self-play and training were running.

## Left / UNVERIFIED
- No real tuning was run, and the fixture's proposed values carry no information. Gain and perturbation schedules for a real tune are not studied. No Elo or speed claim.
- Only the PC fastchess (1.8.2 f618e34) was exercised, not the lock's provenance binary (60d7a7a, Linux CI).
- The exposed exe is a scratch build and is not committed. It was built under `F:\opus_scratch\sol_s15\build`, not `F:\opus_scratch\build\S15_*`, because this task limited writes to `F:\opus_scratch\sol_s15|s16|s17\`; both locations keep it off D:.
- Execution binding: the run proves that the pinned binary applied both settings and that fastchess's result equals the checker's. Move legality rests on fastchess `-strict`.

## Files
`README.md`, `IDEA_SOURCE.md`, `forge_sol_S15_spsa_v2.py`, `test_forge_sol_S15_spsa_v2.py`, `mutation_check_v2.py`, and `logs/` (step 1-7 logs; `v1_to_v2_tool.diff`; archives `step3_fastchess_probes.tar.gz` 45,695 B, `step6_catalog_and_demo.tar.gz` 53,481 B, `step7_fixture_run.tar.gz` 107,327 B). Sizes and sha256 are in `FILES.txt`; checksums in `SHA256SUMS`.
