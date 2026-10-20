# Independent audit of failed hosted attempt 39492317400

**Confirmed harness parser defect; zero match games; no strength acceptance.** The attempt remains `failed_or_inconclusive_no_acceptance`. The failure is fully explained by the parser rejecting the engine's normal benchmark record prefix. It is not evidence of an engine-node mismatch, timeout, NPS regression or Elo result.

Evidence: restored originals at `/workspace/.cloud-setup/promotion-strength-39492317400-original/files/`, from results commit `0e292d6193918fa71a06b99798808ecb60e5807a`, ref `results/promotion-see-strength-39492317400-1`. This audit ran no engine, build, match, replay or mock suite, changed no frozen package or earlier report, and wrote only this report and `AUDIT.json`.

## Concrete failure

Original `strength/candidate-bench11.stdout` is exactly:

```text
info string bench depth 11 nodes 385781 time 222 nps 1737752
```

Stderr is empty. Frozen `package/run_hosted.py:232` uses:

```python
r'^bench depth 11 nodes (\d+) time (\d+) nps (\d+)\r?$'
```

Applying that exact regex to the retained stdout yields zero matches. The frozen candidate's own `src/uci.cpp:408`, read from its archived source tar, emits `"info string bench depth "`. The node signature is therefore correct, but the parser's anchored prefix is wrong. The traceback in `wrapper.log` identifies `verify_candidate_bench_signature:236`, called from readiness at250 and `main:471`, matching this control flow.

The preparation test's `GOOD` string at `test_hosted_promotion_see_strength.py:121` also starts with `bench`, so its success fixture shared the implementation's false assumption. My earlier prelaunch review missed this source/output-versus-fixture mismatch. That review remains immutable; its “no new material defect found” assessment was insufficient and must not be treated as validation of this parser.

The archived failure combines signature/exit/warning conditions and does not separately save the candidate return code before validation. It also occurs before the successful owned-group-empty check and result JSON. Thus expected stdout plus empty stderr is **not** a recorded complete candidate-readiness PASS or independent proof of exit0/group-empty state. The prefix mismatch alone is sufficient to reject these bytes regardless of exit status. `communicate` returned rather than raising the ten-second timeout, and the retained traceback reports this parser exception, not a timeout. The source enters owned-group cleanup on that exception.

## Stage reached and integrity

- Independently checked every restored manifest entry: **75/75 sizes and SHA256 hashes match**.
- Independently remapped and rehashed all **40 frozen inputs** from `final-input-rehash.json`; every expected/actual hash matches the restored bytes, and the record equals the summary's embedded final rehash.
- Both source tar hashes, both **72-file exported-source inventories**, engine/core hashes and CTest-log hashes agree with their archived build provenance. Source pins are baseline14 `21538ec5416c909fc98a08688242a0b3b9710b25` and candidate17 `47f0560221d986e41a309853e1295c557fcf5bf6`. This checks preserved provenance consistency; it is not a rebuilt compiler reproduction.
- Recomputed the original baseline gross A/A ratios from its eight benchmark records. Wall ratios are0.9997688364,1.0028486886,0.9968457087; CPU ratios0.9665909499,0.9956194005,0.9985957344. Both medians and every ratio pass the unchanged frozen gate. These are same-baseline calibration observations, not candidate speed evidence.
- The candidate-readiness exception occurs before the later UCI-default checks, four deterministic A/A pairs and SPRT call. No `aa/` or `sprt/` directory, corresponding command JSON or PGN exists in the complete preserved payload set; no A/A or SPRT result is present in the summary. **Zero actual calibration-match games and zero SPRT games ran.** Fastchess compilation/version identification and CTests are not match games.

The expected candidate node count385781 and printed222ms/1737752NPS must not be turned into a speed comparison. Baseline calibration passed only on this host/attempt; it does not clear previous clock anomalies or authorize transferring readiness to another run. All original failures and the complete unused opening reservation remain preserved.

## Legitimate next verification

The immediate justified work is an **offline parser regression against these exact retained stdout/stderr bytes**, in a separately versioned harness repair outside the frozen failed package. Use the actual source-emitted `info string` format as the positive fixture and retain strict rejection checks for wrong nodes, duplicate/trailing-garbage records, warnings, stderr, nonzero exit and lifecycle faults. This validates a harness repair without playing games or retroactively accepting this run.

Do not relaunch the unchanged candidate17 attempt, relax its gates, edit its archived result, resume it or recycle its reserved openings. Any later strength experiment must be separately justified and prospectively preregistered after independent harness review and explicit authorization; this report neither proposes nor authorizes that launch. The failed attempt supplies no H0/H1 result, no Elo estimate, and no evidence of beating Stockfish at3200.
