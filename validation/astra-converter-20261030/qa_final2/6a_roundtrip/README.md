# QA Final2 item 6a — standalone roundtrip adapter policy

Baseline: e5759a2. The runner now requires `--accept-gpl3` and calls the same external-repository boundary policy as convert/verify before it writes output or launches the adapter. It executes the checked resolved path. Normal repositories, worktrees, bare repositories and symlink/dot-dot repository targets are rejected.

Command: `python3 -m unittest discover -s tests/data2 -p test_roundtrip_policy.py -v`

`red.log` is the unmodified runner with the new tests; `green.log` is 4 passing cases after the fix. The acknowledged external-tool test stops at a mocked process-execution boundary. This is a policy regression, not a rerun of the original million-row conversion; historical conversion evidence is unchanged. No grok-pc activity.

IDEA_SOURCE: QA Final2 item 6; existing convert/verify external GPL-3.0 policy.
