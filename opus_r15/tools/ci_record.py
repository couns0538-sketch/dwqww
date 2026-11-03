#!/usr/bin/env python3
"""ci_record.py - Opus R15: tie a green sanitizer CI run to the exact patches the candidate exes were built from.

usage: python -I -B ci_record.py [--repo D:\\o15\\wt] [--branch opus-r15-20261103] [--run ID] [--root D:\\o15\\cands]
                                 [--evidence-dir D:\\o15\\wt\\opus_r15\\cands] [--dry-run]

Takes the given run (default: the newest COMPLETED opus-r15-san run of the branch), requires conclusion "success",
saves its per-config smoke lines to <evidence-dir>/ci_san_<run>.txt, and for every <root>/<name>/RESULT.json with a
patch: reads the patch file AT THE RUN'S COMMIT (git show <sha>:opus_r15/cands/<name>/<name>.patch) and writes
<root>/<name>/ci.json only when its sha256 equals the record's patch_sha256 (the CI tested exactly the built patch) and
the run's job for that item succeeded. Never overwrites a ci.json that names a newer run. Exit 0 = every candidate
recorded, 1 = a candidate could not be tied to this run (reason printed), 2 = no usable run.
"""
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys


def gh(repo, *args):
    r = subprocess.run(['gh', *args], cwd=repo, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)}: {r.stderr.strip()[:300]}")
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default=r'D:\o15\wt')
    ap.add_argument('--branch', default='opus-r15-20261103')
    ap.add_argument('--run', default='')
    ap.add_argument('--root', default=r'D:\o15\cands')
    ap.add_argument('--evidence-dir', default=r'D:\o15\wt\opus_r15\cands')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if a.run:
        run = json.loads(gh(a.repo, 'run', 'view', a.run, '--json', 'databaseId,headSha,conclusion,status,workflowName,jobs'))
    else:
        runs = json.loads(gh(a.repo, 'run', 'list', '--branch', a.branch, '--workflow', 'opus-r15-san', '--limit', '20',
                             '--json', 'databaseId,headSha,conclusion,status'))
        done = [r for r in runs if r['status'] == 'completed' and r['conclusion'] == 'success']
        if not done:
            print('ci_record: no completed successful opus-r15-san run on the branch', file=sys.stderr)
            return 2
        run = json.loads(gh(a.repo, 'run', 'view', str(done[0]['databaseId']), '--json',
                            'databaseId,headSha,conclusion,status,workflowName,jobs'))
    rid, sha = run['databaseId'], run['headSha']
    if run.get('conclusion') != 'success':
        print(f"ci_record: run {rid} conclusion {run.get('conclusion')} (need success)", file=sys.stderr)
        return 2
    jobs = {j['name']: j['conclusion'] for j in run.get('jobs', [])}
    log = gh(a.repo, 'run', 'view', str(rid), '--log')
    lines = [l.split('\t', 2)[-1] for l in log.splitlines() if '"config"' in l or 'SELFPLAY SMOKE' in l]
    lines = [l.split('Z ', 1)[-1] if 'Z ' in l[:40] else l for l in lines]
    ev = os.path.join(a.evidence_dir, f'ci_san_{rid}.txt')
    if not a.dry_run:
        with open(ev, 'w', newline='\n', encoding='utf-8') as f:
            f.write(f'# opus-r15-san run {rid} on {sha}: {len(lines)} lines\n' + '\n'.join(lines) + '\n')
    print(f'run {rid} on {sha[:12]}: {len(jobs)} jobs, {sum(1 for v in jobs.values() if v == "success")} success; '
          f'evidence {ev} ({len(lines)} lines)')
    bad = 0
    for path in sorted(glob.glob(os.path.join(a.root, '*', 'RESULT.json'))):
        r = json.load(open(path, encoding='utf-8-sig'))
        name = r.get('name')
        if not r.get('patch'):
            continue
        rel = f'opus_r15/cands/{name}/{name}.patch'
        g = subprocess.run(['git', '-C', a.repo, 'show', f'{sha}:{rel}'], capture_output=True)
        if g.returncode != 0:
            print(f'FAIL {name}: {rel} is not in commit {sha[:12]} (CI did not test it)')
            bad += 1
            continue
        ps = hashlib.sha256(g.stdout).hexdigest()
        if ps != r.get('patch_sha256', '').lower():
            print(f'FAIL {name}: the patch at {sha[:12]} ({ps[:16]}) is not the built one ({r.get("patch_sha256", "")[:16]})')
            bad += 1
            continue
        job = [k for k in jobs if k.startswith(f'san ({name},')]
        if not job or jobs[job[0]] != 'success':
            print(f'FAIL {name}: no successful job for this item in run {rid}')
            bad += 1
            continue
        cj = os.path.join(os.path.dirname(path), 'ci.json')
        if os.path.exists(cj):
            old = json.load(open(cj, encoding='utf-8-sig'))
            if int(old.get('run', 0)) > int(rid):
                print(f'KEEP {name}: ci.json names the newer run {old.get("run")}')
                continue
        rec = {'run': rid, 'conclusion': 'success', 'commit': sha, 'patch_sha256': ps, 'job': job[0],
               'workflow': 'opus-r15-san (ASan+UBSan self-play)', 'evidence': f'opus_r15/cands/ci_san_{rid}.txt'}
        if not a.dry_run:
            with open(cj, 'w', newline='\n') as f:
                json.dump(rec, f)
                f.write('\n')
        print(f'OK   {name}: run {rid} tested the built patch ({ps[:16]}...)')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
