# Source-only preparation commands

All commands ran with PYTHONDONTWRITEBYTECODE=1 and Python -B. No engines, native builds, matches, performance comparisons, Git/index/network operations or workflows ran.

- `python -B validation/hosted-see-proof-performance-20261021/test_affinity_lifecycle.py` against the immutable21 default: original RED4, two expected restoration failures.
- `python -B validation/hosted-see-proof-performance-20261021/prepare_packet.py`: source-only new disabled packet; original streams retained.
- `LIFECYCLE_RUNNER=/workspace/dwqww/.github/hosted-see-proof-performance/run_hosted.py python -B validation/hosted-see-proof-performance-20261021/test_affinity_lifecycle.py`: first GREEN4.
- `LIFECYCLE_RUNNER=/workspace/dwqww/.github/hosted-see-proof-performance/run_hosted.py python -B -m unittest discover -s validation/hosted-see-proof-performance-20261021 -p 'test_*.py' -v`: initial available27 pass, before build suite/role adapter were added.
- `python -B validation/hosted-see-proof-performance-20261021/test_build_evidence.py`: adapted existing12 fixtures pass first attempt; no subprocess runs.
- `python -B validation/hosted-see-proof-performance-20261021/test_actual23_capture_adapter.py`: preserved original positive-case RED error, then GREEN3 after explicit original-role selector.
- Final complete same unittest discovery command:42 pass10.454s, original stdout/stderr retained; actual normal session72466 completion exit0 observed.
- `python -B validation/hosted-see-proof-performance-20261021/static_checks.py`:80 source/hash/AST checks passed, no reviewed-code imports/processes.

The preparation driver records the initial source adaptation. Final PACKAGE-ADAPTATION.diff preserves the actual current code including later explicit23-side selector and README clarification. Test fixtures carrying dummy24 PAX, CTest strings or inert artifacts are clearly marked DERIVED and never represent actual24 compilation/captures.
