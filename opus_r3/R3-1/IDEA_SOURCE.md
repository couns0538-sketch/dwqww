# IDEA_SOURCE — R3-1 integration stack

No new engine ideas: R3-1 only integrates features that already passed their own jobs. Sources per feature are the
`IDEA_SOURCE.md` files of the merged job folders (`opus_round1/<JOB>/IDEA_SOURCE.md`, `opus_round1/sol_*/`).

Integration techniques used and where they come from:
- One function instance per option combination (CorrMargins x CorrExt x CuckooRep): generalises the "second
  instance of alphabeta.inc" pattern of jobs O5, O8 and C6 (their REPORTs explain why a runtime test inside the
  default search was avoided: codegen and placement of the AL1 search).
- Build switch from two file versions with `diff -D` (GNU diffutils `--ifdef`), checked by preprocessing both
  configurations (`g++ -E -P`) against the original files and by comparing exes byte for byte.
- Porting hunks by exact context into moved code: the same idea as `patch` with offsets, restricted to a unique
  exact match of the hunk's old side (no fuzz), so a hunk lands only where its context is verbatim.
