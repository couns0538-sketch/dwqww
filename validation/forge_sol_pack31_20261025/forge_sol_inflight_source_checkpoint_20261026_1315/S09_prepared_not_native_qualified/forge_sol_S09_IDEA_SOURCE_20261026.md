# S09 source and reuse record, 2026-10-26

The S09 inventory entry and full handoff's S9 crew rework are the task source.
Engine Coder's CR-passed step1 patch is the mandatory starting point, pinned by
full SHA256 in the README and receipt. Its source and idea record are retained
unchanged. Its output-head formula and layout are reused directly; no search,
NNUE inference or other engine implementation was replaced.

The new trainer source derives from the supplied train_resid_v3b.py. Its record
loaders, feature conventions, QAT/export rounding, single-head math and Adam
helper remain that same project's code. The numeric audit executes unchanged
v3b record-loading functions through AST, avoiding a duplicate record parser.
The converter reuses the exact extracted step1 include parser/formatter and
adds checked deterministic orchestration. No source, constants or tables from
another chess engine were used.

The f006 recipe is grounded in supplied training-log line1627, with stale run
name fields explicitly excluded. Referenced settings dumps are absent, so
unrecovered precision/defaults are disclosed. No new training, holdout loss,
engine parity or strength evidence is inferred from those historical logs.

Independent source review found and helped resolve the commented-head macro
validation bypass and missing standalone optimizer dependency. Unit tests and
raw reports identify the limited CPU/export scope; native and training checks
remain pending root orchestration.
