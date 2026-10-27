# S24: int32 shelf default-build guards

`forge_sol_S24_int32guards_20261027.patch` applies on top of Sol's shelved `forge_sol_exactint32_h256e12_20261025.patch`
(sha256 e661a145…). Order: lock tree → `git apply -p1 <shelf patch>` → `git apply -p1 forge_sol_S24_int32guards_20261027.patch`.

With `FORGE_NNUE_EXACT_INT32_AVX2` off (the default), the result answers `uci` and `bench` exactly like the lock.
With the macro on, the experiment is unchanged: the option, the activation line and the stats line after bench.

`verify_s24.sh <repo> <shelf patch> <lock exe> <build_pc.sh> <uci_check.py> <python> <new dir>` rebuilds and
checks everything from scratch.
