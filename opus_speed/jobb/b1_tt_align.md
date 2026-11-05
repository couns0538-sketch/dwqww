STATE: DONE - NO CHANGE NEEDED (already 64-byte aligned; nothing to time)
# B1 change 2: TT layout check (64-byte alignment, bucket vs cache line) -> already aligned, NO switch

Worker b1tt (Job B part 1), 09:23 PC clock. Result: **the lock's TT array is 64-byte aligned and no bucket
(TTCluster) can straddle a cache line**, so `FORGE_SPD_TT_ALIGN` was not written (nothing to change). No patch.
Evidence below is from the lock source, the plain lock build's code, and a verify-only probe build.

## Source facts (lock `F:\ospd\src\lock`, read-only)
- `include/forge/search.hpp:89` `struct alignas(64) TTCluster { std::array<TTEntry, 4> entries{}; };`
  with `static_assert(sizeof(TTEntry) == 16)` (:92) and `static_assert(sizeof(TTCluster) == 64)` (:93):
  one bucket = 4 entries = exactly one 64-byte line, and the type demands 64-byte alignment.
- `src/search.cpp:233` `std::make_unique<TTCluster[]>(new_count)`: a C++17/20 `new TTCluster[n]()` of an
  over-aligned type, which calls the aligned `operator new[](size_t, std::align_val_t(64))`; the array stride is
  `sizeof(TTCluster)` = 64, so cluster i starts at base + 64 i.
- Indexing `cluster_for()` (search.hpp:175-181) returns `clusters_[index]` (multiply-high of the key), a whole
  cluster, and every TT read / write (probe :247, store :290, hashfull :309, prefetch :127) addresses one cluster.
- `clear()` (:241) assigns in place; `resize()` is the only allocation (start-up `Searcher` 32 MB, `setoption name
  Hash`, bench's `Searcher bench_searcher(16)`).

## Runtime probe (verify-only build, never shipped)
Copy `F:\ospd\src\b1_tt_align_probe` = lock + a print at the end of `TranspositionTable::resize()` of
`clusters_.get() % 64`, the number of clusters whose address is not a multiple of 64 (a straddling cluster would
have to be one of them, as sizeof == 64), `alignof` and `sizeof` (diff `jobb\b1\tt_align\verify_align_probe.diff`,
made by `jobb\b1\tools\make_align_probe.py`). Build `jobb\b1\tt_align\probe\forge.exe` (sha256 9608d6b3...), plain
line. Run (driver `jobb\b1\tools\uci_drive.py`, commands `cmds_align.txt`: start-up, `setoption name Hash value`
1 / 3 / 16 / 64 / 100 / 256, then `bench 1`), log `jobb\b1\tt_align\probe\run_align.log`:

| Hash MB | clusters | base % 64 | misaligned clusters | alignof / sizeof |
|---|---|---|---|---|
| 32 (start-up default) | 524,288 | 0 | 0 | 64 / 64 |
| 1 | 16,384 | 0 | 0 | 64 / 64 |
| 3 | 49,152 | 0 | 0 | 64 / 64 |
| 16 | 262,144 | 0 | 0 | 64 / 64 |
| 64 | 1,048,576 | 0 | 0 | 64 / 64 |
| 100 | 1,638,400 | 0 | 0 | 64 / 64 |
| 256 | 4,194,304 | 0 | 0 | 64 / 64 |
| 16 (bench's own Searcher) | 262,144 | 0 | 0 | 64 / 64 |

(The probe's bench 1 = 884 nodes; it is a verify build, its nodes are not a proof item here.)

## Static evidence (plain lock build `jobb\b1\lock\forge.exe`, listing `jobb\b1\lock\forge.dis`)
`TranspositionTable::resize` at 0x140019730:
```
140019760: shl  $0x6,%rdi                  ; bytes = clusters * 64 (no array cookie added)
140019764: mov  $0x40,%edx                 ; std::align_val_t(64)
140019769: mov  %rdi,%rcx
14001976c: call operator new[](unsigned long long, std::align_val_t)
140019779: call memset                     ; value-initialisation of the clusters
140019788: mov  %rcx,0x10018(%rbx)         ; clusters_ = the returned pointer, unchanged
```
The old array is freed with `operator delete[](void*, std::align_val_t)` (0x14001979c, again `edx = 0x40`). So the
pointer the TT indexes from is exactly the aligned allocation; the runtime table above shows the allocator honours
it on this toolchain (MSYS2 ucrt64 g++ 15.2, static libstdc++).

## Conclusion
Aligned by the type (alignas(64) + aligned new, guaranteed by the language for over-aligned `new[]`), confirmed on
this toolchain's runtime for every size tried and for the bench table. A bucket never straddles a line. An aligned
allocation switch would produce the same addresses and the same code: skipped. Not checked (out of scope here):
large pages / TLB effects (that is the separate S1 LargePages item), and page-level placement.
