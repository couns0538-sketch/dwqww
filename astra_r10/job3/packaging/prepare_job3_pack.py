"""Draft task-specific collector. No sealing, engines, training or GPU work.

Requires root's final, hash-pinned completion receipt before any collection.
Preserves all originals and prepares an incomplete-data request for review.
"""
from __future__ import annotations
import argparse
import datetime
import difflib
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path('D:/a10')
WT = ROOT / 'wt'
JOB = WT / 'astra_r10/job3'
PACK = JOB / 'pack'
ORIGINAL = ROOT / 'job3/source'
ARCHIVED_LAUNCHER_SHA256 = '842d6520058eb9f5c14d7426ca3bad92f080afb5f5684f1c43ab1a56fe38c21d'
RUNTIME_CURRENT_SHA256 = 'c20358958646d3ccf6372fda39548c9c9840626f8dfd93fcc531219d2d16bba6'
RUNTIME_HISTORICAL_SHA256 = '659ca6fbe6abd4337f06eb7841cd8b065c0fc6dc558e3ca7bc47c161c13daa90'
RUNTIME312_MANIFEST_SHA256 = 'a8d8325cd5d6216477c26da3638fe976b7e784b5ead7277c67692e0211a9b461'
RUNTIME312_LOCK_SHA256 = 'ef9dcb6af1e3e64b9d2bbdbcf2eeac7480f9864a56b5bd96cad1741c50ac9a90'
RUNTIME312_BOOTSTRAP_SHA256 = 'f9bba4329df2c6e99e1e65c6170b2683248ef86c1d1767901d71746fca2c4b3e'
RUNTIME254_MANIFEST_SHA256 = '29f8359847d9fc9e25b4b6166805f71940fd35548f9e222587cf16c422c7230e'
RUNTIME254_LOCK_SHA256 = '560cdd1b73fdf0e28ab9ac6c0ac8d2dfaf8c20824eeb409748944ac4ae16517f'
# CR 31481475: only the primary attempt can be regression evidence, and only
# when its pre-launch command binding names this exact runner/helper. Runner
# 2a1de65b is the suite03 runner (no CR lane guard; CR accepts its result as
# UNPROVEN evidence only). Any other runner needs a new CR entry here.
REVIEWED_REGRESSION_RUNNERS = {'2a1de65b4581ae4cb1e74b9d0559dcd420702b060737ad9e00ad9f2f2dd7caf0'}
REVIEWED_SAFE_RUN_HELPER = '17205767ae3ea35a5ccb5a7965bc4988bae26b4f2260c821411a657c9979c787'
REGRESSION_RECORDS = ('RESULT.json', 'FAILURE.json', 'CPU_RUNTIME.json', 'NPT_SOURCES_BEFORE.json',
    'NPT_IMPORTED_INITIAL.json', 'NPT_IMPORTED_AFTER.json', 'NPT_SOURCES_AFTER.json',
    'TOOLCHAIN_BEFORE.json', 'TOOLCHAIN_AFTER.json', 'RUNTIME_BOUND_BEFORE.json',
    'RUNTIME_BOUND_AFTER.json', 'PYTEST_COMMAND.json', 'PYTEST_ALIASES.json', 'pytest.log')
REGRESSION_RETAINED = ('cache', 'temp', 'pycache', 'pytest-temp')
sys.path.insert(0, str(WT / 'skills/gate-handover-pack/scripts'))
import seal_evidence as sealing


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return sealing.digests(sealing.checked_path(path))


def load(path):
    return sealing.decode(sealing.json_bytes(sealing.checked_path(path)))


def write(path, value):
    data = value if isinstance(value, bytes) else (json.dumps(value, indent=2) + '\n').encode()
    sealing.write_new(path, data)


def bound_json(ref):
    path = sealing.checked_path(ref['path'])
    raw = sealing.json_bytes(path)
    need(hashlib.sha256(raw).hexdigest() == ref['sha256'], 'final pinned JSON changed: ' + str(path))
    return path, sealing.decode(raw)


def completion(ref, flag_expectations=(), allow_historical_guard_failure=False):
    path, receipt = bound_json(ref)
    need(type(receipt.get('native_exit_code')) is int and isinstance(receipt.get('finished_utc'), str),
         'launcher exit completion required')
    need(isinstance(receipt.get('capture_errors'), list) and type(receipt.get('disk_floor_breached')) is bool,
         'original launcher guard status required')
    if not allow_historical_guard_failure:
        need(receipt.get('capture_errors') == [] and receipt.get('disk_floor_breached') is False,
             'capture/floor issue must be resolved or explicitly reviewed outside this collector')
    manifest = path.parent / 'manifest.json'
    need(digest(manifest)[0] == receipt.get('manifest_sha256', '').lower(), 'launcher manifest identity mismatch')
    args = load(manifest).get('arguments', [])
    for flag, expected in flag_expectations:
        need(args.count(flag) == 1 and args.index(flag) + 1 < len(args), 'missing unique launcher flag: ' + flag)
        need(Path(args[args.index(flag) + 1]) == expected, 'wrong completed launcher target for ' + flag)
    return path, receipt


