# Fast npt loader - behaviour spec (Opus R14-B, own words; UNPROVEN until Engine NNUE / QA accept it)

The fast loader must hand the trainer the same batches, byte for byte, as the npt loader DLL the queue uses
(`F:\opus_scratch\r6\nnue-pytorch-amd\build\libtraining_data_loader.dll`) run with **one decode worker**. This file
describes that behaviour as observed from the old loader (GPL-3.0 nnue-pytorch, read for behaviour only; no code taken).

## 1. Which old stream is the reference
- The old sparse-batch stream splits `--num-workers N` into `max(1, floor(N/4))` feature builders and
  `max(1, N - builders)` decode workers, plus one file reader per two files (at least one).
  N = 1 and N = 2 both give one decode worker and one builder: one thread runs the skip filter and the window
  shuffles, so the output is a pure function of the file. N = 4 (the live npt line) has three decode workers that race
  for chunks and each keep their own filter state: the order changes from run to run and cannot be reproduced.
- Reference = `--num-workers 1`. The fast loader produces that stream for any thread count.

## 2. File format accepted (fail closed otherwise)
- One binpack file per stream. A file is a sequence of chunks: 4 bytes `BINP`, 4-byte little-endian payload size
  (<= 100 MiB), payload. At end of file a cyclic stream starts again at the first chunk.
- Payload = records, each a 32-byte packed entry followed by a 2-byte big-endian ply count of a move chain.
  Records are read while at least 34 bytes remain; shorter tails are ignored. **Only chain length 0 is accepted**
  (the J1 files are unchained: 34 bytes per record); any other value stops the loader with an error.
- Packed entry (big-endian fields): bytes 0-7 occupancy bitboard (bit i = square i, a1 = 0, h8 = 63);
  bytes 8-23 one 4-bit code per occupied square in ascending square order, low nibble first; bytes 24-25 move
  (not used); bytes 26-27 score; bytes 28-29 `ply` in the low 14 bits and the game result in the top 2 bits;
  bytes 30-31 fifty-move counter (not used).
- Score and result use a zig-zag style 16-bit code: decode `u` by rotating it right by one bit and, if the top bit
  is then set, flipping the low 15 bits; the result code is the top two bits (0 -> 0, 1 -> -1, 2 -> +1).
- Piece codes: 0-11 = piece type * 2 + colour (pawn, knight, bishop, rook, queen, king; white 0, black 1);
  12 = pawn with an en-passant square behind it (white if on rank 4, else black); 13 / 14 = white / black rook with a
  castling right; 15 = black king with black to move. Side to move is white unless code 15 occurs.
- More than 32 occupied squares, or a missing king of either colour, is a format error.

## 3. Skip filter (one sequential pass in file order; state lives for the whole stream)
State: `last_ply = -1`, `last_score = NONE (32002)`, the piece-count history (33 counters + total, all 0), the
number of records that reached the piece-count stage, `alpha = 1`, and one `mt19937_64` with its default seed.
For each record, in this order:
1. `placeholder = ply > last_ply and last_score != NONE and |last_score| > 100 and result != 0 and score == 0`;
   then `last_ply = ply`.
2. score == NONE -> skip. placeholder -> skip. Then `last_score = score`.
3. `ply <= early_fen_skipping` -> skip.
4. If `random_fen_skipping` r > 0: one draw; skip if `draw < (u64)((r / (r + 1)) * 2^64)`.
5. (`filtered`, `wld_filtered`, `simple_eval_skipping` > 0 are rejected at start-up: not in the npt line.)
6. If `soft_early_fen_skipping` S > 0 and `ply < S`: one draw; skip if `draw < (u64)((1 - a[ply]) * 2^64)`, where
   `a` linearly interpolates the points (ply_x1, ply_y1) .. (ply_x4, ply_y4), (S, 1), clamped to [0, 1].
7. Piece count `pc` = popcount(occupancy). Count it in the history (counter[pc] + 1, total + 1, steps + 1).
   At steps 100, 500, 1000, 2500, 5000 and every multiple of 10,000 above 5,000: recompute
   `alpha = (1 - 0.975) / min_pc ratio(pc)` over the piece counts with a positive target weight and a positive count,
   where `ratio(pc) = (total * w[pc]) / (W * counter[pc])`, `w` = the 5-point cubic Hermite spline of
   (0, pc_y0), (8, pc_y1), (16, pc_y2), (24, pc_y3), (32, pc_y4) with central-difference slopes (one-sided at the
   ends), floored at 0, and `W` = the sum of the 33 weights; at multiples of 10,000 also halve all counters and the
   total, after computing alpha.
8. `accept = clamp(alpha * ratio(pc), 0, 1)` (0 if w[pc] or counter[pc] is 0); one draw; skip if
   `draw < (u64)((1 - accept) * 2^64)`. Otherwise keep the record.
The double-to-u64 conversions truncate; `2^64` is `(double)(2^64 - 1)`.

## 4. Shuffle windows (same engine as the filter)
- Kept records collect in a 16,384-entry scratch. When the scratch is full it is appended to the open window; a
  window that reaches its capacity (`shuffle_buffer_entries`, default 1,048,576) is sealed and shuffled at that moment
  with `std::shuffle` (libstdc++) on the same `mt19937_64`, before the next record is filtered. A scratch larger than
  the remaining space spills into a new window.
- Non-cyclic stream at end of file: the remaining scratch is appended (same rule), then a non-empty open window is
  sealed and shuffled.
- Output order = the sealed windows one after another, each in its shuffled order. Batch k = output entries
  [k * B, (k + 1) * B); a batch may span two windows; the last batch of a finite stream may be short.

## 5. Batch content (SparseBatch memory layout read by the trainer's `get_tensors`)
- Header: num_inputs = 73,728 (768 planes x 32 king buckets x 3 states), size, three float pointers, the white and
  black active-feature totals, max_active = 32, four int pointers.
- Float block, contiguous: is_white[size] (1 if white to move), outcome[size] = (result + 1) / 2, score[size].
- Int block, contiguous: white[size * 32], black[size * 32] (unused slots -1), piece_count[size],
  queen_bucket[size] = 2 * (side to move has a queen) + (opponent has a queen).
- Features of row i for perspective c: let k = c's king square, `h` = k on files a-d; orient(s) = s, mirrored
  vertically for black, then mirrored horizontally if `h`. King bucket = 31 - (4 * rank + file - 4) of orient(k).
  State = 2 if c's opponent has a queen, else 1 if any rook or queen is on the board, else 0.
  For every occupied square s in ascending order with piece (type t, colour q):
  `feature = orient(s) + 64 * (2 * t + (q != c)) + 768 * (32 * state + bucket)`.

## 6. Fast-loader design (performance only; output must not depend on it)
reader thread (chunk queue) -> one filter thread (section 3 + window bookkeeping of section 4; shuffles a 4-byte
index permutation instead of moving records) -> batch tasks in order -> N builder threads (section 5; batch k goes
to output k, buffers are taken in task order so no deadlock) -> consumer takes batches in order.
