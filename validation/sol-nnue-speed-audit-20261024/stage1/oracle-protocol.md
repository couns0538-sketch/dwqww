# Original bounded actual-core million-position oracle

This is arithmetic correctness evidence only. It is not a timing or playing-strength experiment.

The original driver `tools/nnue_million_oracle.cpp` is linked separately against the actual frozen OFF and ON `libforge_core.a` archives. The acceptance run executes both resulting programs freshly. The baseline is lock commit `f4911f2709bd5ae7e5fca7aea30aac5d87314a05`; the network SHA256 is `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`. Stage 1 uses actual ON NNUE source SHA256 `e074f3eaf1a40c929cd16d1937f34fe75d4d7a44ef35a8f8e3fc27014a74cb45`. `STAGE1-PROVENANCE.json` is the authoritative pre-run source/archive/binary pin set. It supersedes the initial pre-hardening `PROVENANCE.json`.

## Corpus and exact observations

The fixed seed is `0x243f6a8885a308d3`. Ten board fixtures exhaust every legal first move before random sampling. They guarantee both colors' captures, en passant, both castles, and all four quiet and capturing promotion types. Subsequent independent deterministic legal walks start from those fixtures and last at most 192 plies. Terminal positions restart the walk. Every counted record corresponds to an actual `forge::Board`, with side, 64 actual piece values and board key included in its record. Repeated positions are not presented as unique positions.

Each of the 1,000,000 records independently records every float bit of both perspectives in the incremental accumulator, its actual `nnue::evaluate` integer and validity; it also records every float bit and eval integer from an independent actual `nnue::refresh` of the same board. Incremental and refreshed arrays are compared to their respective fields in the other executable. Their arithmetic histories are not assumed equal to one another.

For every actual move, the driver checks that a distinct-child update leaves every parent float bit and validity unchanged. It also executes an in-place update and checks all its float bits and validity against the distinct child. Initial fixture/walk boards have no predecessor; they record actual refresh results in both array fields. All remaining records derive from actual incremental transitions. A checked trailer records the exact counts of starts, updates, refreshes, parent checks, in-place checks and all guaranteed special types/colors. The fixed header records H256, seed, count, rounding mode and MXCSR controls. The driver requires round-to-nearest and finite observed arrays; NaNs and other rounding modes are outside this corpus.

The existing unchanged `tools/nnue_snapshot.cpp` and `tools/nnue_update_snapshot.cpp` remain independent required supplemental runs. In particular, the latter supplies all 31 generic dirty count/flag patterns, invalid input validity, count-zero copying, signed zero, subnormal and extreme finite synthetic boundaries. Those synthetic cases do not count toward the million genuine board records.

## Byte format and retained evidence

All integer/float-bit words use explicit little-endian serialization without object padding. The header is 64 bytes, each H256 record is 4,216 bytes, and the trailer is 256 bytes. A complete one-million-position stream is therefore exactly **4,216,000,320 bytes per executable**.

The Python runner consumes bounded original stdout chunks (10,000 records each for acceptance). It records independent SHA256 state and byte counts for each entire actual stream, not hashes of another executable's output or a regenerated digest stream. It invokes external `cmp` on every pair of original raw chunks. A mismatch, identical truncation, extra data, invalid header/trailer, incomplete coverage or actual nonzero producer exit is a failure. Partial original chunks and process stderr are retained on failure.

After a raw chunk pair passes `cmp`, SHA256 and length equality, each stream's own raw chunk is independently gzip-compressed with deterministic metadata and level 6. Each archive is decompressed and checked for the original SHA256 and byte count. Both compressed files also pass `cmp`, SHA256 and size equality. Only then are the two new equal archives hardlinked together and made read-only. Each path still losslessly represents its original executable's bytes. The raw chunk files are removed after those proofs; no historical files are opened for writing. Reconstruction is gzip-decompression and concatenation in manifest chunk order. This produces the original stream SHA256 recorded separately for OFF and ON.

An optional later run may use `--dedup-reference-result` with an earlier successful result. Both actual executables still run freshly; all new raw and compressed comparisons above still happen. The runner rejects incompatible corpus/chunk metadata and verifies the canonical prior archive's immutable mode, actual SHA256 and size, plus external `cmp` from each freshly compressed output. It records the reference manifest/source/binary hashes and canonical SHA256 before and after hardlinking. Only new paths are replaced; the canonical inode and its historical paths remain untouched. A differing/corrupt canonical preserves new raw originals and fails.

## Negative controls and resource bounds

Eight focused runner tests passed before source freeze. They cover positive lossless reconstruction, one changed accumulator bit, one changed eval integer bit, identically truncated producers, nonzero producer exit after complete equal output, a hung producer, fresh-run cross-reference deduplication, and intentional canonical corruption. RED logs and the final `runner-eight-green.log` are preserved here. Actual-record one-bit float/eval negative controls are also retained by every real run, and must each produce `cmp` exit 1.

The pilot was a freshly executed OFF/OFF run of 10,000 real positions: 42,160,320 original bytes per stream, SHA256 `0956190dfd392e758d5324e8619a1e6910b7f99e98e5a2dc4b709afa3880197e`, and 13,609,118 physical gzip bytes after proven deduplication. This projects approximately 1.361 GB retained for one million positions, subject to actual later corpus compression. The runner checks disk space before each chunk, reserving 512 MiB plus four worst-case chunk sizes. With 10,000-record chunks the raw pair uses about 84.32 MB. The second compatible fresh run can share already proven canonical gzip inodes.

The acceptance wrapper uses an internal producer watchdog of 2,600 seconds and outer GNU `timeout --kill-after=10s 2700s`. It preserves PID, UID, process start ticks, actual argv, raw stdout/stderr logs and actual outer return code in `stage1-process-record.json`. Producer return codes and independent original-stream hashes/counts are in the result manifest. No benchmark claim is drawn from pilot or oracle elapsed time.

## Build and run protocol

Compiler: `g++ (Debian 14.2.0-19) 14.2.0`.

Both driver links use `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread` and the frozen include directory. The ON driver additionally defines `-DFORGE_AVX512=1`, and links the actual ON core; the OFF driver links the actual lock core. `nnue.hpp` in the candidate and lock exports has the same SHA256. Build logs are `build-lock-driver.log` and `build-avx512-1-driver.log`.

Stage 1 command is preserved literally in `run_stage1.py`, with output in `../oracle-avx512-1/`. Sources `tools/nnue_million_oracle.cpp`, `tools/nnue_million_oracle.py` and `tools/test_nnue_million_oracle.py` are frozen until the run closes. The stage 1 actual ON NNUE source and core archive are also copied here read-only to preserve their exact bytes.

No binaries, build directories, compressed streams or generated evidence are intended for the repository commit. Root alone owns Git and production-source edits.