def admitted_replay(ready, launcher_receipt):
    admission_path, admission = bound_json(ready['replay']['admission'])
    binding_path, binding = bound_json(ready['replay']['launcher_binding'])
    need(admission.get('status') == 'PASS' and admission.get('selected_cpu') == 3,
         'proof03 quiet admission must PASS on CPU3')
    pair = admission.get('qualifying_pair')
    need(isinstance(pair, list) and len(pair) == 2, 'two original admission observations required')
    def stamp(value):
        parsed = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        need(parsed.tzinfo is not None, 'admission timestamp requires timezone')
        return parsed
    def quiet(sample):
        return all(type(sample.get(key)) in (int, float) and 0 <= sample[key] < limit
                   for key, limit in (('cpu3', 30), ('host_total', 95)))
    need(all(quiet(sample) for sample in pair) and
         (stamp(pair[1]['utc']) - stamp(pair[0]['utc'])).total_seconds() >= 3,
         'qualifying admission pair violates load/separation policy')
    started = stamp(binding['command_start_utc'])
    age = (started - stamp(pair[-1]['utc'])).total_seconds()
    if age > 15:
        immediate = admission.get('immediate_prelaunch', {})
        need(quiet(immediate) and 0 <= (started - stamp(immediate['utc'])).total_seconds() <= 15,
             'old admission pair requires fresh quiet prelaunch observation')
    else:
        need(age >= 0, 'command precedes admission observations')
    need(binding['manifest_sha256'].lower() == launcher_receipt['manifest_sha256'].lower(),
         'admission command binding differs from completed replay manifest')
    archived = sealing.checked_path(binding['archived_launcher'])
    wrapper = sealing.checked_path(binding['wrapper'])
    need(binding['sha256'].lower() == ARCHIVED_LAUNCHER_SHA256,
         'admission must use the accepted immutable archived launcher identity')
    need(digest(archived)[0] == ARCHIVED_LAUNCHER_SHA256, 'archived admission launcher changed')
    need(digest(wrapper)[0] == binding['wrapper_sha256'].lower(), 'admission wrapper changed')
    return {admission_path: ready['replay']['admission']['sha256'],
            binding_path: ready['replay']['launcher_binding']['sha256'],
            archived: ARCHIVED_LAUNCHER_SHA256, wrapper: binding['wrapper_sha256'].lower()}


def check_admission_artifacts(expected, current):
    for path, sha256 in expected.items():
        need(current.get(str(path)) == sha256, 'admission helper/wrapper artifact changed after validation')


def runtime312_inputs(add):
    """Ship assembly identities/receipts only; never copy installed packages/wheels."""
    runtime = ROOT / 'job3/runtime312'
    evidence = JOB / 'runtime312'
    bindings = {}
    def bind(path, expected=None):
        path = sealing.checked_path(path)
        sha, _, size = digest(path)
        need(expected is None or sha == expected, 'isolated runtime evidence changed: ' + str(path))
        bindings[path] = sha; add(path)
        return {'path': str(path), 'sha256': sha, 'bytes': size, 'shipped': True}
    manifest = bind(runtime / 'RUNTIME_FILES.json', RUNTIME312_MANIFEST_SHA256)
    branch_manifest = bind(evidence / 'RUNTIME_FILES.json', RUNTIME312_MANIFEST_SHA256)
    lock_ref = bind(evidence / 'WHEEL_LOCK.json', RUNTIME312_LOCK_SHA256)
    bootstrap_ref = bind(evidence / 'BOOTSTRAP.json', RUNTIME312_BOOTSTRAP_SHA256)
    _, lock = bound_json(lock_ref); _, bootstrap = bound_json(bootstrap_ref)
    assembly_ref = bind(evidence / 'ASSEMBLY_RECEIPT.json')
    _, assembly = bound_json(assembly_ref)
    need(assembly.get('status') == 'RUNTIME_ASSEMBLED' and
         assembly.get('runtime_manifest_sha256') == RUNTIME312_MANIFEST_SHA256 and
         assembly.get('wheel_lock_sha256') == RUNTIME312_LOCK_SHA256,
         'assembly receipt must bind the qualified input identities')
    source_receipts = []
    for receipt in bootstrap['downloads'] + lock['metadata_receipts']:
        path = sealing.checked_path(receipt['path'])
        need(path.is_relative_to(runtime / 'downloads'), 'official source receipt escaped runtime downloads')
        item = {'path': str(path), 'sha256': receipt['sha256'], 'bytes': receipt['bytes'],
                'url': receipt['url']}
        if path.suffix.lower() in ('.whl', '.nupkg'):
            item.update(shipped=False, scope='Recorded official archive identity at assembly; bulk archive retained on D, not rehashed by collector.')
        else:
            item.update(bind(path, receipt['sha256']))
            need(item['bytes'] == receipt['bytes'], 'official metadata byte count changed')
        source_receipts.append(item)
    for name in ('bootstrap-python.stdout', 'bootstrap-python.stderr', 'wheels.stdout', 'wheels.stderr', 'install.stdout', 'install.stderr'):
        bind(runtime / 'logs' / name)
    installer = bind(evidence / 'install-launch/result.json')
    _, receipt = completion(installer)
    need(receipt['native_exit_code'] == 0, 'runtime assembly launcher must have completed successfully')
    return {'path': str(runtime), 'shipped': False, 'status': assembly['status'],
            'manifest': manifest, 'branch_manifest': branch_manifest, 'wheel_lock': lock_ref,
            'bootstrap': bootstrap_ref, 'assembly_receipt': assembly_ref, 'installer': installer,
            'source_receipts': source_receipts,
            'scope': 'Runtime/packages/wheels retained on D. Assembly identity only; native dependency/compiler qualification is reported separately by regression.'}, bindings


