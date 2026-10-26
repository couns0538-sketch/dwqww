"""Read-only, exact-allowlist proposal for two root-declared CLOSED S08 v2 caches.

No compiler/native execution, archive disk write, unlink, or source mutation.
Shared hashing/stat/proc/gzip-sink helpers are loaded from frozen wave14 functions
only; its external-root selection/main code is deliberately not executed.
"""
from pathlib import Path
import ast
import collections
import datetime
import gzip
import hashlib
import json
import os
import re
import shlex
import stat

BASE = Path('/workspace/forge-pack24-20261026')
S08 = BASE / 'S08'
OWN = Path(__file__).parent
BUILDS = tuple(S08 / n / 'build' for n in (
    'forge_sol_S08_v2_Release_ON_window1_20261026',
    'forge_sol_S08_ASAN_v2_window1_20261026'))
HELPER = BASE / 'forge_sol_S00_fourteenth_space_proposal_20261026/forge_sol_S00_fourteenth_readonly_audit_20261026.py'
HELPER_SHA = '78c072a4d78ada1347461d95417bae12556d52c1b1384a36fe2fd61c90a208af'
FREEZE = S08 / 'forge_sol_S08_TLS_v2_source_freeze_20261026.json'
FREEZE_SHA = '2923e86c186e357aac177e453f5745993d0839af02422d2622ff9f80dffae5ad'
SOURCE = S08 / 'Lprime_v2'
OUT = OWN / 'forge_sol_S00_sixteenth_closed_cache_proposal_20261026.json'


def scope_path(path):
    """Only explicit old build roots and compiler-cache path shapes are allowed."""
    p = Path(path)
    if not p.is_absolute() or '..' in p.parts or p.resolve() != p:
        return False
    for root in BUILDS:
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        if rel.as_posix() == 'libforge_core.a':
            return True
        return (len(rel.parts) >= 3 and rel.parts[0] == 'CMakeFiles' and
                rel.parts[1].startswith('forge') and rel.parts[1].endswith('.dir') and
                rel.suffix == '.o')
    return False


def format_kind(header, suffix):
    if suffix == '.a' and header[:8] == b'!<arch>\n':
        return 'AR_static_core_library'
    if (suffix == '.o' and len(header) >= 20 and header[:4] == b'\x7fELF' and
            header[5] in (1, 2) and
            int.from_bytes(header[16:18], 'little' if header[5] == 1 else 'big') == 1):
        return 'ELF_ET_REL_compiler_object'
    return None


def group_reasons(rows, bound_paths, prior_paths, active_paths):
    reasons = []
    if not rows or len(rows) != rows[0]['nlink'] or len({r['nlink'] for r in rows}) != 1:
        reasons.append('all_hardlink_aliases_not_accounted')
    if any(not scope_path(r['path']) for r in rows):
        reasons.append('alias_outside_exact_two_build_cache_roots')
    if any(r['path'] not in bound_paths for r in rows):
        reasons.append('alias_has_no_exact_compile_or_static_library_binding')
    if any(r['path'] in prior_paths for r in rows):
        reasons.append('prior_retirement_map_collision')
    if any(r['path'] == p or Path(r['path']).is_relative_to(Path(p)) for r in rows for p in active_paths):
        reasons.append('active_process_reference')
    return reasons


def load_helpers():
    raw = HELPER.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == HELPER_SHA
    wanted = {'utc', 'sha', 'stamp', 'meta', 'process_snapshot', 'CounterSink'}
    tree = ast.parse(raw, filename=str(HELPER))
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in wanted]
    assert {n.name for n in nodes} == wanted
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(HELPER), 'exec'), globals())


def source_hashes(expected):
    actual = {rel: sha(SOURCE / rel) for rel in expected}
    assert actual == expected, 'Lprime_v2 source differs from frozen TLS v2'
    return actual


