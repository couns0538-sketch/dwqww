# IDEA_SOURCE - c1_prunelmrhist (option PruneLmrHist)

- Idea: aligning quiet-move pruning depth with the history term of late move reductions. A general alpha-beta search technique that is described in public engine-development discussions; no
  code, constants, tables or weights of any other engine were read or used for this job.
- Code: written for R15 on the lock tree git d4f43124dde1d1e37de90e18930e374f32ea7ffa (src_al1s198_clean); the patch
  is the only change. Constants are Forge's own existing values or chosen here (see README.md).
- Status: UNPROVEN until the crew gates it; no Elo or speed claim.
