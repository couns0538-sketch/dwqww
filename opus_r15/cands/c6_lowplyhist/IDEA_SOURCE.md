# IDEA_SOURCE - c6_lowplyhist (option LowPlyHist)

- Idea: a move-ordering history table restricted to the first plies of the current search. A general alpha-beta
  search technique that is described in public engine-development discussions; no code, constants, tables or weights
  of any other engine were read or used for this job.
- Code: written for R15 on the lock tree git d4f43124dde1d1e37de90e18930e374f32ea7ffa (src_al1s198_clean); the patch
  is the only change. Constants (4 plies, weight 4 / (ply + 2)) were chosen here.
- Status: UNPROVEN until the crew gates it; no Elo or speed claim.
