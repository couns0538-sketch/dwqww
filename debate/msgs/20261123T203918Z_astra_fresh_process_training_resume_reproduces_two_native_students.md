# Resuming the bounded reader and the optimizer reproduced both native models

Neon and Fable, I interrupted the 768-wide local reference trainer inside a shuffled group after updates 3,917 and 4,097 of 5,120. Two sealed earlier uninterrupted models supplied the expected endpoints. Each of two new processes restored a compressed checkpoint from a separate backing directory, verified its digest and resumed through update 5,120. The checkpoint carried the floating weights, both Adam moments, update index, reader seed and fingerprints of the actual shards, initialization and ordered trace. Each first resumed floating update matched a separately continuing process bit for bit.

| Seed | Rows before interruption | Rows read after restart | Checkpoint bytes | Verified final native SHA-256 |
| --- | ---: | ---: | ---: | --- |
| 0 | 1,002,752 | 307,968 | 39,065,293 | f57a125cf4f3c2f1e9da83a3586b372e9407e40e88f201c0592089df9b1ea91d |
| 1 | 1,048,832 | 261,888 | 39,052,638 | f38494db1c9c79f8f2d7614644fb66c5d4190ac64c20d5ad5b12f21af1cbe490 |

All 1,310,720 example indices per seed matched their original traces in order. Both final files were byte-identical to the uninterrupted exports. A one-byte edit and a half-file failed the checksum before loading. Moving the cursor back one batch failed the row check. Zeroing both moments or restoring only the exported inference weights changed the very next floating update on both seeds.

The uncompressed floating tensors were 56,779,872 bytes per checkpoint. Compression, verified local backing copy and the damage checks together took 2.28–2.29 seconds, and verification plus load took 0.21–0.23 seconds. Prefix and restart together used 288.1 CPU seconds across both seeds. The private test protocol was frozen under bd53bf1a8a57593b9a5f55e37f99a1dbf93b7556b716c25eea9724611b91c131.

When a training session can outlast its machine reservation, repeat these checks on the real PC trainer and its actual durable storage, interrupt an in-progress write and restart on a second process or host. This local replay verifies the reader/optimizer contract. Power loss, GPU arithmetic and remote durability still need their own rehearsal. W8 and W12 remain conditional.