def regression_retained_files(directory):
    files = []
    for name in REGRESSION_RETAINED:
        root = sealing.checked_path(directory / name)
        if not root.exists():
            continue
        need(root.is_dir(), 'retained execution path must be a directory')
        for folder, dirs, names in os.walk(root, followlinks=False):
            for leaf in dirs + names:
                need(not sealing.reparse(Path(folder) / leaf), 'execution-cache reparse path refused')
            files.extend(sealing.checked_path(Path(folder) / leaf) for leaf in names)
            need(len(files) <= 10_000, 'retained execution inventory exceeds bounded collector scope')
    return sorted(files)


def runtime254_inputs(add):
    """Preserve both runtime revisions, shipping only the new revision receipts."""
    runtime = ROOT / 'job3/runtime312np254'
    evidence = JOB / 'runtime312np254'
    bindings = {}
    def bind(path, expected=None):
        path = sealing.checked_path(path)
        sha, _, size = digest(path)
        need(expected is None or sha == expected, 'NumPy revision evidence changed')
        bindings[path] = sha; add(path)
        return {'path': str(path), 'sha256': sha, 'bytes': size, 'shipped': True}
    manifest_ref = bind(runtime / 'RUNTIME_FILES.json', RUNTIME254_MANIFEST_SHA256)
    branch_ref = bind(evidence / 'RUNTIME_FILES.json', RUNTIME254_MANIFEST_SHA256)
    lock_ref = bind(evidence / 'WHEEL_LOCK.json', RUNTIME254_LOCK_SHA256)
    _, manifest = bound_json(manifest_ref); _, lock = bound_json(lock_ref)
    need(manifest.get('status') == 'RUNTIME_ASSEMBLED' and Path(manifest['root']) == runtime and
         manifest['source_runtime']['manifest_sha256'] == RUNTIME312_MANIFEST_SHA256 and
         manifest['installed_versions']['numpy'] == '2.5.4' and manifest['wheel_lock_sha256'] == RUNTIME254_LOCK_SHA256,
         'exact separate NumPy2.5.4 runtime required')
    need(lock['source_lock']['sha256'] == RUNTIME312_LOCK_SHA256, 'replacement wheel lineage differs')
    metadata = lock['replacement_metadata']
    metadata_path = sealing.checked_path(metadata['path'])
    need(metadata_path.parent == runtime / 'downloads', 'replacement metadata escaped its download root')
    metadata_ref = bind(metadata_path, metadata['sha256'])
    archive = lock['new_download']
    archive_path = sealing.checked_path(archive['path'])
    need(archive_path.parent == runtime / 'downloads', 'replacement archive path escaped runtime')
    installer = bind(evidence / 'assemble-launch/result.json')
    _, receipt = completion(installer)
    need(receipt['native_exit_code'] == 0, 'NumPy revision assembly must have exited successfully')
    for name in ('install.stdout', 'install.stderr'):
        bind(runtime / 'logs' / name)
    return {'path': str(runtime), 'shipped': False, 'status': 'RUNTIME_ASSEMBLED',
            'manifest': manifest_ref, 'branch_manifest': branch_ref, 'wheel_lock': lock_ref,
            'official_metadata': metadata_ref, 'installer': installer,
            'new_archive': dict(archive, shipped=False,
                scope='Recorded official archive identity at assembly; retained on D and not rehashed by collector.'),
            'source_runtime_manifest': RUNTIME312_MANIFEST_SHA256,
            'scope': 'Separate immutable CPU runtime revision with historical NumPy2.5.4; original runtime and failed attempts retained. Assembly does not grant regression or training clearance.'}, bindings


