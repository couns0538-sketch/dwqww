# IDEA_SOURCE — S-A3 longer / other LR schedules as trainer arguments (v3d, defaults = v3b)

- **Job:** `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 40 (S-A3, "longer LR schedule as trainer args (after S09-2)") and
  `OPUS_TEST_PLAN.md` row 3: gate **G-A3** "Longer LR schedule (one schedule per gate)", EVAL, "NEW Sol job (trainer arg only;
  S09 defaults restored first)", srand **958591904**. S09-2 (v3b defaults restored, f006 recipe as explicit args) is on
  `opus-sol-S09fix` (`forge_sol_S09_f006_recipe_args_v2.txt`, read only).
- **Idea source (test plan rule):** OPUS_TOP_ENGINES_2025_2026 (the Opus research report; the PDF is not on this PC) and the
  sources it builds on in the lock archive `7_history/ideas/`: `FORGE_IDEA_BOARD.md` l.501 (bullet trainer notes: "a lot of elo"
  from tuning the wdl and lr schedules for a data set, github.com/jw1912/bullet examples/simple.rs) and the NNUE crew note of
  2026-10-25 10:30 (`crew_ideas_older/round_20261025_1030/Engine_NNUE_ideas_20261025_1030.md`): training length is the biggest
  lever measured (G102 e24 +1.85, G100 e32 +8.3, G104 e48 +29.4), so the lr schedule (warmup, decay shape, floor) for e64/e96 runs
  is the open question.
- **Schedule shapes (public, standard):** linear decay to a floor (e.g. Bergsma et al. 2025, "Straight to Zero: Why Linearly
  Decaying the Learning Rate to Zero Works Best for LLMs"); warmup-stable-decay (Hu et al. 2024, MiniCPM; Hägele et al. 2024,
  "Scaling Laws and Compute-Optimal Training Beyond Fixed Training Durations": a constant lr with a short final cooldown matches
  cosine and lets a run be extended or stopped without retraining); cosine = v3b's existing schedule. A schedule horizon separate
  from the run length is what makes "stop early / extend" possible. Own code; no code copied.
- **Base code:** opus-sol-S50's `train_resid_v3c.py` (md5 e7fefe77 = lock-archive v3b md5 b6758004 + S39 + S50).
- **Scope:** trainer arguments only (no engine code, no engine option), CPU smoke on synthetic data, proposed queue lines with a
  dry parse; no GPU, nothing queued. The long-training recipe with only existing v3b arguments is the main session's Astra A7.
