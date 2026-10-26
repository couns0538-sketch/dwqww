S26 portable Linux setup and v4 launcher, 2026-10-26

Use this launcher for new runs. It delegates to the delivered v4 successor; it does not rerun or replace the historical native observations made with frozen tool `275b2c9a…`. The v4 kit has relocated synthetic process coverage, not a new genuine engine qualification. A different base still needs reviewed test-source and net identities, frozen bench references and the appropriate allowlist.

The extracted root must contain `S26/` and `provided_tools/`. Use an existing Python 3.10+ environment with python-chess available, a compiler supporting the canonical x86-64-v3/znver5/C++20 recipe, CMake, CTest and objdump. No setup command installs packages or changes host limits. The full source tree and NNUE nets are separate caller inputs; they are not reconstructed from this evidence packet.

First create a new owner-local dependency FILE and an empty local resource-lock FILE. Both destinations must be new absolute physical paths inside the extracted packet, with existing parent directories. Setup verifies the exact original dependency JSON, all four delivered helper hashes and v4 SHA256 before creating either output. It preserves all supplied originals. Choose this same lock for every local job that must serialize; setup does not replace another job's existing shared lock.

```sh
S26_PACKET_ROOT="$(realpath -- /absolute/path/to/extracted_packet)"
python3 -B "$S26_PACKET_ROOT/S26/forge_sol_S26_setup_local_dependencies_20261026.py" \
  --packet-root "$S26_PACKET_ROOT" \
  --out "$S26_PACKET_ROOT/S26/owner_dependencies_20261026.json" \
  --lock-file "$S26_PACKET_ROOT/S26/owner_resource_20261026.lock"
```

Then run from any working directory. Replace the base, net and tool paths below with your absolute local paths, and choose a NEW output directory. The bench-reference and allowlist arguments are FILES. The suite is the original delivered WAC300 EPD. The local Python selected by `python3` must be able to import python-chess; activate your existing environment first if needed.

```sh
S26_BASE="$(realpath -- /absolute/path/to/reviewed_source_tree)"
S26_NET="$(realpath -- /absolute/path/to/reviewed_net.inc)"
sh "$S26_PACKET_ROOT/S26/forge_sol_S26_run_v4_20261026.sh" \
  --dependencies "$S26_PACKET_ROOT/S26/owner_dependencies_20261026.json" \
  --base "$S26_BASE" \
  --net "$S26_NET" \
  --out "$S26_PACKET_ROOT/S26/owner_native_NEW_20261026" \
  --bench-ref "$S26_PACKET_ROOT/S26/forge_sol_S26_bench_refs_20261026.json" \
  --allowlist "$S26_PACKET_ROOT/S26/forge_sol_S26_allowlist_20261026.json" \
  --suite "$S26_PACKET_ROOT/provided_inputs/WAC300_original.epd" \
  --lock-file "$S26_PACKET_ROOT/S26/owner_resource_20261026.lock" \
  --cmake /absolute/path/to/cmake \
  --ctest /absolute/path/to/ctest \
  --objdump /absolute/path/to/objdump \
  --cxx /absolute/path/to/g++-14 \
  --record-pins
```

The runner uses one allowed CPU at nice19 under the existing local lock. Optional `--cpu NUMBER` selects one CPU from the caller's current affinity. All generated source copies, build products, raw streams and reports stay in the new `--out`; the launcher itself only executes v4 and forwards the original argument boundaries. Unreviewed pin proposals remain unapplied and cannot permit a failure.

For a separate S43 comparison scope, append `--compare-lock /absolute/path/to/reviewed_lock_source_tree` to the intended first invocation and use its own NEW output directory. That argument is a source DIRECTORY, not an executable or dependency file. It builds and screens a separate private lock copy. This kit's relocated synthetic test covers that path; the historical S26 native runs did not execute this comparison.

The new six-test suite uses exact unchanged S07/S05/S01/S27 helper bytes, exact v4 bytes and the existing hash-bound v4 process fixture. Its fake CMake, CTest, compiler, objdump and UCI engine are Python child processes labelled SYNTHETIC. Two fake candidate copies plus a fake compare-lock copy exercise paths containing spaces, argument forwarding and absolute dependencies. It checks input preservation, wrong helper/v4/declaration hashes, existing outputs and path escapes, and keeps temporary contents below1MiB before cleanup.

The initial RED recorded six missing-setup failures. A first integration attempt at the reused fixture's3s command deadline failed at `ctest_discovery`; its cause remains unresolved. Its CLI failure log is retained, but the fixture's normal temporary cleanup removed the original child raw files and cleanup receipt, so those cannot be independently recovered. A separately declared15s command watchdog was used only for the one final relocated integration attempt; all six tests then passed. No original v4 fixture, negative resource/cancellation threshold or native tool timeout was changed. See the portable-kit receipt for exact sources and log hashes.
