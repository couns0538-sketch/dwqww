# t16 fixture repetitions

All 40 fresh sessions completed on the frozen binaries using unchanged plan argv, cwd, environment overlays and input bytes: ten options and ten clamp sessions in each of Release and ASAN. All 40 retain literal expected-file failures.

Every output is byte-identical to its original Release suite output: options SHA256 `39f2d652316b85989d7262040d1bd5d381e507ed7070e99b798618e69ba2fa22`; clamp SHA256 `171f00efa6c9f307693df97ec39cdb6965ca471b56aab58e932098aa2778908a`. Literal diffs contain only added advertised option lines: 44 for options (22 per UCI block), 66 for clamp (22 per block). No lines were removed and no output was stripped to produce a pass.

All sessions exit 0 with empty stderr and no sanitizer diagnostics. No go commands or searches were issued. Original ASAN fixture metadata was absent when this experiment started, so these repetitions make no claim about the upcoming original ASAN suite outcome.

Execution was 2026-11-14T22:26:19.032Z through 2026-11-14T22:27:16.200Z, overlapping the separately controlled ASAN null_threat_verify_test. This is a recurrence/output observation, not a timing or performance claim. The unchanged native timeout arguments were retained; an independent 40-second per-session supervisor and 270-second overall guard were recorded and never triggered. Original plan/input/expected/binary and available original-evidence hashes were checked again after execution.

Each session retains full stdout/stderr, literal diff, exact argv/cwd/env, exit status, hashes and comparison metadata. See summary.txt, prepared-inputs.txt, controller.command.txt, controller.stdout.txt and the inert repeat-fixtures.mjs.txt. Verification: all 40 retained stream hashes and classifications checked by finalize-evidence.mjs.txt.
