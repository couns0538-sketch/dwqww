#!/usr/bin/env python3
"""Read-only verification of completed Forge filter/relabel output folders.

IDEA_SOURCE: this project's FPOS/FHCE format and summary-last publication contract.
A PASS verifies retained bytes and declared accounting, not teacher quality or Elo.
The manifest and its identical optional .pending hard link cannot self-hash;
all other regular files must be covered, including any pending summary receipt.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path, PureWindowsPath
import re
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate JSON object key: '+key)
        value[key] = item
    return value


def read_json(path):
    with path.open(encoding='utf8') as source:
        return json.load(source, object_pairs_hook=_unique_object,
                         parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON number')))


def relative_name(name):
    require(isinstance(name, str) and bool(name), 'manifest path must be nonempty text')
    require(not PureWindowsPath(name).drive and not name.startswith(('/', '\\')),
            'absolute/drive manifest path rejected: '+name)
    require(not any(ord(c) < 32 for c in name), 'control character in manifest path')
    parts = name.replace('\\', '/').split('/')
    require(all(p not in ('', '.', '..') and ':' not in p for p in parts),
            'unsafe relative manifest path: '+name)
    return '/'.join(parts)


def safe_file(root, name):
    relative = relative_name(name)
    path = root.joinpath(*relative.split('/'))
    resolved = path.resolve(strict=True)
    require(resolved.is_relative_to(root), 'symlink escapes bundle: '+relative)
    require(resolved.is_file(), 'bundle entry is not a file: '+relative)
    return path


def digest(path):
    sha = hashlib.sha256(); md5 = hashlib.md5(); size = 0
    with path.open('rb') as source:
        for block in iter(lambda: source.read(4*1024*1024), b''):
            size += len(block); sha.update(block); md5.update(block)
    return {'sha256': sha.hexdigest(), 'md5': md5.hexdigest(), 'bytes': size}


def _count(value, name):
    require(type(value) is int and value >= 0, 'invalid nonnegative count: '+name)
    return value


def _verify_digest(value, actual, name):
    if isinstance(value, str):
        require(re.fullmatch(r'[0-9a-fA-F]{64}', value) is not None, 'invalid SHA256: '+name)
        require(value.lower() == actual['sha256'], 'SHA256 mismatch: '+name)
    else:
        require(isinstance(value, dict), 'invalid manifest metadata: '+name)
        for field, width in (('sha256',64), ('md5',32)):
            expected = value.get(field)
            require(isinstance(expected,str) and re.fullmatch('[0-9a-fA-F]{'+str(width)+'}',expected) is not None,
                    'invalid '+field+': '+name)
            require(expected.lower()==actual[field], field+' mismatch: '+name)
        require(_count(value.get('bytes'),name+' bytes')==actual['bytes'], 'byte count mismatch: '+name)


def check_bundle(folder: Path, *, full_records=False):
    from forge_pos import PosReader, aligned_records
    root = Path(folder).resolve(strict=True)
    require(root.is_dir(), 'bundle must be a directory')
    require(not (root/'failure.json').exists() and not (root/'failure.json').is_symlink(),
            'failure.json present: run is not accepted')
    summary = read_json(safe_file(root,'summary.json'))
    progress = read_json(safe_file(root,'progress.json'))
    require(isinstance(summary,dict) and summary.get('status')=='SEALED', 'summary is not SEALED')
    require(summary==progress, 'summary/progress differ')
    manifest_path = safe_file(root,'manifest.json')
    manifest = read_json(manifest_path)
    require(isinstance(manifest,dict) and bool(manifest), 'manifest must be a nonempty mapping')
    entries = {}; measured = {}
    for supplied_name, expected in manifest.items():
        name = relative_name(supplied_name)
        require(name not in entries, 'duplicate normalized manifest path: '+name)
        require(name not in ('manifest.json','manifest.json.pending'), 'manifest cannot self-hash')
        entries[name] = expected
        actual = digest(safe_file(root,name)); _verify_digest(expected,actual,name)
        measured[name] = actual
    for receipt in ('summary.json','progress.json'):
        require(receipt in entries, 'manifest does not cover '+receipt)
    if 'summary.json.pending' in measured:
        require(measured['summary.json.pending']==measured['summary.json'],
                'pending summary differs from committed summary')
    for path in root.rglob('*'):
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            require(path.resolve(strict=True).is_relative_to(root), 'symlink escapes bundle: '+name)
        if path.is_file():
            require(name in entries or name in ('manifest.json','manifest.json.pending'),
                    'unmanifested file: '+name)
    pending = root/'manifest.json.pending'
    if pending.exists() or pending.is_symlink():
        require(digest(safe_file(root,'manifest.json.pending'))==digest(manifest_path),
                'pending manifest differs from committed manifest')
    config = summary.get('config')
    require(isinstance(config,dict), 'missing configuration receipt')
    stem = config.get('stem')
    require(isinstance(stem,str) and '/' not in relative_name(stem), 'invalid output stem')
    is_filter = 'kept' in summary and 'input_rows' in summary
    is_relabel = 'selected' in summary
    require(is_filter != is_relabel, 'unknown/ambiguous filter or relabel summary')
    count = _count(summary['kept' if is_filter else 'selected'], 'output rows')
    outputs = summary.get('output' if is_filter else 'outputs')
    require(isinstance(outputs,dict), 'missing output hashes')
    names = {suffix:stem+suffix for suffix in ('.pos','.hce','.fen')}
    for suffix,name in names.items():
        require(name in entries, 'manifest does not cover output: '+name)
        require(suffix in outputs, 'summary does not cover output: '+suffix)
        _verify_digest(outputs[suffix],measured[name],name+' summary')
    overlap = None
    if is_filter:
        original = _count(summary['input_rows'],'input_rows')
        rules = summary.get('rules'); require(isinstance(rules,dict) and bool(rules), 'missing filter rules')
        order = summary.get('policy_order')
        require(isinstance(order,list) and all(isinstance(name,str) for name in order) and
                len(order)==len(rules) and set(order)==set(rules), 'invalid/missing filter policy_order')
        remaining = original
        for name in order:
            rule = rules[name]
            require(isinstance(rule,dict), 'invalid filter rule: '+name)
            eligible = _count(rule.get('eligible'),name+' eligible')
            n = _count(rule.get('dropped'),name+' dropped')
            require(n <= eligible <= original, 'invalid waterfall bounds: '+name)
            require(eligible==remaining, 'ordered waterfall eligibility mismatch: '+name)
            remaining -= n
            if 'not_evaluated_after_earlier_rule' in rule:
                require(_count(rule['not_evaluated_after_earlier_rule'],name+' not evaluated')==original-eligible,
                        'ordered waterfall not-evaluated mismatch: '+name)
            for field,denominator in (('fraction_input',original),('fraction_eligible',eligible)):
                if field not in rule: continue
                value = rule[field]
                expected = n/denominator if denominator else (0.0 if field=='fraction_input' else None)
                require((value is None and expected is None) or
                        (expected is not None and type(value) in (int,float) and math.isfinite(value) and
                         math.isclose(value,expected,rel_tol=1e-12,abs_tol=1e-12)),
                        'waterfall fraction mismatch: '+name+' '+field)
        require(count==remaining, 'filter kept+dropped differs from input_rows')
        queries = _count(summary.get('native_queries'),'native_queries')
        require(queries>=count, 'native queries fewer than kept rows')
        if 'in_check' in rules and 'speculative_native_queries_not_used' in summary:
            extra = _count(summary['speculative_native_queries_not_used'],'speculative native queries')
            require(queries==rules['in_check']['eligible']+extra, 'native query eligibility/speculation mismatch')
        overlap = summary.get('supplied_holdout_position_overlap')
        if overlap is not None or config.get('holdouts'):
            require(type(overlap) is int and overlap==0, 'supplied holdout overlap is not verified zero')
    elif 'count' in config:
        require(_count(config['count'],'requested slice count')==count, 'relabel selected differs from requested count')
    record_rows = 0
    with PosReader(safe_file(root,names['.pos']),safe_file(root,names['.hce'])) as reader:
        require(reader.n==count, 'POS/HCE header count differs from summary')
        if full_records:
            for _ in aligned_records(reader,safe_file(root,names['.fen']),sidecar_format='fen'):
                record_rows += 1
            fen_lines = record_rows
        else:
            with safe_file(root,names['.fen']).open('rb') as sidecar:
                fen_lines = sum(1 for _ in sidecar)
        require(fen_lines==count, 'FEN line count differs from summary')
    receipts = sorted(name for name in entries if re.fullmatch(r'probe_logs/worker-[0-9]+/process\.json',name))
    require(bool(receipts), 'missing native process receipts')
    if 'workers' in config:
        require(type(config['workers']) is int and len(receipts)==config['workers'], 'native worker receipt count mismatch')
    total_requests = 0
    if is_filter:
        probe = summary.get('probe')
        require(isinstance(probe,dict), 'missing native binary receipt')
        binary = probe.get('sha256')
    else:
        binary = summary.get('probe_sha256')
    require(isinstance(binary,str) and re.fullmatch(r'[0-9a-fA-F]{64}',binary) is not None,
            'invalid native binary SHA256 receipt')
    for name in receipts:
        process = read_json(safe_file(root,name))
        require(isinstance(process,dict), 'invalid process receipt: '+name)
        require(type(process.get('returncode')) is int and process['returncode']==0, 'native process did not exit cleanly: '+name)
        require(process.get('binary_unchanged') is True, 'native binary changed: '+name)
        requests = _count(process.get('successful_requests'),name+' successful_requests')
        require(_count(process.get('response_count'),name+' response_count')==requests, 'native request/response count mismatch: '+name)
        if binary is not None:
            require(process.get('binary_sha256')==binary, 'native binary receipt differs from summary: '+name)
        total_requests += requests
    expected_requests = summary.get('native_queries') if is_filter else count
    require(_count(expected_requests,'native_queries')==total_requests, 'aggregate native request count mismatch')
    return {'status':'PASS','bundle':str(root),'kind':'filter' if is_filter else 'relabel',
            'manifest_files_verified':len(entries),'manifest_sha256':digest(manifest_path)['sha256'],
            'output_rows':count,'fen_lines':fen_lines,'full_records':bool(full_records),
            'records_and_fen_matches_verified':record_rows,'native_processes_verified':len(receipts),
            'native_requests_verified_from_receipts':total_requests,'supplied_holdout_position_overlap':overlap,
            'scope':('Hashes, sealed receipts, accounting, FPOS/FHCE headers and every record/FEN board+STM match.' if full_records else
                     'Hashes, sealed receipts, accounting, FPOS/FHCE headers and FEN line count. Record values and FEN board/STM matches NOT checked.'),
            'limitations':'Holdout overlap is checked as reported, not recomputed. No game-holdout, native-log semantic replay, legal-history, training-quality or Elo certification.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    parser.add_argument('--full-records',action='store_true')
    args=parser.parse_args(argv)
    try:
        result=check_bundle(args.folder,full_records=args.full_records)
    except (OSError,ValueError,TypeError,KeyError,RuntimeError) as error:
        print(json.dumps({'status':'FAIL','error_type':type(error).__name__,'error':str(error)},indent=2))
        return 1
    print(json.dumps(result,indent=2));return 0

if __name__=='__main__':
    raise SystemExit(main())
