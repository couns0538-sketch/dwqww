# Actual f022 RAM-loader outcome and bounded successor, 2026-10-26

Root authorized exactly one actual frozen63d521 probe in a fresh f022 BUILD
window. It ran CPU1/nice19, all thread limits1, CUDA visibility empty, with a
150-second own-child watchdog and immediate BUILD/BENCH cutoff monitoring.

The attempt finished in31.02 seconds with actual return code1. It independently
verified all129931554 compressed bytes and SHA256, all488851697 decompressed
bytes and SHA256, and all four immutable seals (15). It then failed during
ctypes loading with:

`libgomp-a34b3233.so.1: cannot open shared object file: No such file or directory`

Torch import was not established. No CPU smoke steps, S09 forward/gradient/
export checks, holdout losses or model checkpoints occurred. The absence of
those artifacts is expected, not missing evidence of a claimed pass. Raw
stdout/stderr, controller metadata and the actual result JSON are retained.
The child exited; its memfd/mappings were released. The ordinary CPU library
remains absent, and no library was restored to disk or package edited. The
original missing-library ordinary-import RED remains unchanged.

The precise failing ctypes subcall was not separately instrumented. A second
full attempt was not made. Instead, root authorized a new, tiny dependency
question, using only existing small libraries and no Torch/CPU archive:

- readelf shows the existing hashed-name libgomp has SONAME libgomp.so.1 and
  RUNPATH $ORIGIN. libc10 has SONAME libc10.so and RUNPATH $ORIGIN.
- A child calling bare CDLL(libgomp-a34b3233.so.1) with the ordinary environment
  failed with return code1.
- A fresh child with only LD_LIBRARY_PATH set to the exact private Torch lib
  directory succeeded with return code0; its /proc/maps identified that file.
- Full libgomp/libc10 hashes before and after that tiny question match. These
  are the tiny-question hashes, not retroactively captured f022 pre-run hashes.
- The CPU ELF's DT_NEEDED was not reread because its raw file is absent and no
  second archive decode was authorized. A complete Torch success is not inferred.

This proves the child search-path gap and supports one separate successor.
Original source63d521, the prior322a version, first ordinary RED, full f022
failure and restore-map metadata are all preserved.

The new v2 probe differs only in the f023 window tag and recording its received
LD_LIBRARY_PATH. The separate v2 controller sets the exact private Torch lib
path **before child exec**, leaves the parent environment unchanged, verifies
the v2 source and small-library hashes, requires an active BUILD marker, and
polls BUILD completion/BENCH every0.1 seconds. It kills only its own child group
on deadline or phase transition. Ten toy/source-plan tests pass. Actual v2
archive loading remains UNVERIFIED and awaits explicit root authorization for
a fresh f023 BUILD window. No current retry, Torch import or source change to
the original probe has occurred.

The v2 test packet reuses seven unchanged toy loader/evidence tests and adds
three child-controller tests. Source preparation and tiny-library loading do
not qualify Torch, S09 native1M parity, Std/null-pruning or strength.
