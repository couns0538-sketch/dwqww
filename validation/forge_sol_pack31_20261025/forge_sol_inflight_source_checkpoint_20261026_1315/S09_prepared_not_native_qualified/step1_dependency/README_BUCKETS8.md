# buckets8 — 8 piece-count output heads for the Forge H256 residual NNUE

Status: **STEP 1 (plumbing proof) — UNPROVEN, no Elo claim, do not gate.**
All 8 heads are exact copies of the h256_e12 head, so evaluation, search and bench are identical to the lock by construction.
Step 2 = Engine NNUE's trained 8-head net dropped in as `src/nnue_weights.inc` (no code change).

## What the engine does
Accumulator (768 -> 256 per perspective, float, incremental) is unchanged. The output layer
`out = bias[h] + sum_j SCReLU(stm_j)^2 * W[h][j] + SCReLU(opp_j)^2 * W[h][256+j]` now uses head
`h = output_head(pieces)`, where `pieces = popcount(all occupied squares)` **including both kings**:

    h = clamp((pieces - 1) >> 2, 0, 7)
    pieces: 2-4 -> 0 | 5-8 -> 1 | 9-12 -> 2 | 13-16 -> 3 | 17-20 -> 4 | 21-24 -> 5 | 25-28 -> 6 | 29-32 -> 7

(Head 0 covers 3 legal counts, all others 4. Counts are clamped, so any index is in range.)
Head is chosen from the position being evaluated (after the move), not from the root.
cp = trunc(clamp(out * 400 / 2.25, -30000, 30000)), residual: engine eval = HCE + cp (unchanged).
Lane order of the float sum is the lock's (16 lanes, fixed association), so builds stay bit-identical across SSE/AVX2/scalar.

## .inc layout for an 8-head net (what Engine NNUE must export)
Same file as today's `train_resid.py` export, plus one define and two resized output arrays:

    #include <cstdint>
    #define FORGE_NNUE_RESIDUAL 1
    #define FORGE_NNUE_OUTPUT_HEADS 8          // new; omit (or 1) = legacy single head
    static_assert(forge::nnue::InputCount == 768 && forge::nnue::HiddenSize == 256, "...");
    static_assert(forge::nnue::SigmoidK == 2.25F, "...");
    static_assert(forge::nnue::WeightScale == 4096.0F && forge::nnue::OutputScale == 4096.0F, "...");
    static const std::int16_t NnueW1[196608] = { ... };   // [768 features][256 hidden], round(w*4096), unchanged
    static const std::int16_t NnueB1[256]    = { ... };   // round(b*4096), unchanged
    static const std::int16_t NnueW2[4096]   = { ... };   // [8 heads][512], HEAD-MAJOR:
                                                          //   NnueW2[h*512 + j]       = stm hidden j   (j < 256)
                                                          //   NnueW2[h*512 + 256 + j] = opp hidden j
                                                          //   value = round(w*4096)
    static const std::int16_t NnueB2[8]      = { ... };   // per-head bias, round(b*4096)

- All int16 (quantised by 4096, de-quantised to float at load; float inference, never int16 inference).
- `FORGE_NNUE_OUTPUT_BUCKETS 8` (the bde3dc9d spelling) is also accepted as an alias.
- Shape/size mismatches are compile errors (static_asserts on W1, B1, W2 = heads*2*H, B2 = heads).
- A legacy single-head include (scalar `NnueB2`) still builds: its head is copied into all 8 heads at load.
- Training target/feature definition is unchanged (residual, sigmoid K 2.25, 768 features, perspective flip `sq ^ 56`).
  The trainer must compute the head with the SAME formula from the training position (pieces incl. kings) — off-by-one here silently mis-trains.
- Check a new export with `python3 tools/nnue/make_heads_inc.py check <file.inc> --hidden 256`
  (prints heads, sizes, which heads are identical). Step-1 file was made with `make_heads_inc.py replicate`.

## Parity / proof tools (tools/nnue/)
- `make_heads_inc.py` — replicate | check | control (control = TEST ONLY: head k bias += (k+1)*64 so heads differ).
- `heads_parity.cpp` — links against any Forge core (lock or this tree); per FEN prints head, net cp, HCE cp and incremental==refresh over 8 random plies.
  Build: `g++-14 -std=c++20 -O3 -DNDEBUG <same -march/-ffp-contract flags> -DFORGE_NNUE_HIDDEN=256 -Iinclude tools/nnue/heads_parity.cpp build_release/libforge_core.a -pthread`.
- Step-2 export check suggestion: build heads_parity with `-DFORGE_NNUE_WEIGHTS_FILE="\"/path/net.inc\""` on src/nnue.cpp and compare net cp against the trainer's forward per head (as check_export.py does for 1 head).

## Build (box, same as lock)
    nice -n 19 cmake -S . -B build_release -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++-14 \
      "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
    nice -n 19 cmake --build build_release -j1

## Windows (MSYS2 UCRT64 g++ 15.2, fresh tree)
    g++ -std=c++20 -O3 -DNDEBUG -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -DFORGE_NNUE_HIDDEN=256 -Iinclude src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp src/uci.cpp -o forge_buckets8_h256e12.exe
Not LLVM/clang. Bench must equal the h256_e12 lock exe built with the same line; `objdump -d exe | grep -c vfmadd` = 0.
