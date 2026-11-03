# Writer provenance investigation

Status: UNVERIFIED for authentic target-game bindings. Source inspection is
conditional evidence, not a certificate that this version wrote every shard.

Writer: C:/Users/Administrator/grok-pc/nnue/forge-nnue-tools/forge_selfplay.py
MD5: 0a7f225ae89ace5830b8840f17ada9d6
SHA256: 9ff8a48b5185e10cb184486e762f63537b26aebf6b88ffc936dfb287773632f2

- Lines 385-424 buffer one completed game's eligible records. Lines 475-482 queue
  the whole records/result pair. The single parent handles it completely at
  lines 589-596. This version does not interleave games within an append call.
- Lines 224-257 preserve the game iterator across file rotation: a game can
  straddle files. File boundaries alone do not establish separate games.
- Lines 39-42 hash the first four FEN fields into 128 bits. Lines 231-236 drop
  seen hashes with no maximum gap. Lines 377-382 also omit checks, captures,
  promotions, mate/high scores; lines 412-415 omit bounded scores. A gap above
  eight plies is not evidence of a new game.
- No original game ID or move history is persisted. The game token at line391
  only controls protocol state. Data line239 contains FEN, score, White result;
  database lines121-126 contain hashes and file offsets. No database was opened.
- Lines169-193 import and checksum pre-existing shards. Sidecars alone cannot
  authenticate this writer as the producer.

Historical launcher:
C:/Users/Administrator/grok-pc/nnue/selfplay_guard.py.bak_qa_r8v5_20261029_2015
MD5: 8eeeaedc1ba00f02d72f74b89881bcb0
Lines6/19 default to D:/grok-pc-data/selfplay_out; lines22-24 invoke this writer
with two workers, CPUs12-15, nodes5000 and timeout180. Lines8-19 permit overrides.
No seed, writer/engine hash, shard inventory or game-row receipt authenticates
each target file. Missing seed is randomized at writer line469.

Current guard C:/Users/Administrator/grok-pc/nnue/selfplay_guard.py
MD5: 4ada5ba1b9316c11b51a40c7d9950065
Lines5-6 document switching away from the Python writer on 2026-10-29 20:15 Vienna.

Source checksum list:
C:/Users/Administrator/grok-pc/nnue/forge-nnue-tools/SHA256SUMS.txt
MD5: 629a088c1535bfda3f2e8cee70141e47
Line1 matches the inspected writer SHA256. This authenticates source agreement,
not historical production association with specific shard bytes.

Findings: writer behavior inspected; historical launcher association supported;
version/configuration binding to all target shards UNVERIFIED; original game-ID
mapping UNVERIFIED. Scoped search found no new authentic mapping, not global
absence. A perfect segmenter cannot supply missing original provenance.
