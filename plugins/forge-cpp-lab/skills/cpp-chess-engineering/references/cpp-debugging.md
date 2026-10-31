# C++ debugging and correctness

Start with the failing binary/source/net SHA, compiler/version, exact flags, UCI transcript, FEN **and move history**, threads/hash, warm/cold TT, seed and stopping condition. A FEN alone cannot reproduce repetition history. Verify the native toolchain and C++ standard; do not infer Windows success from Linux or Wine.

## Find the responsible mechanism

1. Reproduce before changing code. Distinguish deterministic logic errors from scheduling, lifetime or timing effects. Minimize FEN/history/command sequence while keeping the defect. A failed-to-start sanitizer is UNVERIFIED, never clean.
2. Compile Release and a separate diagnostic build. Use the project's presets/targets, not guessed FORGE flags. Inspect actual compiler/link commands. GCC/Clang examples of diagnostic flags are `-g -O1 -fno-omit-frame-pointer -fsanitize=address,undefined`; propagate sanitizer flags at link too. Use a separate `-fsanitize=thread` build; do not combine TSan with ASan. Support varies by platform/toolchain. Existing CMake cache values and environment flags can override intent.
3. Preserve complete stderr, exit status and symbolized stack. Use GDB/LLDB breakpoints and native cores/minidumps on the owning machine when permitted. Follow allocation/lifetime/ownership to the first invalid operation, not just the crash site. Inspect C++ signed overflow, invalid shift counts, dangling references/spans, strict aliasing, uninitialized fields, vector reallocation and alignment. Cast after an overflowing operation does not repair it. `volatile` is not synchronization.
4. Reduce to a regression against the real production path. An isolated model test is supplementary. Fix the narrowest root cause. Sanitizer suppression, disabled assertions and changed expected scores are not repairs.

## Chess invariants

After make/unmake, compare board, piece lists/bitboards, occupancy, side, king squares, castling rights, en-passant square, clocks, Zobrist key, repetition stack and NNUE state against an independent recomputation. Cover capture/promotion/underpromotion, en passant discovered check, castling and king-bucket changes, null move, and interrupted searches. Check castling/EP legality, including Chess960 only if supported.

Perft isolates move generation: startpos d5=4865609; canonical Kiwipete d4=4085603 and d5=193690690 at `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`. Use perft divide at the first divergent node. These counts do not validate search scores or evaluation.

Search-specific bugs require search tests: mate/TB score normalization across ply, bound type/depth/context on TT reuse, repetition and rule-50 clocks, checkmate precedence, qsearch stalemate and check evasions before applicable early returns, null-move state, aspiration/PVS re-searches and interruption. A selective-search score difference is not automatically an illegal bound. Test the demonstrated contract; do not disable all pruning merely to make scores equal.

Time management: use monotonic elapsed time from the actual request boundary; test soft <= hard, tiny remaining time, increment >> time, movestogo=1, ponderhit/stop and delayed I/O. Log observed timestamps; last UCI `info time` does not cover later unfinished work.

UCI lifecycle: fresh process, `uci`/`isready`, accepted options, `ucinewgame`, `position`, finite `go`, prompt stop, one bestmove per search, quit/shutdown. Exercise resize/clear during the permitted lifecycle and invalid options. Keep legitimate native stderr as data; on PS5.1 use process APIs/exit status rather than `2>&1` under terminating-error policy.

Record exact pre-existing test failures separately; never silently relabel or adjust expected values. A failed candidate is still useful evidence.
