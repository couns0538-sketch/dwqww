Actual stage 1 million-position differential oracle: **PASS**.

Source commit `7e4c22a300dea7ae89313d4135184a4e6883029a` contains the exact pre-run ON NNUE/tool bytes. Its lock parent is `f4911f2709bd5ae7e5fca7aea30aac5d87314a05`. Network SHA256 is `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`. Compiler is Debian g++ 14.2.0-19 with H256, `-O3 -DNDEBUG -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread`; ON additionally defines `FORGE_AVX512=1`.

Exactly **1,000,000 genuine Board positions** were emitted. They are deterministic legal-walk visits plus guaranteed special-move fixtures; no uniqueness claim is made. Every record compares all 512 incremental accumulator float bits and its eval integer, and all 512 independently refreshed accumulator float bits and its eval integer. All 100 bounded original chunk pairs passed external `cmp`; their independently computed full uncompressed streams both have:

```
bytes:  4,216,000,320
SHA256: e2ccf250bfbf1cc688bba9cbe20a7abffe09ffce8fe9681ea4459ba85341ad6f
```

Both actual producer exit codes and the outer timeout wrapper exit code are **0**. The run elapsed 1,927.83 seconds, reported only as resource accounting. No timing or playing-strength claim is made.

There were 5,409 starts and **994,591 actual move transitions**, each checked with both distinct-child and in-place updates. Parent preservation and in-place equivalence checks each passed 994,591 times. There are 1,000,000 independently refreshed snapshots.

| Transition | White | Black |
|---|---:|---:|
| All moves | 497,348 | 497,243 |
| Captures, including EP/promotion captures | 23,553 | 23,615 |
| En passant | 104 | 109 |
| King-side castle | 113 | 152 |
| Queen-side castle | 199 | 52 |
| Quiet promotion N / B / R / Q | 862 / 624 / 892 / 603 | 702 / 937 / 674 / 998 |
| Capture promotion N / B / R / Q | 81 / 92 / 94 / 94 | 99 / 117 / 105 / 119 |

Both actual-record negative controls changed exactly one output bit: one accumulator float bit and one eval integer bit. Each was detected with external `cmp` exit 1, and original/mutated records and hashes remain retained. All eight runner tests passed before freeze, including equal truncation, nonzero exit, stalled producer, successful fresh cross-run dedup and corrupt-canonical rejection. Independent read-only peer reviews found no false-PASS or evidence-loss issue.

Both original output streams are retained losslessly as independently produced, round-trip-verified gzip chunks. Only after original raw byte/hash/size equality and compressed byte/hash/size equality were proven were equal new gzip archives hardlinked and made read-only. Physical unique gzip storage is **1,363,332,372 bytes**. A separate post-closure ordered decompression audit independently reconstructed all 4,216,000,320 bytes and matched the direct stream SHA256 above. Canonical archive data was not regenerated from the engine for that audit.

Final manifest: `../oracle-avx512-1/result.json`, now read-only, SHA256 `4192f52dd4041d38d1de3837c81ff3c10d1e12c196f0e45f97b68c8b0a62d993`. See `STAGE1-CLOSED-VERIFICATION.json`, `STAGE1-RETENTION-RECONSTRUCTION.json`, `STAGE1-PROVENANCE.json`, `STAGE1-COMMIT-BINDING.json`, both process-receipt JSON files, and `PROTOCOL.md`. All three tool source hashes and frozen driver/source/archive hashes matched their pre-launch pins after closure.

The separate unchanged original snapshot drivers were run by the AVX agent, including all 31 generic dirty count/flag masks and signed-zero/subnormal boundaries. Their authoritative results and lossless restore maps live under `../avx512-agent/`. Those synthetic cases are excluded from the million-position count. NaNs, other rounding modes, native Windows runtime and playing strength are outside this oracle's claim.
