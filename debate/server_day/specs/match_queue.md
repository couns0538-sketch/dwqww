# Optional match queue for measured surplus

**Duty.** Consume only a queue and scope explicitly authorized by the owner's policy and a verified home control. Self-play has priority. Until a complete pair has been measured and assigned, the match share is zero. Keep opening, both colors, engine/options and pair identity bound to the reservation. Include changeover, drain and any simultaneous self-play in the measured budget. Enforce the same dispatch cutoff and D for every engine.

**Inputs and outputs.** Use home's C4 evidence, the approved D4 surplus calculation and bounds, frozen list of pairs, measured duration per complete pair and any accepted changes. Record scheduled, started, completed and unfinished pairs distinctly. A pair interrupted after one color cannot enter the result twice or as half of a complete pair. At the next allowed pair boundary return resources when the forecast falls. After D run no new search. Missing authorization has a complete operational outcome, ordinary self-play only.

**Known answers to check before implementation.**

- With 80,000 s left, two billion rows outstanding, an approved 10% margin and 30,000 kept rows/s, matches may use at most 6,666 whole seconds. With 1,000 s per complete pair, six fit and the seventh does not. At 27,500 rows/s the rate equals the margin boundary: zero pairs. At 26,000 rows/s there is no match allocation.
- If each complete pair needs 7,000 s in the first fixture, none fits although the nominal rate clears the margin. Decision is self-play, with the spare seconds reported. Killing the runner after one of two games leaves one unfinished pair, zero finished pairs. A permitted recovery may complete the pair once and only once before D.
- If the link to home fails after an authorization, the server cannot start or extend matches from silence. If the projected rate falls while a pair runs, reclaim its resources at the first allowed boundary. A cut at D stops any remaining search regardless of pair state.

[Surplus boundary](https://github.com/couns0538-sketch/dwqww/blob/8e705146c6369f523aae1146944e07f61f323b42/debate/server_day/SETUP_PLAN.md?plain=1#L99) · [Match allocation and D11](https://github.com/couns0538-sketch/dwqww/blob/8e705146c6369f523aae1146944e07f61f323b42/debate/server_day/SETUP_PLAN.md?plain=1#L106) · [Control scope and deadlines](https://github.com/couns0538-sketch/dwqww/blob/8e705146c6369f523aae1146944e07f61f323b42/debate/server_day/FORMATS.md?plain=1#L186)
