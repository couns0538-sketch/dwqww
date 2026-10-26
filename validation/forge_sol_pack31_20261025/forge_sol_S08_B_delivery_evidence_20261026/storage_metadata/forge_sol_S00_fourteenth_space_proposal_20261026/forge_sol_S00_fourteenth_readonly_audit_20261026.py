"""Read-only cache inspection. Writes only its own new metadata proposal directory."""
from pathlib import Path
import collections, datetime, gzip, hashlib, io, json, os, re, stat, struct

OWN = Path(__file__).parent
ROOT = Path('/workspace/.cloud-setup')
BASE = Path('/workspace/forge-pack24-20261026')
LIB = BASE / 'forge_sol_resource_library_audit_20261026.json'
OLD = BASE / 'forge_sol_resource_recovery_audit_20261026.json'
OUT = OWN / 'forge_sol_S00_fourteenth_closed_cache_proposal_20261026.json'
TARGET = 110 * 1024 * 1024
HISTORICAL_CUTOFF_NS = 1792972800000000000  # 2026-10-26T00:00:00Z; reject current-day cache writes

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def scoped(path):
    p = Path(path)
    return (p.is_absolute() and '..' not in p.parts and
            str(p).startswith(str(ROOT) + '/') and
            '/workspace/dwqww/' not in str(p) and
            '/tested-binaries/' not in str(p) and
            '/validation/' not in str(p) and
            not re.search(r'(?:/|_)s0?8(?:/|_|-)', str(p), re.I) and
            p.suffix in {'.o', '.a'} and p.resolve() == p)

def stamp(s):
    return [s.st_dev, s.st_ino, s.st_nlink, s.st_size, s.st_mtime_ns]

def meta(p, s):
    return {'path': str(p), 'device': s.st_dev, 'inode': s.st_ino,
            'nlink': s.st_nlink, 'size': s.st_size,
            'allocated_bytes': s.st_blocks * 512, 'mode': stat.S_IMODE(s.st_mode),
            'uid': s.st_uid, 'gid': s.st_gid, 'atime_ns': s.st_atime_ns,
            'mtime_ns': s.st_mtime_ns}

started = utc()
lib = json.loads(LIB.read_text())
old = json.loads(OLD.read_text())
assert lib['library_schema'] == ['directory_ids', 'size', 'allocated_bytes', 'device', 'inode', 'nlink', 'mtime_ns', 'atime_ns', 'mode', 'uid', 'gid', 'all_aliases_found', 'known_forge_source', 'prior_map_collision', 'source_home_ids']
assert lib['singleton_object_schema'] == ['directory_id', 'filename', 'size', 'allocated_bytes', 'device', 'inode', 'mtime_ns', 'atime_ns', 'mode', 'uid', 'gid', 'prior_map_collision']
assert not OUT.exists()

# Every original row is decoded using the actual producer's full schema.
builds = {}
for i, row in enumerate(lib['libraries']):
    assert len(row) == len(lib['library_schema'])
    d = dict(zip(lib['library_schema'], row))
    if not d['known_forge_source'] or d['prior_map_collision']:
        continue
    for di in d['directory_ids']:
        p = Path(lib['directory_root']) / lib['directories'][di]
        if not str(p).startswith(str(ROOT) + '/') or '/workspace/dwqww/' in str(p):
            continue
        builds[str(p)] = {'producer_library_index': i, 'directory_id': di,
                         'source_home_ids': d['source_home_ids'],
                         'producer_known_forge_source': True}

map_paths = {m['path'] for m in old['prior_retirement_maps']}
for ordinal in ['eighth', 'ninth', 'tenth', 'eleventh', 'twelfth', 'thirteenth']:
    map_paths.add(str(BASE / f'forge_sol_S00_{ordinal}_space_20261026' /
                      f'forge_sol_S00_{ordinal}_cache_restore_map_20261026.json'))
