# A natural 101,231-row six-man pilot found one certified opposite-sign label

Neon, we can now price the distinction between encountering six pieces and obtaining a trustworthy label. I measured every exactly-six-piece position actually written in the two 8,192-game banks, including the 388 final suggestions that did not get played. Of 101,231 pre-filter candidates, the available tables and the rule-aware procedure could certify 30,490. Only one certified search value had the opposite sign from a decisive table result. That observation does not establish the rate in the remaining 70,741 candidate rows.

| Independent bank | Raw six-piece rows | Certified rows | Certified decisive rows | Strictly opposite signs | Games contributing certified positions |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 48,757 | 14,337 | 8,427 | 0 | 1,506 |
| B | 52,474 | 16,153 | 11,020 | 1 | 1,580 |

The strict opposite-sign rates among all certified positions are 0 and 0.0062%. A draw or a zero search score never counts as an opposite win/loss sign. A whole-game bootstrap gives 0–0.0206% in B. A’s bootstrap cannot estimate unseen variation with zero events. Counting independent contributing games that contain any such row gives 0/1,506 (exact 95% upper 0.245%) and 1/1,580 (0.0016–0.352%). The most numerous missing classes were KRBPvKR and KRNPvKR in both banks. Thirty-one additional rows reached the conservative fifty-move boundary. The proposed 1% trigger did not fire on supported material. Unknown cases still admit broad rates across the entire candidate set.

The witness is bank B, game 2563, ply 125, FEN `8/8/8/1kR5/p6P/1p1K4/8/8 b - - 0 63`. The actual warm game wrote −54 cp and played b5c5. Both the root and that move are certified winning. Fresh 2k/8k/250k/1M hard-node searches all chose b5c5 and gave +189/+249/+237/+1019 cp. The color-reflected table probe also won. Here the search label was wrong while the played move was right.

| Local scan, candidates/s then certified rows/s | Cold | Immediate repeat |
| --- | ---: | ---: |
| One worker | 1,888 / 569 | 2,193 / 660 |
| Four workers | 2,285 / 688 | 2,918 / 879 |

Each scan reconstructed full histories, matched FEN and checked move legality on every candidate. All four produced the same ordered classification ledger. Only the six private verified table files were evicted; all their 354,569 pages had zero residency at both cold starts. Four cold workers read 108.67 decimal MB and populated 26,531 pages; both repeats registered zero physical reads. One-worker cold per-lookup p95 was 1.64 ms, versus 5.60 ms with four cold workers on this shared machine. CPU 35.9–41.9 seconds per full scan. The table excludes manifest preparation, disposition of unknowns, GPU training and transfer. It prices this local pre-filter sample with partial coverage. The actual PC must repeat on its own files, retained data and disk before a budget or strength decision.

Source-manifest SHA-256 cbfa90ce609f7b7797357b507c7aba53a2cf582058680c2ba9cfc861f4856d78. Classification ledger dcef9b6ab8cba53a469f6e564c033d03bb8223b83b2de855f33ff586055d3d62. Local timing record 0404ea8e7f571af61c2cccc029a000bd270b9ea86e59aa0f69422063fe90c4d7. A later PC run should separately report rows that pass the real filter, table coverage, strict sign errors, effects on raw game outcomes, and head-to-head play with the trained models.
