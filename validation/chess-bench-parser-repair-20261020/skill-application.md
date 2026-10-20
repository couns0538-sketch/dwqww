# Fresh read-only skill application (2026-10-20)

Applied the current repository-local `validating-chess-strength` skill to the three supplied cases. This is an application/static-document check, not engine or experiment acceptance.

## Exact case decisions

1. **Do not give the package freeze PASS.** Sixty-three passing mock tests using prefixless `GOOD` do not test the frozen producer's actual `info string bench` dialect. Preserve byte-exact actual positive captures with producer/transport provenance and hashes; label LF/CRLF derivatives honestly; check real positive captures and malformed, duplicate, warning, stderr and nonzero-exit controls before any future harness freeze. The failed original experiment stays failed.

2. **The replay proves conditional parser behavior only.** With return code supplied as zero, a passing replay shows acceptance of those captured bytes and the expected node count under that assumption. Compared with the actual frozen parser's rejection, it isolates the formatting defect. It does not recover the original exit code or group observations, prove original process success/quiescence or full hosted readiness, rescue the failed attempt, or establish speed/strength. The missing original process facts remain **UNKNOWN**.

3. **Keep the timeout and both evidence stages.** Preserve command/stdin, raw stdout/stderr, distinct pre-verdict and post-cleanup hashes, return code or explicit unknown at each stage, owned-group observations, cleanup actions/attempts/errors, and final return code/group state. Do not overwrite before-hashes with after-hashes; retain the diagnostic bytes as well as their hashes. The recorded fixture has unknown pre-verdict return code, final `-2`, group present before/empty after, and different stderr hashes after SIGINT cleanup. The timeout verdict remains failed.

## Independent static checks

- YAML frontmatter: **PASS** using `/usr/bin/python3` and PyYAML `6.0.2`. Parsed exactly `name`/`description`, expected skill name and a nonempty description.
- Relative inline Markdown file targets: **PASS**, 3 checked across `SKILL.md` and `scenarios.md`; all resolve to existing files. Checks excluded fenced code. No network or heading-anchor checks were needed.
- `.agents/skills/validating-chess-strength/SKILL.md` → `../../../validation/clock-safety-9850x3d/run-quality-sprt.py`: PASS
- `.agents/skills/validating-chess-strength/SKILL.md` → `scenarios.md`: PASS
- `.agents/skills/validating-chess-strength/scenarios.md` → `../../../validation/chess-bench-parser-repair-20261020/REPORT.md`: PASS

## Evidence and limits

Current skill SHA-256: `98346e940173878d2dd0b7f21f908343cf9fef7b400baed312a6f62de2e59b37`. Current scenarios SHA-256: `1e2ee8a55381a1205fb985f08995f96213b1bc0cac64157f6eb32fd355988337`. Report SHA-256: `b11e22f6587ee6eea0f4f353d9f5be82d39abf6ce2b826ceb3b53f144d8bb62f`. The JSON artifact records all read source hashes and full static-check results.

The observed RED is the actual frozen parser's failure against canonical captures, recorded as five expected failing methods out of fifteen. It is not an invented failed no-skill model control. Parent-reported verification of 117 payloads and 15 parser methods was not repeated here. No no-skill control was run for these three cases, so this application establishes **no causal improvement in model behavior**.

The preserved report/proposal/final-verification documents describe their earlier helper-only snapshot as skill unchanged/proposal unapplied. The current skill and scenarios contain the added guidance; their current hashes are recorded without rewriting that historical evidence.

No engines, matches, parser/process test suites, builds, Git commands, cloud-skill operations, installations or network requests were executed. No fresh 63-test certification, full-hosted-readiness pass, retry/resume/pooling/launch authorization, speed gain, clock-reliability claim or Elo/hardware/Stockfish claim follows.
