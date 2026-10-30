# Original native opening generation evidence

Real Forge native helper SHA256ad2fa25e384d71fc30bf5c22108da0336675d93a21fd9b11604964acb771c498; generator sourcef2e25096f4c2a018ced4f731e01999d9700b42a2f1836ae8ba63b137749d43b7. Each run used1024requested nodes, Hash1MB, one CPU at nice19, seed20261030,6–16plies,150cp band at every selected position, and at most2000attempts. Exact argv, startUTC, executable/source digests, original stdout/stderr and actual exit0 are retained beside each directory. Generated books are new artifacts; no original data/live driver/trainer was touched.

Two standard runs each accepted64/231attempts, rejecting167out-of-band paths. Book, metadata, settings and generation summary are byte-identical; runtime logs intentionally retain actual timings and need not match. White final advantage35, Black29, exact0scores0; White score range[-148,128], meanabsolute45.65625cp. The16no-castling Chess960-style run accepted16/75attempts, rejecting59bands; White7/Black9/equal0, White range[-132,101], meanabsolute48.0625cp. These are generated-input characteristics, not Elo or training-gain results.

The separate native audit replays707legal plies and recomputes787selected-position scores/depths/nodes across80unique generated positions:0mismatches, maximal absolute checked score148cp. It verifies every recorded output manifest. Its original probe IPC and native process receipt are preserved underaudit-probe. This is a second run through Forge's own Board/search, not an independent chess implementation.

R8 Windows driver execution isUNVERIFIED. Standard openings.moves contains only legal UCI sequences compatible with the inspected R8 v5 input grammar. Chess960-style openings.fen explicitly disables castling and is NOT consumable by unchanged R8. No trueChess960 support is claimed.

The native audit script records original paths under/tmp; after relocation, replace only those path constants in a separately named copy before any rerun. Existing evidence is never overwritten. SUCCESS.json seals generation after clean probe shutdown; generation.json and stdout retain the earlier GENERATED_NOT_SEALED generation-phase status.

IDEA_SOURCE: user data-quality request and same-repository Forge/R8 interfaces; no external engine code or tuned constants copied.
