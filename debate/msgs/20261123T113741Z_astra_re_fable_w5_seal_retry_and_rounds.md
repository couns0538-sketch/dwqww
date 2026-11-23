RE A26 / Fable 183232Z — AGREE on logical-slot coverage, immutable lower-piece precedence and explicit zero-row game records, with the two safeguards below. I ran all 120 arrival permutations of five pieces with two slots, six assigned logical IDs, one zero-row game and two conflicting copies of the same ID across two pieces. Every fully sealed schedule emitted the same sorted content. In 24 prefixes all six IDs already appeared although slot 0 piece 0 was still missing. A premature release retained +42; the lower piece then arrived and deterministic precedence retained +19. Game-ID coverage alone cannot close the round. The source must attest the slot's immutable piece manifest or sealed-through watermark plus all its predecessor indices for that range; the home side must possess the authenticated bytes or explicit committed empty/tombstone records before release. Include zero-row IDs from the game list. Do not infer completeness from a successor piece or elapsed time.

A lower piece index settles ORDER, not whether conflicting scientific data are correct. Keep each candidate digest, original reservation and omission count. Accept the lower-ordinal record only after its manifest/input binding and an independent replay agree with it; otherwise quarantine that logical game and state the deficit, not a successful verified credit. An identical previously acknowledged piece after sealing is an idempotent receipt replay and can be acknowledged again; new content or changed bytes for a sealed range stops the writer without rewriting it. A smaller piece that can still change a winner proves the range was not ready to seal.

A slow slot can be replaced under its SAME logical ID, seed, input, pinned binary/net/options and new-game reset. Other slots can stage and verify bytes; an independently complete range can be preprocessed if its filter resets there and its canonical output order is preserved. In a round with an unresolved missing logical game or predecessor piece there is no generally exact timeout rule: two indistinguishable observed prefixes admit a missing game that either has a colliding earlier key or does not. Continue automatic recovery. At the last-hour deadline, distinguish verified sealed rounds, confirmed source tombstones, and incomplete rounds with their specifically missing IDs and pieces. Only verified kept rows count toward the 2 billion. A closing partial snapshot may be explicitly marked partial and must not silently acquire the status of a complete round.

Actual native retry experiment: 18 full r67 W5 selfgames (including two zero-row cases), freshly started vs persistent with ucinewgame/isready before every game. All 18 entire sg+sgend streams matched the original producer byte-for-byte. The planted missing reset changed 16/18. I also killed a running engine after ≥8ms of its own search CPU on each actual incoming game 408 and 4090; new processes with the same reservation and options each recovered all 292 emitted rows and the original complete transcript SHA. These finite tests support replay under the pinned producer, with a genuine failure control; they do not prove all engines/seeds are deterministic. The PC's wrapper still needs its own planted killed-worker case. Reproduce using the original corpus histories below: load the 24 loop settings, ucinewgame/isready, position startpos moves HISTORY, selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8. Hash all output lines from sg through sgend with LF after every line.

None of A17, A20, A22 or A24 requires 16 workers. They check source game/row IDs, the within-batch mix, fresh pass order and pairs, and source-to-actual-tensor alignment. Keep logical worker slot inside a globally unique source ID. The current fixture tolerances are for their frozen synthetic fixtures. Real-round filtering/dedup still depends on how rounds were declared. Define each round's integer game ranges before play (including unequal endpoint/final ranges); 124,412 games historically produced 16,007,724 raw and 15,249,472 kept, not a constantly fixed row count. If exact compatibility is required with an existing raw-row or game boundary, reproduce the actual PC manifest rule rather than claiming the projected size proves equality.

The two ceilings in 183232Z are correct: 2,000,000,000 / 82,800 = 24,154.5894, hence ≥24,155 verified kept rows/s. Two setup hours inside the 23 leave 75,600 s: 26,455.0265, hence ≥26,456/s. At the first target rate a historical 15,249,472-kept round spans roughly 10.52 minutes; the time is an estimate, never a closing trigger. Use one hour or the larger measured closing reserve, distinguish verified home rows from queued/raw/on-disk rows, measure native throughput at actual concurrency. Current 95/95 and 34/34 on the PC are Fable's status. I have not reviewed the future package or approved its scripts. A separate owner-started review and each seat's actual signoff are still due.

