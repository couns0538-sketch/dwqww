# fable-review-S27fix

Base: opus-sol-S27fix head. Correction (Fable review, mistake 3): the hygiene tool runs `git apply --check` of the LF
buffix patch against a checkout of the AL1 base and compares frozen SHA256s; on this PC (core.autocrlf=true) the
checkout is CRLF, so three tests report `git_apply_failed` / `control_authority`. Fix: a repository-root
`.gitattributes` with `* -text`, so every checkout of this branch is byte-identical to the blobs. Verification: the job
test in a fresh worktree of this branch (result recorded in FABLE_REVIEW_OPUS.md).
