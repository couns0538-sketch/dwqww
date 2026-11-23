PROPOSAL N9: Document the current fixed teacher net and target weight in `PLAN.md`/`STATE.md`, and add a controlled two-net test (current teacher weight vs teacher weight = 0) before or alongside P3's 2B / P4's 1024-wide training so an older 0.38B teacher does not silently cap a 2B or 1024-wide net.

KIND: explanation

EVIDENCE:
1. `debate/PLAN.md:22-24` states every round trains "a new net from nothing on the newest 25 rounds (at most 388,000,000 kept positions, 40 passes, **with a fixed older net as teacher for part of the target**)".
2. `debate/PLAN.md:256` (P9) rejects only "A net as its own teacher: -8.3" — NOT training without a teacher (weight 0), nor changing which teacher is used when scaling data 5x (0.38B -> 2B) and width (768 -> 1024).
3. Neither `PLAN.md` nor `STATE.md` records which net is the current fixed teacher, its strength relative to round 67, or its target weight `lambda_teacher` (not checked; private trainer config on PC).
4. Mechanical risk: if the training target is `(1 - w_t) * target_data + w_t * eval_teacher(pos)` with a fixed older 768 teacher trained on <= 0.38B positions, then for every one of the 2B positions (and for the 1024-wide net in P4), a fraction `w_t` of the loss pulls the student toward the older, weaker teacher's predictions rather than the 2B search/outcome targets. That could act as an artificial ceiling on both P3 and P4 — or conversely, removing it could hurt if teacher smoothing genuinely regularizes 2k-softnode labels. Only a controlled game match on this engine decides (Rule 3).

QUESTION (to Fable): Which net is the current fixed teacher in the loop trainer, what is its target weight, and was `teacher_weight = 0` ever tested on round 67's data (with games/Elo)?

COST:
- Documentation: 0 CPU / 0 GPU hours (read trainer config on PC).
- Controlled test (only if `teacher_weight > 0` and `teacher_weight = 0` has not already been measured on current-era data): 1 extra training run (`49 min` on 388M or `~4.2 h` on 2B, comparing against an already-planned baseline run) + 1 match (4,000 games at 250,000 nodes = `~3 CPU hours`).

HOW IT IS JUDGED:
1. Record the current teacher net identity, target formula, and weight in `PLAN.md` / `STATE.md`.
2. If `teacher_weight > 0` and no clean `teacher_weight = 0` match exists on current-era data, train two 768-wide nets on identical rounds, seed, and recipe (first cheaply on the 388M or 1B r67 pool, or directly on the first 2B run):
   - Control: current fixed teacher weight.
   - Treatment: `teacher_weight = 0` (pure search-score + WDL-result target).
   Judge at 250,000 nodes (4,000 games, equal settings per J9): adopt `teacher_weight = 0` for P3/P4 if 95% LB > 0; keep teacher if UB < 0; if inconclusive, test a refreshed/smaller teacher weight only after P3's 2B net lands.

WHAT WOULD CHANGE MY MIND:
- If Fable's PC log already shows `teacher_weight = 0` lost decisively against the fixed older teacher on current-era data (with games, node limit, and 95% CI), or if the trainer already sets `teacher_weight = 0` for P3/P4, withdraw the test immediately and record those existing numbers in `PLAN.md`.
