# S11 timeout capture: source-only diagnostic

The strongest source fact is guard granularity: before every pipe-drain iteration, the guard re-reads events, scans all `/proc/[0-9]*/stat` for group membership and reads RSS. See observer312–318, consumer136–151 and owned helper83–91. This is not measured root-cause attribution.

Read cap128KiB; actual lengths/counts unrecorded. Retained918,556,004B implies at least7009 positive stdout reads. There is no Python per-position unpack loop, and `select(.05)` is not mandatory50ms sleep. Pump/gzip and child inherit the same single CPU2.

Gzip is already level1 with10k-record chunks and memoryview slicing. Three raw SHA streams, synchronous compressed-file hash rereads and chunk/ledger fsyncs add work/backpressure. There are90 chunk/ledger fsyncs plus one index fsync for45 closed chunks, not per-record fsyncs. Input prehash is before arm timing; cross-arm decode/compare never ran.

Observed closed metadata:499.038271s,444176 complete records,44 full chunks plus4176 last records, no trailing bytes, complete_length=false, SIGTERM-15, leader reaped/no members. Outer arms map empty. Index reports620,408,607 compressed bytes; chunks were not opened/decompressed here.

Parent owns the separate tiny synthetic guard-count demo and C++ producer review. Any reviewed successor must retain cheap clock/stop/PID identity checks, resource policy, cleanup and byte proofs. No implementation, native retry/B/advisory/profiling or speed/Elo claim. Original failed evidence untouched.

Detailed JSON SHA256: `14ac86f0768790a7d96a2a72614b163092ab57584446efb394387502666ce0c9`.
