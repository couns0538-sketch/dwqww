# fable-review-S39

Base: opus-sol-S39 head d9be88f8. Correction (Fable review): test_v3c_s39.py::test_copies SHA256-compares the v3c trainer file
in this folder byte-for-byte with the staged LF copy F:/opus_scratch/sol_S39/opus_nnue_smoke_s39_v3c.py. On a checkout with
core.autocrlf=true (this PC) the folder's file arrives as CRLF, so the comparison is checkout-dependent: it fails here although
it passed in Opus's LF environment (LF-normalised the two files are identical; every other test in the file already passes).
Fix: `.gitattributes` with `* -text` in this folder, so every file is checked out byte-identical to its blob. Verified:
test_v3c_s39.py prints OK in a fresh detached worktree of this branch on the PC. No trainer or test logic changed.
