# Astra round 2 B3 — NNUE v2 loader preflight regression

Base: `b7c177222038e9332965a95ec53ea3b94e90dbc9`, `origin/forge-bundle-int`.
Branch: `astra2-nnue-loader`, independently based on the bundle.

**Existing protection verified; no engine repair was needed.** The bundle already seeks the file size,
checks the supported maximum, reads/validates only the fixed 160-byte header, and checks the size implied
by that header before allocating or reading weights (`src/nnue.cpp`, `nnue::v2::load`). This is the
bundle's FORGENN2 v2 loader. No NNUE-v3 source, format or option was ported or claimed fixed.

IDEA_SOURCE: Forge's documented v2 format and its existing loader/tests. Original focused fixture writer
and regression. No code or tuned constants from another engine.

The added test isolates preflight from the much larger accumulator/parity suite. It uses a small
streaming zero-network writer solely as a valid loader control. Before each rejection, the test loads
and activates that control; after rejection it checks that both the loaded and active pointers are null.
Invalid files are written sparsely, using only a 160-byte header and a final byte, without allocating an
oversized payload buffer. Every execution creates its own new directory and preserves all fixtures.

| Input | Logical bytes in H256 build | Expected payload reads | Verified |
|---|---:|---:|---|
| Empty file | 0 | 0 bytes total | PASS |
| Truncated header | 159 | 0 bytes total | PASS |
| Truncated payload | 394921 | 160-byte header only | PASS |
| Extra payload byte | 394923 | 160-byte header only | PASS |
| Wrong magic | 394922 | 160-byte header only | PASS |
| Unsupported version | 394922 | 160-byte header only | PASS |
| Wrong hidden width | 394922 | 160-byte header only | PASS |
| Oversized sparse file | 18236105 | 0 bytes total | PASS |

Every case returned false with the expected descriptive error and cleared the previously active net.
The valid control reads all 394922 bytes. Empty-file rejection also works with a null error-output pointer.
These counters are the existing loader's `last_load_bytes_read()` diagnostics, supported by inspection of
its allocation/read order; this is not a separate operating-system I/O trace.

Focused native result: **41 checks / 0 failures, exit 0**, against the **unmodified baseline core**.
There is no before-fix failure because the requested preflight behavior already exists. No new UCI option
is needed: engine files are unchanged. No speed or Elo claim.

## Exact focused commands

```
g++-14 -std=c++20 -O2 -pthread -DFORGE_NNUE_HIDDEN=256 -Iinclude \
  tests/nnue_loader_preflight_tests.cpp \
  /tmp/forge-astra2-build-base/libforge_core.a -o /tmp/astra2_b3_preflight_base
/tmp/astra2_b3_preflight_base /tmp/astra2_b3_preflight_fixtures
```

The linked baseline core was built by the root with GCC 14.2, C++20 Release,
`-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`.
`focused_receipt.json` identifies exact source/core/executable hashes and commands. Original output is
`focused_base.log`; the compiler output is `focused_build.log`. `fixture_manifest.json` records every
fixture's deterministic hash, logical size and actual allocated bytes. Large fixtures are not committed;
the preserved test regenerates the same bytes. Existing general v2/UCI tests remain enabled.

After a normal CMake build:

```
ctest --test-dir BUILD -R '^forge_nnue_loader_preflight_tests$' --output-on-failure
```

The new CTest has a 30-second timeout. Complete build/CTest, bench and perft qualification is root-owned;
those conclusions require their final raw logs, not just this focused pass. Windows execution is UNVERIFIED.

## Final complete qualification

Commit `951a57787edf529cb9fb4f76125fa3b22d5c86b0` adds tests only. Complete Release build PASS.
Native loader preflight **41/41**; full CTest **55/56**, only the four known `forge_tests` diagnostics.
OFF bench d11/13/16/20/22: **312866 / 862329 / 3024920 / 12389307 / 34048354**.
Perft5 **4865609**; NNUE FMA **0**. Full commands/configuration and binary hash: `qualification.json`.
The built engine SHA256 equals the untouched baseline exactly:
`c87c99aae9f3c1248d9dd468e584099d5313566e5407d7a5aa456f9852b80397`.
Original CTest output including successful tests is under `ctest/`; each bench record is in `BENCH_RESULTS.md`.
No engine gap was found, so no engine patch or UCI option was added. No speed/Elo claim.
Porting and repairing the separate v3 loader from fable-nnue-arch remains a later job.
