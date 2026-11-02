# Six-hour quality continuation — UNPROVEN

Authorized window: 2026-11-02 21:51 UTC through 2026-11-03 03:51 UTC.
Reserve 03:21–03:51 UTC for final review, defect repair and verification. Redirect
blocked work to the next useful converter/filter task; no training, GPU, engine,
relabel or fast-loader changes. Preserve all datasets and earlier evidence.

Latest delegation preference: do most work inline; use only a few focused
subagent reviews when useful. Two initial broad audits were interrupted before
they ran probes or changed source. Do not restart them merely to consume time.

1. Reproduce and fix strict-input gaps: variants, malformed PGNs, source parsing,
   typed normalized metadata and explicit error accounting. Preserve the no-flag
   converter byte contract. Review at a coherent parsing milestone.
2. Check converter configuration boundaries, source stability and publication.
   Exercise adversarial failures and actual binary/metadata alignment without
   rewriting existing datasets or production tools.
3. Improve data-quality evidence beyond the already quiet first-million sample:
   inspect closed source availability; define a bounded, hash-bound audit over
   multiple source regions, report score/result/phase/ply composition and filtering
   coverage. Avoid claiming that statistics alone prove a better net.
4. Improve the crew handoff and reusable skills where the completed steps reveal
   a real need. Extend existing skills before adding overlapping ones. Use official
   documentation and connected tools only for concrete questions.
5. Finish with current-candidate correctness checks, exact evidence pins, final
   focused review/fixes, updated recipes and recorded limitations. Push reviewed
   milestones approximately every ten minutes; RESULTS.md accompanies each push.

New runtime artifacts: `C:/astra8_data/quality6h_20261102/`; C >50 GB, D >=50 GB,
aggregate retained C/D/F artifacts <=15 GB. Two CPU workers maximum, BelowNormal.
The previous approved handoff and source commit e526fc12 remain historical proof.
Any new runtime changes require a newly verified handoff before crew use.

At 23:22 UTC, the first seven closed sources (45,255,639 rows) all pass the
descriptive scan. All have zero in-check and mate-score rows. Given the measured
one-worker rate and remaining window, extend the audit to the other 22 closed
001–039 sources (still excluding 013/014). Use the same frozen profiler, a separate
new output and one additional CPU worker only after the current handoff checks.
Together both scans cover the existing source inventory; they do not create
training data, game-ID proof or a changed recipe. Keep the 03:11 deadline and
final 30-minute review reserve. If a storage/source check fails, preserve evidence
and redirect the remaining time without touching any crew process.

Next risk found by main's static review: filter `workers=2` currently constructs
two pool workers while its parent also parses/serializes records. Qualify and fix
the aggregate compute budget (parent plus one child), preserving deterministic
output. New red/green process-allocation checks wait until the first source scan
frees a compute slot. Repeat the seven affected million-row two-worker timings
only after both scans finish; reserve about 4.3 GB for the separately named full
outputs and retain every earlier measurement as historical evidence. Do not
attribute the old two-child timings to the corrected aggregate two-worker path.

Tool selection so far: Forge C++ engineering/evidence checker, Skill Creator,
existing training-data validation guidance, Context7 official python-chess docs,
GitHub connector read-only issue lookup. No matching open datafilter issue found.
No CodeRabbit or external AI agent launched under the request to limit agents.
