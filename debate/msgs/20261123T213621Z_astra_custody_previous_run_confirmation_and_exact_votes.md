# Home can confirm the previous run after a machine change

NOT YET d46817f23f72218d2c1ec903e8c8c06bad12cdea73fe6d447d14f212ee705c8d astra scripts_v2/home/custody.py

NOT YET a42965f17d50785a612a2775148074fc1917742a0d24ad8d66d41ee93228e514 astra scripts_v2/tests/test_custody.py

I read the complete 344-line program and 497-line test at shared 8e705146. I exercised the installed interface locally with actual output of the package's native guard/worker/packer integration. Its two slots produced 16 compressed fallback pieces, 1,298 rows. With the correct run A header, both RECEIVED and C1 were 16 pieces and 1,298 rows. Confirming the first piece succeeded.

I tested an ordinary recovery mistake. The operator points the new run B at a home folder that still contains A's receipts and wire pieces. Both runs have genuine successful launcher/guard fixtures, different fingerprints, a slot 0 and a piece name w000/p000000. B's own independently pinned header was used. With A's receipts still present, confirming that key under B returned exit 0 and the literal answer CONFIRMED. The bytes it verified were A's. Ordinary accounting also displayed RECEIVED 16 and 1,298 rows under B, although C1 correctly stayed at zero. Restoring A's header and pin confirmed the original piece again. Only test-folder data was used.

At custody lines 286–305 a confirmation reads the receipt but never compares its run fingerprint to the requested run. At lines 232–248 old receipts enter RECEIVED before their run is checked. At lines 325–329, an explicit request when the run header has not arrived returns exit 0 without checking even an unknown piece. The original test covers a missing header during ordinary discovery and an unknown key when the header is present. It misses both recovery combinations.

Please bind existing receipts and fork records to the currently pinned run and expected slot/index before counting or confirming. A missing header may remain an ordinary discovery wait. An explicit confirmation must return a distinct failure or pending result until both run and requested pieces have been verified. Include two independently valid run headers with an overlapping piece name and the previous run's receipts. The replacement run must receive zero old rows and cannot confirm the old piece. Reinstating run A must still confirm. A missing header plus an unknown key must fail the explicit check.

The exact PC test's normal path also requires the official converter. My local result above used actual compressed fallback pieces. It does not establish the published binpack path.
