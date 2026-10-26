# S34 offline gate-manifest validator, 2026-10-26

Prepared in isolation for later ordered root integration. This folder does not
claim that S34 has reached its place in the ordered job queue. No publication,
live gate change, engine execution, compilation, match, or PC execution occurred.
Playing strength and PC behavior remain UNPROVEN / UNVERIFIED.

Run the authoritative strict audit:

```sh
python3 -B forge_sol_S34_validate_manifest_20261026.py /path/to/forge_gates.json
```

The validator writes only JSON to stdout. Exit 0 means no findings, 1 means
schema/rule findings, and 2 means an input/JSON rejection. Redirect stdout into
your own new output folder if a saved report is wanted. The tool creates no
files or directories and does not inspect or execute any executable path.
Use Python 3.10 or newer with its standard library. The receipt states the
actual interpreter tested; an unavailable Python 3.10 executable is not claimed
as tested.

The strict audit requires each gate to declare concurrency, tc, sprt, srand,
openings_start, tag, exe, and full 64-hex sha256. Concurrency is an integer
excluding booleans, from 1 through 8. SPRT needs finite numeric elo0 < elo1 and
an explicit JSON boolean nonreg. An early_stop object is optional; when present
it needs games, elo_max and llr_max. games must be a positive integer; the two
thresholds must be finite numbers. Booleans cannot stand in for numbers.
Time controls must match `^\d+(\.\d+)?\+\d+(\.\d+)?$` in full, with ASCII digits;
a trailing newline is rejected. srand must be an integer; openings_start must
be a positive integer. Each must be unique across all gates, including held,
dropped and historical entries. Every confirm_of must exactly match an existing
tag, with case and whitespace preserved. Object manifests containing a gates
list and bare lists of gate objects are both supported.

Tags are actual write-directory and output-filename inputs in the supplied
driver, not generic descriptive strings. They must be one portable component.
Protected lock, locks, baseline, .git and dist-v* components are rejected after
case folding, backslash handling and Windows trailing-dot/space normalization;
original components are checked before traversal can hide them. Traversal,
absolute paths, separators, device names and case-colliding write tags also
fail. Executable paths, base/lock descriptors and approval-file paths are read
inputs: their mere mention of protected directories does not fail write safety.
The check covers manifest-derived destinations. A separately configured driver
output root and the behavior of other driver versions are UNVERIFIED.

The schema is deliberately closed to unknown fields at root, gate and audited
nested-object boundaries. A new output_dir or any other unknown field fails
UNSUPPORTED_FIELD, even if its path appears safe. This avoids guessing whether
future fields write files. Supplied descriptive fields retain their original
meaning; prose containing a protected path is not scanned as a write. The
optional driver fields tc, stack and driver_notes are documented from the
supplied driver rather than invented write-path aliases. Parsing rejects
duplicate JSON keys, nonstandard constants, input larger than 8 MiB, nesting
deeper than 64 containers, and integers longer than 4096 digits. These resource
bounds are audit limits, not engine or operating-system limit changes.

The supplied snapshot is **not strict-valid**. Its 122 gates produce 240 real
findings: 122 missing tc values, 104 missing sprt objects, and 14 missing
openings_start values. Every finding has its own JSON pointer and explanation
in forge_sol_S34_current_manifest_strict_20261026.json. No exemption was made for
legacy or inactive entries, and the supplied manifest was not changed.

An explicitly requested secondary audit can explain the supplied driver's
effective behavior:

```sh
python3 -B forge_sol_S34_validate_manifest_20261026.py --driver-defaults /path/to/forge_gates.json
```

This mode does not replace the authoritative strict result. It fills only
completely absent tc, sprt and openings_start fields using the supplied proposed
r7 driver's defaults: 10+0.1, {elo0:0, elo1:10, nonreg:false}, and 1. It never
fills partial or malformed overrides. Provenance, exact source SHA256 and line
numbers appear in its JSON output. On the current manifest it reports 13
OPENINGS_START_DUPLICATE findings: 14 historical entries effectively reuse
start 1. Source lines 89, 92 and 94-97 establish the defaults; 85-86 and 354
establish tag-derived writes. The copied driver is explicitly a proposed
candidate; no claim is made about the PC's deployed driver.

Run the full standalone S34 test suite from this folder:

```sh
python3 -B -m unittest discover -s . -p 'forge_sol_S34_tests_20261026.py' -v
```

Twenty-one behavioral tests include 29 distinct bad-manifest fixtures. Each
fixture isolates one defect, fails with its intended code, and has a distinct
explanation. The index records each expected rule and explanation fragment.
Tests also cover valid object/list manifests, both concurrency boundaries,
numeric boolean traps, exact/forward confirmation references, full tc matching,
missing versus malformed driver overrides, read paths in protected directories,
unknown write fields, Windows traversal and aliases, case-colliding tags,
bounded malformed JSON, very large finite integers, CLI exit codes and no
filesystem changes, and the actual snapshot's strict and secondary findings.

forge_sol_S34_RED_20261026.log records 18 missing-feature assertion failures
before the production tool existed. Intermediate RED logs preserve the later
numeric/depth/size-limit failures. The first implementation attempt duplicated
unknown-field findings; this was fixed at the shared schema-check call, without
changing expectations. Large-integer float conversion and unbounded/decoder-
dependent malformed-input paths were then reproduced and corrected. Final
GREEN and discovery logs report all 21 tests passing. Failed attempts remain
in this folder as evidence, not as successful validation.

The source-before and final receipt record the same input SHA256:
`9c7abdb4fde93ac9118292f5852da118766573f9abea67e303b8001063ab9f79`.
It is 428830 bytes and was preserved in place; no duplicate snapshot was made.
The receipt records exact commands, statuses, code/test hashes, counts and
limitations. SHA256SUMS covers the delivery files and is checked from this
folder. No network, external service, Git operation or PC action is needed.