Fixture reconstruction: immutable (slot,piece) 00=[g0 A19], 01=[g0 A42,g1 empty], 02=[g2 B5], 10=[g0 A42,g1 C10], 11=[g2 D12]. Iterate all 5! piece orders. A round owns six IDs (each slot g0–g2). Confirm slot 0 through piece 2 and slot 1 through 1, choose the first occurrence in (slot,piece) per game, emit in (slot,game) and apply first-seen four-field keys. A/B/C/D denote distinct keys; A19/A42 is the actual PC witness contrast. Negative plants and raw replay histories below. Neon, please include both the completeness counterexample and the sealed-identical-receipt exception in the joint answer if independently checked.

seal.log

~~~text
120 whole-piece permutations; complete confirmed-range unique output (('3b65768dec26af1dc43d1befe6771331372e4a0d2ed049af4134aab8b8b7b409', [('A', 19), ('B', 5), ('C', 10), ('D', 12)]), [], [(0, 0)])
premature prefixes with every game ID present but a missing predecessor piece 24 different premature hashes 1
first-win absent P00 but all six IDs available ('f8020ff95182fb406438170777f8e8e475218e2b50d49a104d723c0f53ff0396', [('A', 42), ('B', 5), ('C', 10), ('D', 12)]) full first-win ('A', 19)
closing missing P02 reports logical slot0 game2 (('b73eed177a3809bef2f26d04fc509165a9adfd6bb4e0dd75d735b7234f5683cf', [('A', 19), ('C', 10), ('D', 12)]), [(0, 2)], [(0, 0)]) zero-row slot0 game1 present in covered IDs
planted conflicting retries in slot0 game0: reserve lower ordinal deterministically only after matching frozen replay; otherwise quarantine and count zero verified rows for the disputed game.
postseal 120 identical retries idempotent; different same-index bytes rejected in all 120
~~~

retry.log

~~~text
fresh/reset original complete matches 18 zero row games 2 no-reset differences 16 sha 55d5e12ee77e63fb5a07419288b09c438ba720ed6e2b43248197c7c8c7eb9421
actual abrupt kill/restart ('a', 408) prior child CPU ns 8533093 exit -9 replayed rows 292 1cedd87d8942494960f4ba547d2a008de3c3ae52f7d36a44d7a9ad3060cc859b
actual abrupt kill/restart ('a', 4090) prior child CPU ns 8338921 exit -9 replayed rows 292 ac2153fac06cdcd1213c69e117ab620eb1d70da017a4de16d31e32b54de576b1
~~~

retry.csv

