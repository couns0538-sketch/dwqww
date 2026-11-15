# Strict-depth parser for the amended softnodes workload

Fresh immutable v2 preparation, cloud only. No engine runs, Git operations or root-state writes were performed. The earlier depth-64 generation, including its unused declaration and all source/tool pins, remains unchanged.

The depth-64 exception remains authorized by `55ddf61a754ceffc4f940b847ad97143148d0434`, whose exact decision text and SHA256 `5e2d573b7e553ec49e84918bd1dfd6a28ccfd2ca7236b6834c3b041965945e2f` are pinned by the new controller. This revision strictly parses the entire depth token as a nonnegative decimal integer that fits in `int`. A duplicate depth field makes that exact line incomplete. A later malformed exact line replaces the earlier line's completeness rather than retaining its depth. All other parser and engine behavior is unchanged.

The new binary compiled successfully using the same frozen independent Board/bitboard objects and old compile arguments with fresh source/output paths. `compile.txt` contains the actual command, flags, hashes and complete output. Native SHA256: `17dd75a673996e04185819383589b3f04b450750594fec6b357dd6330058f555`.

All 29 parser self-tests passed, including six new cases: `64junk`, negative depth, uint64 overflow, int overflow, duplicate depth fields and a malformed last exact depth following a valid depth-64 line. The earlier depth-63, exact-depth-64 and bounded-line tests also passed. Full command/output is in `parser-selftest.txt`; both helper syntax checks and metadata consistency checks passed. No sanitizer game is claimed by these checks.

Root invocation:

```text
node /workspace/work/parity-softnodes-depth64-v2-preparation/control.mjs declare d9a8587df8ad4d0ff1231632cb1ac72b590c04bf --freeze-authorized
node /workspace/work/parity-softnodes-depth64-v2-preparation/control.mjs run 0 --execute-authorized
node /workspace/work/parity-softnodes-depth64-v2-preparation/audit.mjs 0
```

Indices 0–11 use fresh `depth64-v2-` labels and seeds 202611155201–202611155212. Raw output and the new declaration go to `/workspace/work/parity-run/softnodes-depth64-v2-batches`. All twelve original groups retain their engine binaries, thread/options/limits, 180-second target, 420-second harness deadline and 440-second outer bound. The absolute Job A deadline remains 2026-11-15 02:19:40 UTC.

Use the corresponding v2 recorder, which the parent agent is preparing. No old finding, root stop, declaration or acceptance result is cleared by these tools. `FROZEN-PINS.txt` pins the final native, plan, helpers and source; only documentation and metadata-check output were added afterward.
