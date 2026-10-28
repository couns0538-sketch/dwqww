# fable-review-S46

Base: opus-sol-S46 head. Correction (Fable review, mistake 3): the job tests compared golden logs and regenerated
fixture files byte for byte, so they passed only in a checkout with the same line endings as the author's (CRLF on
the PC) and failed from an LF export (30 failures). The comparisons now normalise `
` to `
` on both sides.
Verified: the test passes in a CRLF worktree and in an LF export of the job folder. No simulator logic changed.
