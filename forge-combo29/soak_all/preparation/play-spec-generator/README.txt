VM-only generator for additional fresh Part2 D/E/F self-play specs.

Example (inspect first; remove --dry-run to create this one spec):
node /workspace/work/all-run/play-spec-generator/make-play-spec.mjs --phase D --id 5 --seed 9500100 --threads 1 --nodes 2000 --seconds 300 --dry-run

D/F accept Threads1 or2 and nodes2000 or20000. E accepts Threads2 or4,
nodes0 and uses depth9. All invocations use seconds300, full --trace,
unique --trigger paths, Hash16, OwnBookfalse, UseNNUEtrue and MultiPV1.
D/E explicitly disable all three candidate options; F enables all three.
ASan/UBSan and TSan environments match the reviewed existing drivers.

The helper reads current state and all prepared JSON specs. It rejects
existing phase/id, non-increasing phase IDs, used normalized seeds, declared
artifact paths, and existing files. It verifies the selected reviewed driver
SHA256 before generating anything. Dry-run reads only.

A successful non-dry invocation creates only:
  /workspace/work/all-run/specs/2PHASE-ID.json
  /workspace/work/all-run/specs/2PHASE-ID.command.txt
The command text contains the exact JSON spec, argv/environment/shell form,
driver/source/generator hashes and hashes of the inspected state/spec snapshot.
It is included in rawFiles alongside the final trigger. Root later invokes
control.mjs run-spec on the JSON spec; this generator does not do that.

Run generator invocations sequentially. The exclusive writes prevent file
overwrites but do not reserve different IDs sharing a seed across concurrent
generator processes. If the final spec write fails, command evidence remains
for inspection. Original artifacts are never removed or replaced.

This helper is for fresh coverage. It rejects seeds from incomplete attempts
as well as completed attempts; preparation of an intentional retry is separate.
The example ID/seed are not reserved and can become unavailable as root proceeds.
The unchanged driver checks its 300-second deadline between games; the
controller's 450-second timeout remains the hard bound. Sanitizer diagnostics
must be audited separately from the driver's chess-fault counter.

Validation:
node --check /workspace/work/all-run/play-spec-generator/make-play-spec.mjs
node /workspace/work/all-run/play-spec-generator/fixtures.mjs
Fixtures use pure synthetic snapshots plus real read-only dry-run/collision
checks. They do not create production specs, execute engines/controllers,
change state, or touch a branch.
