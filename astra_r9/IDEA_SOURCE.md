# Idea and license provenance

Implementation source: Couns's AL1 s198 lock supplied for this task.
No third-party engine code or constants copied, translated, or paraphrased.
Refresh-cache concept requested by Couns; no GPL source consulted so far.
Python validation dependencies: psutil 7.2.2 (BSD-3-Clause), python-chess 1.999 / chess 1.11.2 (GPL-3.0+), used as external test tools only, not linked or incorporated into engine code.

AVX-512 implementation is original code written from the supplied lock's sixteen-lane
arithmetic contract; no external engine implementation consulted or copied.
Sanitizer toolchain: llvm-mingw 20261020 UCRT x86_64, used as an external diagnostic
compiler only. Its upstream documents Windows ASan/UBSan support:
https://github.com/mstorsjo/llvm-mingw . Archive and bundled licenses retained under
D:\a9\toolchain; production builds use only the unchanged mandated GCC kit.