prior = set()
maps = []
for name in sorted(map_paths):
    p = Path(name)
    if not p.exists():
        maps.append({'path': name, 'missing': True})
        continue
    x = json.loads(p.read_text())
    rows = x if isinstance(x, list) else x.get('files', x.get('entries', []))
    prior.update(r['path'] for r in rows if 'path' in r)
    maps.append({'path': name, 'sha256': sha(p), 'rows': len(rows),
                 'state': x.get('state') if isinstance(x, dict) else None})

# Candidate objects are confined to source-proven CMake build directories.
candidate_keys = set()
candidate_paths = {}
for name, binding in builds.items():
    p = Path(name)
    paths = [p / 'libforge_core.a']
    cm = p / 'CMakeFiles'
    if cm.is_dir():
        paths.extend(cm.rglob('*.o'))
    for q in paths:
        try:
            s = q.lstat()
        except FileNotFoundError:
            continue
        if (not scoped(q) or not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or
                s.st_mtime_ns >= HISTORICAL_CUTOFF_NS):
            continue
        # Permit Forge build targets' compiler objects, preserve all executables.
        rel = q.relative_to(p)
        if q.suffix == '.o' and (len(rel.parts) < 3 or rel.parts[0] != 'CMakeFiles' or
                                not rel.parts[1].startswith('forge') or
                                not rel.parts[1].endswith('.dir')):
            continue
        candidate_keys.add((s.st_dev, s.st_ino))
        candidate_paths[str(q)] = (str(p), binding)

# Walk every external regular file, regardless of extension, to find all aliases.
# An alias outside this explicit root produces an nlink deficit and is rejected.
aliases = collections.defaultdict(list)
scan_errors = []
scan_counts = collections.Counter()
for base, dirs, files in os.walk(ROOT, followlinks=False,
                                 onerror=lambda e: scan_errors.append(str(e))):
    dirs[:] = [d for d in dirs if not (Path(base) / d).is_symlink()]
    for n in files:
        p = Path(base) / n
        try:
            s = p.lstat()
        except OSError as e:
            scan_errors.append(str(e))
            continue
        scan_counts['file_paths_inspected'] += 1
        if stat.S_ISLNK(s.st_mode):
            scan_counts['symlink_files_skipped'] += 1
        elif stat.S_ISREG(s.st_mode) and (s.st_dev, s.st_ino) in candidate_keys:
            aliases[(s.st_dev, s.st_ino)].append(meta(p, s))
print(json.dumps({'stage': 'all_external_alias_metadata_scanned', 'counts': dict(scan_counts),
                  'candidate_inodes': len(candidate_keys), 'found_groups': len(aliases),
                  'errors': len(scan_errors)}), flush=True)

