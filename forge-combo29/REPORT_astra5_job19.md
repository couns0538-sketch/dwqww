# Astra5 job 19 — kF at two deep node limits and 76 tuning edges

## 1. Step 0 passed on both builds

Each command ran in a fresh process on the unchanged job 16 executables. `nproc` returned 5. Every network-enabled check logged `NNUE v3 active` and checksum `30ab43b4ba5db5f3`. [Build and network identities](astra5/job19/step0/identities.txt)

| Options | Command | r15d nodes | kF nodes |
| --- | --- | --- | --- |
| No setoptions | `bench 11` | 312,866 | 312,866 |
| No setoptions | `bench 13` | 862,329 | 862,329 |
| No setoptions | `go perft 5` | 4,865,609 | 4,865,609 |
| PC20 + net768 | `bench 11` | 882,074 | 882,074 |
| PC20 + net768 | `bench 13` | 4,275,906 | 4,275,906 |

| File | SHA-256 |
| --- | --- |
| r15d | `9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671` |
| kF | `c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb` |
| Synthetic net768 | `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7` |

[r15d gate receipts](astra5/job19/step0/r15d/checks.txt) · [kF gate receipts](astra5/job19/step0/kF/checks.txt)

## 2. K19 and C19 passed

Driver F played book lines 3791–3792 at `go nodes 250000` on r15d. The two PC20 repeats were byte-identical (`cmp` exit 0). Lowering `LmrQuietBase` from 93 to 60 changed the record in 2 of the 2 games (`cmp` exit 1). The first difference was on book line 3791, played ply 1. [K19 comparison](astra5/job19/audit/K19/cmp.txt) · [C19 opening, prefix and first difference](astra5/job19/audit/C19/first-difference.txt)

| Arm | LmrQuietBase | Games | Records | NA | Numeric nodes | Record SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| K19-1 | 93 | 2 | 135 | 0 | 20,617,303 | `11c8a62c811fef3f05081c0c1c32e541c90881f88a0e6be3ca73d8a6d6a9b4bb` |
| K19-2 | 93 | 2 | 135 | 0 | 20,617,303 | `11c8a62c811fef3f05081c0c1c32e541c90881f88a0e6be3ca73d8a6d6a9b4bb` |
| C19 | 60 | 2 | 155 | 0 | 24,924,432 | `33f2a25ad24fcee3999af3127e8bedaeda7654e6344fddf4f05ece66c7a34ce9` |

```text
K19  3791 1 d5d6 213822
C19  3791 1 f3f6 248671
```

## 3. Frozen prediction and grades

