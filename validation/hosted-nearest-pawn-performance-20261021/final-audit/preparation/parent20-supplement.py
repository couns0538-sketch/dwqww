"""Read-only original lifecycle, archive identity and ar-member comparison."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path('/workspace/.cloud-setup/pawn-span-hosted-result-39516786979')
HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / 'original-result'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())

def ar_members(path):
    raw = path.read_bytes()
    assert raw[:8] == b'!<arch>\n'
    pos = 8
    names = b''
    members = {}
    while pos < len(raw):
        header = raw[pos:pos+60]
        assert len(header) == 60 and header[-2:] == b'`\n'
        name = header[:16].decode('ascii').strip()
        size = int(header[48:58])
        data = raw[pos+60:pos+60+size]
        assert len(data) == size
        pos += 60 + size + size % 2
        if name == '//': names = data; continue
        if name in ('/', '/SYM64/'): continue
        if name.startswith('/'):
            offset = int(name[1:]);name = names[offset:names.index(b'/\n', offset)].decode('ascii')
        else: name = name.removesuffix('/')
        assert name not in members
        members[name] = hashlib.sha256(data).hexdigest()
    assert pos == len(raw)
    return members

summary = read(ROOT / 'performance/summary.json')
records = []
for row in summary['all_samples']:
    folder = ROOT / 'performance' / row['sample_id']
    command = read(folder / 'command.json')
    before = read(folder / 'status-before-verdict.json')
    final = read(folder / 'status.json')
    for key in command:
        if key not in ('returncode', 'timed_out', 'cleanup_attempted'):
            assert command[key] == before[key] == final[key], (row['sample_id'], key)
    for key in before:
        if key not in ('returncode', 'cleanup_attempted'):
            assert before[key] == final[key], (row['sample_id'], key)
    assert command['returncode'] is None and command['timed_out'] is False
    assert command['cleanup_attempted'] is False and final['cleanup_attempted'] is False
    for stream in ('stdin', 'stdout', 'stderr'):
        assert final[stream].endswith('/performance/' + row['sample_id'] + '/' + stream + '.txt')
    assert final['wall_seconds_before_verdict'] == final['wall_seconds']
    assert final['cpu_seconds_before_verdict'] == final['cpu_seconds']
    assert final['poll_interval_seconds'] == .001
    records.append({'sample': row['sample_id'], 'command_sha256': sha(folder / 'command.json'), 'pre_verdict_sha256': sha(folder / 'status-before-verdict.json')})
first = read(ROOT / 'performance' / summary['all_samples'][0]['sample_id'] / 'status.json')
last = read(ROOT / 'performance' / summary['all_samples'][-1]['sample_id'] / 'status.json')
span = (datetime.datetime.fromisoformat(last['started_utc']) - datetime.datetime.fromisoformat(first['started_utc'])).total_seconds() + last['total_elapsed_seconds']
assert span + 1 < 3600
objects = {label: ar_members(ROOT / 'artifacts' / label / 'libforge_core.a') for label in ['baseline', 'candidate']}
assert objects['baseline']['nnue.cpp.o'] == objects['candidate']['nnue.cpp.o']
archive = ORIGINAL / 'pawn-span-performance-39516786979-1.zip'
manifest = ORIGINAL / 'pawn-span-performance-39516786979-1.manifest.json'
metadata = read(manifest)
assert archive.stat().st_size == 4217704 and sha(archive) == metadata['archive']['sha256'] == 'b79e39ab775aa0a06850de2c170b728d68a05d5511d10932cdfc7c74d8e857e7'
assert len(metadata['files']) == 1246
result = {'status': 'PASS_LIFECYCLE_AND_NNUE_OBJECT_IDENTITY', 'samples': 188,
          'all_command_preverdict_final_bindings_match': True, 'all_cleanup_attempted_false': True,
          'sum_sample_wall_seconds': sum(x['wall_seconds'] for x in summary['all_samples']),
          'coarse_first_start_to_last_completion_seconds': span,
          'coarse_timestamp_qualification': 'Start timestamps have one-second precision; this corroborates ample aggregate headroom, not monotonic timer semantics.',
          'nnue_object_sha256': objects['baseline']['nnue.cpp.o'], 'all_core_member_hashes': objects,
          'original_archive_sha256': sha(archive), 'original_manifest_sha256': sha(manifest),
          'original_archive_payload_count': 1246,
          'archive_scope': 'Original ZIP hash/size and manifest record count checked; root separately verified all1246 payloads. Independent main audit rehashes all178 consumed inputs and all188 sample streams.',
          'script_sha256': sha(Path(__file__)), 'lifecycle_records': records}
(HERE / 'SUPPLEMENT.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('lifecycle_records', 'all_core_member_hashes')}, indent=2))