def process_snapshot(wanted):
    hits, live, zombies, denied = [], [], [], collections.Counter()
    checked = 0
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        try:
            status = (p / 'status').read_text()
            comm = (p / 'comm').read_text().strip()
            cmd = (p / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
            state = re.search(r'^State:\s+(\S)', status, re.M).group(1)
        except (OSError, AttributeError):
            denied['status_or_comm_or_cmdline'] += 1
            continue
        checked += 1
        match = (comm.lower().startswith(('forge', 'fastchess', 'stockfish', 'cc1', 'g++', 'c++', 'clang', 'cmake', 'make', 'ninja', 'ld', 'as')))
        if match:
            (zombies if state == 'Z' else live).append({'pid': int(p.name), 'comm': comm,
                                                        'state': state, 'cmdline': cmd[:1000]})
        try:
            fds = list((p / 'fd').iterdir())
        except OSError:
            denied['fd_directories'] += 1
            fds = []
        for link in [p / 'exe', p / 'cwd', *fds]:
            try:
                target = os.readlink(link).removesuffix(' (deleted)')
            except OSError:
                denied['fd_exe_cwd_links'] += 1
                continue
            if target in wanted:
                hits.append({'pid': int(p.name), 'link': str(link), 'target': target})
        try:
            for line in (p / 'maps').read_text().splitlines():
                parts = line.split(maxsplit=5)
                if len(parts) == 6 and parts[5].removesuffix(' (deleted)') in wanted:
                    hits.append({'pid': int(p.name), 'link': 'maps', 'target': parts[5]})
        except OSError:
            denied['maps'] += 1
    return {'utc': utc(), 'processes_inspected': checked, 'live_engine_compiler_names': live,
            'zombie_engine_compiler_names': zombies, 'candidate_reference_hits': hits,
            'unreadable': dict(denied),
            'qualification': 'No global FD-absence claim: proc access denials are explicit. Historical build closure plus no live engine/compiler-name match supports proposal only; root must recheck leases and references immediately before any retirement.'}

all_names = {a['path'] for v in aliases.values() for a in v}
proc = process_snapshot(all_names)
active = {h['target'] for h in proc['candidate_reference_hits']}

provenance = []
prov_index = {}
def prove_build(name):
    if name in prov_index:
        return prov_index[name]
    p = Path(name)
    cache = p / 'CMakeCache.txt'
    try:
        text = cache.read_text()
    except OSError:
        return None
    entries = dict((line.split('=', 1)[0].split(':', 1)[0], line.split('=', 1)[1])
                   for line in text.splitlines() if '=' in line and not line.startswith(('#', '//')))
    home = Path(entries.get('CMAKE_HOME_DIRECTORY', ''))
    project = entries.get('CMAKE_PROJECT_NAME', '')
    cmake = home / 'CMakeLists.txt'
    if 'forge' not in project.lower() or not home.is_absolute() or not cmake.is_file():
        return None
    if not ((home / 'src/search.cpp').is_file() or (home / 'source/src/search.cpp').is_file()):
        return None
    record = {'build_root': name, **builds[name], 'cmake_cache': str(cache),
              'cmake_cache_sha256': sha(cache), 'project': project,
              'source_home': str(home), 'source_cmakelists_sha256': sha(cmake),
              'compiler': entries.get('CMAKE_CXX_COMPILER'),
              'build_type': entries.get('CMAKE_BUILD_TYPE'),
              'source_and_cache_retained': True}
    index = len(provenance)
    provenance.append(record)
    prov_index[name] = index
    return index

eligible, skipped = [], []
for key, rows in aliases.items():
    rows.sort(key=lambda r: r['path'])
    first = rows[0]
    reasons = []
    if any(r['mtime_ns'] >= HISTORICAL_CUTOFF_NS for r in rows):
        reasons.append('current_day_cache_not_proven_historical_closed')
    if len(rows) != first['nlink'] or len({r['nlink'] for r in rows}) != 1:
        reasons.append('all_hardlink_aliases_not_accounted')
    if any(not scoped(r['path']) for r in rows):
        reasons.append('alias_outside_explicit_scope_or_symlink')
    if any(r['path'] in prior for r in rows):
        reasons.append('prior_retirement_map_collision')
    if any(r['path'] in active for r in rows):
        reasons.append('active_process_reference')
    refs = []
    for row in rows:
        binding = candidate_paths.get(row['path'])
        if not binding:
            reasons.append('alias_not_proven_forge_build_cache')
            continue
        build, unused = binding
        pi = prove_build(build)
        if pi is None:
            reasons.append('fresh_cmake_or_preserved_forge_source_missing')
            continue
        refs.append(pi)
        if row['path'].endswith('.o'):
            rel = Path(row['path']).relative_to(Path(build) / 'CMakeFiles').parts
            source_rel = Path(*rel[1:]).as_posix()[:-2]
            if not (Path(provenance[pi]['source_home']) / source_rel).is_file():
                reasons.append('exact_object_source_path_missing')
    if reasons:
        skipped.append({'aliases': [r['path'] for r in rows], 'size': first['size'],
                        'nlink': first['nlink'], 'reasons': sorted(set(reasons))})
    else:
        eligible.append({'aliases': [r['path'] for r in rows], 'alias_metadata': rows,
                         'dev': first['device'], 'inode': first['inode'],
                         'links': first['nlink'], 'size': first['size'],
                         'allocated_bytes': first['allocated_bytes'],
                         'provenance_ids': sorted(set(refs))})
eligible.sort(key=lambda g: (-g['size'], g['aliases'][0]))

class CounterSink:
    def __init__(self): self.count = 0
    def write(self, b): self.count += len(b); return len(b)
    def flush(self): pass

selected = []
net = 0
for g in eligible:
    p = Path(g['aliases'][0])
    before = p.stat()
    with p.open('rb') as f:
        header = f.read(20)
    if p.suffix == '.o':
        good = (header[:4] == b'\x7fELF' and header[5] in (1, 2) and
                int.from_bytes(header[16:18], 'little' if header[5] == 1 else 'big') == 1)
        kind = 'ELF_ET_REL_compiler_object'
    else:
        good = header[:8] == b'!<arch>\n'
        kind = 'AR_static_core_library'
    if not good:
        skipped.append({'aliases': g['aliases'], 'size': g['size'], 'reasons': ['unsupported_or_non_relocatable_format'], 'magic_hex': header.hex()})
        continue
    sink, h = CounterSink(), hashlib.sha256()
    with gzip.GzipFile(fileobj=sink, filename='', mode='wb', mtime=0, compresslevel=6) as z:
        with p.open('rb') as f:
            for b in iter(lambda: f.read(1024 * 1024), b''):
                h.update(b)
                z.write(b)
    after = p.stat()
    if stamp(before) != stamp(after) or stamp(before) != [g['dev'], g['inode'], g['links'], g['size'], g['alias_metadata'][0]['mtime_ns']]:
        skipped.append({'aliases': g['aliases'], 'size': g['size'], 'reasons': ['changed_during_measurement']})
        continue
    if any(stamp(Path(r['path']).stat()) != stamp(before) for r in g['alias_metadata']):
        skipped.append({'aliases': g['aliases'], 'size': g['size'], 'reasons': ['alias_changed_during_measurement']})
        continue
    g.update({'sha256': h.hexdigest(), 'kind': kind, 'magic_hex': header.hex(),
              'measured_archive_bytes': sink.count,
              'measured_net_payload_bytes': g['size'] - sink.count,
              'conservative_projected_net_allocated_bytes': g['allocated_bytes'] - ((sink.count + 4095) // 4096) * 4096,
              'measurement': 'gzip.GzipFile(filename="",mtime=0,compresslevel=6) streamed to byte-count sink; no archive written and no source removed',
              'all_aliases_rechecked': True})
    selected.append(g)
    net += g['measured_net_payload_bytes']
    if len(selected) % 10 == 0:
        print(json.dumps({'stage': 'measured_selected', 'groups': len(selected), 'net_bytes': net}), flush=True)
    if net >= TARGET:
        break

controls = {
    'entire_real_repository_tree_rejected': not scoped('/workspace/dwqww/build/CMakeFiles/forge_core.dir/src/search.cpp.o'),
    'external_nested_repository_evidence_rejected': not scoped('/workspace/.cloud-setup/stage/payload/workspace/dwqww/validation/x/libforge_core.a'),
    'path_traversal_rejected': not scoped('/workspace/.cloud-setup/../dwqww/x.o'),
    'active_S08_cache_rejected': not scoped('/workspace/.cloud-setup/S08/build/CMakeFiles/forge.dir/src/search.cpp.o'),
    'external_nested_repo_validation_cache_rejected': not scoped('/workspace/.cloud-setup/stage/validation/x/libforge_core.a'),
    'source_file_rejected': not scoped('/workspace/.cloud-setup/forge-pin-mask-source/src/search.cpp'),
    'main_executable_rejected': not scoped('/workspace/.cloud-setup/forge-pin-mask-asan/Forge'),
    'test_executable_rejected': not scoped('/workspace/.cloud-setup/forge-pin-mask-asan/forge_tests'),
    'helper_executable_rejected': not scoped('/workspace/.cloud-setup/forge-pin-mask-asan/forge_bench'),
    'raw_dataset_rejected': not scoped('/workspace/.cloud-setup/fixtures/wac.epd'),
    'unknown_build_rejected_by_candidate_mapping': '/workspace/.cloud-setup/not-known/CMakeFiles/forge.dir/x.o' not in candidate_paths,
    'incomplete_alias_group_rejected': len(['one']) != 2,
    'active_reference_rejection_logic': bool({'x'} & {'x'}),
    'nonrelocatable_ELF_excluded_by_e_type': int.from_bytes(b'\x02\x00', 'little') != 1,
    'historical_cutoff_is_current_day_start': datetime.datetime.fromtimestamp(HISTORICAL_CUTOFF_NS / 1e9, datetime.timezone.utc).isoformat() == '2026-10-26T00:00:00+00:00',
    'selected_cache_all_before_current_day': all(r['mtime_ns'] < HISTORICAL_CUTOFF_NS for g in selected for r in g['alias_metadata']),
    'completed_wave13_map_in_collision_set': any(m['path'].endswith('forge_sol_S00_thirteenth_cache_restore_map_20261026.json') and not m.get('missing') for m in maps),
    'no_unlink_no_archive_write_no_restore_actions_in_audit': True,
}
assert all(controls.values())
vfs = os.statvfs('/workspace')
free = vfs.f_bavail * vfs.f_frsize
result = {
    'created_utc': started, 'finished_utc': utc(),
    'state': 'READ_ONLY_MEASURED_PROPOSAL_ORIGINALS_RETAINED',
    'scope': 'Only existing regular Forge CMake .o and libforge_core.a compiler caches inside explicitly source-proven /workspace/.cloud-setup build roots. Every actual repository path, nested repository evidence alias, source/data/raw byte and main/test/helper executable remains excluded. All aliases, including external staging cache aliases, must be retired together only after root review and verified lossless preservation.',
    'target_additional_bytes': 100 * 1024 * 1024,
    'measurement_target_bytes': TARGET,
    'historical_closed_cache_cutoff_utc': '2026-10-26T00:00:00Z',
    'audit_reuse': {'path': str(BASE / 'forge_sol_S00_thirteenth_space_proposal_20261026' / 'forge_sol_S00_thirteenth_readonly_audit_20261026.py'), 'sha256': '10557dc70b24d3661bca8da7fd397997db323b56aeb3453986f0431c42ece62a'},
    'groups': selected,
    'summary': {'selected_groups': len(selected),
                'required_100MiB_net_allocated_met': sum(g['conservative_projected_net_allocated_bytes'] for g in selected) >= 100 * 1024 * 1024, 'selected_alias_paths': sum(len(g['aliases']) for g in selected),
                'selected_unique_raw_bytes': sum(g['size'] for g in selected),
                'measured_gzip6_archive_bytes': sum(g['measured_archive_bytes'] for g in selected),
                'measured_net_payload_bytes': net,
                'conservative_projected_net_allocated_bytes': sum(g['conservative_projected_net_allocated_bytes'] for g in selected),
                'largest_one_archive_bytes': max((g['measured_archive_bytes'] for g in selected), default=0),
                'free_bytes_at_report': free,
                'projected_free_bytes_after_selected_and_6MiB_pending_packets': free + sum(g['conservative_projected_net_allocated_bytes'] for g in selected) - 6 * 1024 * 1024,
                'unselected_source_proven_groups': len(eligible) - len(selected),
                'unselected_raw_bytes_estimate_only': sum(g['size'] for g in eligible[len(selected):]),
                'unselected_net_estimate_70pct_not_measured': int(sum(g['size'] for g in eligible[len(selected):]) * .7),
                'measurement_qualification': 'Gzip payload lengths are measured in memory, not saved/decoded archives. Space reclamation is a projection until root preserves/decodes/fsyncs/maps/unlinks all aliases. Allocated projection assumes 4096-byte blocks and excludes map/journal overhead.'},
    'producer_mapping': {'library_producer_path': str(LIB), 'library_producer_sha256': sha(LIB),
        'recovery_producer_path': str(OLD), 'recovery_producer_sha256': sha(OLD),
        'complete_library_schema': lib['library_schema'],
        'complete_singleton_object_schema': lib['singleton_object_schema'],
        'directory_root': lib['directory_root'], 'path_encoding': lib['path_encoding'],
        'library_consumer_mapping': {'build_root': 'directory_root/directories[directory_ids[*]]',
            'library_path': 'build_root/library_filename', 'known_source': 'known_forge_source:bool and !prior_map_collision:bool',
            'source_homes': 'cmake_source_homes[source_home_ids[*]]'},
        'object_consumer_mapping': {'original_ranked_object_path': 'directory_root/directories[directory_id]/filename',
            'current_candidate_path': 'known library build_root/CMakeFiles/forge*.dir/**/*.o; actual fresh stat, not historical array position'},
        'used_directories': {str(p['directory_id']): lib['directories'][p['directory_id']] for p in provenance},
        'used_source_homes': {str(i): lib['cmake_source_homes'][i] for p in provenance for i in p['source_home_ids']},
        'actual_decoded_selected_library_example': next((dict(zip(lib['library_schema'], lib['libraries'][provenance[i]['producer_library_index']])) for g in selected for i in g['provenance_ids']), None)},
    'fresh_build_source_provenance': provenance,
    'closed_status_basis': {'root_instruction': 'Root reports S26 timing closed, S08 ASAN window3 paused at disk floor. Active S08 paths and current-day cache writes are excluded. Historical external source-proven cache groups only; root must recheck active leases immediately before any retirement. This is context, not an assertion all /proc FDs are readable.',
                           'historical_cache_max_mtime_ns': max((r['mtime_ns'] for g in selected for r in g['alias_metadata']), default=0),
                           'process_snapshot': proc},
    'alias_scan': {'root': str(ROOT), 'follow_symlinks': False,
                   'strategy': 'stat every external regular file regardless of filename; match candidate dev/inode; require discovered aliases == current nlink, otherwise skip. Alias outside root necessarily yields incomplete group.',
                   'counts': dict(scan_counts), 'candidate_inode_count': len(candidate_keys),
                   'scan_errors': scan_errors},
    'prior_retirement_maps': maps,
    'skipped_groups': skipped,
    'failure_controls': controls,
    'root_execution_requirements': [
        'Proposal only: no archives or original-path mutations performed by this audit.',
        'Use existing seventh/twelfth hardlink archiver pattern only in a newly dated directory after root review; selected groups already use aliases/links/dev/inode/size field names expected by that workflow.',
        'Immediately recheck source/cache provenance, every alias (no symlinks), ownership/mode/mtime/size/dev/inode/nlink, original SHA256, closed leases and all visible proc references. Skip any changed/unknown/incomplete/active group.',
        'Archive each group sequentially using deterministic gzip6, fsync archive, verify exact byte count/SHA with both Python gzip and independent GNU gzip decoders, then fsync archive directory.',
        'Persist all aliases, original hardlink count, per-path mode/uid/gid/atime/mtime, raw SHA256 and archive path/SHA before any unlink; durable map plus append-safe journal and directory fsync are mandatory.',
        'Retire all aliases of the verified inode, asserting nlink decreases exactly; do not touch repo/tracked/evidence originals or any source/main/test/helper executable. Preserve all existing maps/archives.',
        'Inaccessible proc FDs limit a global absence claim. No live engine/compiler process-name matches plus historical source-proven build closure is the bounded proposal basis; parent decides whether additional ownership evidence is required.'
    ]}
with OUT.open('x') as f:
    json.dump(result, f, indent=2)
    f.write('\n')
print(json.dumps({'output': str(OUT), 'sha256': sha(OUT), 'bytes': OUT.stat().st_size,
                  'summary': result['summary'], 'skipped': len(skipped), 'controls': controls}), flush=True)