The prediction was pushed alone at 00:46:29Z after C19. The first measured D1 game started at 00:46:33.463Z. A differing game has at least one different four-field record. [Frozen prediction](astra5/job19/prediction.txt) · [Prediction-only commit](https://github.com/couns0538-sketch/dwqww/commit/deb1de5ee20940f37c73063f14f534895424b40c) · [UTC checkpoints](astra5/job19/stamps.txt)

| Run | Point estimate | Inclusive range | Observed differing games | Grade |
| --- | --- | --- | --- | --- |
| D1 | 0 of 16 | 0–1 | 0 | Point hit, inside range |
| E | 0 of 380 | 0–4 | 0 | Point hit, inside range |
| D2 | 0 of 4 | 0–1 | 0 | Point hit, inside range |

Each played edge also had a forecast of 0 of 5 differing games, range 0–1. Of the 76 completed edge comparisons, 76 hit the point estimate and 76 fell inside the range. The four edges marked `start` had no scheduled games or forecast. The results table gives the observed count for each edge.

## 4. D1, all 80 edges, E and D2

**KEEPS.** D1, each of the 76 played edges, their concatenation E, and D2 had byte-identical records on both builds.

The D1 schedule used book lines 3793–3808 at `go nodes 250000` and the D2 schedule used lines 3809–3812 at `go nodes 1000000`. In driver F, one fixed engine played White and another played Black. The first searched ply after the book FEN is numbered 1. Both drivers used PC20, synthetic net768, Threads 1 and Hash 16 MiB. Each build ran one game at a time, with at most two games in flight across both builds. [Driver implementation](astra5/job19/driver/selfplay.py)

Driver R scheduled five games per eligible edge at `go softnodes 2000`. For edge *e*, the first game ID was 500001 + 10 × (*e* − 1). The ID seeded eight random legal plies from the initial position. A single persistent process then played both colors, retaining the opening history. Its first searched ply is numbered 8. Each edge changed one option from the job 18 start values. The four minima already at their starts were skipped. Both engines advertised every requested bound, so all played edges used their table values. [All edge settings and game IDs](astra5/job19/settings/edge-sets.tsv) · [Both UCI range declarations](astra5/job19/settings/uci-bounds.txt)

All 152 playable build and edge combinations accepted the setup with the active net. For each combination, the probe read back 39 tuning values. `DrawJitter` reports a fixed default in `uci`, so its check used the handler’s assignment and the absence of a refusal. [Option acceptance and readback](astra5/job19/settings/edge-option-probe.txt)

The stage link opens its byte comparison. A single figure or digest applies to both builds. Unequal measurements are given in r15d / kF order. The node sum uses the last info line before each bestmove and omits any `NA`. E concatenates the played edge files in numeric edge order and adds no games beyond those rows.

| Run or edge | Setting | Games | Records | NA | Numeric nodes | Record SHA-256 | cmp exit | Differing games | Reading |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [D1](astra5/job19/audit/D1/cmp.txt) | PC20, 250,000 nodes | 16 | 1,355 | 0 | 214,700,630 | `0e0bc627162e519754482cc7c958c5f7a0c8b4dbab1330eba35a4442abc2c263` | 0 | 0 | IDENTICAL |
| [E](astra5/job19/audit/E/cmp.txt) | All played edges, 2,000 softnodes | 380 | 44,103 | 0 | 183,377,838 | `f3455a96cda53ac15dcd979143bf368e25e0aa9bcc5d9fbfcd5a7ec02475f84f` | 0 | 0 | IDENTICAL |
| E01 | `DrawJitter` min = 0 | 0 | — | — | — | — | — | — | start |
| [E02](astra5/job19/audit/E02/cmp.txt) | `DrawJitter` max = 8 | 5 | 641 | 0 | 2,628,521 | `ac54671f224bb9829ec682291dc8c707686cf88386a45f55cc949aa9b54b8296` | 0 | 0 | IDENTICAL |
| [E03](astra5/job19/audit/E03/cmp.txt) | `LmrQuietBase` min = 0 | 5 | 878 | 0 | 4,028,277 | `0843b4b89b9f39fd2d041e2dea80c6e4d491c70e3f3640c05d48975db8de5e6e` | 0 | 0 | IDENTICAL |
| [E04](astra5/job19/audit/E04/cmp.txt) | `LmrQuietBase` max = 300 | 5 | 434 | 0 | 1,492,099 | `011b45518a177a4a87a0662a0db067e36b77f0d120d45d3001be6cc741fa98ab` | 0 | 0 | IDENTICAL |
| [E05](astra5/job19/audit/E05/cmp.txt) | `LmrQuietDivisor` min = 100 | 5 | 594 | 0 | 2,331,670 | `438becb9bc2eb8b8586b8d676ce1902ad4fc91c716c0bd21be36fb2adef9a152` | 0 | 0 | IDENTICAL |
| [E06](astra5/job19/audit/E06/cmp.txt) | `LmrQuietDivisor` max = 500 | 5 | 622 | 0 | 3,073,845 | `c0053452c7578b5d9176c1d04589419eacd0a515adeacca1e835d5b24fe6d943` | 0 | 0 | IDENTICAL |
| [E07](astra5/job19/audit/E07/cmp.txt) | `LmrNoisyBase` min = 0 | 5 | 607 | 0 | 2,539,313 | `c3428234c3cd9afe1cc09233898f686a7d25698cd2950523513d3f219e82eef8` | 0 | 0 | IDENTICAL |
| [E08](astra5/job19/audit/E08/cmp.txt) | `LmrNoisyBase` max = 300 | 5 | 619 | 0 | 2,547,971 | `e73bfc9394a2acddf407d9625f74d7e931b79f37393e3dcabc04c9d5f741c78f` | 0 | 0 | IDENTICAL |
| [E09](astra5/job19/audit/E09/cmp.txt) | `LmrNoisyDivisor` min = 100 | 5 | 490 | 0 | 2,024,334 | `e3f4849cfbbaab2426913443fc6332133be75096eccf5482deaaa403fc8bc88c` | 0 | 0 | IDENTICAL |
| [E10](astra5/job19/audit/E10/cmp.txt) | `LmrNoisyDivisor` max = 800 | 5 | 752 | 0 | 3,192,075 | `41260fabc55221e4c20305484d756d6ff8ebab74de9d84167f8e84741a460691` | 0 | 0 | IDENTICAL |
| [E11](astra5/job19/audit/E11/cmp.txt) | `NullMoveMinDepth` min = 1 | 5 | 588 | 0 | 2,449,346 | `6efd71f7a10611a93044ca9111b0f5d6c7138e0375a287c9f2262bd83d7351a8` | 0 | 0 | IDENTICAL |
| [E12](astra5/job19/audit/E12/cmp.txt) | `NullMoveMinDepth` max = 10 | 5 | 572 | 0 | 2,386,123 | `a3f06e01f9f6dfcc013bc04b1e88a0aa12dc0d9c92ff4386016a783bb5e80400` | 0 | 0 | IDENTICAL |
| [E13](astra5/job19/audit/E13/cmp.txt) | `NullMoveBase` min = 1 | 5 | 696 | 0 | 2,892,932 | `65290d01a29ab02f7e705a50b155919c9feeaa384b05751c57f07ced76d49214` | 0 | 0 | IDENTICAL |
| [E14](astra5/job19/audit/E14/cmp.txt) | `NullMoveBase` max = 6 | 5 | 560 | 0 | 2,372,274 | `4cead76dbb174ed32eb0c4ba47e0455a5234d2d02e88a1cd5ea86c54be7b57d6` | 0 | 0 | IDENTICAL |
| [E15](astra5/job19/audit/E15/cmp.txt) | `NullMoveDepthDivisor` min = 1 | 5 | 807 | 0 | 3,336,099 | `17764caafc88a7a58d0eccbf8c0fcb6ee103ae94bd1738c80a99562e56693f37` | 0 | 0 | IDENTICAL |
| [E16](astra5/job19/audit/E16/cmp.txt) | `NullMoveDepthDivisor` max = 10 | 5 | 797 | 0 | 3,392,744 | `39ab425915367b0a69c8aa08bca28f5142a37a09b67219d3f39ca47383891ccd` | 0 | 0 | IDENTICAL |
| [E17](astra5/job19/audit/E17/cmp.txt) | `NullMoveEvalDivisor` min = 50 | 5 | 622 | 0 | 2,621,609 | `4df144546e70ce66d20acf3654e31f148875b69502fab92dfb6eac6e1d8b17f8` | 0 | 0 | IDENTICAL |
| [E18](astra5/job19/audit/E18/cmp.txt) | `NullMoveEvalDivisor` max = 1000 | 5 | 628 | 0 | 2,704,906 | `d9fdd8d9f60941bc20b3c88d592ffaec775f5ca231be2dfa4e621498e868f402` | 0 | 0 | IDENTICAL |
| [E19](astra5/job19/audit/E19/cmp.txt) | `RfpDepth` min = 0 | 5 | 401 | 0 | 1,698,652 | `33d8a3fd98183aa3a10cb6c3d6f20c8f4326b4df1837c1a1616f8691b5dab272` | 0 | 0 | IDENTICAL |
| [E20](astra5/job19/audit/E20/cmp.txt) | `RfpDepth` max = 15 | 5 | 504 | 0 | 2,068,402 | `e131416c04b83450da5b6396a40bacb1b170ff92e2a98d37db7385624e658a37` | 0 | 0 | IDENTICAL |
| [E21](astra5/job19/audit/E21/cmp.txt) | `RfpMargin` min = 10 | 5 | 582 | 0 | 2,232,642 | `ff8cda06fbbf3df843c45aff02054aabfd739440bb3fc7dfab6a35dc4b427c77` | 0 | 0 | IDENTICAL |
| [E22](astra5/job19/audit/E22/cmp.txt) | `RfpMargin` max = 300 | 5 | 477 | 0 | 2,087,175 | `769ee6db6e340e11fb03e663498bd6825ec7fca90b8cc3f9174e5c142f35f6ca` | 0 | 0 | IDENTICAL |
| [E23](astra5/job19/audit/E23/cmp.txt) | `RfpImproving` min = 0 | 5 | 492 | 0 | 1,943,310 | `1ddc5804a2a60c5440d331868e7459d07c5308df2e2c12d8793c1e270f9993a4` | 0 | 0 | IDENTICAL |
| [E24](astra5/job19/audit/E24/cmp.txt) | `RfpImproving` max = 200 | 5 | 581 | 0 | 2,325,503 | `d90b5d101f81acd5625ad4af59974d471b312bad7e3d94879cf8c2a5adb52b02` | 0 | 0 | IDENTICAL |
| [E25](astra5/job19/audit/E25/cmp.txt) | `RazorDepth` min = 0 | 5 | 464 | 0 | 1,855,654 | `58687e04ef58c3050559e358ea05916069a538a4ef4ad0eb1ff75a51172792a2` | 0 | 0 | IDENTICAL |
| [E26](astra5/job19/audit/E26/cmp.txt) | `RazorDepth` max = 6 | 5 | 584 | 0 | 2,461,788 | `a334d7c4066b82083925c6bd73cd05249684a0d3e43486d75b80b898ac3f5f69` | 0 | 0 | IDENTICAL |
| [E27](astra5/job19/audit/E27/cmp.txt) | `RazorBase` min = 0 | 5 | 587 | 0 | 2,514,012 | `68eb1cf53bb6cf3dd5f91fbeac3e9d3a7f143553225253d1bdd1eef161589d0a` | 0 | 0 | IDENTICAL |
| [E28](astra5/job19/audit/E28/cmp.txt) | `RazorBase` max = 1000 | 5 | 760 | 0 | 3,334,291 | `59ee1b3b7a962c300938e2c8b3e0be26af3a16fe7d24212ddd039353cb9c9c34` | 0 | 0 | IDENTICAL |
| [E29](astra5/job19/audit/E29/cmp.txt) | `RazorMultiplier` min = 0 | 5 | 525 | 0 | 2,185,820 | `b39fca2c7d5dde9bdc15fe5df2c85d17fb0ea2a5eb8b04a419f44dc6df43cecb` | 0 | 0 | IDENTICAL |
| [E30](astra5/job19/audit/E30/cmp.txt) | `RazorMultiplier` max = 1000 | 5 | 469 | 0 | 1,916,268 | `57045e13eb4af2956209fa3fb24119e6cbaa36d0bc7711b7581fa5977f66fb31` | 0 | 0 | IDENTICAL |
| [E31](astra5/job19/audit/E31/cmp.txt) | `FutilityDepth` min = 0 | 5 | 959 | 0 | 4,512,163 | `a8e5bb7e9bc2b440ed2860e8df29cd86cd4868e8370a4def83ee366274617e5d` | 0 | 0 | IDENTICAL |
| [E32](astra5/job19/audit/E32/cmp.txt) | `FutilityDepth` max = 15 | 5 | 537 | 0 | 2,333,556 | `95a64ca68d216b7bb7b78e64a316629f97e5f00fda1875b820b30dba5623f618` | 0 | 0 | IDENTICAL |
| [E33](astra5/job19/audit/E33/cmp.txt) | `FutilityBase` min = 0 | 5 | 466 | 0 | 1,851,874 | `4189675abbbed7af61a2638e89be9f9aca8d2236187be9724a36d1b6885d504f` | 0 | 0 | IDENTICAL |
| [E34](astra5/job19/audit/E34/cmp.txt) | `FutilityBase` max = 500 | 5 | 794 | 0 | 3,510,781 | `515adbe934ff1f2522e318da0d25b0dbdfebb22c213c974203536e648279ea41` | 0 | 0 | IDENTICAL |
| [E35](astra5/job19/audit/E35/cmp.txt) | `FutilityMultiplier` min = 0 | 5 | 542 | 0 | 1,955,035 | `81759bd14c3d1048a06d03c92c42041780bf00d113a78c41599c49f4702ace27` | 0 | 0 | IDENTICAL |
| [E36](astra5/job19/audit/E36/cmp.txt) | `FutilityMultiplier` max = 500 | 5 | 675 | 0 | 2,879,374 | `ded91725464cf58e8774839f57b526cb8fce275e49814c05e3932b7aa23b0fd3` | 0 | 0 | IDENTICAL |
| [E37](astra5/job19/audit/E37/cmp.txt) | `LmpBase` min = 0 | 5 | 605 | 0 | 2,541,700 | `57e24deb5d2414ab448faeaa06033895a25df529acf1ecbb428bf9b94aee713f` | 0 | 0 | IDENTICAL |
| [E38](astra5/job19/audit/E38/cmp.txt) | `LmpBase` max = 20 | 5 | 810 | 0 | 3,565,347 | `8e596bb23bb95a394062c66d10cbe8bd689030c14757239c830d8df7133ed6f2` | 0 | 0 | IDENTICAL |
| [E39](astra5/job19/audit/E39/cmp.txt) | `HistoryPruneDepth` min = 0 | 5 | 642 | 0 | 2,747,053 | `79d1cad7be6435417d5c455a7fc86a8bbb48788889da091196febdce6bcf4ddf` | 0 | 0 | IDENTICAL |
| [E40](astra5/job19/audit/E40/cmp.txt) | `HistoryPruneDepth` max = 10 | 5 | 450 | 0 | 1,855,783 | `3f88c354a5061a923d6b36de4185935557d31bd517f46d570bebcb8d3803f0e0` | 0 | 0 | IDENTICAL |
| [E41](astra5/job19/audit/E41/cmp.txt) | `HistoryPruneMultiplier` min = 0 | 5 | 416 | 0 | 1,699,426 | `3d6efa4031ee7ddb57140dee684f2559f3c591c4d083bb36af97f3660ebf255e` | 0 | 0 | IDENTICAL |
| [E42](astra5/job19/audit/E42/cmp.txt) | `HistoryPruneMultiplier` max = 20000 | 5 | 532 | 0 | 2,225,146 | `33dbd16552a138531c99141a4dc553c0117bca019169a9b90287706da8f4934a` | 0 | 0 | IDENTICAL |
| [E43](astra5/job19/audit/E43/cmp.txt) | `SeeQuietMultiplier` min = 0 | 5 | 538 | 0 | 2,090,804 | `953ee4e8f0f7ae77f3b64671371b24a7bbd5f63c7233a4274d3f8c9224d3deba` | 0 | 0 | IDENTICAL |
| [E44](astra5/job19/audit/E44/cmp.txt) | `SeeQuietMultiplier` max = 200 | 5 | 490 | 0 | 1,966,225 | `b68eafc2e59eccc70e4f955d13a692379a7f107904d113f362ba3a9959b6262b` | 0 | 0 | IDENTICAL |
| [E45](astra5/job19/audit/E45/cmp.txt) | `SeeNoisyMultiplier` min = 0 | 5 | 547 | 0 | 2,303,066 | `94afdf7374562744b9aef8c912e0d96a9d05ceea07408e5613029f4b34d2ba8d` | 0 | 0 | IDENTICAL |
| [E46](astra5/job19/audit/E46/cmp.txt) | `SeeNoisyMultiplier` max = 1000 | 5 | 321 | 0 | 1,249,408 | `ea410946ffad0517875c774f20a586fa4a32bd24b85f8f3db1190749d78afb24` | 0 | 0 | IDENTICAL |
| [E47](astra5/job19/audit/E47/cmp.txt) | `SingularDepth` min = 2 | 5 | 551 | 0 | 1,901,705 | `76ea9275a2df9487bce275a0f22d960611e193078ef733b24a06f730c229c1f4` | 0 | 0 | IDENTICAL |
| [E48](astra5/job19/audit/E48/cmp.txt) | `SingularDepth` max = 20 | 5 | 500 | 0 | 1,788,193 | `ed461083936ca31cbbf86b28cce4ab41cdcdee7a00d2d14ae27a705120351699` | 0 | 0 | IDENTICAL |
| [E49](astra5/job19/audit/E49/cmp.txt) | `SingularMargin` min = 0 | 5 | 511 | 0 | 1,999,959 | `b2aabcc8caf6ae9aa6750b2f0564ab05f1bc9acce1e903d836fc277f976fef6a` | 0 | 0 | IDENTICAL |
| [E50](astra5/job19/audit/E50/cmp.txt) | `SingularMargin` max = 10 | 5 | 609 | 0 | 2,437,306 | `14df8b77bc3a5578f5033d38f7bc2a9f978ac87f9df1519fecade04c4be74ebb` | 0 | 0 | IDENTICAL |
| [E51](astra5/job19/audit/E51/cmp.txt) | `IirDepth` min = 1 | 5 | 667 | 0 | 2,863,916 | `28ee9d7fb36ec6780fc60fceca21285c830d5bdbca25bcdcc5f45231f7c76813` | 0 | 0 | IDENTICAL |
| [E52](astra5/job19/audit/E52/cmp.txt) | `IirDepth` max = 20 | 5 | 614 | 0 | 2,773,315 | `0aed826bd4d01bac77a197a4d221489a9042f904aca600ecf180cbbce2f9d21e` | 0 | 0 | IDENTICAL |
| [E53](astra5/job19/audit/E53/cmp.txt) | `ProbcutDepth` min = 1 | 5 | 631 | 0 | 2,718,766 | `3f07bfd210a58d731169a621995d5af50eae20e3963de900df5af3a94904d7a1` | 0 | 0 | IDENTICAL |
| [E54](astra5/job19/audit/E54/cmp.txt) | `ProbcutDepth` max = 20 | 5 | 617 | 0 | 2,620,994 | `a948d3ea3261a305acb1c5fcc90c0f7acd7b20f4424ea7a7ac968619df08edf3` | 0 | 0 | IDENTICAL |
| [E55](astra5/job19/audit/E55/cmp.txt) | `ProbcutMargin` min = 0 | 5 | 414 | 0 | 1,622,063 | `d31eaef97840ae7b74d864d9494554d22db96b69b5334b329297f2c9c9887544` | 0 | 0 | IDENTICAL |
| [E56](astra5/job19/audit/E56/cmp.txt) | `ProbcutMargin` max = 1000 | 5 | 562 | 0 | 2,369,775 | `4fcaa5d3fc0d0ff6e3a5a6ac54e99270e8a17b4d8641471966cd6a003434e06c` | 0 | 0 | IDENTICAL |
| [E57](astra5/job19/audit/E57/cmp.txt) | `QsFutilityMargin` min = 0 | 5 | 568 | 0 | 2,426,876 | `b7afee3d7aa7add105aad330b2134a070c2ad5561a3f2b6d40f96291ee155ba9` | 0 | 0 | IDENTICAL |
| [E58](astra5/job19/audit/E58/cmp.txt) | `QsFutilityMargin` max = 1000 | 5 | 542 | 0 | 2,207,305 | `53022266a22d50838cde30c6ad0f02e6935af57eedbea3f45ec2b35b86b2862d` | 0 | 0 | IDENTICAL |
| [E59](astra5/job19/audit/E59/cmp.txt) | `AspirationDelta` min = 4 | 5 | 461 | 0 | 1,880,056 | `cf6759999364cd6ee972cc2b5f7dcf0bc97f920a4b8f02cf6e51f197af1cebe5` | 0 | 0 | IDENTICAL |
| [E60](astra5/job19/audit/E60/cmp.txt) | `AspirationDelta` max = 200 | 5 | 506 | 0 | 1,992,661 | `57f2b844d7d4a212d6309bc3928e52046eee44645031ccdeb9f22d6c8cec759a` | 0 | 0 | IDENTICAL |
| [E61](astra5/job19/audit/E61/cmp.txt) | `HistoryBonusQuadratic` min = 0 | 5 | 816 | 0 | 3,474,608 | `f4741efd5a9718f5228caedb5e11349205922f83ff96b1df7bd1431c12329a2f` | 0 | 0 | IDENTICAL |
| [E62](astra5/job19/audit/E62/cmp.txt) | `HistoryBonusQuadratic` max = 100 | 5 | 511 | 0 | 2,109,351 | `38618a4cd3060a34bbae46800f24f025edf2773d6a44ec9794a6a6c4b1423f3b` | 0 | 0 | IDENTICAL |
| [E63](astra5/job19/audit/E63/cmp.txt) | `HistoryBonusLinear` min = 0 | 5 | 605 | 0 | 2,540,015 | `b28b8f0c07eb28333b1c42374eb532428b689ccf72b0da9ed712780466d5cb00` | 0 | 0 | IDENTICAL |
| [E64](astra5/job19/audit/E64/cmp.txt) | `HistoryBonusLinear` max = 500 | 5 | 590 | 0 | 2,294,597 | `1e9ce59b644658c1ff28c7510a57075ff5a57063f65c319ddb953812b637e934` | 0 | 0 | IDENTICAL |
| [E65](astra5/job19/audit/E65/cmp.txt) | `HistoryBonusMax` min = 100 | 5 | 601 | 0 | 2,612,934 | `6b9c4b0e397cf9affd32d15554755cc1c7d8bb83d32f9d3a65bba9b2ba1a8cc5` | 0 | 0 | IDENTICAL |
| [E66](astra5/job19/audit/E66/cmp.txt) | `HistoryBonusMax` max = 10000 | 5 | 654 | 0 | 2,780,621 | `5dc479e1de55eb2e25864fd58d7005dafa82517ee2ca920406bce39a88ead1fc` | 0 | 0 | IDENTICAL |
| [E67](astra5/job19/audit/E67/cmp.txt) | `LmrHistoryDivisor` min = 1000 | 5 | 581 | 0 | 2,523,423 | `3eedc4f28333dd0c4e9c611437aef058ee8d9580d59a74fbcc1129a20726fa66` | 0 | 0 | IDENTICAL |
| [E68](astra5/job19/audit/E68/cmp.txt) | `LmrHistoryDivisor` max = 30000 | 5 | 655 | 0 | 2,612,671 | `fd23c5cdc574e3ad39b305c7b980134d6e3817d955fb487bd5f1de210d7e9c4d` | 0 | 0 | IDENTICAL |
| [E69](astra5/job19/audit/E69/cmp.txt) | `CheckExtensionDepth` min = 1 | 5 | 712 | 0 | 2,988,902 | `feec5fd37629a85bd400f25a06f5561f9fb5b648f4dff4f4ba24654bb0c00803` | 0 | 0 | IDENTICAL |
| [E70](astra5/job19/audit/E70/cmp.txt) | `CheckExtensionDepth` max = 30 | 5 | 604 | 0 | 2,357,688 | `084f50ed6bf8de1364f9b969409ad1f64c2fcef029eda56bebe2460f4f1e25c2` | 0 | 0 | IDENTICAL |
| [E71](astra5/job19/audit/E71/cmp.txt) | `LmrCutoffThreshold` min = 0 | 5 | 631 | 0 | 2,580,612 | `b50989067da6e90583c4deafb7a93ad79f9a27d62a4b9efbb3e7063da8951d87` | 0 | 0 | IDENTICAL |
| [E72](astra5/job19/audit/E72/cmp.txt) | `LmrCutoffThreshold` max = 20 | 5 | 471 | 0 | 1,930,986 | `ad38c4fe128c0f7ea4756f68d12d5a193954c2957423538b43b2da318fd9c3ba` | 0 | 0 | IDENTICAL |
| [E73](astra5/job19/audit/E73/cmp.txt) | `MaterialCorrectionWeight` min = 0 | 5 | 502 | 0 | 2,028,092 | `953bf1ef291925825731216eb25a31cc3ee2b3ea8f3e82aefd36d137b0d29647` | 0 | 0 | IDENTICAL |
| [E74](astra5/job19/audit/E74/cmp.txt) | `MaterialCorrectionWeight` max = 300 | 5 | 478 | 0 | 1,898,120 | `d88044da0e5efdc2dd77570150ef3442128354fb6571144aa33f12bdf8cb67b1` | 0 | 0 | IDENTICAL |
| E75 | `CaptureFutilityBase` min = 0 | 0 | — | — | — | — | — | — | start |
| [E76](astra5/job19/audit/E76/cmp.txt) | `CaptureFutilityBase` max = 1000 | 5 | 367 | 0 | 1,417,438 | `03712f528c104067ac3c775785c03b836b3b1307614c151ce7b62ecc499ec70b` | 0 | 0 | IDENTICAL |
| E77 | `FailLowContinuationBonus` min = 0 | 0 | — | — | — | — | — | — | start |
| [E78](astra5/job19/audit/E78/cmp.txt) | `FailLowContinuationBonus` max = 300 | 5 | 450 | 0 | 1,825,151 | `90f0bcbf442b1b806a9bb1eadbee6eae9cb84ae3fbb47bedef6802d2ce508135` | 0 | 0 | IDENTICAL |
| E79 | `EvalSwingMult` min = 0 | 0 | — | — | — | — | — | — | start |
| [E80](astra5/job19/audit/E80/cmp.txt) | `EvalSwingMult` max = 64 | 5 | 465 | 0 | 1,875,343 | `d63f0386a5ef85a55fe6b61258abe4e34e192b1ccf9e6fab12010818012fc116` | 0 | 0 | IDENTICAL |
| [D2](astra5/job19/audit/D2/cmp.txt) | PC20, 1,000,000 nodes | 4 | 237 | 0 | 142,803,112 | `31e8ece38525bcab41311e270026d76baef0df8c6c3f7cab89e1dc8e6d3fb5c9` | 0 | 0 | IDENTICAL |

## Facts

Each build recorded 45,695 searched plies in 400 measured games, including 0 rows without a node count. The recorded node sum was 540,881,580 per build. The controls and E’s duplicate aggregate are excluded from these totals.

The game start and completion timestamps showed at most 2 simultaneous measured games across both builds. The recorded stage order matched D1, then the played edges in increasing edge number, then D2.

The lower and upper ends of the 40 options produced 80 entries. Four lower bounds equalled their start value. The other 76 supplied 380 scheduled random-opening games per build. [Edge manifest totals](astra5/job19/settings/edge-summary.txt)

## Suspicions

The record format would expose a search difference that changed a bestmove or the last reported node count. A difference confined to an internal hash-table probe or accumulator update could leave both fields unchanged.

## What I did not do

This job measured move and node identity. It included no strength match, wall-clock benchmark or search-internal trace.

**What this cannot see**, in the job’s words

> the PC's engine build (clang 23 for Windows, its profile), its trained nets (net768 is made up), values between the edges other than job 18's sets, two or more settings at an edge at once, more than one thread.

## What I am not sure about

I cannot infer how often a new opening would expose a difference. The deepest comparison covers four specific book positions played to completion, and each played edge has its own five opening seeds.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job19`.

```text
A  forge-combo29/REPORT_astra5_job19.md
M  forge-combo29/astra5/job19/stamps.txt
forge-combo29/astra5/job19:
C19
D1-kF
D1-r15d
D2-kF
D2-r15d
E-kF
E-r15d
E02-kF
E02-r15d
E03-kF
E03-r15d
E04-kF
E04-r15d
E05-kF
E05-r15d
E06-kF
E06-r15d
E07-kF
E07-r15d
E08-kF
E08-r15d
E09-kF
E09-r15d
E10-kF
E10-r15d
E11-kF
E11-r15d
E12-kF
E12-r15d
E13-kF
E13-r15d
E14-kF
E14-r15d
E15-kF
E15-r15d
E16-kF
E16-r15d
E17-kF
E17-r15d
E18-kF
E18-r15d
E19-kF
E19-r15d
E20-kF
E20-r15d
E21-kF
E21-r15d
E22-kF
E22-r15d
E23-kF
E23-r15d
E24-kF
E24-r15d
E25-kF
E25-r15d
E26-kF
E26-r15d
E27-kF
E27-r15d
E28-kF
E28-r15d
E29-kF
E29-r15d
E30-kF
E30-r15d
E31-kF
E31-r15d
E32-kF
E32-r15d
E33-kF
E33-r15d
E34-kF
E34-r15d
E35-kF
E35-r15d
E36-kF
E36-r15d
E37-kF
E37-r15d
E38-kF
E38-r15d
E39-kF
E39-r15d
E40-kF
E40-r15d
E41-kF
E41-r15d
E42-kF
E42-r15d
E43-kF
E43-r15d
E44-kF
E44-r15d
E45-kF
E45-r15d
E46-kF
E46-r15d
E47-kF
E47-r15d
E48-kF
E48-r15d
E49-kF
E49-r15d
E50-kF
E50-r15d
E51-kF
E51-r15d
E52-kF
E52-r15d
E53-kF
E53-r15d
E54-kF
E54-r15d
E55-kF
E55-r15d
E56-kF
E56-r15d
E57-kF
E57-r15d
E58-kF
E58-r15d
E59-kF
E59-r15d
E60-kF
E60-r15d
E61-kF
E61-r15d
E62-kF
E62-r15d
E63-kF
E63-r15d
E64-kF
E64-r15d
E65-kF
E65-r15d
E66-kF
E66-r15d
E67-kF
E67-r15d
E68-kF
E68-r15d
E69-kF
E69-r15d
E70-kF
E70-r15d
E71-kF
E71-r15d
E72-kF
E72-r15d
E73-kF
E73-r15d
E74-kF
E74-r15d
E76-kF
E76-r15d
E78-kF
E78-r15d
E80-kF
E80-r15d
K19-1
K19-2
audit
driver
prediction.txt
settings
stamps.txt
step0

forge-combo29/astra5/job19/C19:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/C19/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job19/D1-kF:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/D1-kF/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job19/D1-r15d:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/D1-r15d/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job19/D2-kF:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/D2-kF/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job19/D2-r15d:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/D2-r15d/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job19/E-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
sources.tsv

forge-combo29/astra5/job19/E-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
sources.tsv

forge-combo29/astra5/job19/E02-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E02-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E02-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E02-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E03-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E03-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E03-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E03-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E04-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E04-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E04-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E04-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E05-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E05-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E05-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E05-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E06-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E06-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E06-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E06-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E07-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E07-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E07-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E07-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E08-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E08-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E08-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E08-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E09-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E09-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E09-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E09-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E10-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E10-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E10-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E10-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E11-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E11-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E11-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E11-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E12-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E12-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E12-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E12-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E13-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E13-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E13-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E13-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E14-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E14-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E14-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E14-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E15-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E15-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E15-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E15-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E16-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E16-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E16-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E16-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E17-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E17-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E17-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E17-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E18-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E18-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E18-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E18-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E19-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E19-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E19-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E19-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E20-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E20-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E20-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E20-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E21-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E21-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E21-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E21-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E22-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E22-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E22-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E22-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E23-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E23-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E23-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E23-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E24-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E24-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E24-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E24-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E25-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E25-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E25-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E25-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E26-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E26-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E26-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E26-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E27-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E27-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E27-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E27-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E28-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E28-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E28-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E28-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E29-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E29-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E29-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E29-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E30-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E30-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E30-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E30-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E31-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E31-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E31-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E31-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E32-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E32-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E32-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E32-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E33-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E33-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E33-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E33-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E34-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E34-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E34-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E34-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E35-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E35-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E35-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E35-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E36-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E36-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E36-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E36-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E37-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E37-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E37-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E37-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E38-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E38-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E38-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E38-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E39-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E39-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E39-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E39-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E40-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E40-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E40-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E40-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E41-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E41-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E41-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E41-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E42-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E42-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E42-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E42-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E43-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E43-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E43-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E43-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E44-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E44-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E44-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E44-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E45-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E45-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E45-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E45-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E46-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E46-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E46-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E46-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E47-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E47-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E47-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E47-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E48-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E48-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E48-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E48-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E49-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E49-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E49-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E49-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E50-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E50-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E50-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E50-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E51-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E51-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E51-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E51-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E52-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E52-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E52-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E52-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E53-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E53-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E53-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E53-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E54-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E54-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E54-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E54-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E55-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E55-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E55-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E55-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E56-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E56-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E56-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E56-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E57-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E57-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E57-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E57-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E58-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E58-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E58-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E58-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E59-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E59-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E59-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E59-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E60-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E60-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E60-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E60-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E61-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E61-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E61-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E61-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E62-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E62-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E62-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E62-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E63-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E63-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E63-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E63-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E64-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E64-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E64-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E64-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E65-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E65-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E65-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E65-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E66-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E66-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E66-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E66-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E67-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E67-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E67-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E67-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E68-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E68-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E68-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E68-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E69-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E69-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E69-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E69-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E70-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E70-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E70-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E70-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E71-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E71-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E71-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E71-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E72-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E72-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E72-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E72-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E73-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E73-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E73-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E73-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E74-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E74-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E74-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E74-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E76-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E76-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E76-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E76-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E78-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E78-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E78-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E78-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E80-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E80-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/E80-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/E80-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job19/K19-1:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/K19-1/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job19/K19-2:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job19/K19-2/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job19/audit:
C19
D1
D2
E
E02
E03
E04
E05
E06
E07
E08
E09
E10
E11
E12
E13
E14
E15
E16
E17
E18
E19
E20
E21
E22
E23
E24
E25
E26
E27
E28
E29
E30
E31
E32
E33
E34
E35
E36
E37
E38
E39
E40
E41
E42
E43
E44
E45
E46
E47
E48
E49
E50
E51
E52
E53
E54
E55
E56
E57
E58
E59
E60
E61
E62
E63
E64
E65
E66
E67
E68
E69
E70
E71
E72
E73
E74
E76
E78
E80
K19
aggregate.py
audit.py
concurrency
monitor.py
overview.py
reading.txt
stage-order.tsv
stage-summary.tsv

forge-combo29/astra5/job19/audit/C19:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
live-first-difference.txt
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/D1:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/D2:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E:
arms.tsv
assembly.txt
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
source-index.txt
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E02:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E03:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E04:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E05:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E06:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E07:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E08:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E09:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E10:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E11:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E12:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E13:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E14:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E15:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E16:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E17:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E18:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E19:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E20:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E21:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E22:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E23:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E24:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E25:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E26:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E27:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E28:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E29:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E30:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E31:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E32:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E33:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E34:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E35:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E36:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E37:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E38:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E39:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E40:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E41:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E42:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E43:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E44:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E45:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E46:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E47:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E48:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E49:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E50:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E51:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E52:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E53:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E54:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E55:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E56:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E57:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E58:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E59:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E60:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E61:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E62:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E63:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E64:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E65:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E66:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E67:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E68:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E69:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E70:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E71:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E72:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E73:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E74:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E76:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E78:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/E80:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/K19:
K19-1-controller.txt
K19-2-controller.txt
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job19/audit/concurrency:
arm-intervals.tsv
check_design.py
concurrency.txt
driver-review.txt
timeline.py

forge-combo29/astra5/job19/driver:
aggregate.py
arm.py
compare_stage.py
selfplay.py
stage.py

forge-combo29/astra5/job19/settings:
check-played-settings.py
edge-option-probe.txt
edge-sets.tsv
edge-summary.txt
make-edges.py
manifest-check.txt
played-settings-audit.tsv
probe-edges.py
uci-bounds.txt
verify_manifest.py

forge-combo29/astra5/job19/step0:
identities.txt
kF
pc20.txt
r15d

forge-combo29/astra5/job19/step0/kF:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt

forge-combo29/astra5/job19/step0/r15d:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
```
