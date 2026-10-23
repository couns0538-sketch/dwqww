# Fixed pure-teacher pilot learning curves

This read-only diagnostic evaluates every exported checkpoint on the same complete 14,895 fresh training positions. Validation MSE comes from the authenticated original full 4,149-position reports. Teacher targets are constant across epochs. The original online training loss uses changing result weights and parameters during each epoch; it is a different metric and cannot establish teacher-loss learning or overfitting.

| Run | Initial train MSE | Epoch 20 train MSE | Initial validation MSE | Epoch 20 validation MSE |
| --- | ---: | ---: | ---: | ---: |
| zero | 0.0061279211 | 0.0024297396 | 0.0066605362 | 0.0076272026 |
| warm | 0.0055287028 | 0.0015423693 | 0.0060820491 | 0.0072062214 |

Train-down/heldout-up divergence is consistent with overfitting to these small fresh training games. It does not establish behavior on the full legacy corpus or playing strength. All 42 exports, reports, source modules and prepared inputs were authenticated; original selection is unchanged. No training, model modification, CI, acceptance or Elo conclusion is produced.

| Epoch | Zero train MSE | Zero original validation MSE | Warm train MSE | Warm original validation MSE |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0.0061279211 | 0.0066605362 | 0.0055287028 | 0.0060820491 |
| 1 | 0.0060835949 | 0.0066497456 | 0.0044470247 | 0.0062152625 |
| 2 | 0.0056472694 | 0.0066894531 | 0.0037952532 | 0.0063628628 |
| 3 | 0.0051283573 | 0.0068026824 | 0.0033120242 | 0.0064669767 |
| 4 | 0.0046302725 | 0.0068981646 | 0.0028979963 | 0.0065729174 |
| 5 | 0.0041781512 | 0.0069360195 | 0.0025663684 | 0.0066811885 |
| 6 | 0.0037749747 | 0.0069578589 | 0.0023097917 | 0.0067710986 |
| 7 | 0.0034343458 | 0.0070390849 | 0.0021045893 | 0.0068331382 |
| 8 | 0.0031744049 | 0.0071917405 | 0.0019435074 | 0.0069053525 |
| 9 | 0.0029404286 | 0.0072111837 | 0.0018226194 | 0.0069674415 |
| 10 | 0.0027762085 | 0.0072912414 | 0.0017295984 | 0.0070115886 |
| 11 | 0.0026582372 | 0.0073890527 | 0.0016584054 | 0.0070586167 |
| 12 | 0.0025637443 | 0.0074100753 | 0.0016095802 | 0.0070900284 |
| 13 | 0.0025072827 | 0.0074663803 | 0.0015781705 | 0.0071162627 |
| 14 | 0.0024600919 | 0.0075224787 | 0.0015558628 | 0.0071561041 |
| 15 | 0.0024389977 | 0.0075435291 | 0.0015447226 | 0.0071663441 |
| 16 | 0.0024294360 | 0.0075747120 | 0.0015396005 | 0.0071835384 |
| 17 | 0.0024278003 | 0.0076023547 | 0.0015394908 | 0.0071939567 |
| 18 | 0.0024269367 | 0.0076145590 | 0.0015400113 | 0.0072002133 |
| 19 | 0.0024277998 | 0.0076217381 | 0.0015409213 | 0.0072021904 |
| 20 | 0.0024297396 | 0.0076272026 | 0.0015423693 | 0.0072062214 |
