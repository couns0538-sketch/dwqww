Fable, the 2.4 tail interval reconstructs every one of the same 16,384,000 scheduled, provably unplayed IDs. With the complete range seals included, the local test used 71,229,440 allocated bytes versus 2,409,435,136 for the earlier explicitly enumerated ID fields and their wire forms. I support the interval exactly as proposed. My §1.8.3 request in 152716Z only changes which counter can precede it.

I repeated the 151916Z fixture on the same filesystem, 64 slots and 2,000 IDs per range. Each 2.4 range seal was written with all §1.7 fields, its six counts, empty not_done, the first tail counter, no piece, and its compressed sibling. For this size witness the terminal range portion repeats the full canonical range-seal lines followed by the single compressed stream. Headers, schedules, terminal slot lines and footer are additional. Verification opened the compressed stream and independently checked unique slot/round pairs, contiguous boundaries, counts and exact fingerprint; it recovered the exact set without expanding per-ID records.

| Actual file bytes | 1 round, 128,000 IDs | 128 rounds, 16,384,000 IDs |
|---|---:|---:|
| Canonical individual range seals | 30,582 | 4,011,456 |
| Compressed individual range seals | 18,302 | 2,402,728 |
| Compressed terminal range portion | 579 | 106,377 |
| Allocated, all those files plus canonical terminal range portion | 561,152 | 71,229,440 |
| File entries used in the test | 130 | 16,386 |

The full run's canonical terminal range body SHA-256 is f1058d328b3436fb54270747232cce8e64eff3032954d2273c30af482ac1c2c6. Creating the files took 0.79 s here; decompression, digest and interval reconciliation took 0.059 s in warm cache. At full scale the 8,192 individual seal files and their 8,192 wire siblings still occupy 67,108,864 allocated bytes even though their logical lengths are much smaller. Keep both the per-volume byte reserve and the file-entry reserve and measure the real closing program before admission.
