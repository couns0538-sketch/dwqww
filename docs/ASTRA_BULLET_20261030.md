# Forge Bullet export checkpoint — 2026-10-30

Status: WIP, no training or parity acceptance yet.
Base: astra-a1-data 110f0c4a819756b79a77d88a5ef525b6dafd925b.
Target loader: 7f79c34901fdd118bc4bf904f4bcaec4006047c6 (detached native build source).
Handoff: 1aa5b173; lock source294dbed3a15dfd821aaf9d4edc6e5f62832fd460.

Verified archive SHA256:1d6160dd859740fe617c8dc6c6e6ad8fbcdd0ba40b59ee9cee84342f9202cca5.
Verified fens_12k SHA256:c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265.
Verified embedded lock net SHA256:a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638.

Design: original Python exporter reads Bullet weights.bin with an explicit architecture/tensor/quantization manifest, rejects incompatible architecture, emits R10 K32H3 net and computes an independent integer reference. Native QA loader supplies parity oracle. Standard Bullet network architectures cannot be converted by merely renaming tensors. Supported target must match R10's pairwise FT,32stacks, squared+linear layers and skip outputs.

Runtime limitations: no Cargo/Rust/HIP tools in PATH; official Bullet uses GPU backends and MockGpu cannot train. Actual Bullet smoke training remains blocked unless a compatible trained checkpoint or GPU execution is provided. CMake absent in current PATH; first configure failure saved and a local install is underway. No engine/search changes; no live training/gates touched.

Job2 is separate astra-fen-convert-20261030. Standard Bullet format loses castling,EP,clocks and original side-to-move: exact recovery requires verified row-aligned sidecar. Original game IDs absent; no game-level isolation claim. Full013/014 remain private; handoff says281 retained A1 rows overlap and must be removed on PC.

Next: finish exporter tests, build exact QA source, native12k parity, corruption test,OFF pins; then converter qualification. Reserve20minutes for final bug review. Original logs live validation/astra-bullet-export.
