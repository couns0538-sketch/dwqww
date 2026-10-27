# Forge S17 development report — 2026-10-26

S17 is implemented and locally validated. It produces a deterministic group split and dedupe manifests using unchanged S16/Job D dependencies. Engine and trainer code are untouched. Ordered publication and immutable readback remain the lead agent's next step; this local report does not advance the published job count.

The tool SHA256 is `a0331979574f84e12e03b13870951c215ca0f6933417933df23abc2ae1a25894`. S16 dependency is `5dd0c009566bc5a8c8e06300a8541c5d130d458ca75266a432d1477d1d156332`; its original codec is `6ccf78c864c44155cea22044fe05d0584bec5241acdc5ebb2b71e23886007ab3`.

| Check | Result |
|---|---|
| Behavioral tests, including multi-file continuation and planted interleaving | PASS 14/14 |
| Missing authoritative IDs/provenance in production | PASS: refused before output |
| Reopened A/B/A/B authoritative fixture IDs | PASS: rejected |
| Valid supplied fixture IDs across file edges | PASS: zero cross-split groups; exact POS/HCE round-trip |
| Actual916 defined grouping | PASS: 12 conservative groups, 2 assigned to validation |
| Actual916 retained records | 774 train + 142 validation = 916; zero dropped |
| Actual916 output cross-split defined groups / positions | PASS 0 / 0 |
| Actual916 first vs repeat: every output and MD5 manifest | PASS: byte-identical, no normalization |
| Read-only outputs and source-input rehashes | PASS |
| Manifest over actual916 plus four sealed S16 t300 shards | PASS: 5 files, 158582 records, 158582 unique, zero duplicate/conflicting records |
| Whole-shard duplicate and duplicate-row accounting | PASS on planted fixtures |
| Scratch failure and EOF-without-LF handling | PASS; original RED failures retained |
| Authentic game isolation on actual916 | UNVERIFIED: no authoritative IDs |
| Actual916 binary export/trainer load | UNVERIFIED: real HCE absent; no placeholders or binary pair emitted |
| Real013/014 exclusion and production training approval | UNVERIFIED: external inputs/certificate absent |
| Windows and exact Python3.10 runtime | UNVERIFIED; actual runtime Python3.12/Linux |
| Elo, strength or speed gain | UNVERIFIED; no engine, match or training experiment |

The actual text source SHA256 is `ab429836ee5920e92a61bfb09cf29c15318a7b0e3d63643cf176d1d0962ee0bb`; the matching supplied POS SHA256 is `82dcd3098648684c92b50e6cb7d70b8b9896cb4537b9bc8222be576a820b29bf`. These original sample files are not claimed to be sealed production shards. The four additional S16 files are read-only synthetic t300 outputs; they are manifest inputs only, not additional ordered split rows. Their total157666 records plus916 explains158582 without inventing game metadata.

The declared protocol uses seed20261026 and1000 validation basis points. S16's existing helper finds11 chronology/result boundaries, hence12 defined groups, with no reset at file boundaries. The actual sample lacks authentic game IDs, so `game_overlap_verified=false`, `authentic_game_overlap=UNVERIFIED...` and `training_approved=false` remain explicit. A zero defined-group intersection does not prove authentic-game isolation under unknown interleaving. The parser's absence of castling/EP/clock fields is also retained in the identity limitation.

The first and repeat output-manifest SHA256 is `fff2c54c6f552116ff4b104f069f2f385017186d3f58628cb27810956d6fa1b6`, MD5 `c71b5a9786f92b5efcad03d3ccc8e041`. All output rows preserve their STM score and WHITE result. Missing HCE remains unknown; synthetic tests supply explicit fixture HCE to exercise the unchanged binary writer.

The three actual CLI invocations, configurations, original stdout/stderr, exit status and complete output hashes are preserved under `forge_sol_S17_actual916_qualification_20261026`. Each child alone ran on CPU4 at nice19, with a1GiB address-space cap and120-second timeout. The caller was not pinned. All exited0 with empty stderr and no remaining owned group. Peak child RSS was19368KiB; recorded durations0.678/1.750/15.155seconds are completion evidence only. At the S10 WAC pause check, the controller was already closed; no additional S17 qualification or test workload was launched during that screen.

The initial12 tests failed because the feature was absent, then passed after implementation. Independent source review found two issues: scratch creation outside the failure block, and avoidable full-text/key memory use. The executed original version is retained. Scratch failure is now marked UNSEALED; text verification streams through SQLite audit tables. A separate valid-input test exposed merged records when a source's last line lacked LF; export now appends only the needed separator and preserves CRLF. Two new controls failed before these repairs; all14 pass afterward. The reviewer confirmed the fixes without identifying another concrete issue.

No reference implementation, tuned engine constant or record codec was copied. Idea sources are listed separately. All generated files are new; original source/shards and S16 artifacts remain unchanged. SQLite scratch is removed only after successful audits; failure scratch is retained with an UNSEALED marker. The complete source, original failed versions, tests, raw results and reviews accompany the recoverable checkpoint.

Next: publish and verify this tool in its ordered place. On owner data, provide chronological text/POS, actual HCE and authoritative row IDs for every split source, and every sealed directory for manifest coverage. Run S16 against real013/014 before any production training or real-data threshold ablation. This tool does not queue training or adopt an engine candidate.
