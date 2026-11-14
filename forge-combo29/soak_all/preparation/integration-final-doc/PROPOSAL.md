# Integration-branch documentation proposal

Ready file: `INTEGRATION_ALL.ready.md`.
Minimal single-file diff against `e04556ddc3a430b2e751159b0d46111ef56c8b89`: `INTEGRATION_ALL.proposed.patch.txt`.
Target: `forge-combo29/INTEGRATION_ALL.md` on the parent's authorized `integrate/combo29-all` branch, near the end of the eight-hour job. This proposal is scratch only; it has not been applied, committed, pushed or copied into a worktree.

The ready file preserves the base/source commits, three merge inputs, reconciliation description and all three source SHA256 rows exactly. It explicitly states that the source stays pinned to `f27b1971e459581ad4c85b7015f6af83bbfd4af6`, and that validation is not all-pass: four unchanged fixture comparisons fail, and eight required low-clock equality failures repeat in10/10 additional fresh pairs each. Both full ASan timeout attempts remain incomplete; the later completed split coverage is separately identified.

Every evidence link explicitly targets GitHub's `soak/combo29-all` branch. Later logs are not copied to the integration branch. The live/final soak report carries dynamic match, sanitizer and Part4 results and limitations; the ready file claims no unexecuted match or sampled-audit outcome and no overall phase completion. Root should publish the latest soak evidence before or alongside this document so those links are current.

Validation performed without engine workloads: the three source hash rows and full merge-description/input block match the e04556dd document; all13 evidence links point explicitly at the soak branch and their corresponding local evidence paths exist. Remote HTTP resolution was not tested. Read-only Git diff confirms no src/include difference between f27b197 and e04556dd. Root should repeat its source/branch checks when actually publishing, because this proposal does not freeze later repository state.

Exact read commands and outputs are in `read-commands.txt`; the static link/content checker is `check-document.mjs`. The final shell call returns1 because Unix `diff` found the intended documentation differences; the checker itself returned0. No compilation or engine test failed or ran. All writes were confined to this scratch folder; no worktree, branch, ref, controller or state changes were made.

Ready-file SHA256: `5b12ce8214bf4505c83145f9768df7ad1b2a18ef67fce7b36a853db1ebc6fe6b`.

Independent read-only review found no blocker. Its two clarity suggestions were applied: the aggregate is labeled KRK sanitizer executions, and the live/final report link is not labeled complete. The final checker passed again with the source/hash details preserved and all13 link occurrences (11 unique targets) directed at existing soak evidence paths.
