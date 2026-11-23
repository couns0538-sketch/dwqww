I tested the home duplicate index at the PC forecast's full scale of 16.4 million games. In this local SQLite implementation, retaining every candidate including its later replacements took 840,445,952 allocated bytes after checkpoint. The index writer's observed peak memory was 20,240 KiB. A home progress reader that left one snapshot open materially changed the storage requirement.

The inputs were synthetic 32-byte digests for 16,400,000 identities in 32,800 pieces of 500. I kept an ordinal, piece reference and eligibility flag per candidate, plus an immutable receipt digest per piece. The fixture had 16,072,010 distinct digests and 327,990 alternate candidates. Taking the first owner out of eligibility inside a transaction selected its next eligible candidate immediately. Rolling back restored the first. The real reader must also keep its full evidence and source metadata.

| Local measurement | Result |
|---|---:|
| Insert all candidates, including one intentional exit/restart | 338.17 s, 48,497 candidates/s |
| Largest allocated database + write-ahead log + shared memory sampled after a piece commit | 846,581,760 bytes |
| Final allocation after checkpoint | 840,445,952 bytes |
| Stop immediately before committing piece 8,200 (zero-based) | Exactly 8,200 prior pieces and 4,100,000 candidates survived |
| Independent final audit | All 16,400,000 digest/ID/owner rows and all 32,800 piece digests matched; SQLite integrity check passed |

I used 4 KiB pages, an 8 MiB page cache, WAL with FULL synchronous commits and one transaction per piece. On two private copies of the finished database I wrote 50,000 additional entries under identical conditions. A promptly closed reader gave a largest WAL of 5,920,472 bytes and a 849,104,896-byte combined allocation. One held reporting snapshot gave a 279,653,272-byte WAL and 1,120,657,408 allocated bytes. At the end of those writes a passive checkpoint copied zero of 67,877 frames in the held-reader arm. Closing the reader and checkpointing left the same 843,149,312 allocated bytes for the database in both arms. A lower write time while the snapshot was held merely deferred that work.

This supports §2.2's short reads and real-volume reserve. The measured 0.84 GB is one implementation's candidate index alone; the real PC also needs receipts, stored pieces, round staging, temporary and log growth. Validate it at its actual page size and workload. The ordered candidate-map SHA-256 was e72db23c309fce40856873af0ec04326797424c9475d5be85b7c622cafcaeea1; the ordered piece-commit SHA-256 was 8f71ec09f6adf22614f335dc240271c7e0481e48fe8d6009fc9ae8d101713876. These are index measurements and establish neither C4 capacity nor a paid-server rate.
