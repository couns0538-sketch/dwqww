# Forge crew skills 1.1.0 — delivery and continuation checkpoint

Created all seven requested skills in the existing `forge-cpp-lab` plugin, retaining `cpp-chess-engineering`. Branch: `astra-crew-skills-20261101`, recovered from published plugin source `9761eb367c3ae4e541fc316380699f78eb493a3c`. No engine source, live queue, trainer or grok-pc process was changed. Crew installation is pending; it was not performed here.

Installation, standalone-copy commands and one Codex invocation per skill: [CREW_SKILLS_20261101.md](../../CREW_SKILLS_20261101.md).

## Checks actually run

| Check | Result | Evidence / limit |
|---|---|---|
| Integrated Python regression suite | PASS, 111 tests | `integrated-final.log`, Python 3.12.14; includes 15 retained original tests |
| Lock-proof helper | PASS, 25 tests | `../crew-proof/`; original failures preserved, final normal and optimized runs pass |
| Exact-eval checker | PASS, 14 tests | `../crew-eval/`; stale identities, consumed-byte changes and corrupt-weight controls |
| ABBA checker | PASS, 17 tests | `../crew-abba/`; calibration, order, nodes, identities, timing and statistics |
| Independent holdout auditor | PASS, 11 tests | `../crew-data-holdout-final-v2.log`; synthetic normalized exports only |
| Restart helper | PASS, 7 tests | `../crew-data-root-resume.log`; real interruption of an owned disposable fixture |
| Safe-run portable checks | PASS, 6 tests | `../crew-safe-run/`; static checks are not Windows execution |
| Gate pack helper | PASS, 16 tests | `../crew-gate/`; tested subject/options binding, snapshot freshness and collision refusals |
| PowerShell AST | PASS, all 5 scripts | `powershell-syntax-final.json`; PowerShell 7.4.6 on Linux |
| PowerShell pure helpers and actual C# pipe drain | PASS | `powershell-helpers-final.log`; quoting, refusal cases, successful/failed-sink drains |
| Names, frontmatter, local skill links, manifests, marketplace, Python CLIs | PASS | `package-structure.json`; eight unique names including the retained original |
| Portable plugin schema | PASS | Official schema hash in `package-structure.json` |
| Codex plugin command syntax | PASS | CLI 0.159.2 help inspected; this is not installation or client discovery |
| Native Windows PowerShell 5.1, D-drive, Idle/affinity | UNVERIFIED | Windows checks are supplied for crew execution |
| Actual Forge LTO+PGO, OFF/ON benches, perft, T1/T4, ASan/UBSan | UNVERIFIED | Native adapter receipts and original logs must come from the actual checkout |
| Actual fens12k / quiet-core ABBA | UNVERIFIED | Checkers were tested; no engine parity or speed result is claimed |
| Real private 013/014, native decoder and authentic game-ID separation | UNVERIFIED | Missing authentic IDs cannot pass the requested game-level gate |
| Actual production shard restart / live gate clearance | UNVERIFIED | Fixture proof and fresh supplied snapshots do not replace production-specific checks |

Exact integrated command from the marketplace root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -W error::ResourceWarning -m unittest discover -s plugins/forge-cpp-lab/tests -v
```

The preserved disposable restart had child exit `-15`, a genuinely incomplete next-shard stage, and identical uninterrupted/resumed MD5 `efd4d2e8d2829b84108d7da32bae00dd` and SHA256 `703ae72d2663d0f196854151eebfc9a1f85a22f3cb8606898a5fdebfe121916f`. See `../crew-data-restart-proof-v2/RESTART_PROOF.json`. This is a fixture result, not evidence about the production converter. Earlier failed tests and superseded fixture evidence remain labeled historical.

## Decisions preserved

- T4 requires a separate authorized four-thread host; `grok-pc-safe-run` retains its two-worker limit.
- An ON-bench difference applies to behavior-changing feature gates. Exact SIMD changes use parity and search identity, not an artificial node difference.
- No scripts control other processes or edit a live queue. The optional disposable restart test terminates only its own newly created test worker.
- The PowerShell wrapper validates declared policy; it is not an OS sandbox or arbitrary child-thread limiter. Reviewed native recipes must propagate the thread budget to compiler/LTO/BLAS subprocesses.
- The helper receipts and hashes bind evidence to files; they cannot establish that an untrusted native adapter told the truth. Original logs and source review remain required.
- New skills extend existing owners rather than duplicate generic development/resume skills. No external engine code was copied; see `../../IDEA_SOURCE.md`.

## Publication and next action

Code checkpoints: `84d7d04` scope/routing, `5433e85` gate, `332121c` holdout/restart, `d73f3e9` safe-run, `3f06707` proof, `9ee2f5a` parity/timing. Each was pushed to the same new branch. The subsequent integration/package commits contain this report, final source/test hashes and the download; the archive manifest records the exact packaged source commit.

Next: install one route, start a new Codex session, confirm all seven skill names are discovered, then provide the current lock and reviewed native recipes for the relevant task. Run the supplied Windows tests in an approved test folder before a real grok-pc workload. Full engine proof uses an authorized host that permits T4. Real holdout clearance needs complete immutable 013/014 exports plus original game-ID and FEN provenance.

No NPS or Elo improvement is claimed. This delivery qualifies helper behavior and package structure, not a Forge candidate.
