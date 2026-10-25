#!/usr/bin/env python3
"""Read-only archive-identity coverage control; never runs a chess executable."""
from pathlib import Path
import argparse, ast, gzip, hashlib, json, sys


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            value.update(chunk)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('old', 'inventory'), required=True)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--old-controller', type=Path, required=True)
    parser.add_argument('--history-root', type=Path, required=True)
    args = parser.parse_args()
    selection = json.loads(args.selection.read_text())
    # Required helpers are selected by the frozen restore record, not a guessed count.
    selected = [row for row in selection['files'] if Path(row['path']).name != 'libforge_core.a']
    if not selected:
        raise ValueError('selection has no support helpers')
    source = ast.parse(args.old_controller.read_text())
    function = next(node for node in source.body
                    if isinstance(node, ast.FunctionDef) and node.name == 'archive_map')
    generations = []
    if args.mode == 'old':
        namespace = {'Path': Path, 'json': json, 'P': args.old_controller.parent}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(args.old_controller), 'exec'), namespace)
        lookup = {key: [value] for key, value in namespace['archive_map']().items()}
    else:
        lookup = {}
        for path in sorted(args.history_root.glob('forge_sol_S00_*/forge_sol_S00_*cache_restore_map_20261025.json')):
            generations.append({'path': str(path), 'sha256': digest(path)})
            for row in json.loads(path.read_text())['files']:
                lookup.setdefault(row['path'], []).append(row)
    rows = []
    for item in selected:
        candidates = lookup.get(item['path'], [])
        row = {'original_path': item['path'], 'expected_sha256': item['sha256'],
               'expected_bytes': item['size'], 'candidate_records': len(candidates)}
        if not candidates:
            row.update(status='MISSING_IDENTITY', reason='Archive inventory omits this selected helper')
        elif any(value['sha256'] != item['sha256'] or value['size'] != item['size'] for value in candidates):
            row.update(status='CONFLICTING_IDENTITY', reason='An archive generation disagrees with the frozen selection')
        else:
            archive = next((value for value in candidates if Path(value['compressed_path']).is_file()), None)
            if archive is None:
                row.update(status='ARCHIVE_UNAVAILABLE')
            else:
                path = Path(archive['compressed_path'])
                if digest(path) != archive['archive_sha256']:
                    raise ValueError('Compressed archive hash mismatch: ' + str(path))
                value = hashlib.sha256()
                length = 0
                with gzip.open(path, 'rb') as stream:
                    for chunk in iter(lambda: stream.read(1 << 20), b''):
                        value.update(chunk)
                        length += len(chunk)
                if value.hexdigest() != item['sha256'] or length != item['size']:
                    raise ValueError('Decoded archive identity mismatch: ' + str(path))
                row.update(status='READY_IDENTITY_VERIFIED', archive=str(path),
                           archive_sha256=archive['archive_sha256'], decoded_sha256=value.hexdigest(),
                           decoded_bytes=length)
        rows.append(row)
    missing = [row['original_path'] for row in rows if row['status'] != 'READY_IDENTITY_VERIFIED']
    result = {'status': 'INCOMPLETE_IDENTITY_INVENTORY' if missing else 'PREFLIGHT_READY',
              'mode': args.mode, 'selection_sha256': digest(args.selection),
              'old_controller_sha256': digest(args.old_controller), 'generation_inventory': generations,
              'required_helpers': len(selected), 'not_ready': len(missing), 'rows': rows,
              'scope': 'Read-only metadata and gzip decode, no engine execution, restoration, writes, caller control or native test'}
    print(json.dumps(result, sort_keys=True, indent=2))
    return 1 if missing else 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as error:
        print('PREFLIGHT_OBSERVER_ERROR: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
