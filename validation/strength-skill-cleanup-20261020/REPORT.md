# Strength-validation cleanup skill checkpoint

Extended the existing `.agents/skills/validating-chess-strength` skill with one
concise requirement: cleanup/reaping of owned children must run unconditionally,
and an independent outer-finally path must restore original caller affinity even
when hashing, status persistence or cleanup fails. Missing observations stay
unknown; persistence failure invalidates the original attempt and later successes
cannot rescue it. No duplicate skill or global/cloud installation is claimed.

The existing independent mock is retained byte-for-byte: after a mocked timeout,
status persistence raised, one mocked child was spawned and cleanup was called
zero times. No real process or affinity operation occurred in that mock. The
baseline skill and scenarios and their exact diffs are retained here. The old six
skill-validation files remain unchanged. The performance packet, engine and prior
proofs were not modified.

One new scenario covers post-timeout stdout-hash and status-write exceptions. A
fresh independent agent read only the updated skill and the supplied scenario
facts, with no expected answers or old applications. Its actual response passed
all seven recorded application criteria: invalid/fail closed; owned-only bounded
cleanup; independent affinity restoration through further failures; unknown
original facts; partial bytes/errors retained; no rescue; future fault injection
and a new preregistered identity. It also distinguishes supplied facts from actual
telemetry and restoration attempts from confirmed restoration success.

Static validation passed both frontmatter fields and all six relative links.
The static command/stdout/stderr and reusable lightweight checker are retained.
No engine, build, helper regression, match, affinity, network or Git action ran.
The observed historical failure provides motivation, not a fresh unguided-agent
comparison. No causal skill improvement, actual cleanup behavior, clock reliability,
speed, NPS or Elo gain is established.

Skill SHA256: `f1e59d7b26cab2d25c57a018a49d7809b4b34b5830c990343194a0e90a242e4a`.
Scenarios SHA256: `2e9dd6f3d050a25340fc9b74fdc9ec720aa0ec9b543323173d730d470fde2cdc`.
Independent application SHA256: `a2bfd7a56153b4639cfe7c69e36a6e31409b52c29cbcd629f83e94f2d30ae578`.

Files are ready for root review and preservation. The next engine experiment and
its helper behavior validation remain separate from this documentation checkpoint.
