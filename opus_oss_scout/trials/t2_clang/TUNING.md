# T2 clang build: PC-specific ideas for the crew (not tried in this job unless RESULT.md says so)

1. **Library choice decides node identity, not the compiler.** With its own libc++, clang 23 gives other bench nodes
   (d11 369996, net-off 369292). With MSYS2's GCC 15.2 runtime it gives the lock's nodes:
   `--sysroot=C:/msys64/ucrt64 -stdlib=libstdc++ -rtlib=libgcc -unwindlib=libgcc`.
   - Cause: the MovePicker sorts with `std::sort` (search.cpp:632), which leaves ties in a library-specific order.
   - The R12 / speed-job note "MSVC ASan build of the lock source: bench 16 = 2587341" is very likely the same effect
     (MSVC STL sort).
2. **Make every toolchain node-identical (Coder + owner).**
   - Replace the tie-dependent `std::sort` by an own stable sort (or `std::stable_sort`; the stable order is defined
     by the standard), and build the LMR table without libm (`std::log`), e.g. an integer table or a constexpr log.
   - This changes node counts once (a new lock and new pins). After that, MSVC / clang-cl / libc++ / ASan builds would
     all match the lock, and QA's MSVC ASan level would stop being "N/A".
3. **A clang path for QA's kit.** Add a clang 23 + libstdc++ line to the kit: ThinLTO + IR PGO with the kit's own
   workload. QA would then time it against the g++ kit build with its ABBA rules. T2's screening number is in RESULT.md.
4. **CS-IRPGO.** `-fcs-profile-generate` on top of the IR profile (one more training run), then
   `llvm-profdata merge` of both profiles. LLVM's context-sensitive PGO often gains a little over plain IR PGO; not
   measured here.
5. **Workload.** Kit workload v1 runs only benches (OFF path). As the 30-h job found, an option-only path stays
   PGO-cold. Use the kit's v2n / mix workloads for a clang build too.
6. **Flags to sweep later (one at a time, ABBA each):**
   - `-mprefer-vector-width=512`: the net kernels use ZMM with NNUE_ZMM.
   - `-flto=full` vs thin.
   - `-mllvm -enable-ext-tsp-block-placement`: block layout, the in-compiler relative of BOLT, which cannot run on
     Windows PE.
   - Each needs its own pin_check.
7. **Installed LLVM 18 + VS 18 do not mix.** The VS 18 STL (14.51) requires clang >= 20 (STL1000). Keep using
   llvm-mingw (portable, no PATH change), or have the owner install a newer LLVM for clang-cl.
8. **Debug info for profiling.** llvm-mingw writes a PDB with `-g -gcodeview -Wl,--pdb=<file>`, which Windows
   profilers (samply, WPA, uProf) read. A PDB build of the exact lock flags is a cheap way to get symbols for T3-style
   profiles.
