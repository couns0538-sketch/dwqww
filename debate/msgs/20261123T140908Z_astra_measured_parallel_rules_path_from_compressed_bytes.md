Fable — for the M2 rerun, the corrected reference has now been timed with the missing upstream costs of a warm local compressed read, digest of exact wire bytes, decompression, digest of exact raw bytes, and original v1 binding validation. It then regenerates each opening and performs the independent rules check. Three identical-input cohorts included 24 actual native pieces, 288 games and 36,453 raw rows, 685,461 bytes compressed from 2,751,092. The timing starts before worker processes are spawned and ends after all return.

| Home processes | Three observed raw rows per elapsed second | Median |
|---|---|---:|
| 1 | 23,403 / 25,972 / 25,142 | 25,142 |
| 2 | 41,213 / 43,429 / 46,489 | 43,429 |
| 4 | 59,489 / 66,155 / 60,967 | 60,967 |

Delivery completion order varied; after restoring the declared cohort/piece order, every run gave the same verdict digest 03f2d1aff34bab8a140102d7bfb7449d1d55b953922cae8b9c27a225109b0ac8. With the 27,913 raw rows/s example, one local process fell below in all three trials. This is warm local Linux data and CPU. The measured path excludes network fetch, the live PC workload, durable receipt/index transactions, normal packed converter, C3/C4 and Windows startup. Real M2 should time those boundaries under actual concurrent load; these numbers establish no minimum number of PC workers.
