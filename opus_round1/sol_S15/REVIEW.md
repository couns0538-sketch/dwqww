# fable-review-S15

Base: opus-sol-S15 head 3d22bb52. Correction (Fable review): the job test loads tools/match/pgn_stats.py through the tool's
load_pgn_checker, which SHA256-checks that file against a hash frozen on the LF content stored in git. On a checkout with
core.autocrlf=true (this PC) every text file arrives as CRLF, so the check is checkout-dependent: it fails here although it
passed in Opus's LF environment. Fix: a repository-root `.gitattributes` with `* -text` on this branch, so every file (the
checker under tools/ included) is checked out byte-identical to its blob. Verified: test_forge_sol_S15_spsa_v2.py prints OK in a
fresh detached worktree of this branch on the PC. No tool or test logic changed.
