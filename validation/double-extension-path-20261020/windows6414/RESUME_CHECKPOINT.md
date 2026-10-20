# Forge 6.4.14 Windows checkpoint

Completed from exact frozen source21538ec5416c909fc98a08688242a0b3b9710b25,
parentcecf0b9e3af5602053bcaf5c5d16ffc09f58850d. One-job LLVM-MinGW23.1.3
C++20 Release/staticZen5 build preserves strict float/no-FMA flags. Only search
path bookkeeping and version labels changed; NNUE/evaluation/network inputs
remain byte-identical. Source export and all186parent records stayed unchanged.

All eight Wine checks passed: core/perft, coherentTT8, rule50,18,947legal-witness
comparisons, UCI, ponder, OwnBook5 and bench11 at351,063nodes. SIMD/output-layer
checks pass. The independent artifact review passed914/914checks and ran no
engines. No new NPS, strength, native Windows/Ryzen or Stockfish result exists.

Release: releases/forge-6.4.14-candidate-windows-zen5.zip
Release SHA256: 6364f10a3aa1240fe1a8567e67b0720e1d015ce0bd1f0f26e384813b517ec269
Exact tested engine SHA256: 9db37be54c7b3407096a0721f07f9ab622f396e8b9260966915fe325707fd715
Actual core SHA256: 796bd5359e250df611af7bd769c60535b4e4c45f6b8c1253d36d56c479061e4e
Raw Windows original archive SHA256: 569921a209e973297845a4cd2ccc720ef60991b39eb213f9171abe68352d410f

windows-originals.zip contains156immutable original files plus its manifest:
sixPEfiles, actual core, frozen source, exact commands/build flags/test logs and
disassembly. Packaging captures and audit outputs follow that immutable snapshot
and are covered by final evidence-SHA256.json. Packaging captured its own
stdout/stderr outside the snapshot before copying completed records, preventing
self-changing archive members. All originals remain on disk.

Build, validation and package phase commands each returned0. No failed build or
Wine attempt occurred. No production file or Git state was changed by this task.
The parent may now archive/commit the complete owned evidence and release paths.
Native sanitizer results are tracked separately by the parent and were not
asserted by this Windows packaging task. All owned files are final.
