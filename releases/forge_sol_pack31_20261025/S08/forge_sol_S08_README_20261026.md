# Forge S08 delivery — 2026-10-26

The report records actual results and limitations. All files are listed in `forge_sol_S08_SHA256SUMS_20261026.txt`; check it from this folder with `sha256sum -c forge_sol_S08_SHA256SUMS_20261026.txt`.

Apply `forge_sol_S08_profcounters_TLS_v2_20261026.patch` and the corresponding `forge_sol_S08_documentation_{L,Lprime,B}_TLS_v2_20261026.patch` to a NEW copy of the matching supplied base. The core patch applies unchanged to all three. Do not patch the original input.

Example Linux commands, using fresh source/output paths:

```sh
git -C "$NEW_SOURCE" apply --check "$DELIVERY/forge_sol_S08_profcounters_TLS_v2_20261026.patch"
git -C "$NEW_SOURCE" apply "$DELIVERY/forge_sol_S08_profcounters_TLS_v2_20261026.patch"
git -C "$NEW_SOURCE" apply "$DELIVERY/forge_sol_S08_documentation_Lprime_TLS_v2_20261026.patch"
cmake -S "$NEW_SOURCE" -B "$NEW_BUILD" -DCMAKE_BUILD_TYPE=Release \
  -DFORGE_NATIVE=OFF -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF -DFORGE_PROF=ON \
  -DCMAKE_CXX_FLAGS='-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
cmake --build "$NEW_BUILD" -j1
printf 'bench 11\nquit\n' | "$NEW_BUILD/forge"
# Proceed only if first d11 is 308972:
ctest --test-dir "$NEW_BUILD" --output-on-failure
printf 'bench_prof 11\nbench_prof 13\nbench_prof 16\nbench_prof 20\nbench_prof 22\nquit\n' | "$NEW_BUILD/forge"
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v test_forge_sol_S08_delivery_20261026.py
```

`FORGE_PROF` is OFF by default; the compiled-ON build has `Profile=false` by default. `bench_prof` opts into counters independently of ordinary `bench`. For ordinary searches, set `Profile=true` before `go`. The collector's `--help` describes bounded collection, manifest and new-output requirements. Resolve the delivered corpus manifest from its `corpus/` directory; do not reinterpret its relative paths.

These commands are a short reproduction entry point, not a replacement for the report's full frozen UCI/perft/sanitizer evidence. No Windows test, speed gain, Elo gain or lock switch is asserted. The accepted source/network are unchanged.
