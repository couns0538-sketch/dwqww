#!/usr/bin/env python3
"""opus_promote_export.py - turn the staged guard-band candidate into the training export (R14 finish; own code).

NOT run by the R14 finish: the Job 3 proof is UNVERIFIED (authentic game IDs missing; the npt-data-holdout-check
audit returns UNVERIFIED for null game IDs). Couns decides whether the guard-band evidence is enough; this is the
one command for that decision:
  D:\\a14\\runtime\\python\\python.exe -I -B D:\\a14\\tools\\opus_promote_export.py --confirm-owner-decision
      [--split D:/a14/sep/guardband01/SPLIT.json] [--proof D:/a14/sep/guardband01/PROOF.json] [--out D:/a14/export]
It refuses unless the proof's scoped checks are PASS and every staged file still has its SPLIT.json md5; it copies
(never moves) train.txt / val.txt / *.rowids into --out (refused if it exists) and writes MANIFEST.json: rows per
split, White-result counts, score histogram, md5 + sha256 of every file, the SPLIT / PROOF md5s, the proof's audit
status and "authentic_game_ids": "UNVERIFIED". Mate rows are already excluded (|score| >= 30000); old440k is not
part of jobA.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys


def digests(path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 22), b''):
            md5.update(block)
            sha.update(block)
    return md5.hexdigest(), sha.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--split', default='D:/a14/sep/guardband01/SPLIT.json')
    ap.add_argument('--proof', default='D:/a14/sep/guardband01/PROOF.json')
    ap.add_argument('--out', default='D:/a14/export')
    ap.add_argument('--confirm-owner-decision', action='store_true')
    a = ap.parse_args()
    if not a.confirm_owner_decision:
        sys.exit('refusing: the export needs the owner\'s decision (--confirm-owner-decision); see GUARDBAND_SEPARATION.json')
    split = json.load(open(a.split, encoding='utf-8'))
    proof = json.load(open(a.proof, encoding='utf-8'))
    if proof.get('scoped_checks') != 'PASS' or proof.get('problems'):
        sys.exit('refusing: the proof\'s scoped checks are not PASS')
    if proof['split']['md5'] != digests(a.split)[0]:
        sys.exit('refusing: SPLIT.json changed after the proof')
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    files = {}
    for side in ('train', 'val'):
        for kind, item in split['staged'][side].items():
            md5, sha = digests(item['path'])
            if md5 != item['md5']:
                sys.exit(f'refusing: staged {side}.{kind} changed after the split')
            files[f'{side}.{kind}'] = (item['path'], md5, sha)
    os.makedirs(a.out)
    manifest = dict(schema=1, tool='opus_promote_export.py', source='jobA guard-band split (sep/guardband01)',
                    authentic_game_ids='UNVERIFIED', proof_audit_status=proof.get('audit_status'),
                    owner_decision='export promoted by explicit --confirm-owner-decision',
                    split=dict(path=a.split, md5=digests(a.split)[0]), proof=dict(path=a.proof, md5=digests(a.proof)[0]),
                    rows=split['retained'], stats=split['stats'], exclusions=['mate rows |score| >= 30000', 'old440k'],
                    format='FEN | score (side to move, 20k-node relabel) | White result', files={})
    for name, (src, md5, sha) in files.items():
        dst = os.path.join(a.out, name)
        shutil.copyfile(src, dst)
        if digests(dst) != (md5, sha):
            sys.exit(f'copy of {name} does not match its source')
        manifest['files'][name] = dict(path=dst, bytes=os.path.getsize(dst), md5=md5, sha256=sha)
    with open(os.path.join(a.out, 'MANIFEST.json'), 'x', encoding='utf-8', newline='\n') as stream:
        json.dump(manifest, stream, indent=1)
    print(f'export written to {a.out} (MANIFEST.json)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
