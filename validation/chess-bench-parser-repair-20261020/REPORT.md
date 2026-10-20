# Future-only bench parser and failure-evidence repair

The launched parser rejects both preserved canonical engine outputs because its regex requires `bench` at the beginning, while the actual UCI emitter produces **`info string bench`**. The original synthetic `CandidateBenchReadinessTest.GOOD` fixture used the same invented prefixless dialect, hiding the mismatch. This repair is confined to this validation directory; the failed experiment, launched package/workflow/protocol and repository skill are unchanged.

The untouched captures are:

```text
info string bench depth 11 nodes 385781 time 1016 nps 379705
info string bench depth 11 nodes 385781 time 222 nps 1737752
```

They come respectively from native 17 `native/bench-attempt1/stdout.bin` and restored run `39492317400` `files/strength/candidate-bench11.stdout`. Both end in LF and have empty captured stderr. `INPUT-PROVENANCE.json` records original paths, exact hashes and copied command/build/summary records. Two LF-to-CRLF derivatives are explicitly marked as derived, not actual Windows captures. These timings/NPS establish no comparative performance result.

Native `COMMAND.json` records exit 0. **The original hosted helper did not archive its candidate process return code or group-empty observations before rejecting the output. Hosted exit status therefore remains UNKNOWN.** Parser replay supplies return code 0 to isolate the formatting defect; it does not recover missing process facts, demonstrate full hosted readiness, or rescue the failed run. Root separately verified that its gross A/A passed and zero games were played; no engine or match was run here.

The future parser requires the literal canonical prefix, ASCII decimal fields, exact depth 11, frozen integer node expectation 385781 and exactly one complete output record, with LF/CRLF or end-of-file termination. It rejects the old prefixless GOOD dialect, duplicate/malformed/extra output, wrong node/depth/numeric tokens, warnings/errors, nonzero exit and any stderr. Zero time/NPS remain syntactically permitted; no timing threshold was introduced.

The future process helper writes command/stdin, return code, stdout/stderr hashes and owned-group observations **before** parsing or asserting group emptiness. Its final record retains separate pre-verdict/post-cleanup hashes, final return code/group state and cleanup attempt/error facts. The original 10-second communication formula and inherited bounded owned-group cleanup are unchanged. These facts are recorded for pass, parser/exit/stderr failure, timeout and process-launch exceptions; the concrete runtime tests below cover the listed five benign subprocess cases.

| Executed proof | Result |
| --- | --- |
| Original parser against new captured-byte suite | RED: 15 methods, 5 expected failures: both original LF captures, both derived CRLF captures, false acceptance of prefixless output |
| Original helper against benign process-fact suite | RED: 5 methods, all fail because process facts are absent |
| Review regression against first proposal | RED: timeout exposes overwritten pre-verdict hashes |
| Final patch applied with `patch --batch --fuzz=0` to an owned original-module copy | Applied bytes equal proposed module |
| Final applied parser | GREEN: 15/15 methods, including captured bytes and strict negative subcases |
| Final applied process helper | GREEN: 5/5 actual benign Python processes: success, malformed output with exit 0, exit 7, stderr with exit 0, unchanged 10-second timeout |

The timeout fixture records return code unknown before cleanup, final `-2`, group present before/empty after, and empty pre-verdict stderr versus SIGINT-added diagnostic stderr after cleanup. This proves the need to retain both hashes. All test commands, environment overrides and raw RED/GREEN stdout/stderr are under `logs/`; fixture raw/process records are under `fixture-runs/`. No chess engine, compiler, Fastchess, Git mutation or hosted launch/retry was used. This is not a new full-runner 63-test certification; those frozen tests were not edited or rerun.

`run_hosted.original.py.data` preserves the original full module. `run_hosted.future-only.patch` and `run_hosted.proposed.py.data` contain only the future parser/process-fact changes, while `corrected_helper.py` is the isolated helper copy. The first proposal and its GREEN outputs remain preserved (`superseded-v1/`, original green logs); review found its before-hash overwrite, and the final proposal fixes it. Final applied module SHA256 is **`b3f74d82928773e3bdd41a97dd43d963b007d6b20ff2c78f70ddebccccc40493`**; patch SHA256 **`b5307ff2e0eb541551574ad9d70d8d3762f67516d94da8dcbe227c71fba571a9`**. `FINAL-VERIFY.json` rechecks original input/skill hashes and binds final test commands to that module.

An independent read-only reviewer confirmed the canonical grammar, preserved 10-second guard/cleanup and corrected distinct before/after hashes. `SKILL-PROPOSAL.md` proposes a brief addition to existing `.agents/skills/validating-chess-strength/SKILL.md` about real captured positive fixtures and preserving process facts before verdicts. It is **unapplied**; no duplicate/cloud skill or installation is claimed. The TDD skill guided the observed RED/GREEN sequence; no further cloud skill capability was assumed after the catalog update.

All acceptance restrictions remain: original 17 attempt failed, original 16 full-batch failure remains retained, and this future-only helper proof authorizes no retry, resume, pooling, new hosted launch, speed or Elo claim.
