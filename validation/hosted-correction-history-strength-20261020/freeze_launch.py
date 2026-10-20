"""Bind verified finite evidence and freeze one new experiment. No engine or Git runs."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PACKAGE = REPO / '.github/hosted-correction-history-strength'
WORKFLOW = REPO / '.github/workflows/forge-hosted-correction-history-strength.yml'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

def main():
    cfg = json.loads((PACKAGE / 'protocol.json').read_text())
    assert cfg['status'] == 'DRAFT_BLOCKED_CANDIDATE18_GATES_PENDING'
    assert cfg['correctness_evidence_sha256'] == {}
    before = WORKFLOW.read_text()
    assert 'on: []' in before and 'if: ${{ false }}' in before
    scope = ROOT / 'root-input-review/SOURCE-SCOPE-FINAL.json'
    assert scope.is_file(), 'Independent exact-source scope review is required'
    proofs = {}
    def bind(path, expected=None):
        path = Path(path)
        assert path.is_file() and not path.is_symlink(), str(path)
        relative = path.resolve().relative_to(REPO.resolve()).as_posix()
        digest = sha(path)
        if expected is not None:
            assert digest == expected, relative
        proofs[relative] = digest
    native = REPO / 'validation/correction-history-native-20261020'
    manifest = native / 'EVIDENCE-SHA256SUMS'
    bind(manifest, '8967fb6d352e752d136eda9ebbab650de54c09b71dad7a5d0717015ba6f64840')
    for line in manifest.read_text().splitlines():
        expected, relative = line.split('  ', 1)
        assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
        bind(native / relative, expected)
    assert len(proofs) == 114
    windows = REPO / 'validation/correction-history-windows-20261020'
    win_manifest = windows / 'evidence-SHA256.json'
    bind(win_manifest)
    for relative, record in json.loads(win_manifest.read_text()).items():
        assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
        bind(windows / relative, record['sha256'])
    for directory, names in [
        (native, ['ROOT-NATIVE-PROOFS.json', 'FINAL-RECEIPT.json']),
        (windows, ['ROOT-WINDOWS-PROOFS.json', 'final-verification.json']),
        (REPO / 'validation/promotion-see-20261020/native', [
            'ROOT-NATIVE-PROOFS.json', 'frozen-source-47f0560-files.json',
            'frozen-release-attempt1/summary.json', 'frozen-asan-attempt1/summary.json',
            'frozen-tsan-attempt1/summary.json', 'active-uci-tsan-attempt1/summary.json']),
        (REPO / 'validation/correction-history-residual-20261020', [
            'BASELINE-BUILD-INPUT-EQUIVALENCE.json', 'PROVENANCE.json', 'RESULTS.json',
            'ROOT-REVIEW.json', 'INTEGRITY.json', 'independent-review/REPORT.md',
            'independent-review/PRODUCTION-REVIEW.md']),
        (ROOT, ['opening-check.json', 'INDEPENDENT-OPENING-REVIEW.md',
            'PREPARATION-CHECKPOINT-PHASE2.json', 'PHASE2-CLOSURE.md',
            'independent-review/PHASE2-CLOSURE.md', 'independent-review/PHASE2-CLOSURE.json',
            'root-input-review/SOURCE-SCOPE-FINAL.json', 'root-input-review/SOURCE-SCOPE-FINAL.md'])
    ]:
        for name in names:
            bind(directory / name)
    receipt = native / 'FINAL-RECEIPT.json'
    native_result = json.loads(receipt.read_text())
    assert native_result['source_commit'] == cfg['candidate_sha']
    assert native_result['ctest_total_passed'] == 30
    assert native_result['active_default_tsan_scenarios_passed'] == 8
    win_result = json.loads((windows / 'final-verification.json').read_text())
    assert win_result['status'] == 'passed'
    assert win_result['source_and_tests_commit'] == cfg['candidate_sha']
    assert win_result['runtime_checks'] == 9 and win_result['independent_checks'] == 1064
    independent = json.loads((ROOT / 'independent-review/PHASE2-CLOSURE.json').read_text())
    assert independent['success'] and independent['tests_run'] == 16
    review = ROOT / 'ROOT-ONE-ATTEMPT-AUTHORIZATION.json'
    assert not review.exists()
    save(review, {
        'status': 'AUTHORIZED_ONE_FRESH_READINESS_ATTEMPT_CONDITIONAL_FINAL_ENABLED_METADATA_REVIEW',
        'utc': datetime.now(timezone.utc).isoformat(),
        'standing_user_authorization': 'User explicitly authorized ordinary isolated code/build/test/GitHub experiments without repeated permission requests.',
        'baseline_sha': cfg['baseline_sha'], 'candidate_sha': cfg['candidate_sha'],
        'phase2_preserved_commit': 'be2033884a2cd82c5c9bd8d4b56dc2ca6ed72acd',
        'source_scope': 'One correction-history arithmetic line, version strings and permanent behavior-contract test only; NNUE/guards/weights/clamps unchanged.',
        'finite_validation': '30 CTests,8 active default-TSan UCI transitions,9 Wine checks,1064 Windows artifact checks; raw finite manifest records independently rehashed before binding.',
        'baseline_qualification': 'Genuine47 historical native checks remain labeled47;72 build input bytes/modes equal b590. Hosted job must actually archive/build b590 and pass9 named CTests.',
        'prior_anomalies': '16 failed full TSan batch,14 barebench timeout, old TT time forfeit and failed17 parser attempt remain unresolved/retained; no general reliability claim or gate waiver.',
        'experiment': 'One new18vs17 serial10+0.1 logistic0/+10 SPRT alpha=beta=.05,4AA+256SPRT pairs,18000s emergency invalidates acceptance.',
        'retry_policy': 'No retry/resume/reset/pooling; first workflow attempt only. A final independent enabled-workflow/proof-binding review and package verification are required before the sole trigger push.',
        'elo_evidence': None, 'nps_comparison': None,
        'engines_or_builds_or_matches_executed_by_this_freeze': 0
    })
    bind(review)
    enabled = before.replace(
        '# PREPARATION ONLY: disabled until root and Astra review all proofs and inventory.\n# Future trigger, if separately authorized: one new forge/hosted-correction-history-strength-20261020-* push.\n',
        '# Frozen one-attempt experiment; source, correctness proofs and workflow hash are gated before builds.\n')
    enabled = enabled.replace(' (DRAFT DISABLED)', '')
    enabled = enabled.replace('on: []', "on:\n  push:\n    branches:\n      - 'forge/hosted-correction-history-strength-20261020-*'")
    enabled = enabled.replace('    if: ${{ false }} # Root must explicitly replace this only after final review.',
        "    if: ${{ github.run_attempt == 1 && startsWith(github.ref, 'refs/heads/forge/hosted-correction-history-strength-20261020-') }}")
    WORKFLOW.write_text(enabled)
    cfg.update(status='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH',
        source_gates_status='PASSED', source_scope_review_status='PASSED',
        root_review_status='PASSED', astra_review_status='PASSED',
        correctness_evidence_sha256=dict(sorted(proofs.items())),
        operational_qualification_status='authorized_for_one_fresh_host_readiness_attempt_with_prior_anomalies_unresolved',
        workflow_status='FROZEN', workflow_sha256=sha(WORKFLOW), blocked_reasons=[],
        hypothesis='Residual-increment correction-history ablation under unchanged guards, depth weights, clamps and material weight. Actual-method fixed-key6cp feedback learns6cp versus old3/4cp; the larger64cp envelope and stale/noisy/aliased feedback may regress strength. Not a demonstrated bug repair.',
        source_gates='Current fc51 candidate first-attempt Release10/ASanUBSan10/defaultTSan10 plus8active UCI;9Wine and1064artifact checks PASS. Exact manifests and raw proof bytes are bound and enter final rehash. No historical anomaly waived.',
        candidate_bench_readiness='Actual native18 capture freezes321912nodes, baseline17 is385781. Canonical UCI bytes, empty stderr,exit0/noowneddescendants required; pre-verdict and post-cleanup process facts retained. Signatures establish no NPS ratio.',
        workflow_draft_bounds='Historical disabled phase2 preserved at be203388; enabled workflow freezes job360/build8/match310 minutes and collector450s work budget with30s finalization headroom. One future-prefix push only; no dispatch/resume/retry.',
        workflow_preservation_requirements='Required actual source exports/compiler/cache/compilecommands/cores/binaries/exact9+10CTest and original process facts. Every consumed proof/build byte frozen and finally rehashed; always archive/upload/fresh-results-branch publication with remote verification.',
        root_authorization_path=review.relative_to(REPO).as_posix())
    cfg['candidate_source_history']['additional_diff']='fc51 fixture fail-fast guard before index use; production search/NNUE/version bytes match first arithmetic source, independently verified.'
    cfg['remaining_gate_input_paths']['root_full_gate_manifest']['state']='Bound exact finite evidence hashes; no additional engine tests required locally. Future fresh host build/readiness remain mandatory.'
    cfg['remaining_gate_input_paths']['astra_review']='Independent phase2 code review is bound; final enabled metadata review must precede sole trigger push.'
    cfg['remaining_gate_input_paths']['root_review_authorization_and_workflow']='Bound root one-attempt authorization and enabled workflow SHA; final independent metadata check before sole push.'
    save(PACKAGE / 'protocol.json', cfg)
    readme = PACKAGE / 'README.md'
    readme.write_text('''# Correction-history ablation — frozen one-attempt experiment

Baseline17 `b5908f0fe9db227158d39e156652f2467252e68a`; candidate18 `fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b`. One correction-history residual-increment hypothesis; not a demonstrated bug repair or accepted gain. NNUE, guards, weights and clamps are unchanged. Wider retained correction and noisy feedback may regress strength.

All current18 finite tests passed: Release10, ASan/UBSan10, defaultTSan10,8active UCI,9Wine and1064artifact checks. Exact original proof hashes are frozen in protocol.json and rechecked finally. Historical47 baseline evidence remains labeled47; all72 build inputs equal b590, which this host must actually export/build and pass9tests before any games. Candidate must pass all10tests. Required original source/build/compiler/core/executable/CTest provenance is checked before readiness. Executable modes are preserved and required.

Exactly one new future-prefix push is authorized after final enabled-metadata review. Serial native Threads1/Hash32/OwnBook=false/MoveOverhead10/Ponder=false/restart, equal10+0.1, logistic0/+10 SPRT alpha=beta=.05,4deterministic baseline-AA pairs followed by256fresh paired openings,512-game natural cap.18,000-second emergency invalidates acceptance. Faults, missing pairs, changed bytes, warnings, crashes and timeouts invalidate acceptance. No retry/resume/reset/pooling/adjudication/move cap. Natural cap without boundary is inconclusive.

Canonical captured native output fixes bench signatures321912/385781; these are reproducibility checks, not speed measurements. Same-baseline gross readiness and legal deterministic AA must pass before A/B. Process facts persist before semantic assertions, with separate final cleanup observations. All raw logs/PGNs are retained, independently audited and split-archived/published on a fresh results branch.

Phase1/phase2 preparation, RED controls and96 passing offline tests remain immutable in Git; phase2 disabled state is preserved at be2033884a2cd82c5c9bd8d4b56dc2ca6ed72acd. Draft-only status tests describe that historical state. The previous17 attempt remains failed with zero games and unknown missing original candidate exit/group facts. Earlier TSan/timeout/forfeit anomalies remain unresolved and are not waived. No positive Elo, calibrated NPS, physical Ryzen, native Windows or Stockfish claim is established by preparation.

The collector450-second work budget reserves30seconds inside the8-minute step for cleanup/copy/finalization. Job/build/match bounds360/8/310minutes leave evidence-preservation headroom; infrastructure loss is not guaranteed recoverable. Final workflow, runner and package inventory hashes are checked before collection and play.
''')
    inventory = PACKAGE / 'PACKAGE-SHA256SUMS'
    paths = sorted([p for p in PACKAGE.rglob('*') if p.is_file() and p != inventory] + [WORKFLOW])
    inventory.write_text(''.join(sha(p) + '  ' + p.relative_to(REPO).as_posix() + '\n' for p in paths))
    spec = importlib.util.spec_from_file_location('root_frozen_runner', PACKAGE / 'run_hosted.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runner.require_launch_protocol(cfg)
    assert len(runner.verify_package_inventory(REPO, PACKAGE)) == 24
    print(json.dumps({'status':'FROZEN_PENDING_FINAL_ENABLED_METADATA_REVIEW',
        'proof_files_bound':len(proofs), 'workflow_sha256':sha(WORKFLOW),
        'protocol_sha256':sha(PACKAGE/'protocol.json'), 'inventory_sha256':sha(inventory),
        'engine_executions':0}, indent=2))

if __name__ == '__main__':
    main()
