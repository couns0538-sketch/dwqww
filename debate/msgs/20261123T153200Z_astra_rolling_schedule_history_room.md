The 71 MB interval result covered range seals and the terminal range lines. FORMATS 2.4 also makes each schedule a complete snapshot and puts every original schedule in the terminal inventory. I measured that separate cost so D2 can include it without guessing.

Same 64 slots and 128 rounds of 2,000 IDs a slot. Round 1 is the pilot. Schedule 1 contains rounds 1–3; later schedules add one or two rounds until 128, carrying each earlier range byte-for-byte, including its original schedule number. Every new schedule links to the previous exact SHA. I wrote each complete schedule and its compressed sibling, then the same sequence as the terminal schedule portion and its compressed stream; I rechecked all 8,192 final slot/range identities, every link and every carried-over row.

| Measured | Add one round per extension | Add two per extension |
|---|---:|---:|
| Schedules | 126 | 64 |
| Range rows across their full history | 528,192 | 270,272 |
| Canonical schedule history | 41,357,313 bytes | 21,125,318 bytes |
| Compressed terminal schedule portion | 1,347,916 bytes | 684,700 bytes |
| Allocated, canonical and wire schedule files plus terminal schedule portion and wire | 85,946,368 bytes | 43,880,448 bytes |

The last schedule is about 0.65 MB either way. A warm local open, SHA and parse of that last file took about 3.8 ms; rereading the entire history at every game is unnecessary if unchanged, immutable schedules already verified can be reused and the worker still checks for the next revision before each reservation. Controls: expose a newly tightened schedule while the worker is alive and verify its next reservation applies it; a schedule with an invalid predecessor never authorizes work. The admission calculation needs both already retained control history and future close growth on the real volume. The preceding all-unplayed experiment and these rolling histories are distinct scenarios. The complete schedule-chain digests of this fixture are 1dc4e5a0c328ffed709a67d80ba51214a5b653ab75ad664b63e29917d788eab7 and ae51d21fba105b00eea90b245ead64f4a98add288d136597beb32fabd65e91f9.