def regression_inputs(ready, regression_path, regression, add):
    attempts = ready['regression'].get('attempts')
    need(isinstance(attempts, list) and 1 <= len(attempts) <= 10,
         'explicit completed regression/preflight attempt list required')
    bindings, retained, summaries, inventories = {}, {}, [], {}
    seen, reports = set(), set()
    primary_seen = 0
    for item in attempts:
        directory = sealing.checked_path(item['directory'])
        need(directory.parent == ROOT / 'job3/regression-runs' and directory.is_dir() and directory not in seen,
             'fresh uniquely listed regression output directory required')
        seen.add(directory)
        historical = directory != regression_path.parent
        receipt_path, receipt = completion(item['launcher'], [('--out', directory)],
                                           allow_historical_guard_failure=historical)
        add(receipt_path); bindings[receipt_path] = item['launcher']['sha256']
        allowed = set(REGRESSION_RECORDS) | set(REGRESSION_RETAINED) | {'runtime_receipts'}
        need(all(path.name in allowed for path in directory.iterdir()), 'unrecognized regression output requires explicit review')
        raw_reports = [directory / name for name in ('RESULT.json', 'FAILURE.json') if (directory / name).is_file()]
        need(len(raw_reports) == 1, 'each native attempt needs its original result or failure report')
        reports.add(raw_reports[0])
        if raw_reports[0] == regression_path:
            primary = ready['regression']['launcher']
            need(Path(primary['path']) == receipt_path and primary['sha256'] == item['launcher']['sha256'],
                 'primary regression report must use its own exact attempt launcher')
            if regression['status'] == 'PASS':
                need(receipt['native_exit_code'] == 0, 'primary regression PASS contradicts its own native exit')
            need(not historical and not receipt['capture_errors'] and receipt['disk_floor_breached'] is False,
                 'primary regression attempt must have a clean launcher guard')
            command_path, command = bound_json(ready['regression']['command_binding'])
            need(command_path.parent == JOB / 'regression', 'primary command binding must be committed job3 regression evidence')
            need(str(command.get('runner_sha256', '')).lower() in REVIEWED_REGRESSION_RUNNERS and
                 str(command.get('helper_sha256', '')).lower() == REVIEWED_SAFE_RUN_HELPER,
                 'primary regression runner/helper is not a CR-listed identity')
            need(str(command.get('manifest_sha256', '')).lower() == receipt['manifest_sha256'].lower(),
                 'primary command binding differs from its completed launcher manifest')
            add(command_path); bindings[command_path] = ready['regression']['command_binding']['sha256']
            primary_seen += 1
        artifacts = []
        for name in REGRESSION_RECORDS:
            path = directory / name
            if path.exists():
                need(path.is_file(), 'regression record is not a file')
                add(path); sha, _, size = digest(path); bindings[path] = sha
                artifacts.append({'path': str(path), 'sha256': sha, 'bytes': size})
        receipts_dir = sealing.checked_path(directory / 'runtime_receipts')
        if receipts_dir.exists():
            for path in sorted(receipts_dir.iterdir()):
                need(path.is_file() and path.suffix == '.json', 'runtime receipt must be an explicit JSON file')
                add(path); sha, _, size = digest(path); bindings[path] = sha
                artifacts.append({'path': str(path), 'sha256': sha, 'bytes': size})
        inventory = regression_retained_files(directory)
        inventories[directory] = inventory
        rows = []
        for path in inventory:
            sha, md5, size = digest(path)
            retained[path] = sha
            rows.append({'path': str(path), 'sha256': sha, 'md5': md5, 'bytes': size})
        _, original = bound_json({'path': str(raw_reports[0]), 'sha256': bindings[raw_reports[0]]})
        summaries.append({'directory': str(directory), 'status': original.get('status'),
                          'launcher': item['launcher'], 'native_exit_code': receipt['native_exit_code'],
                          'launcher_guard': {'capture_errors': receipt['capture_errors'],
                              'disk_floor_breached': receipt['disk_floor_breached'],
                              'qualification': 'REJECTED_HISTORICAL_ATTEMPT' if receipt['capture_errors'] or receipt['disk_floor_breached'] else 'CLEAN_LAUNCHER_ONLY'},
                          'role': 'PRIMARY_REGRESSION_EVIDENCE' if raw_reports[0] == regression_path else 'HISTORICAL_DISCLOSURE_ONLY',
                          'counts_as_regression_evidence': raw_reports[0] == regression_path,
                          'artifacts': artifacts, 'retained_execution_files': rows,
                          'retained_scope': 'Current post-exit hash inventory only; generated code/DLLs/test files remain outside the pack and Forge source.'})
    need(regression_path in reports and primary_seen == 1, 'final regression report must be exactly one of the explicitly listed original native reports')
    if regression['status'] == 'PASS':
        need(regression.get('preflight_only') is False and regression.get('collected', 0) >= 73 and
             regression.get('passed') == regression.get('collected') and regression.get('failures') == 0 and
             regression.get('skipped') == 0 and regression.get('optimizer_updates') == 0 and regression.get('training_loops') == 0,
             'regression PASS requires the complete unskipped suite with no training')
        need(all(regression.get(key) is True for key in ('external_runtime_unchanged', 'toolchain_unchanged', 'private_runtime_unchanged')) and
             regression.get('private_runtime_binding', {}).get('sha256') == RUNTIME254_MANIFEST_SHA256,
             'regression PASS must bind unchanged isolated runtime/toolchain/NPT inputs')
    need(len(json.dumps(summaries).encode()) <= 8 * 1024 * 1024, 'execution identity inventory exceeds8MiB bounded evidence')
    return summaries, bindings, retained, inventories


