# Existing tactical failure audit — 2026-10-28 UTC

Commands: `python3 -B /tmp/astra-review-smp/tactical_audit.py`; the WAC enumeration used the same body preserved in `wac_mate_enumeration.py` via `PYTHONPATH=/workspace/.cloud-setup/venv/lib/python3.12/site-packages python3 -B` stdin. No compilation, engine modifications, test-expectation changes or tuning.

Native engine: candidate Release `/tmp/forge-astra-build-j5fix-20261029/forge`; Hash1MB, Threads1, OwnBook=false, other options default. Raw stdin/stdout/stderr for all seven searches preserved. Source is unchanged from the previously qualified A2 binary.

- White depth1 unrestricted: **c6d6**, **569cp**; forced c7c8r **451cp**; forced c7c8q **0cp**. Independent python-chess confirms all moves legal and queen promotion really stalemates.
- Mirrored black depth1: **c3d3**, **569cp**; forced c2c1r **451cp**; forced c2c1q **0cp**, again genuine stalemate. Thus these two current assertions fail on shallow move preference: the engine chooses a legal king move valued above immediate rook promotion. They do not demonstrate failure to recognize the queen-promotion stalemate. No game-theoretic outcome of the alternative king moves is claimed here.
- WAC001 depth12: **f6h5**, **623cp**, legal. Independent enumeration confirms **g3g6** really forces mate on the following white move: all **34** legal black replies permit a mate-in-one. The expected tactical solution is therefore valid chess; the engine's current depth12 search misses it. This is a pre-existing tactical weakness (baseline produced the exact same diagnostics), not evidence that the expectation is wrong. Its precise selective-search cause is not established by this bounded audit.

These results do not justify silently weakening or relabelling expected values. A sanitizer run can have zero sanitizer diagnostics while CTest still reports these four tactical assertion lines. The established explicit known-failure gate should be reported separately from raw CTest status. No new bug fix or strength claim is made.

IDEA_SOURCE: Owner's sanitizer-review request and Forge's existing tests only.