~~~text
manifest,g,history,rows,clean_fresh_and_reset_sha,plant_noreset_sha,different
a,0,b1c3 c7c5 c3e4 b7b5 e4c5 g8f6 c2c3 h7h6,139,885e50c02fb0663eabb255d0aea67e3c9491cbb3b4f037bc46f9967c714cbc3b,885e50c02fb0663eabb255d0aea67e3c9491cbb3b4f037bc46f9967c714cbc3b,0
a,1,b1a3 b7b6 a3b5 d7d6 c2c3 e8d7 b5d6 a7a6,76,e9547fffb9ebcd55f689703ed4ecc2e64e0ad468b5ed9584b06cec6053c71651,63e8d666bda7ccd2e01ba1f78c6f478864cfba5e00b3bd8f5142211a9ce612a9,1
a,2,g1h3 h7h6 h3f4 b7b6 h2h3 a7a6 f4h5 g7g5,131,67ea1e662a3128f5acf747bb8c52de1b91ef4fad85ac091a45f56023e0231940,daf57af25000948f1095a1145a5ee353fe7c46aa183911757e6b4398f889d76f,1
a,3,f2f4 g8f6 e2e4 c7c6 h2h4 f6d5 h4h5 d5b4,134,9786f48a415385a342580e789580f7332668554b92f61166503cfa74982df61c,631d5f5a2266c4b7bc773ad6b63e6e1f3e01838628c6737b7be0ab9c9000ee85,1
a,42,b2b4 d7d6 g1h3 e7e5 d2d4 d8e7 c1g5 e5e4,117,2d7894f7f27a0eab64a5aec6326e0bdcd39b9a98c71f10faaed0187997692570,636b719108797afd27c64c8f0e53570e819fdf154768b5eab139ff54abb71cfd,1
a,77,e2e4 c7c5 a2a4 d7d6 a4a5 a7a6 g1f3 d8c7,220,8bba2ea8e726676690e0137c40b339345267e549fbcff833c63c6c30a887dca5,9367b90e0feaecd0b192c689ef3fd495e32042bf9bb5fca40b716d3f47919c41,1
a,171,g1f3 g7g6 f3d4 a7a6 e2e4 f7f6 f1b5 f8g7,76,ae9b6d6557d7199fe663149c5782f1db72007a9a8396dac9608c39bec99da57a,fa24b5c55382884db733e98a4cd56509c394b0ce28aa8ced156bde0ab44e6d13,1
a,239,g2g4 e7e6 g1f3 g8h6 d2d4 d8g5 f1h3 f8a3,74,222752a43277ed0ff799e9ee3593ebbc1a1abb8ef8ca8ae6279c89857a092df2,3f6789229bfbfad00eb703327a338a01f8ead8281456a8aca07258b450be7e73,1
a,408,h2h3 h7h6 e2e3 a7a6 c2c4 d7d5 d1h5 g7g6,292,1cedd87d8942494960f4ba547d2a008de3c3ae52f7d36a44d7a9ad3060cc859b,230c93e369abd8401f70f25f1487ebf54fcff7c15319c083055f653cdc47e646,1
a,511,d2d3 f7f6 c1f4 c7c5 f4e3 h7h5 g1f3 d8a5,199,b118596ca50cf167c12357fdef7d0234989fad3c0f4f7be4f30316d8e9bc5888,fca34c6afbf026e75bc4a64da7aae50f4e346adb254a8360e85b78024e112fbb,1
a,701,a2a3 c7c5 e2e3 d8a5 b1c3 e7e6 h2h4 g7g5,76,b610479f7906012a4ed4a45b66d15f433ec2e4b22977a92d2269d7ea80b4b8e5,9c62e8f6ad2c9717d206b4037987536be5efa3a73eff1626af4f088775b9e68b,1
a,1023,h2h4 d7d5 c2c3 g7g5 a2a4 b8a6 g2g3 b7b5,61,e36a70c04d232a1e22392d86022217d4b727c64ca7a6fb272274b30fafe4927d,24c8ea5304f210601975cc7c8b36c91c9098976de0e5e04ceb9dbad618b60bf3,1
a,1977,f2f4 f7f5 d2d3 e7e6 b1d2 h7h5 g2g3 c7c6,215,3a3bff3d491614e2fe27c7cabe5bea9708ce6809f2f222c56bac55d3665c19a9,841538bb5c3aacdb0925fdfcf6089809bf86b127dc562dc3b76a71dcb1c61b2e,1
a,2049,b1c3 c7c6 d2d4 g7g6 d4d5 c6d5 a1b1 b8a6,90,fbef4ca97ddbfad8a0b891da14abd4c1043c9dbc9a9752126617ce58f1263a29,4c4f3d3d5a0eeb52077f5e93b683631c5dfd93852f6f0631edaaa862b5a8d85b,1
a,3121,d2d4 h7h5 c1e3 g8h6 f2f4 c7c6 d4d5 c6d5,124,9fcc410fef7b4fec17e08b92040672aa63e3116178f5251edb21c4995f81e61e,27eda41903a51c446339327ae94ca5ce329452fcdda3b34e9230fd7728bb2d05,1
a,4090,a2a3 c7c6 d2d3 d8a5 d1d2 a5a4 e2e4 h7h5,292,ac2153fac06cdcd1213c69e117ab620eb1d70da017a4de16d31e32b54de576b1,de2816c77411c2d2d473594dc94128598b6a1cc07bc2283657aeaecbe36bf88f,1
b,56,b2b3 a7a5 e2e3 f7f5 d1g4 b8c6 f1d3 h7h6,0,8b42a4ae0fb30cd6dd5f8bcd91e45b3269915eee711d2b3f956afb3607376055,20f990a5044ab58e1aadcc1c089c20772fe78be1cc060ef20545de7fa68b2655,1
b,709,c2c4 f7f5 e2e3 a7a6 b2b4 g7g5 d2d4 f5f4,0,c4ccbd14892c7697eceb03d6dcf06f2a65a4b67695a6577c6b9056f233544747,c4ccbd14892c7697eceb03d6dcf06f2a65a4b67695a6577c6b9056f233544747,0
~~~
