"""Freeze an untouched actual-lock timing fixture; no engine execution. UNPROVEN."""
import hashlib
import json
import os
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetPriorityClass.argtypes = (ctypes.c_void_p, ctypes.c_ulong)
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x4000):
            raise ctypes.WinError(ctypes.get_last_error())
    root = Path(__file__).resolve().parent
    previous = root / 'evidence/final_smoke_openings'
    metadata = json.loads((previous / 'manifest.json').read_text(encoding='utf-8'))
    source = Path(metadata['source_path'])
    raw = source.read_bytes()
    assert digest(raw) == metadata['source_sha256'], 'Opening source changed'
    canonical = lambda fen: ' '.join(fen.split()[:4])
    training = {canonical(f) for f in metadata['training_fens']}
    calibration = {canonical(f) for f in metadata['calibration_fens']}
    earlier_raw = (previous / '8moves_final100.epd').read_bytes()
    assert digest(earlier_raw) == metadata['selected_sha256']
    earlier = {canonical(f) for f in earlier_raw.decode().splitlines() if f.strip()}
    excluded = training | calibration | earlier
    positions = {}
    for line in raw.decode('utf-8-sig').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        fields = line.split()
        assert len(fields) >= 4
        key = ' '.join(fields[:4])
        tail = ' '.join(fields[4:6]) if len(fields) >= 6 and all(x.isdigit() for x in fields[4:6]) else '0 1'
        positions.setdefault(key, key + ' ' + tail)
    seed = 2026110112
    eligible = [fen for key, fen in positions.items() if key not in excluded]
    selected = sorted(eligible, key=lambda fen: digest(f'{seed}\n{fen}'.encode()))[:100]
    selected_keys = {canonical(fen) for fen in selected}
    assert len(selected_keys) == 100 and not selected_keys & excluded
    data = ('\n'.join(selected) + '\n').encode('ascii')
    output = root / 'evidence/lock_smoke_openings'
    output.mkdir(exist_ok=False)
    (output / '8moves_lock100.epd').write_bytes(data)
    record = dict(strength='UNPROVEN', purpose='Actual-lock qualification; fresh openings after the base port',
                  source_path=str(source), source_sha256=digest(raw), source_unique_fens=len(positions),
                  seed=seed, selected_fens=100, selected_sha256=digest(data),
                  excluded_training=len(training), excluded_calibration=len(calibration),
                  excluded_previous_smoke=len(earlier), excluded_union=len(excluded),
                  eligible_unique_fens=len(eligible), intersections_with_exclusions=0,
                  previous_smoke_fixture_sha256=digest(earlier_raw),
                  generator_sha256=digest(Path(__file__).read_bytes()),
                  mapping_frozen=dict(a=742,b=3000,lo=650,hi=1750),
                  baseline='294dbed3a15dfd821aaf9d4edc6e5f62832fd460',
                  patch_sha256=digest((root / 'tmfit-lock.patch').read_bytes()),
                  canonicalization='first four FEN fields',
                  ordering='SHA256(str(seed)+newline+full FEN), ascending; first100',
                  note='No parameter changed after the earlier fallback smoke outcome.')
    (output / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
