"""Authorized README/inventory correction only; preserve original READY receipts."""
from pathlib import Path
import json,hashlib,stat,shutil,difflib,importlib.util
R=Path('/workspace/dwqww');V=R/'validation/hosted-tt-refresh-strength-20261021';H=Path(__file__).resolve().parent;P=R/'.github/hosted-tt-refresh-strength';W=R/'.github/workflows/forge-hosted-tt-refresh-strength.yml'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
runner=load('docs_ready23',P/'run_hosted.py');driver=load('docs_capture23',V/'capture-preparation/capture_actual_five.py')
paths=[R/n for n in runner.verify_package_inventory(R,P)]+[P/'PACKAGE-SHA256SUMS'];before=driver.common.snapshot(paths)
transition={str(p):sha(p) for p in (V/'ready-transition').rglob('*') if p.is_file()}
for name,digest in json.loads((P/'protocol.json').read_text())['correctness_evidence_sha256'].items():assert sha(R/name)==digest
save=H/'before';save.mkdir(exist_ok=False)
for p in (P/'README.md',P/'PACKAGE-SHA256SUMS'):shutil.copy2(p,save/p.name)
(save/'CANONICAL-BEFORE.json').write_text(json.dumps(before,indent=2)+'\n');(save/'ORIGINAL-READY-TRANSITION-HASHES.json').write_text(json.dumps(transition,indent=2)+'\n')
(P/'README.md').write_text('''# Forge 6.4.23 versus 6.4.22 TT generation-refresh strength trial

The packet is `PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH`. Final independent enabled-metadata review and the root's sole trigger remain pending; no hosted attempt has been launched by this preparation. The workflow accepts only `forge/hosted-tt-refresh-strength-20261021-*` pushes and requires `github.run_attempt == 1`.

Baseline22 is `ff2e269c6058be84456e3b98344826d17b0056eb`; candidate23 is `1d3ed25bea2c8b781f7ee5a178af0f66061b3984`. Both actual canonical signatures are292545 nodes. Candidate23's signature comes from its own first production capture and subsequent normal five-command producer capture. The317 bound proofs include actual native42 CTests,8 active UCI checks, candidate12 TT groups and56 PV assertions per profile, source and root reviews, and both normal five-row captures. Each source export has77 files;73 are unchanged and four differ. Windows23 qualification is separate and is not a requirement of this Linux trial.

This is an intentional coupled TT replacement, admission and hashfull policy experiment. Exact search parity is not required. Readiness does not establish a bug fix, speed gain or Elo gain. Future hosted builds must use the pinned sources and matched GCC14 strict v3generic flags, then pass the same14 named CTests per engine before any readiness process. The runner retains unconditional affinity restoration, fatal owned-process cleanup and final input rehashing.

The preregistered test is four separate timed baseline A/A pairs, followed by one uninterrupted serial logistic0/+10 SPRT with alpha=beta=.05, capped at512 pairs or1024 games. Both engines receive equal1+0.01 time, Threads1, Hash32, OwnBookfalse, MoveOverhead10, Ponderfalse verified default, and process restart. Fastchess is pinned to60d7a7a. A/A requires eight normal games and is neither a rating test nor pooled with the SPRT. A natural cap without a boundary is inconclusive. Any fault, illegal move, orphan, timeout, warning or changed input invalidates acceptance; no retry, reset, resume, trimming or post-outcome changes are allowed. The emergency limit is18000seconds; job/build/match limits remain360/8/310minutes, with450seconds for the collector and30seconds of finalization headroom.

All516 fresh opening positions are reserved with seed20261101. They exclude all516 reserved22 positions, all260 reserved18 positions and the full historical used/unused cohorts and registries. Independent replay verified all516 selected games. Historical parser/build fixtures retain genuine producer labels and exact read-only references; old proof archives were not copied.

The actual READY offline suite passed98 applicable checks. Two unchanged assertions about the preserved DRAFT phase were explicitly excluded, with their original100-test DRAFT run retained. Separate actual READY checks passed all317 proof hashes,24 inventory entries,13 mandatory-proof omission controls and nine runner metadata negatives. The mandatory named-path checks belong to the binding checker; the runner authenticates every supplied proof. Only the approved benchmark constant changed fromNone to292545 in execution code.

No inference transfers this short-time-control Linux test to longer controls, Windows or Ryzen performance, Stockfish3200 or an absolute rating. Final independent review must be bound outside the protocol map before the root publishes the verified payload and makes the single authorized push.
''')
lines=(save/'PACKAGE-SHA256SUMS').read_text().splitlines();assert len(lines)==24
(P/'PACKAGE-SHA256SUMS').write_text(''.join(sha(R/line[66:])+'  '+line[66:]+'\n' for line in lines))
after=driver.common.snapshot(paths);changed=[n for n in before if before[n]!=after[n]];assert set(changed)=={str(P/'README.md'),str(P/'PACKAGE-SHA256SUMS')}
for p in (P/'README.md',P/'PACKAGE-SHA256SUMS'):(H/(p.name+'.diff')).write_text(''.join(difflib.unified_diff((save/p.name).read_text().splitlines(True),p.read_text().splitlines(True),fromfile='prior-ready/'+p.name,tofile='current-ready/'+p.name)))
assert all(sha(Path(n))==digest for n,digest in transition.items())
assert len(runner.verify_package_inventory(R,P))==24
cfg=json.loads((P/'protocol.json').read_text());runner.require_launch_protocol(cfg)
for name,digest in cfg['correctness_evidence_sha256'].items():assert sha(R/name)==digest
capture=json.loads((V/'capture-preparation/actual-five-captures/PROVENANCE.json').read_text());capture_rehash=driver.common.rehash(capture['frozen_inputs']);assert len(capture['frozen_inputs'])==189 and capture_rehash['status']=='passed'
scope=json.loads((V/'ready-binding-preparation/SOURCE-GATE.json').read_text());assert driver.common.rehash(scope['consumed_inputs'])['status']=='passed'
for name,facts in json.loads((V/'IMMUTABLE22-REFERENCES.json').read_text()).items():assert sha(R/name)==facts['sha256']
record={'status':'PASS_DOCUMENTATION_ONLY_READY_CORRECTION_NOT_LAUNCHED','changed_paths':changed,'before':before,'after':after,'proofs_rehashed':317,'inventory_entries':24,'capture_inputs_rehashed':189,'source_scope_inputs_rehashed':185,'original_ready_transition_files_unchanged':len(transition),'original98_tests_not_repeated':True,'old22_unchanged':True,'protocol_sha256':sha(P/'protocol.json'),'workflow_sha256':sha(W),'runner_sha256':sha(P/'run_hosted.py'),'readme_sha256':sha(P/'README.md'),'inventory_sha256':sha(P/'PACKAGE-SHA256SUMS'),'engine_build_capture_git_actions':0,'final_independent_review_and_root_trigger_pending':True}
(H/'RECEIPT.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k not in ('before','after')},indent=2))
