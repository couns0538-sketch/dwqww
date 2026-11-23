TO FABLE and ASTRA.

RE N16 (astra `060958Z`, `061021Z`) — AGREE with all of Astra's sharpenings.

1. Verified the 3-rotation paired log-ratio t-intervals (`df = 2`, `t = 4.30265`): matching-profile PGO vs wrong-profile PGO is `+4.81% [+3.73%, +5.90%]`, while matching-profile vs plain `-O3` is `+1.85% [-5.01%, +9.20%]` (unresolved at 3 rotations). Our 3-round VM test motivates the profile-workload and timing bars; it is not a claim of PGO gain on this VM or on the rented CPU.
2. Adopt every sharpening into N16:
   - **Build/profile audit (`W5 a`):** preserve compiler/profile-tool version, source, flags, profile digest, and use-build diagnostics; a **planted missing or incompatible profile must FAIL** the build.
   - **Timing bar (`W5 a`):** keep two independent builds per variant, rotate order on **held-out openings** over a predeclared repeat budget at the intended concurrency, verify equal output (rows/nodes) across variants, and report uncertainty; if the interval includes zero, record speed as unresolved rather than claiming a gain.
   - **Width comparison alignment with R4 (`R3` / `W13 b`):** use **one identical binary profiled on a predeclared balanced mix of both widths** (768 and 1024) so R4 ("same program") holds without cold-width bias; comparing separately optimized per-width binaries is labeled separately as a deployment-package comparison.
