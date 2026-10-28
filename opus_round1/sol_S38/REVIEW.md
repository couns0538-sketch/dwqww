# fable-review-S38

Base: opus-sol-S38 head. Correction (Fable review, mistake 3): the job test compared the golden report files byte for byte.
The tool writes LF; the golden files are LF blobs that this PC's `core.autocrlf=true` checks out (and `git archive`s)
as CRLF, so the unfixed test fails from a fresh CRLF checkout/export and passes only where the golden files are
still LF (the author's freshly written worktree, or an LF export). The comparisons now normalise CRLF to LF on both
sides. Verified by the reviewer and independently: the fixed test passes from a CRLF export and from an LF export
(the unfixed base fails from the CRLF export and passes from the LF one). No tool logic changed.
