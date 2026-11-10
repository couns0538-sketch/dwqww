# Patch replay order

These are sequential source-only exports, not independent cherry-picks. Start
with locked commit `16833ecc03b425586f91f4c8834dea8807bf4c22` and apply:

1. F6-uci-case.patch
2. S1-book-reuse.patch
3. F1-smp-reset.patch
4. S2-nnue-castling.patch
5. F2-final-nodes.patch
6. F5-init-once.patch
7. F3-stop-latch.patch
8. F4-exception-cleanup.patch
9. S3-material-cache.patch
10. E1-continuation4.patch
11. F7-tt-depth.patch
12. S4-legal-witnesses.patch
13. C1-material-cache-gating.patch
14. C2-option-order.patch
15. C3-uci-exception-recovery.patch
16. C4-restricted-fallback.patch
17. C5-default-uci-gating.patch
18. S5-compact-pawn-cache.patch
19. S6-tt-replacement-cache.patch
20. S7-picker-self-swap.patch
21. S8-weak-queen-mask.patch

On 2026-11-10, every patch applied successfully to a fresh archive of the
locked source. Recursive comparison of the resulting `src/` and `include/`
trees against the tested branch found zero differences. Test evidence lives
on the branch and is not included in these source-only patch exports.

Every switch defaults off; E1 additionally defaults its runtime weight to
zero. All performance/strength acceptance statuses remain UNPROVEN. See
`REPORT.md` for findings, scope, finite tests and outstanding native gates.