def main():
    assert not OUT.exists()
    load_helpers()
    started = utc()
    assert sha(FREEZE) == FREEZE_SHA
    freeze = json.loads(FREEZE.read_text())
    expected = freeze['source_sha256']
    assert len(expected) == 80 and freeze['source'] == str(SOURCE)
    source_before = source_hashes(expected)

    receipts = []
    source_provenance = []
    bindings = {}
    retained_elfs = []
    receipt_names = ('forge_sol_S08_v2_Release_ON_window2_20261026/forge_sol_S08_Release_build_result_20261026.json',
                     'forge_sol_S08_ASAN_v2_window4_20261026/forge_sol_S08_ASAN_build_result_20261026.json')
    expected_receipts = ('094d2ca2e928655d4f7becdcddc3094e3c00a1021c937f2d92f0d29cf456045d',
                         '64f0ce7e2bd196f72684aafcf8cef18ada838e5ef81361a4966f3c664fc11b21')
    expected_elfs = ('9208252eba0bc2aee5aa383806f854dff506c1ecd11c151d647c2567c64a3de2',
                     '4f6b1b5e919b43e691a45f8effbe7c5a419581e9a27d1ecaa39788f0df7475c5')
    for i, build in enumerate(BUILDS):
        receipt_path = S08 / receipt_names[i]
        assert sha(receipt_path) == expected_receipts[i]
        result = json.loads(receipt_path.read_text())
        assert result['status'] == 'PASS_BUILD_ONLY' and not result['pending_targets']
        assert len(result['completed_targets']) == 12
        assert result['source_freeze_sha256'] == FREEZE_SHA
        assert result['source'] == str(SOURCE) and result['build_dir'] == str(build)
        assert result['source_before'] == expected
        assert result.get('source_after', expected) == expected
        assert result.get('source_unchanged', True)
        if i < 2:
            assert all(not c.get('running_group_members_after_close') for c in result['commands'])
        receipts.append({'path': str(receipt_path), 'sha256': sha(receipt_path),
                         'status': result.get('status'), 'phase': result.get('phase'),
                         'root_declared_closed': True})
        cache = build / 'CMakeCache.txt'
        entries = dict((l.split('=', 1)[0].split(':', 1)[0], l.split('=', 1)[1])
                       for l in cache.read_text().splitlines() if '=' in l and not l.startswith(('#', '//')))
        assert entries['CMAKE_HOME_DIRECTORY'] == str(SOURCE)
        assert entries['CMAKE_PROJECT_NAME'] == 'ChessEngineForge'
        assert entries['CMAKE_CXX_COMPILER'] == freeze['compiler']
        assert sha(Path(entries['CMAKE_CXX_COMPILER'])) == freeze['compiler_sha256']
        cc = build / 'compile_commands.json'
        commands = json.loads(cc.read_text())
        pi = len(source_provenance)
        source_provenance.append({'build_root': str(build), 'source_home': str(SOURCE),
            'cmake_cache': str(cache), 'cmake_cache_sha256': sha(cache),
            'source_cmakelists_sha256': source_before['CMakeLists.txt'],
            'source_freeze': str(FREEZE), 'source_freeze_sha256': FREEZE_SHA,
            'source_sha256': source_before, 'compiler': entries['CMAKE_CXX_COMPILER'],
            'compiler_sha256': freeze['compiler_sha256'], 'build_type': entries['CMAKE_BUILD_TYPE'],
            'project': entries['CMAKE_PROJECT_NAME'], 'compile_commands': str(cc),
            'compile_commands_sha256': sha(cc), 'source_and_cache_retained': True,
            'FORGE_PROF': entries['FORGE_PROF'], 'FORGE_ENABLE_SANITIZERS': entries['FORGE_ENABLE_SANITIZERS']})
        for c in commands:
            assert c['directory'] == str(build)
            src = Path(c['file'])
            rel = src.relative_to(SOURCE).as_posix()
            assert rel in source_before and sha(src) == source_before[rel]
            obj = build / c['output']
            assert scope_path(obj) and obj.suffix == '.o'
            assert str(obj) not in bindings
            parts = shlex.split(c['command'])
            assert parts[parts.index('-o') + 1] == c['output']
            assert parts[parts.index('-c') + 1] == c['file']
            bindings[str(obj)] = {'provenance_id': pi, 'source': str(src),
                'source_sha256': source_before[rel], 'output': c['output'],
                'compile_command': c['command']}
        library = build / 'libforge_core.a'
        link = build / 'CMakeFiles/forge_core.dir/link.txt'
        link_text = link.read_text()
        assert 'libforge_core.a' in link_text
        core_outputs = [Path(q).relative_to(build).as_posix() for q in bindings
                        if Path(q).is_relative_to(build) and '/forge_core.dir/' in q]
        assert core_outputs and all(q in link_text for q in core_outputs)
        bindings[str(library)] = {'provenance_id': pi, 'link_recipe': str(link),
            'link_recipe_sha256': sha(link), 'compiled_core_objects': core_outputs}
        assert sha(build / 'forge') == expected_elfs[i]
        for f in build.iterdir():
            if not f.is_file() or f.is_symlink():
                continue
            with f.open('rb') as h:
                header = h.read(20)
            if header[:4] == b'\x7fELF' and format_kind(header, '.o') is None:
                retained_elfs.append({'path': str(f), 'sha256': sha(f), 'size': f.stat().st_size})

    qualification_receipts = []
    for name in ('forge_sol_S08_v2_Release_qualification_once_20261026/forge_sol_S08_v2_Release_qualification_result_20261026.json',
                 'forge_sol_S08_ASAN_FULL_NATIVE_20261026/forge_sol_S08_ASAN_full_qualification_v2_result_20261026.json',
                 'forge_sol_S08_ASAN_PROFILE_EXTRA_NATIVE_20261026/forge_sol_S08_ASAN_profile_extra_result_20261026.json'):
        path = S08 / name
        record = json.loads(path.read_text())
        assert record['status'] == 'PASS' and record['source_freeze_sha256'] == FREEZE_SHA
        qualification_receipts.append({'path': str(path), 'sha256': sha(path), 'status': record['status']})

    prior = set()
    prior_maps = []
    observed_maps = set(BASE.glob('forge_sol_S00_*space_20261026/*restore_map*.json'))
    old = BASE / 'forge_sol_resource_recovery_audit_20261026.json'
    observed_maps.update(Path(m['path']) for m in json.loads(old.read_text())['prior_retirement_maps'])
    for m in sorted(observed_maps):
        if not m.is_file():
            continue
        raw = m.read_bytes()
        x = json.loads(raw)
        rows = x if isinstance(x, list) else x.get('files', x.get('entries', []))
        prior.update(r['path'] for r in rows if 'path' in r)
        prior_maps.append({'path': str(m), 'sha256': hashlib.sha256(raw).hexdigest(), 'rows': len(rows)})

    candidates = {}
    missing_bound_objects = []
    for name, binding in bindings.items():
        f = Path(name)
        try:
            s = f.lstat()
        except FileNotFoundError:
            missing_bound_objects.append(name)
            continue
        assert scope_path(f) and stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid()
        candidates[(s.st_dev, s.st_ino)] = True

    # No broad producer/library scan: only aliases of these exact candidate inodes.
    # All workspace regular-file paths are statted so aliases outside allowlist
    # reject the whole group. An alias outside workspace gives an nlink deficit.
    aliases = collections.defaultdict(list)
    scan_errors = []
    inspected = 0
    for base, dirs, files in os.walk('/workspace', followlinks=False,
                                     onerror=lambda e: scan_errors.append(str(e))):
        dirs[:] = [n for n in dirs if not (Path(base) / n).is_symlink()]
        for n in files:
            f = Path(base) / n
            try:
                s = f.lstat()
            except OSError as e:
                scan_errors.append(str(e))
                continue
            inspected += 1
            if stat.S_ISREG(s.st_mode) and (s.st_dev, s.st_ino) in candidates:
                aliases[(s.st_dev, s.st_ino)].append(meta(f, s))
    wanted = {r['path'] for rows in aliases.values() for r in rows} | {str(p) for p in BUILDS}
    proc = process_snapshot(wanted)
    active = {r['target'] for r in proc['candidate_reference_hits']}
    activity_file = BASE / 'forge_sol_S00_fifteenth_space_proposal_20261026/forge_sol_S00_fifteenth_activity_preflight_20261026.py'
    assert sha(activity_file) == 'f5c0273a23f801e6dffc9bd092212435df45b727ba2fd8be2f323270d7c5a2ae'
    tree = ast.parse(activity_file.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {'affected_build', 'snapshot_proc'}]
    assert len(nodes) == 2
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(activity_file), 'exec'), globals())
    activity = snapshot_proc()
    active.update(activity['blocked_build_roots'])
    active_commands = [r for r in proc['live_engine_compiler_names']
                       if any(str(b) in r['cmdline'] for b in BUILDS)]
    assert not active_commands, 'live compiler/engine uses one of the exact closed roots'

    groups, skipped = [], []
    for rows in aliases.values():
        rows.sort(key=lambda r: r['path'])
        reasons = group_reasons(rows, bindings, prior, active)
        if reasons:
            skipped.append({'aliases': [r['path'] for r in rows], 'reasons': reasons})
            continue
        f = Path(rows[0]['path'])
        before = f.stat()
        with f.open('rb') as h:
            header = h.read(20)
        kind = format_kind(header, f.suffix)
        if kind is None:
            skipped.append({'aliases': [r['path'] for r in rows], 'reasons': ['not_AR_or_ELF_ET_REL_compiler_cache']})
            continue
        sink, digest = CounterSink(), hashlib.sha256()
        with gzip.GzipFile(fileobj=sink, filename='', mode='wb', mtime=0, compresslevel=6) as z:
            with f.open('rb') as h:
                for chunk in iter(lambda: h.read(1024 * 1024), b''):
                    digest.update(chunk)
                    z.write(chunk)
        assert stamp(before) == stamp(f.stat())
        assert all(stamp(Path(r['path']).stat()) == stamp(before) for r in rows)
        assert stamp(before) == [rows[0][k] for k in ('device', 'inode', 'nlink', 'size', 'mtime_ns')]
        groups.append({'aliases': [r['path'] for r in rows], 'alias_metadata': rows,
            'dev': before.st_dev, 'inode': before.st_ino, 'links': before.st_nlink,
            'size': before.st_size, 'allocated_bytes': before.st_blocks * 512,
            'provenance_ids': sorted({bindings[r['path']]['provenance_id'] for r in rows}),
            'compiler_bindings': {r['path']: bindings[r['path']] for r in rows},
            'sha256': digest.hexdigest(), 'kind': kind, 'magic_hex': header.hex(),
            'measured_archive_bytes': sink.count, 'measured_net_payload_bytes': before.st_size - sink.count,
            'conservative_projected_net_allocated_bytes': before.st_blocks * 512 - ((sink.count + 4095) // 4096) * 4096,
            'all_aliases_rechecked': True})
        print(json.dumps({'measured_groups': len(groups), 'net_bytes': sum(g['measured_net_payload_bytes'] for g in groups)}), flush=True)
    groups.sort(key=lambda g: (-g['size'], g['aliases'][0]))
    assert groups
    assert source_hashes(expected) == source_before
    for f in retained_elfs:
        assert sha(f['path']) == f['sha256']
    assert sha(FREEZE) == FREEZE_SHA
    free = os.statvfs('/workspace').f_bavail * os.statvfs('/workspace').f_frsize
    out = {'created_utc': started, 'finished_utc': utc(),
        'state': 'READ_ONLY_MEASURED_PROPOSAL_ORIGINALS_RETAINED',
        'scope': 'NEW explicit root-authorized scope: only the exact TWO CLOSED S08 v2 build roots in allowed_build_roots. Only compiler-bound CMakeFiles/forge*.dir/**/*.o with ELF ET_REL and libforge_core.a AR caches. EVERY hardlink alias must remain within this exact allowlist and be source/compiler bound. Preserve all source80, metadata, logs/receipts, .o.d/build recipes, nets, raw executables and all other active builds including B. This is not a broad prefix extension.',
        'allowed_build_roots': [str(p) for p in BUILDS], 'groups': groups,
        'summary': {'selected_groups': len(groups), 'selected_alias_paths': sum(len(g['aliases']) for g in groups),
            'selected_unique_raw_bytes': sum(g['size'] for g in groups),
            'measured_gzip6_archive_bytes': sum(g['measured_archive_bytes'] for g in groups),
            'measured_net_payload_bytes': sum(g['measured_net_payload_bytes'] for g in groups),
            'conservative_projected_net_allocated_bytes': sum(g['conservative_projected_net_allocated_bytes'] for g in groups),
            'largest_one_archive_bytes': max(g['measured_archive_bytes'] for g in groups),
            'free_bytes_at_report': free,
            'qualification': 'Measured gzip lengths only. No archive written/decoded, no originals removed; actual gain requires root reviewed lossless preservation and complete alias retirement.'},
        'generator_reuse': {'path': str(BASE / 'forge_sol_S00_fifteenth_space_proposal_20261026/forge_sol_S00_fifteenth_readonly_audit_20261026.py'), 'sha256': 'c615f986638ea4f4a937a592fcc1e8182be226ab359598a5e8f0a7507648a84e'},
        'source_freeze': {'path': str(FREEZE), 'sha256': FREEZE_SHA, 'root': str(SOURCE),
            'files_checked': len(source_before), 'before': source_before, 'after': source_before,
            'current_CMake_home_matches_frozen_source': True},
        'fresh_build_source_provenance': source_provenance,
        'closed_status_basis': {'root_instruction': 'Root explicitly declares only these two CLOSED v2 windows CLOSED. Both v2 forges and all helpers remain preserved; B/OFF caches are excluded. Do not resume or rerun old native builds.',
            'build_receipts': receipts, 'qualified_native_receipts': qualification_receipts, 'whole_root_activity_gate': activity,
            'process_snapshot': proc, 'active_exact_root_compiler_commands': active_commands,
            'qualification': 'Current-day mtime is expected; exact root authorization plus closed receipts and fresh visible-reference checks are used. Proc denials limit global absence.'},
        'preserved_ELFs_before_after': retained_elfs,
        'alias_scan': {'root': '/workspace', 'follow_symlinks': False, 'file_paths_inspected': inspected,
            'candidate_inodes': len(candidates), 'scan_errors': scan_errors,
            'qualification': 'Only selected inode identities are collected; all workspace regular files are statted regardless of name. Outside-workspace aliases cause nlink deficit and whole-group rejection.'},
        'prior_retirement_maps': prior_maps, 'missing_bound_objects_not_claimed': missing_bound_objects,
        'skipped_groups': skipped, 'reuse': {'helper': str(HELPER), 'sha256': HELPER_SHA,
            'functions_only': ['utc', 'sha', 'stamp', 'meta', 'process_snapshot', 'CounterSink']},
        'failure_controls': {'exact_two_roots_only': len(BUILDS) == 2,
            'all_selected_aliases_exact_allowlist_and_compile_bound': all(not group_reasons(g['alias_metadata'], bindings, prior, active) for g in groups),
            'source80_before_after_identical': source_before == source_hashes(expected),
            'all_selected_cache_formats_ET_REL_or_AR': all(g['kind'] in {'ELF_ET_REL_compiler_object', 'AR_static_core_library'} for g in groups),
            'retained_main_and_helper_ELFs_unchanged': all(sha(r['path']) == r['sha256'] for r in retained_elfs),
            'no_candidate_process_references': not any(r['target'] in {a for g in groups for a in g['aliases']} for r in proc['candidate_reference_hits']),
            'no_archive_write_no_unlink_no_native_compiler_execution': True},
        'root_execution_requirements': ['Root review of the exact new allowlist is required before any retirement; subagent did not unlink.',
            'Recheck all source80/freeze/cache/compile/link recipe hashes, every alias metadata/content, closed leases and visible references immediately before action; reject any changes or unknown binding.',
            'Archive sequentially with deterministic gzip6, fsync, decode/hash with Python and GNU gzip, persist full aliases/metadata/hash/restore map and journal durably, then unlink all aliases with exact nlink accounting.',
            'Retain every existing source, ELF, dataset/net, raw log, build recipe, receipt, map and archive. Never touch B or any unlisted/active build.']}
    assert all(out['failure_controls'].values())
    with OUT.open('x') as f:
        json.dump(out, f, indent=2)
        f.write('\n')
    print(json.dumps({'output': str(OUT), 'sha256': sha(OUT), 'bytes': OUT.stat().st_size, 'summary': out['summary']}), flush=True)


if __name__ == '__main__':
    main()
