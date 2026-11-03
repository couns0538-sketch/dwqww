"""Seal closed R8 artifacts with fresh hashes and original attribution. UNPROVEN."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parents[2]
WORK = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
from filter_positions import input_identity, low_priority, sha256
from resource_policy import BUDGET_ROOTS, storage_guard
from seal_admission import BoundInputs
from verify_handoff import verify

HELPER = Path('C:/astra8_data/quality6h_20261102/pack_completion.py')
HELPER_SHA = '25a4626eb6a3116070600019eb636714a0267df02931afc8496a09f40e40f874'
V7 = Path('C:/astra8_data/extension3h_20261103/handoff_v7')
V7_SHA = '52f39e0ceeb6fc6c63422514296b928b308ede862754e8d69addde1aa44fc720'
PGN_BASE_SHA = '6e2354dffa7d273eca732bafac8c54c2830fe8d9a677cc217801a8f599c43c00'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
    storage_guard(path, allowance=len(data)+1024*1024)
    with path.open('xb') as stream:
        stream.write(data)


def exact_json(bound, path):
    return bound.read(path)


def source_set(mapping):
    require(isinstance(mapping, dict) and mapping, 'nonempty source map required')
    require(all(isinstance(path,str) and isinstance(digest,str)
                and re.fullmatch('[0-9a-f]{64}',digest) for path,digest in mapping.items()),
            'invalid source identity map')
    names = {str(Path(path).resolve()).casefold() for path in mapping}
    require(len(names) == len(mapping), 'duplicate source aliases')
    return names


def check_collection(bound, path, sources, arguments):
    collection = exact_json(bound, path)
    require(collection['status'] == 'PASS' and collection['source_files'] == sources,
            'collection source identity differs from full suite')
    targets = collection['targets']
    paths = sorted((HERE/'tests').glob('test_*.py'))
    integration = HERE/'tests/test_integration.py'
    require(integration in paths, 'integration tests missing')
    paths.remove(integration)
    paths.append(integration)
    require(targets == [p.relative_to(WORK).as_posix() for p in paths]
            and arguments[7:] == targets, 'ordered full-suite file set differs')
    entries = collection['collections']
    require([entry['name'] for entry in entries] == ['broad', 'ordered'],
            'both collection commands required')
    node_sets = []
    for entry in entries:
        expected = ['astra_r8/datafilter'] if entry['name'] == 'broad' else targets
        require(entry['exit_code'] == 0 and entry['command'][1:] ==
                ['-B', '-m', 'pytest', '-q', '--collect-only', '-p', 'no:cacheprovider', *expected],
                'collection command differs')
        logs = {}
        for stream in ('stdout', 'stderr'):
            log_path = path.parent/(entry['name']+'.'+stream+'.log')
            payload = log_path.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            require(digest == entry[stream+'_sha256'] == sha256(log_path),
                    'collection log bytes differ')
            bound.files[str(log_path.resolve())] = digest
            logs[stream] = payload
        nodes = [line.strip() for line in logs['stdout'].decode('utf-8').splitlines()
                 if line.startswith('astra_r8/datafilter/') and '::' in line]
        require(nodes == entry['nodes'] and len(nodes) == len(set(nodes)) == collection['nodes']
                and len(nodes) >= 564, 'collection nodes incomplete or duplicated')
        node_sets.append(set(nodes))
    require(node_sets[0] == node_sets[1], 'collection omitted or added cases')
    return collection['nodes']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--suite', required=True, type=Path)
    parser.add_argument('--validation', required=True, type=Path)
    parser.add_argument('--handoff', required=True, type=Path)
    parser.add_argument('--validation-mode', choices=('original', 'pgn'), default='original')
    parser.add_argument('--collection', type=Path)
    args = parser.parse_args()
    require((args.validation_mode == 'pgn') == (args.collection is not None),
            'PGN mode requires its complete collection proof')
    low_priority()
    output = Path(storage_guard(args.output, allowance=15_000_000)['destination'])
    require(not os.path.lexists(output), 'refusing existing final pack')
    output.mkdir()
    candidate = subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORK,text=True).strip()
    files = sorted([*HERE.glob('*.py'), *HERE.glob('*.ps1'),
                    *(HERE/'tests').glob('*.py'), HERE/'evidence/conftest.py',
                    Path(__file__).resolve()])
    pins = {str(path):sha256(path) for path in files}
    write(output/'RUN.json', dict(candidate=candidate, source_files=pins,
          started_utc=datetime.now(timezone.utc).isoformat(), strength='UNPROVEN',
          excluded_directory=str(output),
          exclusion_reason='This new pack and its metadata are excluded from their own inventory. Keep command stdout outside inventoried files until closure.'))
    bound = BoundInputs()

    def pin(path, digest):
        path = Path(path).resolve()
        require(isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest),
                'invalid expected linked-file digest')
        require(sha256(path) == digest and bound.files.get(str(path),digest) == digest,
                'linked-file identity differs: '+str(path))
        bound.files[str(path)] = digest

    tested_paths = [*HERE.glob('*.py'), *(HERE/'tests').glob('*.py')]
    expected_tested = {str(path.resolve()).casefold() for path in tested_paths}
    validation_driver = HERE/'evidence/extension5h/verify_input_repair.py'
    complete = exact_json(bound, args.validation/'COMPLETE.json')
    require(complete['status'] == 'PASS', 'fresh input validation did not pass')
    require(source_set(complete['source_files']) == expected_tested | {str(validation_driver.resolve()).casefold()},
            'validation source set incomplete or unexpected')
    for path,digest in complete['source_files'].items():
        pin(path,digest)
    expected_receipts = ({'source_lineage.json', 'native_admission.json', 'published_verify.json'}
                         if args.validation_mode == 'pgn' else
                         {'shared_selfplay_source.json', 'native_admission.json',
                          'bounded_filter.json', 'published_verify.json'})
    require(set(complete['receipts']) == expected_receipts,
            'validation receipt set incomplete or unexpected')
    require(set(complete.get('stages', {})) ==
            (set() if args.validation_mode == 'pgn' else {'identity','orientation'}),
            'validation stage set incomplete or unexpected')
    if args.validation_mode == 'pgn':
        require(complete['base_proof_sha256'] == PGN_BASE_SHA,
                'preceding self-play proof identity differs')
    for name,item in complete['receipts'].items():
        require(Path(item['path']).resolve() == (args.validation/name).resolve(),
                'validation receipt points to a different proof')
        pin(item['path'],item['sha256'])
    for name,item in complete.get('stages', {}).items():
        require(Path(item['receipt']).resolve() == (args.validation/(name+'_receipt.json')).resolve(),
                'validation stage points to a different proof')
        pin(item['receipt'],item['sha256'])
    if args.validation_mode == 'pgn':
        base_path = args.validation.parent/'input_repair_validation/COMPLETE.json'
        base = exact_json(bound, base_path)
        require(bound.files[str(base_path.resolve())] == PGN_BASE_SHA,
                'exact preceding proof bytes required')
        inherited = {name:dict(path=item.get('path', item.get('receipt')), sha256=item['sha256'])
                     for name,item in {**base['receipts'], **base['stages']}.items()}
        lineage = exact_json(bound, args.validation/'source_lineage.json')
        records_path = str(HERE/'records.py')
        require(lineage['status'] == 'PASS' and lineage['base_proof_sha256'] == PGN_BASE_SHA
                and lineage['inherited_receipts'] == inherited
                and lineage['before_records_sha256'] == base['source_files'][records_path]
                and lineage['current_records_sha256'] == complete['source_files'][records_path],
                'PGN lineage does not bind the complete preceding proof')
        mandatory = dict(complete['source_files'])

        def add_required(path, digest):
            key = str(Path(path).resolve())
            require(mandatory.get(key, digest) == digest, 'conflicting inherited dependency')
            mandatory[key] = digest

        add_required(base_path, PGN_BASE_SHA)
        add_required(HERE/'evidence/extension5h/verify_pgn_repair.py', complete['driver_sha256'])
        add_required(args.validation.parent/'pgn_raw_fen_review/records_before.py.txt',
                     base['source_files'][records_path])
        add_required(args.validation.parent/'handoff_v8/manifest.json', base['manifest_sha256'])
        add_required(args.handoff/'manifest.json', complete['manifest_sha256'])
        for item in inherited.values():
            add_required(item['path'], item['sha256'])
        require(source_set(complete['bound_inputs']) == source_set(mandatory)
                and complete['bound_inputs'] == mandatory,
                'inherited dependency set is incomplete or conflicting')
        for path, digest in mandatory.items():
            pin(path, digest)
    published = verify(args.handoff/'manifest.json')
    require(published['manifest_sha256'] == complete['manifest_sha256'], 'handoff identity differs')
    manifest = exact_json(bound,args.handoff/'manifest.json')
    pin(args.handoff/'manifest.json',published['manifest_sha256'])
    require(complete['runtime'] == manifest['runtime'], 'validation runtime differs from verified handoff')
    write(output/'published_verify.json', published)
    suite = exact_json(bound, args.suite/'exit.json')
    require(suite['exit_code'] == 0 and suite['source_stable'] is True, 'full suite did not pass stably')
    before = exact_json(bound, args.suite/'source_before.json')
    after = exact_json(bound, args.suite/'source_after.json')
    require(before == after and source_set(after) == expected_tested,
            'full-suite source set or identity differs')
    for path,digest in after.items():
        pin(path,digest)
    command = exact_json(bound, args.suite/'command.json')
    arguments = command['arguments']
    require(len(arguments) >= 8
            and arguments[:6] == ['-B','-m','pytest','-q','-p','no:cacheprovider']
            and arguments[6].startswith('--basetemp='),
            'full-suite command was narrowed')
    if args.validation_mode == 'pgn':
        expected_count = check_collection(bound, args.collection, after, arguments)
    else:
        require(arguments[7:] == ['astra_r8/datafilter'], 'full-suite command was narrowed')
        expected_count = None
    log = (args.suite/'pytest.log').read_bytes()
    require(hashlib.sha256(log).hexdigest() == suite['log_sha256'], 'full-suite log changed')
    pin(args.suite/'pytest.log',suite['log_sha256'])
    matches = re.findall(r'(\d+) passed,.*?(\d+) subtests passed in', log.decode('utf-8'))
    require(len(matches) == 1 and int(matches[0][0]) >= 544 and int(matches[0][1]) == 11,
            'full-suite completion count missing')
    require(expected_count is None or int(matches[0][0]) == expected_count,
            'executed full-suite count differs from collection')
    runtime_paths = list(args.suite.rglob('cpu_runtime_*.json'))
    require(len(runtime_paths) == 1, 'exactly one full-suite runtime receipt required')
    runtime = exact_json(bound, runtime_paths[0])
    require(runtime['before'] == runtime['after'] == manifest['runtime']
            and source_set(runtime['after']['files']), 'tested runtime differs from verified handoff')
    for path,digest in runtime['after']['files'].items():
        pin(path,digest)
    protected = {path.relative_to(V7).as_posix():sha256(path)
                 for path in sorted(V7.rglob('*')) if path.is_file()}
    require(protected.get('manifest.json') == V7_SHA and protected == complete['protected_v7'],
            'protected v7 tree changed')
    for name,digest in protected.items():
        pin(V7/name,digest)
    pin(HELPER,HELPER_SHA)
    spec = importlib.util.spec_from_file_location('pinned_inventory', HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)

    def membership():
        paths, aliases = [], []
        for root in BUDGET_ROOTS:
            if not root.exists():
                continue
            helper.ROOT = root
            found, links = helper.inventory_paths(output)
            paths.extend(found)
            aliases.extend(links)
        return sorted(paths), sorted(aliases, key=lambda item:item['path'])

    paths, aliases = membership()
    inventory = []
    for index,path in enumerate(paths):
        inventory.append(input_identity(path))
        if index and index % 1000 == 0:
            print(json.dumps({'event':'inventory_progress','files':index}),flush=True)
            storage_guard(output, allowance=0)
    require(membership() == (paths, aliases), 'inventory membership changed')
    for path,item in zip(paths,inventory):
        current = path.stat()
        require((current.st_dev,current.st_ino,current.st_size,current.st_mtime_ns,current.st_ctime_ns)
                == (item['device'],item['inode'],item['bytes'],item['mtime_ns'],item['ctime_ns']),
                'inventoried file metadata changed')
    require(all(sha256(path) == digest for path,digest in pins.items()), 'pack source changed')
    require({str(path.resolve()).casefold() for path in
             [*HERE.glob('*.py'), *(HERE/'tests').glob('*.py')]} == expected_tested,
            'tested source membership changed')
    require({path.relative_to(V7).as_posix() for path in V7.rglob('*') if path.is_file()} == set(protected),
            'protected v7 membership changed')
    bound.verify()
    write(output/'full_output_hashes.json', dict(roots=list(map(str,BUDGET_ROOTS)),
          excluded_directory=str(output), files=inventory, aliases=aliases,
          regular_files=len(inventory), payload_bytes=sum(item['bytes'] for item in inventory)))
    write(output/'COMPLETE.json', dict(status='PASS', strength='UNPROVEN', candidate=candidate,
          source_files=pins, suite=str(args.suite), passed_tests=int(matches[0][0]), subtests=11,
          validation=str(args.validation), validation_sha256=sha256(args.validation/'COMPLETE.json'),
          validation_mode=args.validation_mode,
          manifest_sha256=published['manifest_sha256'], protected_v7=protected,
          inventory_sha256=sha256(output/'full_output_hashes.json'), bound_receipts=bound.files,
          regular_files=len(inventory), resource=storage_guard(output, allowance=0),
          finished_utc=datetime.now(timezone.utc).isoformat(),
          limitations=['Hashes establish retained bytes, not independent experiment truth.',
                      'Historical measurements retain their original source identities.',
                      'Metadata closure checks are not protection against adversarial timestamp restoration.',
                      'No training, GPU, engine change, speed or strength claim.']))
    print(json.dumps({'status':'PASS','files':len(inventory),'candidate':candidate}),flush=True)


if __name__ == '__main__':
    main()