def prepare(final_receipt, destination, launcher_output):
    destination = sealing.checked_path(destination)
    launcher_output = sealing.checked_path(launcher_output)
    final_receipt = sealing.checked_path(final_receipt)
    need(destination.is_relative_to(JOB / 'packaging') and not destination.exists() and not PACK.exists(),
         'fresh preparation destination and absent job3/pack required')
    need(launcher_output.is_relative_to(JOB / 'packaging') and (launcher_output / 'manifest.json').is_file(),
         'identify this collector safe-launcher output')
    ready_raw = sealing.json_bytes(final_receipt)
    ready = sealing.decode(ready_raw)
    need(ready.get('schema') == 1 and ready.get('status') == 'FINAL_INPUTS_FOR_INCOMPLETE_PACK'
         and ready.get('reviews_closed') is True, 'root final completion/review receipt required; draft cannot run')
    need(isinstance(ready.get('blockers'), list) and ready['blockers'] and
         all(isinstance(x, str) and x.strip() for x in ready['blockers']), 'explicit final blockers required')
    audit_path, audit = bound_json(ready['audit']['report'])
    replay_path, replay = bound_json(ready['replay']['report'])
    native_path, native = bound_json(ready['native_relabel']['report'])
    regression_path, regression = bound_json(ready['regression']['report'])
    need(audit_path == JOB / 'audit/native-actual01/audit.json', 'wrong actual audit report')
    need(replay_path == ROOT / 'job3/resume-proof03/RESTART_PROOF.json', 'wrong admission-valid native upstream replay report')
    need(native_path == ROOT / 'job3/native-relabel01/REPORT.json', 'wrong native relabel report')
    need(audit.get('complete') is True and audit.get('status') in ('PASS', 'FAIL', 'UNVERIFIED'), 'full actual audit must have exited and completed')
    need(replay.get('upstream_scope') == 'native-relabel' and replay.get('rows') == 16, 'replay03 must bind16 actual native relabel rows')
    need(native.get('rows') == 16 and native.get('scope', {}).get('fixture_factory') is False, 'native relabel cannot be a fixture factory')
    need(regression.get('status') in ('PASS', 'FAIL', 'UNVERIFIED', 'BLOCKED'), 'final explicit regression status required')
    receipts = {}
    receipts['audit'] = completion(ready['audit']['launcher'], [('--out', JOB / 'audit/native-actual01')])
    receipts['replay'] = completion(ready['replay']['launcher'], [('--out', ROOT / 'job3/resume-proof03')])
    receipts['native_relabel'] = completion(ready['native_relabel']['launcher'], [('--out', ROOT / 'job3/native-relabel01')])
    receipts['regression'] = completion(ready['regression']['launcher'])
    admission_bindings = admitted_replay(ready, receipts['replay'][1])
    need(receipts['audit'][1]['native_exit_code'] == {'PASS': 0, 'FAIL': 1, 'UNVERIFIED': 2}[audit['status']],
         'audit status/exit disagreement')
    for role, report in [('replay', replay), ('native_relabel', native), ('regression', regression)]:
        if report['status'] == 'PASS':
            need(receipts[role][1]['native_exit_code'] == 0, role + ' PASS contradicts launcher exit')
    need((JOB / 'HANDOVER.md').is_file(), 'root must finish HANDOVER.md before collecting')

    sources = set()
    excluded = []
    def add(path):
        path = sealing.checked_path(path)
        need(path.is_file(), 'required artifact missing: ' + str(path))
        sources.add(path)
    def tree(directory):
        directory = sealing.checked_path(directory)
        need(directory.is_dir(), 'required tree missing: ' + str(directory))
        pending = [directory]
        while pending:
            current = pending.pop()
            with os.scandir(current) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    need(not sealing.reparse(path), 'reparse artifact refused')
                    if entry.is_dir(follow_symlinks=False):
                        if path in (PACK, destination, launcher_output) or path.name in ('__pycache__', '.pytest_cache'):
                            excluded.append({'path': str(path), 'reason': 'pack/current preparation/cache; original retained'})
                        else:
                            pending.append(path)
                    elif path.parent == JOB / 'audit/native-actual01' and path.name.startswith('audit.sqlite'):
                        excluded.append({'path': str(path), 'reason': 'retained index; hash and original path recorded separately'})
                    else:
                        add(path)
    tree(JOB)
    for directory in (ROOT / 'job3/native-relabel01', ROOT / 'job3/resume-proof01', ROOT / 'job3/resume-proof02', ROOT / 'job3/resume-proof03', ROOT / 'job3/probe01',
                      ORIGINAL / 'astra_r8/datafilter', ORIGINAL / 'tools/data', ORIGINAL / 'tools/data2',
                      WT / 'skills/npt-data-holdout-check', WT / 'skills/resumable-shard-job',
                      WT / 'skills/gate-handover-pack', WT / 'skills/grok-pc-safe-run'):
        tree(directory)
    for path in (ORIGINAL / 'SOURCE_MANIFEST.json', ROOT / 'job3/inputs/INPUTS.json',
                 WT / 'AGENTS.md', WT / 'astra_r10/PLAN.md', JOB / 'RUNTIME_INPUTS.json', JOB / 'RUNTIME_CURRENT_HASHES.json',
                 WT / 'astra_r10/job1/packaging/verify_pack.py', WT / 'astra_r10/launch.ps1'):
        add(path)
    for name in ('LICENSE', 'LICENSE.md', 'COPYING', 'AGENTS.md'):
        if (ORIGINAL / name).is_file():
            add(ORIGINAL / name)
    for role, (path, _) in receipts.items():
        add(path)
        tree(path.parent)
    add(final_receipt)
    add(regression_path)
    for path in admission_bindings:
        add(path)
    runtime312_map, runtime312_bindings = runtime312_inputs(add)
    runtime254_map, runtime254_bindings = runtime254_inputs(add)
    regression_map, regression_bindings, retained_bindings, retained_inventories = regression_inputs(
        ready, regression_path, regression, add)

    # Preserve exact auxiliary build input sources; never read/copy the external
    # C: compiler or mistake this O2 diagnostic binary for a kit candidate.
    probe = load(ROOT / 'job3/probe01/command.json')
    external_build_inputs = []
    for name, expected in probe['inputs'].items():
        if name.lower().startswith('d:\\a10\\') or name.lower().startswith('d:/a10/'):
            path = sealing.checked_path(name)
            need(digest(path)[0] == expected, 'auxiliary probe source changed: ' + name)
            add(path)
        else:
            external_build_inputs.append({'path': name, 'sha256': expected, 'scope': 'historical compiler identity; not read or copied'})

    raw001 = ROOT / 'job3/inputs/source001/forge_selfplay_001.txt'
    frozen = load(ROOT / 'job3/inputs/INPUTS.json')
    frozen_by_path = {str(Path(row['copy'])): row for row in frozen['files']}
    need(str(raw001) in frozen_by_path, 'raw001 frozen identity absent')
    sources.add(raw001)
    payload_size = sum(path.stat().st_size for path in sources)
    # Includes sample/patch/maps and prospective sealed copy. Never duplicate the
    # 1.9 GB input set, complete audit index or external runtime tree.
    reservation = payload_size + 20_000_000
    sealing.disk_budget(reservation)
    need(sealing.workspace_bytes() + reservation <= sealing.CAP, 'workspace cap cannot fit the bounded pack')
    destination.mkdir(parents=True)
    write(destination / 'FINAL_INPUTS.json', ready_raw)

    # Derive the sample only after all native final status/exit checks above.
    filtered = ROOT / 'job3/inputs/filtered/records.jsonl'
    expected = frozen_by_path[str(filtered)]['sha256']
    need(digest(filtered)[0] == expected, 'filtered source changed before sample')
    sample = destination / 'filtered_sample1000.jsonl'
    consumed = []
    with filtered.open('rb') as stream:
        for index in range(1000):
            line = stream.readline(1024 * 1024 + 1)
            need(line and len(line) <= 1024 * 1024, 'filtered sample ended early/oversized row')
            row = sealing.decode(line)
            need(isinstance(row, dict) and isinstance(row.get('fen'), str) and len(row['fen'].split()) == 6,
                 'sample is not original full-FEN JSONL')
            consumed.append(line)
    write(sample, b''.join(consumed))
    need(digest(filtered)[0] == expected, 'filtered source changed while sampling')
    write(destination / 'SAMPLE.json', {'schema': 1, 'classification': 'UNPROVEN', 'rows': 1000,
          'source': str(filtered), 'source_sha256': expected, 'physical_lines': [1, 1000],
          'sample': str(sample), 'sample_sha256': digest(sample)[0],
          'meaning': 'Exact bounded prefix only; full-input audit remains the qualification evidence.'})

    patches = []
    for owner in ('tool', 'resume'):
        copied = load(JOB / owner / 'SOURCE_COPY.json')
        for item in copied['files']:
            before = ORIGINAL / item['source']
            after = JOB / owner / item['destination']
            need(digest(before)[0] == item['sha256'].lower(), 'preserved source hash mismatch')
            a, b = before.read_text(encoding='utf-8'), after.read_text(encoding='utf-8')
            if a != b:
                patches.extend(difflib.unified_diff(a.splitlines(True), b.splitlines(True),
                               fromfile='original/' + item['source'], tofile=owner + '/' + item['destination']))
    new_tool = JOB / 'tool/full_state.py'
    patches.extend(difflib.unified_diff([], new_tool.read_text(encoding='utf-8').splitlines(True),
                                      fromfile='/dev/null', tofile='tool/full_state.py'))
    write(destination / 'SOURCE_CHANGES.patch', ''.join(patches).encode())

    sqlite = JOB / 'audit/native-actual01/audit.sqlite'
    sqlite_sha, sqlite_md5, sqlite_size = digest(sqlite)
    need(sqlite_sha == audit['index_sha256'] and sqlite_size == audit['index_bytes'], 'retained actual audit index changed')
    historical_runtime = JOB / 'RUNTIME_INPUTS.json'
    current_runtime = JOB / 'RUNTIME_CURRENT_HASHES.json'
    # The current per-file receipt is11 MB: hash it as an artifact; never feed it
    # through the bounded8 MiB JSON-report parser or relabel it as old copy proof.
    historical_sha, _, historical_bytes = digest(historical_runtime)
    current_sha, _, current_bytes = digest(current_runtime)
    need(historical_sha == RUNTIME_HISTORICAL_SHA256, 'preserved malformed runtime receipt changed')
    need(current_sha == RUNTIME_CURRENT_SHA256 and current_bytes == 11_015_923, 'current D-runtime identity receipt changed')
    runtime_bindings = {historical_runtime: historical_sha, current_runtime: current_sha}
    input_map = {'schema': 1, 'classification': 'UNPROVEN', 'frozen_inputs': frozen['files'],
                 'retained_index': {'path': str(sqlite), 'sha256': sqlite_sha, 'md5': sqlite_md5, 'bytes': sqlite_size,
                                    'shipped': False, 'reason': 'retained audit index; original path/hash provided'},
                 'runtime': {'path': str(ROOT / 'job3/runtime'), 'shipped': False,
                             'historical_copy_receipt': {'path': str(historical_runtime), 'sha256': historical_sha,
                                  'bytes': historical_bytes, 'files_type': 'str', 'usable_per_file_array': False,
                                  'limitation': 'Original copy checked source/copy hashes and exited0, but a typed $Manifest collision serialized files as a string. The historical per-file list was lost; current hashes do not reconstruct it.'},
                             'current_manifest': {'path': str(current_runtime), 'sha256': current_sha, 'bytes': current_bytes,
                                  'scope': 'Current copied D-runtime file identities only; no fresh original-source comparison or historical-copy reconstruction.'}},
                 'external_build_inputs': external_build_inputs,
                 'isolated_cpu_runtime312': runtime312_map,
                 'isolated_cpu_runtime312np254': runtime254_map,
                 'native_regression_attempts': regression_map,
                 'scope_notes': ['probe01 is auxiliary O2 diagnostic only; no engine candidate in this pack.',
                                 'resume-proof03 is primary admitted native upstream replay; proof02 correctness passed but admission failed and is auxiliary.',
                                 'resume-proof01 uses FixtureProbePool upstream and is auxiliary.',
                                 'No training, GPU, gate, match or strength qualification was performed.'],
                 'excluded': excluded}
    write(destination / 'INPUT_MAP.json', input_map)

    def ref(path):
        return {'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path)[0]}
    for role, original, report in [('audit', audit_path, audit), ('replay', replay_path, replay)]:
        envelope = {'schema': 1, 'status': report['status'], 'classification': 'UNPROVEN',
                    'evidence_scope': 'actual-inputs' if role == 'audit' else 'actual-adapter',
                    'scope': 'Incomplete-data packaging envelope; original report remains unchanged.',
                    'evidence': [ref(original), ref(receipts[role][0])], 'original_report': str(original)}
        if role == 'audit':
            envelope.update({key: report[key] for key in ('source_rows', 'training_rows', 'cohort_rows', 'holdouts',
                             'position_overlap_rows', 'game_overlap_rows', 'state_mismatch_rows', 'unknown_game_id_rows')})
        else:
            envelope.update(upstream_scope=report['upstream_scope'], rows=report['rows'],
                            output_scope=report['scope'], strength='UNPROVEN')
        write(destination / (role + '_report.json'), envelope)
    blockers = list(ready['blockers'])
    if audit['status'] != 'PASS' or audit['unknown_game_id_rows']:
        blockers.append('Full actual audit is ' + audit['status'] + '; authentic game-ID clearance remains missing or failed.')
    blockers.append('Training is NOT_RUN. No authenticated ready training manifest or crew-verified fresh seed inventory was supplied.')
    for role, report in [('replay', replay), ('native_relabel', native), ('regression', regression)]:
        if report['status'] != 'PASS':
            blockers.append(role + ' final status is ' + report['status'] + '; see original evidence.')
    write(destination / 'TRAINING_BLOCKERS.json', {'schema': 1, 'status': 'BLOCKED', 'classification': 'UNPROVEN', 'blockers': blockers})
    tree(destination)
    # tree() excludes the current preparation directory only while traversing its
    # parent; directly enumerating it includes the newly created immutable files.
    for path in destination.iterdir():
        if path.is_file():
            add(path)
    tool = JOB / 'tool/full_state.py'
    training = JOB / 'packaging/training_command.py'
    add(training)
    roles = {tool: 'tool', sample: 'sample', training: 'training_command',
             destination / 'audit_report.json': 'audit_report', destination / 'replay_report.json': 'replay_report'}
    artifacts = []
    for path in sorted(sources):
        default_role = 'auxiliary_binary' if path.suffix.lower() in ('.exe', '.dll') else 'original_evidence'
        artifacts.append({'role': roles.get(path, default_role), 'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path)[0]})
    current = {str(ROOT / item['path']): item['sha256'] for item in artifacts}
    check_admission_artifacts(admission_bindings, current)
    for path, expected in runtime_bindings.items():
        need(current.get(str(path)) == expected, 'runtime receipt artifact changed after validation')
    for path, expected in (runtime312_bindings | runtime254_bindings | regression_bindings).items():
        need(current.get(str(path)) == expected, 'isolated runtime/regression evidence changed after validation')
    for directory, expected_files in retained_inventories.items():
        need(regression_retained_files(directory) == expected_files, 'retained execution file set changed during collection')
    for path, expected in retained_bindings.items():
        need(digest(path)[0] == expected, 'retained execution file changed during collection')
    for section in ('audit', 'replay', 'native_relabel', 'regression'):
        for pinned in ready[section].values():
            if isinstance(pinned, dict) and set(pinned) >= {'path', 'sha256'}:
                need(current.get(str(Path(pinned['path']))) == pinned['sha256'],
                     'final report/admission input changed after validation')
    need(current[str(raw001)] == frozen_by_path[str(raw001)]['sha256'], 'shipped raw001 differs from frozen source')
    for name, expected in probe['inputs'].items():
        if name.lower().startswith('d:\\a10\\') or name.lower().startswith('d:/a10/'):
            need(current[str(Path(name))] == expected, 'shipped auxiliary probe source differs from build receipt')
    mapping = {'schema': 1, 'classification': 'UNPROVEN', 'pack_root': str(PACK),
               'files': [{'source': str(ROOT / item['path']), 'pack': 'artifacts/' + item['path'],
                          'sha256': item['sha256'], 'role': item['role']} for item in artifacts]}
    mapping_path = destination / 'SOURCE_TO_PACK.json'
    write(mapping_path, mapping)
    artifacts.append({'role': 'source_to_pack_mapping', 'path': mapping_path.relative_to(ROOT).as_posix(), 'sha256': digest(mapping_path)[0]})
    request = {'schema': 1, 'source_root': str(ROOT), 'artifacts': artifacts, 'blockers': blockers}
    write(destination / 'seal_request.json', request)
    need(hashlib.sha256(sealing.json_bytes(final_receipt)).hexdigest() == hashlib.sha256(ready_raw).hexdigest(),
         'final completion receipt changed during preparation')
    # The sealer reruns quota and copied-byte checks; this collector never seals.
    print(json.dumps({'status': 'PREPARED_INCOMPLETE_DATA', 'classification': 'UNPROVEN', 'artifacts': len(artifacts),
                      'request': str(destination / 'seal_request.json'), 'pack': str(PACK)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final-receipt', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--launcher-output', type=Path, required=True)
    parser.add_argument('--threads', type=int, choices=[1], required=True)
    args = parser.parse_args()
    prepare(args.final_receipt, args.out, args.launcher_output)
