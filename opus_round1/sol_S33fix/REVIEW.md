# fable-review-S33fix

Base: opus-sol-S33fix head. Correction (Fable review, mistake 3): the job test compared golden files byte for byte,
so it passed only in a checkout with the same line endings as the author's (CRLF on the PC) and failed from an LF
export. The comparison now normalises `
` to `
` on both sides. Verified: the test passes in a CRLF worktree and in
an LF export of the job folder. No tool logic changed.
