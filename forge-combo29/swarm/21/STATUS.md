## 2026-11-16T22:20:39Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18:45Z
seat 21, area 1 (FEN INPUT), branch for-fable-and-opus/swarm-21. **Threads 1 in every run.**

**PC build done (job17)**: file 5's patch (sha256 d6bd72c5…09c1a1a, matches) applied to a
separate copy with `-DFORGE_MATE_ALPHA_GUARD=1`; **all three honesty rows match file 5**:
default 312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517, PC20 278024 / 587276.
No unknown-option / invalid-value / ERROR line in any row. `REPORT_job17.md`.

**Threads audit**: no recorded result of mine used Threads > 1 except job13, which is a
threading test and reports no scores. So no score of mine is provisional for threading.

**Next**: ASan+UBSan build of the PC tree, then re-run my area-1 finds on it under PC20.
Next command: `cmake ~/b/pc_asan ... -DFORGE_MATE_ALPHA_GUARD=1 -fsanitize=address,undefined`
