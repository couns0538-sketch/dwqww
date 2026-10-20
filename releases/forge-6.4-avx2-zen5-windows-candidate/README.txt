Forge 6.4 AVX2 candidate for Windows x64 / Ryzen 7 9850X3D (Zen 5).

Candidate, not an accepted strength release. No verified Elo improvement or victory over full-strength Stockfish is claimed. Clock overruns interrupted strength trials on the cloud VM.

NNUE output arithmetic is wider; tested evaluation streams match baseline byte-for-byte on Linux and Windows Wine. Linux4/4CTest and Windows core/UCI/ponder checks pass. Windows baseline/candidate bench11 signature:343022.

Built with verified LLVM-MinGW 20261006/Clang23.1.3: Release, -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static. Tested under Wine10, not native Windows or the physical Ryzen. Requires a Zen5-compatible x64 CPU and Windows UCRT system DLLs (Windows10/11).

Point your UCI chess GUI at forge-6.4-avx2-ryzen-9850x3d.exe. Start with Threads=1, Hash=256; choosing more threads is a separate strength/runtime experiment. For controlled comparisons use OwnBook=false and identical resources. This build reports engine version6.4.0.

Source/evidence: https://github.com/couns0538-sketch/dwqww/tree/forge/nnue-avx2-9850x3d
See validation/nnue-avx2-9850x3d/README.md for complete evidence and limitations.
