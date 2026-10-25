# S28 observational lock-transition kit — 2026-10-25

The current h256_e12 lock remains the lock. This kit qualifies a copied source tree with either the current network or the candidate e48f006 network. Qualification does not adopt a new lock and establishes no speed or Elo gain.

Place the Python file and shell wrapper beside one another. Python 3.10+, Bash, GCC with C++20, CMake, CTest, GNU patch, objdump and sha256sum are required. The generated source is a complete fresh Release build; no cached core objects are substituted. Compile flags are `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`. Build parallelism is at most two.

The existing S01 pin helper is an explicit dependency, not a renamed duplicate. Pass its path with `--pin-helper`. Required SHA256:

`d64465edb75a69e517e153f394e570766a4debcfedcb5417376bf94cb0c097c6`

## Run

Use a parent directory that already exists and an output directory that does not exist, including no dangling symlink. Dry-run is the default:

```bash
bash forge_sol_S28_lock_transition_20261025.sh \
  --tree /absolute/path/to/complete/lock-or-buffix-tree \
  --net /absolute/path/to/nnue_weights.inc \
  --pin-helper /absolute/path/to/forge_sol_S01_rerecord_pins_20261025.py \
  --out /absolute/path/to/NEW_forge_sol_S28_dryrun_20261025
```

A dry run validates inputs and writes only a plan, a result and their SHA256SUMS inside the new output. It does not copy source, patch, compile, invoke an engine or adopt the proposed network. The checksum command is still executed inside the output directory.

Use a different NEW output path and add `--execute` for actual qualification. Add `--queue /absolute/path/to/forge_sol_S28_queue_20261025.json` for independent queued candidates. Optional `--cmake`, `--ctest`, `--objdump` and `--fma-checker` select installed tools explicitly. The supplied FMA checker is supplementary; its scope is recorded separately from the independent whole-executable and NNUE-object disassembly counts. `--jobs 1` lowers build parallelism.

Each queue row specifies the exact original patch and an advertised, nondefault ON value:

```json
[
  {
    "id": "P23b",
    "path": "/absolute/path/to/p23b_refutlmr_h256_vs_lock.patch",
    "sha256": "30cdfb0923b00f5cde1803fe7d2b0deb6d3e17f5aadf14d447ef25a29c6ee7cb",
    "option": "RefutLmr",
    "value": 1,
    "time_only": false
  }
]
```

A row can also provide `repair_path` and `repair_sha256`. The tool first records the ORIGINAL `patch -p1 -F0 --dry-run`. Only an actual original failure permits that supplied repair. A successful original is applied unchanged even when a repair is listed. The tool does not invent patches or regenerate copies under new names. All queue candidates start independently from fresh copies of the same input tree and selected net. Each candidate exposes tunables in its build; the control build does not. Requested ON options must be advertised exactly once with default zero and the supplied nonzero value in their legal range. No unknown-option silence is treated as activation evidence.

## Fixed oracles and evidence

| Network | SHA256 | d11 / d13 / d16 / d20 / d22 |
|---|---|---|
| Current h256_e12 | `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b` | 308972 / 745494 / 2460422 / 11901452 / 31111774 |
| Candidate e48f006, not adopted | `0fdf9bdb6bdf4c9f1622bcef29921912acb139fdf388e541b017a948118d4661` | 328459 / 945640 / 3024381 / 9162399 / 20421972 |

Every new engine's first invocation is OFF `bench 11`; any mismatch stops later native work. OFF benchmarks use five fixed references, Threads=1, Hash=16, OwnBook=false and a fresh process each time. Both perft5 totals must be 4865609 and 193690690. Whole-executable and NNUE-object FMA counts must both be zero. ON benchmarks record the actual node counts. The PC precheck depth is the first listed depth where ON differs; `null` means none. A time-management-only patch must preserve every fixed-depth count, and `null` is expected for it.

The existing original forge_tests executable is built and run without relabeling source assertions. Both its exact four FAIL lines and full CTest's actual four FAIL lines must match the same observed allowlist. CTest may fail only its original forge_tests target. Candidate-net values are derived from independent S01 searches, not from the old net's score pins. Every queued candidate must reproduce the independent base OFF pin signature exactly: case, depth, bestmove, score kind, score and full PV. Its exact FAIL multiset must also equal the base. Thus the candidate net cannot silently redefine a known failure when an OFF patch leaks into a pin position outside the five benchmark positions. The generated allowlist records source, binary and net hashes and the pin observations. It is scoped to that exact qualification output.

All subprocess stdin/stdout/stderr bytes are preserved losslessly in base64 JSON, with byte counts, SHA256, command, working directory, waited exit and completed capture. The original engine text is never silently normalized. CTest-generated working logs and all complete build products remain in the private output; publishing the full copied source/build directory is unnecessary. Publish the encoded evidence and hashes, not new unencoded legacy banners. A source copy retains its upstream contents for a reproducible local build.

The selected input files, external patches, helper, net and manifest are hashed before and after. Source symlinks, path traversal, output/input overlap, existing output, malformed queue and incorrect hashes fail before creating output. Child temporary files are directed to the new output. README and IDEA_SOURCE receive dated appended sections; their original byte prefixes and hashes are recorded. No source input is edited. Checksums cover every retained output file except SHA256SUMS itself, and both generation and `sha256sum -c` execute with the output as working directory. The tool prints the final manifest hash after it is closed and verified, alongside numeric OFF/ON, perft and FMA stage summaries.

## Tool tests

```bash
python3 -B forge_sol_S28_lock_transition_tests_20261025.py \
  --fixture-tree /absolute/path/to/complete/lock-tree \
  --fixture-net /absolute/path/to/current/nnue_weights.inc \
  --pin-helper /absolute/path/to/forge_sol_S01_rerecord_pins_20261025.py -v
```

Tests create temporary fixtures only below the kit folder and remove those fixtures after the test. They exercise default dry run, output collisions, symlinks, path containment, wrong net/helper/patch hashes, duplicate queues, unsafe paths, option activation validation, LF/CRLF parsing, raw transport, fixed independent oracles, exact known-failure counts, append-only metadata and actual GNU patch original-failure/repair behavior. They do not build an engine, run a native benchmark or establish PC results.

Linux native qualification and the exact write-path trace are reported separately by the coordinating runner. Windows qualification, PC adoption, gate confirmation and Elo are UNVERIFIED by this kit. No default was switched.

The coordinating native matrix began with the frozen v2 implementation. Final v3 adds the exact queued-OFF/base pin equality guard and printed summaries. `forge_sol_S28_native_pin_postcheck_20261025.py` imports those final pure functions and validates original closed v2 pin records read-only. Native run versions and any final v3 rerun are stated separately; a postcheck is not described as a repeated native matrix.
