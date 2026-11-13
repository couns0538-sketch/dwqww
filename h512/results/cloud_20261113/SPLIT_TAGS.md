# Holdout shard tags stop at a digit boundary

Date: 2026-11-13. No real shard was read or rewritten. This is not an Elo result.

`fable_nnue_data.py split` selected a holdout file when `--holdout-shards` was a substring of the file name. The default tags are `_013,_014`. That selects `fb2_013.pos`. It also selected `fb2_0130.pos`, which would then be removed from training and sampled into the holdout.

`shard_tag_matches` requires the character after the tag to be absent or not a digit. `fb2_013.pos`, `fb2_014.pos`, and `fb2_013_extra.pos` still match. `fb2_0130.pos` and `fb2_001.pos` do not match `_013`. Names `fb2_001` through `fb2_038` are unchanged under the default tags.

`h512/train/test_split_tags.py` ran the matcher and a split of three tiny FPOS files in a temporary directory (`fb2_013.pos`, `fb2_0130.pos`, `fb2_001.pos`, four rows, partitions 2, train shards 2, seed 1). The manifest holdout list was only `fb2_013.pos`. `fb2_0130.pos` stayed a training shard with its one row kept. The training copy of the holdout row was dropped (kept 1, dropped 1). Train rows written: 2. Exit 0.

The trainer `--exclude` flag is unchanged. Its help text says it is a substring filter.
