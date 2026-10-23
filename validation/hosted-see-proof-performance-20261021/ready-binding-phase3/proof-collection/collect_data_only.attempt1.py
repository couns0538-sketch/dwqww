"""Read/hash closed finite originals only. No reviewed-module imports or processes."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import hashlib, json, stat, tarfile

R = Path('/workspace/dwqww')
V = R / 'validation/hosted-see-proof-performance-20261021'
H = Path(__file__).resolve().parent
PRESERVED = V / 'transport-adapter-phase2/before'
BASE = '1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
CAND = '7db08eac6ead99d641834c56ccec06a06600586a'
files, directories, proofs, aliases = {}, {}, {}, {}

def need(ok, why):
    if not ok:
        raise ValueError(why)

def sha(p):
    with Path(p).open('rb') as f:
        h = hashlib.sha256()
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def put(name, value):
    with (H / name).open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')

def file(p, expected=None):
    p = Path(p)
    need(p.is_absolute() and p.is_file() and not p.is_symlink(), 'Unsafe/missing file ' + str(p))
    row = {'sha256': sha(p), 'bytes': p.stat().st_size, 'mode': stat.S_IMODE(p.stat().st_mode)}
    if expected is not None:
        for k, v in expected.items():
            need(row[k] == v, 'Original differs: ' + str(p) + ':' + k)
    if str(p) in files:
        need(files[str(p)] == row, 'Input changed during collection: ' + str(p))
    files[str(p)] = row
    if p.is_relative_to(R):
        proofs[p.relative_to(R).as_posix()] = row['sha256']
    return row

def frozen_input(name, expected):
    original = Path(name)
    original = original if original.is_absolute() else R / original
    preserved = PRESERVED / original.relative_to(R) if original.is_relative_to(R) else None
    actual = preserved if preserved is not None and preserved.is_file() else original
    file(actual, expected)
    if actual != original:
        aliases[str(original)] = {'physical_path': str(actual), 'historical_sha256': expected['sha256'],
                                  'basis': 'Authorized preserved pre-adapter original; not current canonical bytes'}

def tree(root, expected, dir_modes=None):
    root = Path(root)
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    need(actual == set(expected), 'Whole tree file set differs: ' + str(root))
    for name, row in expected.items():
        file(root / name, row if isinstance(row, dict) else {'sha256': row})
    if dir_modes is not None:
        for name, mode in dir_modes.items():
            p = root / name
            need(p.is_dir() and not p.is_symlink() and stat.S_IMODE(p.stat().st_mode) == mode,
                 'Directory mode differs: ' + str(p))
            directories[str(p)] = mode

def manifest(folder, name='EVIDENCE-SHA256SUMS'):
    p = folder / name
    file(p)
    rows = {}
    for line in p.read_text().splitlines():
        digest, relative = line.split('  ', 1)
        q = PurePosixPath(relative)
        need(not q.is_absolute() and '..' not in q.parts and q.as_posix() == relative and relative not in rows,
             'Unsafe/duplicate manifest member ' + relative)
        file(folder / relative, {'sha256': digest})
        rows[relative] = digest
    return rows

def archive_inventory(p, commit):
    file(p)
    result = {}
    with tarfile.open(p) as tar:
        need(tar.pax_headers.get('comment') == commit, 'Source TAR/PAX commit differs')
        for member in tar:
            if member.isdir():
                continue
            name = PurePosixPath(member.name)
            need(member.isfile() and not name.is_absolute() and '..' not in name.parts and
                 name.as_posix() == member.name and member.name not in result, 'Unsafe source TAR member')
            result[member.name] = hashlib.sha256(tar.extractfile(member).read()).hexdigest()
    return result

def collect_native(label, commit, native_name, root_name, tar_name):
    native = R / 'validation' / native_name
    root = R / 'validation' / root_name / 'root-verification/NATIVE.json'
    gate_path = native / 'ROOT-FROZEN-SOURCE-GATES.json'
    gate, final, root_record = read(gate_path), read(native / 'FINAL-RECEIPT.json'), read(root)
    need(gate['source_commit'] == final['source_commit'] == root_record['source_commit'] == commit,
         'Native source identity differs: ' + label)
    need(final['status'] == 'STABLE' and final['native_ctests'] == root_record['ctest'] == 42 and
         final['default_tsan_active_checks'] == root_record['active_uci'] == 8 and
         final['pv_metadata_assertions_each_profile'] == root_record['pv_metadata_assertions_each_profile'] == 56 and
         final['tt_coherence_groups_each_profile'] == root_record['tt_groups_each_profile' if label == 'candidate' else 'tt_coherence_groups_each_profile'] == 12,
         'Native finite schema differs: ' + label)
    rows = manifest(native)
    need(root_record['native_manifest_sha256'] == sha(native / 'EVIDENCE-SHA256SUMS') and
         root_record['native_final_receipt_sha256'] == sha(native / 'FINAL-RECEIPT.json'), 'Root native receipt binding differs')
    snapshot = read(native / 'ORIGINALS-FINAL-SHA256.json')
    need(snapshot['source_commit'] == commit and sha(native / 'ORIGINALS-FINAL-SHA256.json') == final['originals_snapshot_sha256'],
         'Original snapshot binding differs')
    need(sum(len(v['files']) for v in snapshot['trees'].values()) == 644, 'Expected complete644 originals')
    for t in snapshot['trees'].values():
        tree(t['root'], t['files'], t['directory_modes'])
    for row in snapshot['single_files'].values():
        file(row['path'], {k: row[k] for k in ('sha256', 'bytes', 'mode')})
    compiler = snapshot['compiler']
    file(Path(compiler['resolved_path']), {'sha256': compiler['sha256']})
    inventory = archive_inventory(native / tar_name, commit)
    need(len(inventory) == 77 and inventory == gate['inputs'], 'Actual source77/TAR/gate differs')
    need({n: row['sha256'] for n, row in snapshot['trees']['source']['files'].items()} == inventory,
         'Frozen source export differs')
    summaries = {}
    for profile in ('release', 'asan', 'tsan'):
        p = native / ('frozen-' + profile + '-attempt1/summary.json')
        s = read(p)
        need(s['status'] == 'PASS' and s['source_commit'] == commit and len(s['ctest_names']) == 14 and
             s['ctest_names'][5] == 'forge_pv_metadata_tests' and s['pv_metadata_contract_actual_summaries'] == [['56', '0']] and
             s['tt_coherence_contract_actual_groups'] == ['12'], 'Actual profile schema differs')
        if label == 'candidate':
            need(s['see_threshold_contract_actual_summaries'] == [['504', '0']], 'Actual SEE504 absent')
        summaries[profile] = {'path': p.relative_to(R).as_posix(), 'sha256': sha(p), 'named_ctests': s['ctest_names']}
    release = read(native / 'frozen-release-attempt1/summary.json')
    build = Path(snapshot['trees']['release']['root'])
    engines = {n: file(build / n)['sha256'] for n in ('forge', 'libforge_core.a')}
    need(all(release['binary_sha256_after'][n] == h for n, h in engines.items()), 'Actual release binaries differ')
    file(root)
    for p in root.parent.iterdir():
        if p.is_file() and (p.name.startswith(('native', 'NATIVE', 'verify_native', 'verify-native'))):
            file(p)
    return {'commit': commit, 'source_gate_path': gate_path.relative_to(R).as_posix(),
            'source_gate_sha256': sha(gate_path), 'source_inputs': inventory, 'source_root': snapshot['trees']['source']['root'],
            'root_proof_path': root.relative_to(R).as_posix(), 'root_proof_sha256': sha(root),
            'native_manifest_entries': len(rows), 'whole_native_original_files': 644, 'consumed_parent_single_files': len(snapshot['single_files']),
            'ctest': 42, 'active_uci': 8, 'pv_each_profile': 56, 'tt_groups_each_profile': 12,
            'engine_paths': {n: str(build / n) for n in engines}, 'engine_sha256': engines, 'profiles': summaries}

def capture(provenance_path, label, expected_commit, native, required_status):
    file(provenance_path)
    p = read(provenance_path)
    need(p['status'] == required_status, 'Wrong original capture schema/status')
    row = p['captures'][label]
    need(row['source_commit'] == expected_commit and row['rows'] == 5 and row['status'] == 'PASS_ACTUAL_FIVE_CANONICAL_ROWS', 'Capture role/source differs')
    need(row['source_sha256_before'] == row['source_sha256_after'] == native['source_inputs'] and
         row['binary_sha256_before'] == row['binary_sha256_after'] == native['engine_sha256'] and
         row['binary_paths'] == native['engine_paths'] and row['source_manifest_sha256'] == native['source_gate_sha256'], 'Capture source/core/executable correspondence differs')
    folder = provenance_path.parent / label
    for q in folder.iterdir():
        if q.is_file():
            file(q)
    facts = read(folder / 'status.json')
    need(facts == row['process_facts'] and facts['returncode'] == facts['returncode_before_verdict'] == 0 and
         facts['owned_group_empty_before_verdict'] is True and facts['owned_group_empty_after_cleanup'] is True and
         facts['affinity_after_restore'] == p['original_affinity'], 'Capture process not normal/closed/restored')
    need((folder / 'stdin.txt').read_bytes() == b'bench 11\n' * 5 + b'quit\n' and not (folder / 'stderr.txt').read_bytes(), 'Capture transport differs')
    return {'source_commit': expected_commit, 'original_capture_label': label, 'provenance_path': provenance_path.relative_to(R).as_posix(),
            'provenance_sha256': sha(provenance_path), 'provenance_status': p['status'], 'rows': 5,
            'engine_sha256': native['engine_sha256'], 'facts_path': (folder / 'status.json').relative_to(R).as_posix()}

def main():
    baseline = collect_native('baseline', BASE, 'tt-refresh-native-20261021', 'tt-refresh-20261021', 'frozen-source-1d3ed25.tar')
    candidate = collect_native('candidate', CAND, 'see-proof-reuse-native-20261021', 'see-proof-reuse-candidate-20261021', 'frozen-source-7db08ea.tar')
    changed = [n for n in baseline['source_inputs'] if baseline['source_inputs'][n] != candidate['source_inputs'][n]]
    need(len(changed) == 4 and len(baseline['source_inputs']) - len(changed) == 73, 'Expected73same/4delta')
    source_folder = R / 'validation/see-proof-reuse-candidate-20261021'
    for q in source_folder.iterdir():
        if q.is_file():
            file(q)
    for q in (source_folder / 'independent-source-review').rglob('*'):
        if q.is_file():
            file(q)
    review = read(source_folder / 'independent-source-review/REVIEW.json')
    need(review['parent_commit'] == BASE and review['all77_candidate_inputs'] == candidate['source_inputs'], 'Precommit source review bytes differ from actual24')
    observer = R / 'validation/see-proof-reuse-20261021'
    manifest(observer, 'FINAL-SHA256SUMS')
    for q in observer.rglob('*'):
        if q.is_file():
            file(q)
    for root, record in read(observer / 'COMPLETE-OUTSIDE-ORIGINALS.json').items():
        need(record['files'] == len(record['sha256']), 'Observer count differs')
        tree(root, record['sha256'])
    old_capture = R / 'validation/hosted-tt-refresh-strength-20261021/capture-preparation/actual-five-captures/PROVENANCE.json'
    new_capture = V / 'capture-preparation/actual-five-captures/PROVENANCE.json'
    need(sha(old_capture) == '7418f8f3f4fff2ee19acb5e70bb5b97fac7a00ff7b3337279dfe7de8f24a0da1' and
         sha(new_capture) == '928769628a1332d2f6abe1271798c9dd7126d6de04e98b4e3da248a1ae301506', 'Actual capture pins differ')
    captures = {'baseline': capture(old_capture, 'candidate', BASE, baseline, 'PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE'),
                'candidate': capture(new_capture, 'candidate', CAND, candidate, 'PASS_ONE_ACTUAL24_FIVE_COMMAND_CAPTURE_NOT_SPEED_EVIDENCE')}
    closed = read(V / 'capture-preparation/ROOT-CAPTURE-CLOSED.json')
    need(closed['status'] == 'ROOT_OBSERVED_SINGLE_CAPTURE_CLOSED_EXIT_ZERO' and closed['outer_tool_exit_code'] == 0 and
         closed['provenance_sha256'] == sha(new_capture) and closed['candidate_engine_processes'] == 1 and closed['baseline23_engine_processes'] == 0,
         'Actual single24 closure differs')
    for q in (V / 'capture-preparation').rglob('*'):
        if q.is_file():
            file(q)
    p = read(new_capture)
    need(len(p['frozen_inputs']) == 363 and p['final_rehash']['status'] == 'passed' and p['final_rehash']['observed'] == p['frozen_inputs'], 'Capture final363 differs')
    for name, expected in p['frozen_inputs'].items():
        frozen_input(name, expected)
    for q in PRESERVED.rglob('*'):
        if q.is_file():
            file(q)
    pending = ['validation/hosted-see-proof-performance-20261021/ROOT-PREPARATION-REVIEW.json',
               'validation/hosted-see-proof-performance-20261021/ROOT-ONE-ATTEMPT-AUTHORIZATION.json',
               'validation/hosted-see-proof-performance-20261021/independent-review/REVIEW.json']
    missing = [name for name in pending if not (R / name).is_file()]
    for name in pending:
        if name not in missing:
            file(R / name)
    # Re-observe all collected originals without importing any engine/helper code.
    for name, expected in list(files.items()):
        file(name, expected)
    put('PROOF-SHA256.json', dict(sorted(proofs.items())))
    put('INPUT-BYTES-MODES.json', dict(sorted(files.items())))
    put('DIRECTORY-MODES.json', dict(sorted(directories.items())))
    put('HISTORICAL-PATH-ALIASES.json', aliases)
    put('SOURCE-CORRESPONDENCE.json', {'baseline': baseline, 'candidate': candidate, 'unchanged': 73, 'changed_paths': changed,
        'independent_source_review_original_commit_label': review['candidate_commit'],
        'independent_source_review_actual77_hashes_equal_frozen24': True,
        'qualification': 'Preserves genuine precommit review wording; no retroactive commit relabel.'})
    put('SCHEMA-CAPTURE-MAPPING.json', captures)
    result = {'status': 'PASS_FINITE_ORIGINAL_COLLECTION_NOT_READY_AUTHORIZATION', 'utc': datetime.now(timezone.utc).isoformat(),
              'baseline': BASE, 'candidate': CAND, 'repository_proof_files': len(proofs), 'all_input_files': len(files),
              'directory_modes': len(directories), 'historical_preserved_aliases': len(aliases), 'missing_future_gate_paths': missing,
              'source_counts': {'baseline': 77, 'candidate': 77}, 'source_unchanged': 73, 'source_delta': changed,
              'actual_new24_capture_processes': 1, 'new23_capture_processes': 0,
              'candidate_see_assertions_each_profile': 504, 'candidate_exact_cold_warm': 56,
              'reviewed_modules_imported': False, 'engine_build_test_git_network_actions': 0,
              'scope': 'Read/hash existing finite originals only. Current package/adapter and genuine future root READY authority remain separately owned. No speed or Elo claim.'}
    put('RESULT.json', result)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
