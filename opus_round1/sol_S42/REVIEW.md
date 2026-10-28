# fable-review-S42

Base: opus-sol-S42 head. Correction (Fable review, mistake 3): this job verifies SHA256 provenance of text files whose
frozen hashes are of the LF content stored in git. On a Windows checkout with core.autocrlf=true (this PC) the files
are checked out and `git archive`d as CRLF, so the check fails on the PC itself. Fix: `.gitattributes` with `* -text`
in the job folder, so every file stays byte-identical to its blob. Verified: the job test passes from a fresh
`git archive` export of this branch. No tool logic changed.
