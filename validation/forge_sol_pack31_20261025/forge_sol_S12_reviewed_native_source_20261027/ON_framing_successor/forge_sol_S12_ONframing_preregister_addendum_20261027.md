# S12 ON observer correction — source-only successor, 2026-10-27

The original44-file packet is frozen and preserved, including its34 pure passing
controls and the independently reproduced ON observer defect. Do **not** execute
its `forge_sol_S12_feature_qualify_20261027.py` for ON qualification. The old
normal OFF S25 parser correctly requires the bench summary at byte0; required
S12 active/stats output therefore makes that old ON call site falsely fail.

Only the two ON feature-run commands in the original preregistration are
superseded. Build, FIRST bare11, full runtime-OFF Std, baseline reuse, helper,
counter and bounded-parity commands are unchanged. No engine patch, build flag,
UCI option, net or expected node value changes. Native execution is still held
until root's source review, actual S11 closure/publication and a new serial grant.

Run the successor directly from its separate directory; never apply the
tool-only audit patch inside the frozen original packet. It verifies the
original feature source hash and imports the original frozen Std/build/binding
dependencies. Its own ON validator is a separate adjacent module, pinned before
import and checked again at postflight together with the runner source. Actual
and expected parser hashes are recorded in the runtime result.

```bash
FORGE_S12_SUCCESSOR=/tmp/forge_sol_S12_ONframing_successor_20261027
FORGE_S12_OUTPUT=/tmp/forge_sol_S12_native_20261027
FORGE_S12_CPU=2
FORGE_S12_BASE=Lprime  # Repeat B only under its own finite grant.
FORGE_S12_GRANT=ROOT_SUPPLIED_NEW_SERIAL_LEASE
cd "$FORGE_S12_SUCCESSOR"
sha256sum -c forge_sol_S12_ONframing_SHA256SUMS_20261027.txt

taskset -c "$FORGE_S12_CPU" nice -n 19 python -B "$FORGE_S12_SUCCESSOR/forge_sol_S12_feature_qualify_successor_20261027.py" --execute --authorization-reference "$FORGE_S12_GRANT" --arm "$FORGE_S12_OUTPUT/${FORGE_S12_BASE}_candidate_Release_ON_arm.json" --out "$FORGE_S12_OUTPUT/${FORGE_S12_BASE}_Release_ON_feature_v2" --cpu "$FORGE_S12_CPU" --max-seconds 600

# Separate process with unlimited AS, owned RSS limit, leak detection ON:
taskset -c "$FORGE_S12_CPU" nice -n 19 python -B "$FORGE_S12_SUCCESSOR/forge_sol_S12_feature_qualify_successor_20261027.py" --execute --authorization-reference "$FORGE_S12_GRANT" --arm "$FORGE_S12_OUTPUT/${FORGE_S12_BASE}_candidate_ASAN_ON_arm.json" --out "$FORGE_S12_OUTPUT/${FORGE_S12_BASE}_ASAN_ON_feature_v2" --cpu "$FORGE_S12_CPU" --max-seconds 300
```

Every output directory must be NEW. All original stdout/stderr/stdin/receipts
remain saved by the unchanged owned transport. The ON observer consumes the
complete captured stdout bytes and verifies their recorded hash/length, empty
stderr, exact rc0 type, complete EOF and valid protocol closure. It accepts only
one active line at process start, exactly eight ordered typed stats per bench,
and each fixed-depth/node terminal with a line ending. Repeated same-process
bench validation occurs **after close**, against the entire original two-bench
raw capture, with active once globally. Unknown lines, prefix/tail/blank bytes,
duplicate active/summary, truncation, counter overflows and substituted captures
fail. No arbitrary lines are stripped or presented as original output.

The original normal OFF S25 parser remains byte-identical and strict. No native
bench, sanitizer, correctness, timing, speed or Elo result exists for this
successor. Pure source-framed fixtures demonstrate observer behavior only.
