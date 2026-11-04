# Item A - training data audit (o30_data.py, 2026-11-03 17:02-17:12 PC clock, 588.6 s)

Inputs read only (never modified): FPOS / FHCE shards `D:\grok-pc-data\forge_push\nnue_data\{pos,hce}\forge_selfplay_001..039`,
the R14-B relabel proof jobA `D:\o14b\r2\proof\jobA` and Astra R13's mate-row flags `D:\a13\p5qc\mate_rows.jsonl`.
Outputs: `D:\o30\data` (AUDIT.json md5 39408df5abcdbc91541ad151de299de4; holdout_keys.npy dca01d2244663beb98030ea9158ff9cc;
jobA_val.pos f85f1ccbb413ca39113f2066ef2a1bb7 / .hce df1fc5f3135678fd449113920af5187d; skip/ and override/ per shard).

## What the training set is
- Train = shards 001-039 except 013 and 014: **304,999,573 rows = exactly the record count of the npt data**
  (`F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack`, 304,999,573 records, 34 bytes each): the J1 binpack is
  these rows re-encoded; the FPOS / FHCE shards add the per-row hand-crafted evaluation the residual target needs.
- Holdout = 013 + 014, 16,388,575 rows (16,387,223 distinct board + side-to-move keys) = the lock net's data split;
  scores use the crew's S31 subset of it (1,024,286 rows, md5 9ebe2f9c / c8723ec2).
- Relabelled data (P5 relabel = R14-B jobA, 20k-node labels on original FENs): all 999,921 rows map to their source
  rows (selfplay 001: 466,506; 002: 533,415) with **0 board, 0 side-to-move, 0 old-score and 0 result mismatches**.
  Its train split (minus mate rows and overlap rows) replaces the self-play score of the same rows: 988,336 overrides.
  Its val split (8,844 rows, 99 games; game-level split by relabel2.py) is removed from training and kept as a second
  holdout with the 20k-node labels: `jobA_val.pos/.hce`, 8,821 rows after the mate rows.
- job1 (440,000 rows on reconstructed FENs, castling / ep / clocks lost) is NOT used (Astra R13: lossy).
- Astra R13's mate flags: 2,717 jobA rows = exactly the rows with |score_stm| >= 30000 (set equality checked); they are
  excluded. The self-play shards themselves have 0 rows with |score| >= 30000.

## Train / holdout separation (evidence)
- Game level: train and holdout are different self-play files (shards 013 / 014 are whole files of their own games).
  An authentic game-id proof across the production shards is not possible: Astra R13 could not recover the original
  game bindings of selfplay 001 / 002 and holdouts 013 / 014 (its report: production game separation UNVERIFIED).
- Position level (done here): every training row whose 64-bit key of board + side to move occurs in the holdout is
  skipped: **7,706 rows** (0.0025 %; opening positions shared by many games). The trainer reads the skip lists, so no
  training position equals a holdout position (up to a 64-bit key collision, which would only drop a row).

## Totals
| item | rows |
|---|---|
| training rows (shards) | 304,999,573 |
| skipped: holdout overlap | 7,706 |
| skipped: jobA val split | 8,844 |
| skipped: mate rows | 0 |
| jobA label overrides | 988,336 |
| holdout rows (013 + 014) | 16,388,575 |

