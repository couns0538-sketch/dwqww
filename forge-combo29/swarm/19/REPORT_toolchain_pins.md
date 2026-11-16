# REPORT — are the node-count pins tied to the standard library version, or only to the algorithm?

seat 19 · area 9 · branch `for-fable-and-opus/swarm-19`
Follow-up question from the coordinator, deciding how bad the 19-F16 risk is.

## 1. The three lines

**What was asked.** 19-F15 showed that replacing `std::sort` with `std::stable_sort` moves three of the four
honesty numbers, and 19-F16 said the pins therefore depend on libstdc++'s current `std::sort` tie behaviour.
The question: **does that dependence actually exist across standard-library versions?** Build the same
unmodified source with older g++ (12, 11) and see whether bench 11/13/16 hold. "Record whichever answer you
get, including 'toolchain not available'."

**The answer.** **The pins hold exactly.** g++ 13.3.0, g++ 12.4.0 and g++ 11.5.0 — three *genuinely different
binaries* (three different sha256 hashes) — all report bench 11 = **312,866**, bench 13 = **862,329**,
bench 16 = **3,024,920**, perft 5 = **4,865,609**. So the risk in 19-F16 is **theoretical for the toolchains
tested** and should be stated that way.

**How sure.** Certain of the measurement: three compilers, fresh build directories, same CMake release flags,
one fresh engine process per honesty line, raw output kept for each. Not tested: older than g++ 11 (not
available from this distribution), and not tested against a different libstdc++ *runtime* than the system one.

## 2. The numbers

| compiler | bench 11 | bench 13 | bench 16 | perft 5 | binary sha256 (first 12) |
|---|---|---|---|---|---|
| g++ 13.3.0 (baseline) | 312,866 | 862,329 | 3,024,920 | 4,865,609 | `e06310eca336` |
| g++ 12.4.0 | 312,866 | 862,329 | 3,024,920 | 4,865,609 | `976a24c3c10c` |
| g++ 11.5.0 | 312,866 | 862,329 | 3,024,920 | 4,865,609 | `daba9373842d` |

The binaries differ — `sha256sum` over the three build directories returns 3 distinct hashes — so this is not
"the same binary three times". Each compiler produced its own code, and the tree the search explores is
identical in all three.

Command: `bash forge-combo29/swarm/19/toolchain/toolchain_pins.sh ~/base/forge-combo29 <outdir> g++-13 g++-12 g++-11`

## 3. Answering the question directly

**"Does the pin drift depend on the standard library version or only on the algorithm?"**

- **Across the three toolchains tested: only on the algorithm.** The `std::sort` tie behaviour that 19-F15
  exploits is evidently the same in libstdc++ 11, 12 and 13 for these ranges, so the pins do not move.
- **So the 19-F16 risk is theoretical, not live.** I said in 19-F16 that "a standard-library upgrade could
  silently move them". That statement should be read as *unverified* at the time I wrote it, and this test
  now **weakens** it: two older major versions do not move the pins. What remains true is the narrower
  claim from 19-F15: the pins depend on *some* property of the sort, because a stable sort moves them. That
  is a fact about the algorithm choice, and it does not imply fragility to a version bump.

## 4. Table: step | done-partly-not done | evidence file | result

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| older compilers available from the distribution | done | `toolchain/out/meta_g-12.txt`, `meta_g-11.txt` | g++ 12.4.0 and 11.5.0 installed via apt |
| same unmodified source, same flags, three compilers | done | `toolchain/toolchain_pins.sh` | pristine `~/base/forge-combo29`, three build dirs |
| four honesty numbers on each | done | `toolchain/out/bench_*_{g-13,g-12,g-11}.txt`, `perft5_*` | all twelve equal the committed pins |
| prove the three builds are not the same binary | done | `toolchain/out/meta_*.txt` | 3 distinct sha256 values |
| test a toolchain older than g++ 11 | **not done** | — | not available from this Ubuntu release; I did not add a third-party repo |
| test a different libstdc++ runtime (e.g. an older .so at run time) | **not done** | — | all three builds link the system `libstdc++.so.6`; the `.so` version is not what changed here, the compiler was |

## 5. Finding

**19-F17 — the four node-count pins are stable across g++ 11.5.0, 12.4.0 and 13.3.0, so 19-F16's
standard-library risk is theoretical, not live.**
Three different binaries, all twelve honesty numbers identical. This does not retract 19-F15 (a stable sort
does move the pins); it bounds 19-F16 (the pins did not move across two earlier major libstdc++ versions).
Practically: a seat can build this source with any of these three compilers and compare bench numbers
directly.

### Suspicions, not proven

- That the *reason* the pins hold is that the compared ranges are short enough for libstdc++'s insertion-sort
  path, whose tie behaviour has been unchanged for a long time. Plausible and consistent with the data, but I
  did not read three versions of the libstdc++ headers to confirm it.
- That a 32-bit build, or a libc++ (clang) build, would behave differently. Opus's file 1 says the PC uses
  clang with ThinLTO; I did not test clang here, and that is the case most worth testing next if anyone has
  clang on the machine.

## 6. What I did NOT do

- No clang build. The owner's PC uses clang, and clang uses libc++ or libstdc++ depending on the flag — that
  is the untested gap that matters most for the PC, and I am naming it rather than papering over it.
- No toolchain older than g++ 11.
- I did not test whether *any* source edit plus a compiler change interacts; only the unmodified source.

## 7. What I am NOT sure about

- Whether clang's `std::sort` (with either library) gives the same tie order. Untested, and it is the one
  that matters for the PC build.
- Whether optimisation flags other than `-O3` (e.g. the PC's ThinLTO+PGO) change tie order. Untested.

## 8. Times and files

`toolchain/out/meta_*.txt` carry the compiler version, exe path, sha256, `id name` and the linked libstdc++
for each build. Files: `toolchain/toolchain_pins.sh`, `toolchain/out/` (12 raw engine outputs + 3 metas).
