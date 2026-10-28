# fable-review-SA2

Base: opus-sol-SA2 head 1c1a44ed. Correction (Fable review): test_trainer_clip_sa2.py::test_copy_matches SHA256-compares
trainer_v3c_clip.py in this folder byte-for-byte with the staged LF copy F:/opus_scratch/sol_SA2/opus_nnue_smoke_sa2_clip.py.
On a checkout with core.autocrlf=true (this PC) the folder's file arrives as CRLF, so the comparison is checkout-dependent: it
fails here although it passed in Opus's LF environment (LF-normalised the two files are identical; every other test already
passes). Fix: `.gitattributes` with `* -text` in this folder, so every file is checked out byte-identical to its blob. Verified:
test_trainer_clip_sa2.py prints OK in a fresh detached worktree of this branch on the PC. No trainer or test logic changed.