## Per shard
| shard | role | rows | holdout-overlap rows skipped | jobA val rows skipped | jobA label overrides | pos sha256 | hce sha256 |
|---|---|---|---|---|---|---|---|
| forge_selfplay_001 | train | 466,506 | 27 | 3238 | 461965 | 395fa49d8f026bf6a014751ae8e6e1768e8f1a67e16c50d990f690262cd6a1d9 | a83be23bebe7642921f42a0a0a2875f147db1c95a370d6813f5aded8b497f291 |
| forge_selfplay_002 | train | 3,126,714 | 120 | 5606 | 526371 | d68de8bccb9046e3e376a5be9b928bf655043c37423078d4482441023c56003b | e7321834c6eea8f28400727e4c2a0a7ddc24e1fc1f8983f062a659c78c9bfa9d |
| forge_selfplay_003 | train | 10,000,000 | 339 | 0 | 0 | d322089c80c8c753bf9eb744d50b530af6d33a5f06bdd3aa5b86a51b61febb10 | 8e237a1c85753b65ed88c146bdfe197ca2814e09b6dd0a60d17b6b8e5163edf3 |
| forge_selfplay_004 | train | 10,000,000 | 323 | 0 | 0 | d4c63ff757910a88691c99f884c029596e59476cd3795141b9e8b45dde2adc77 | 87e6318716d2f703dbde84cc916468e971aeff4c3753729fd593c983cb9ebd7d |
| forge_selfplay_005 | train | 10,000,000 | 326 | 0 | 0 | c9c3f901980f27688306e960ff75e26e8bf785d65ed521141376c1bfa734112e | 3739994407577da10294380504d3b9af48d91b4c4ab06090f5e9182e374c0b08 |
| forge_selfplay_006 | train | 9,544,563 | 310 | 0 | 0 | 0c0e9228fd269516fa1964870b9edc2430cadf9c8f16fc8915abbd4f26a66b9c | 4483d941e37313f1dc8de970e1bbed82a2540603251c1f7902332db2dc3a4bdb |
| forge_selfplay_007 | train | 10,000,000 | 293 | 0 | 0 | a741c2655cb8d9ccdee749a1b7bdc038134e49c6f72d151f713ed29fc1b6f109 | a395241c3c0bc62c9a7401705fb3f3f88938cfbcf17f46a847de34837959865f |
| forge_selfplay_008 | train | 10,000,000 | 271 | 0 | 0 | 8d3ab3d531cdd5572b9ab254c94fc4feb57a9189625b196c67d684da9c79bd96 | 57a5d5d707e2434c6d3b12333f07e2302a65422eb6da815d3653e94680866770 |
| forge_selfplay_009 | train | 9,491,886 | 234 | 0 | 0 | 7aae7e34881bb43b427bed40bace476608638a066d66e2d7d674ce659bd2a0b6 | 90902426d7f81b42dca1bbbc052f4bd7beb2e4824db96564bc9bfe80820615a8 |
| forge_selfplay_010 | train | 10,000,000 | 210 | 0 | 0 | 7c75e3ac595054fa43e5b6823c32a24869340d5e61b1d6d5692d9d004b95278c | 7048d338dd4468acfcd043c122a760edecc19073f982176dcdaee63af8b3ca0d |
| forge_selfplay_011 | train | 104,596 | 3 | 0 | 0 | 9ee384d2e7b9d1067554f3a26476e5784c2a4fca6953906618392e3adb0ce821 | deb9b5daa0bace85dadb875726e43da8a8764b23fee77234a7e770a3267b80f8 |
| forge_selfplay_012 | train | 2,625,970 | 56 | 0 | 0 | c7bd00082381fecbb927d75ed90f38e0609700845b0a78d529cca8ef7698632f | 862d404a16f02a4fa11adb0fea70e2159b803a00c0b3fd747318802a3ff1a7ee |
| forge_selfplay_013 | holdout | 10,000,000 | - | - | - | 904e6527717bfb37cdbe9f18f70029ec62eb55b5752a22e7a9ab75921d18e9ef | 0f4fdb34ab9ebc6e7f3458f5abe34c4dd151689b175c7ef3bac5e17d6ae2b7a7 |
| forge_selfplay_014 | holdout | 6,388,575 | - | - | - | 255afc00584add90d838c36395a626f2db2f45cd0764a179763bc8bf7925ff9d | 469479c30e5a49933c4844b66293a55cc3fa8042bad80b4f80a19f5ee2112f09 |
| forge_selfplay_015 | train | 10,000,000 | 238 | 0 | 0 | bc5eb6d33a92515571bea5e43b590babc2773c30a54d7e33179f4b6c9503a909 | f8c558265fcc4534f868cfa328c4c1ad9397049a6a55cc252ce5bc10b331a26b |
| forge_selfplay_016 | train | 10,000,000 | 290 | 0 | 0 | 3d5a83f6f6cd60c2229545211038670a3027e4ec1d6cfa0bb78dd152e15255ca | 0fb7bd560adfaaf185e7bdad3cf27bf3e8a06c11742fd3c5d10aecce027df27a |
| forge_selfplay_017 | train | 2,612,839 | 53 | 0 | 0 | a64cb7e2af6336f49c5693e3478bf3cbccad2e7203860b9216564266f14b6be1 | 688d4baf14f7d8fb955848df8b7284368927ee08b19f6ee8100e90d8aa08e3fc |
| forge_selfplay_018 | train | 10,000,000 | 257 | 0 | 0 | 3b42bb371a863b4af9a2a67afe2216d7dfc90085706312122b8e8a9cb7931033 | 12c580f14f03de0dec7b1c5dd0ea4202fe5e6064532ceea28adbb4dc64c9f0d8 |
| forge_selfplay_019 | train | 2,721,866 | 70 | 0 | 0 | e14b065f43d36fdaf8a4aebb9ce5f18269be011890263cecbbf4bf457b2015cf | 5e5a24c867b282fbbfd63f69b06d4b1f82efb8b58d21c2c9176988d589a0fa56 |
| forge_selfplay_020 | train | 6,686,147 | 159 | 0 | 0 | a6e40b29387f9c9d050743c814952a0c348e84a8b3778570f4f447c747d1725e | 09e76bb291c5b8390f59728f8a5eb90dbacbc7addd01f5ede1aaef50710a41f6 |
| forge_selfplay_021 | train | 10,000,000 | 218 | 0 | 0 | e7a46cab25d062cb36674897448cf7f05d4407190ef1c33ada64ebf0fff43094 | 8f5ca511d6d7573c5e50d5c3894e61b24f9bd0fe5c75525c538af1982a1d0c71 |
| forge_selfplay_022 | train | 10,000,000 | 192 | 0 | 0 | 273bd4da5cb6c8252f1fea697ba76cf69f927cfb3795953b86de042088a370d5 | b577d608ac8fc610cd68b156de3bd5fe16ef5c49dd67ac1912207e273a24cdec |
| forge_selfplay_023 | train | 4,532,807 | 85 | 0 | 0 | 72526576477d757517957efdce9cae8f6a22dec09b745ede2cc88dd3b1b3a5c0 | 8430b341099a7ead69c7c09042a5b165cf87e8c40362390cfd806c441360f97e |
| forge_selfplay_024 | train | 10,000,000 | 225 | 0 | 0 | 870ac4b908678e7e7b865f5ec4bda1d8c6f0f860a6b916a3159c28f9e401f1ff | bb17c07a911e9fd6f62b525bac17c4e31c60899dbe7072f0afb53b5c28530b40 |
| forge_selfplay_025 | train | 10,000,000 | 267 | 0 | 0 | 4701b4fbfd002e3a9202ddd130bc6b15eead057be1dc4330d85ada74773b8b19 | 2be8a400c08999cbeb9fab4c3e251ce37df5452812935016f66ff927bed7e7a8 |
| forge_selfplay_026 | train | 10,000,000 | 241 | 0 | 0 | d297d5e5902e2a1a96dc21ec02786f0679fccabf400a4f2ed66c92c3a5f1cd92 | 6d977c4e916da9480fe5e509ea30ca1374c756b6e8eec5008843c9a4d8f956be |
| forge_selfplay_027 | train | 10,000,000 | 234 | 0 | 0 | b60c4a4e77595aaf2f21985cb09505d3531deb14b0ddad4847d65e04bf434803 | dd89d10a761b21dd138b8f3d2f5acd93df0c007050b2f703e32f2b9ccf2ba2db |
| forge_selfplay_028 | train | 10,000,000 | 259 | 0 | 0 | 0ef5afcb61ac665dd2f6ae38138cb8bf38bd54c7ecfa6c61b4f9e624e45cfcab | 0c127e3e12b556ce5f06cb87e93277709aa31f27308794e5cb8071013e992325 |
| forge_selfplay_029 | train | 10,000,000 | 282 | 0 | 0 | 2876a6c821309471d5fa653c9f76925ee9d7e2ad6bd3798329b083df7a20840b | 15186fd953245a3a34dc83225833e75dd9d474caac01add691a09e35d52c686a |
| forge_selfplay_030 | train | 10,000,000 | 263 | 0 | 0 | b2d06aae2dd22c8a0dfc014903c36a2b09e6c3e045b328c0e93588cf99e81357 | 820fcaa0aa202ab9cefcc4a6539821b4d3733619d611b5f8aa5dfd0b20ba1835 |
| forge_selfplay_031 | train | 10,000,000 | 229 | 0 | 0 | 641f397fed9c1aeb8cb253a84b0513de046284acb29e97e65082b525e79cd681 | b223c947afabb07245ae6b552b743090c65fde1a5440d91452aca7a1bdee81da |
| forge_selfplay_032 | train | 10,000,000 | 220 | 0 | 0 | e40258093071b74ffe25808c2e5bb616caeaf97d267f07950e64ab7f05ac27af | 96047099478d410c61a9e5dfddc92de8253e14f6808446c6e461fd63eb9103a7 |
| forge_selfplay_033 | train | 10,000,000 | 264 | 0 | 0 | 8f82a6b60710ea6aadb82a0c96191d3698f8c7c2dc196a6dffd172a21591e968 | 897815b5d4485c6669356b604f8e719570ac54750e56ee7433c5617b8063b789 |
| forge_selfplay_034 | train | 10,000,000 | 233 | 0 | 0 | bc7e557628fbd1ad4f3ee98edd43b1a24da6c0fbb21271f1bcc590682d2abd32 | 59d4ac8eef2e3324aac3b667e6c30c99e7f107fbe875722901e7f90060a247d7 |
| forge_selfplay_035 | train | 10,000,000 | 217 | 0 | 0 | 3d1351a3afd9829986cbbc0e572d029bd64445209f2fccea74aa6daed26fb907 | 7d610a874e8cfa9237c54c7e41c34b4a29ede0530f2d4369948ff384174a2da8 |
| forge_selfplay_036 | train | 10,000,000 | 227 | 0 | 0 | 86163ded0074a40cc74c776033a8cdc7327004a3264418c557d5075c91656461 | a5a38944d7bedb09f578d9bee7ab427e541a6f9957242c8a020ac02f4a9e0fa2 |
| forge_selfplay_037 | train | 10,000,000 | 234 | 0 | 0 | 8626f7dcfdb790824ead68634d0bacd49bfd861cc96af98d635ce0f16cbea1c3 | 1a5aa86f852879e34e9983a2e11135ff4a19729773615f14a806c3abec3a6469 |
| forge_selfplay_038 | train | 10,000,000 | 165 | 0 | 0 | 2265909c55837b83dbaf48dc0339fb67b1dd23886b11859774d26d4504f29ebc | aa0af7ef2f1d7273e02795f9e101f22381069491ebfcd95e624e6616798f4011 |
| forge_selfplay_039 | train | 3,085,679 | 72 | 0 | 0 | 5d526742c8774df81f7156f3144b20fa42adce6f6e264719f8acd6f7c5d8a0d1 | 976e0afd35cbf16c74050966f1b11cfb1228b7713109721748b364f0300f0425 |
