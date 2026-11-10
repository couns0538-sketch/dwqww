# cand.py - one candidate = one patch against the frozen baseline (ruling R5 of the approved plan).
#   prepare NAME : out\work\NAME\a = copy of the clone's forge-combo29 include + src (baseline), ...\b = copy to edit
#   patch NAME   : unified diff a -> b, written to fable_cpu_speed\patches\NAME.patch
#   verify NAME  : inside the clone: git apply --check; git apply; copy the patched include + src to ...\p;
#                  git apply -R; confirm the clone equals the lock commit again and that p equals b byte for byte.
# Builds use ...\p only, so every build is literally "lock commit + this patch". Nothing patched is committed.
import argparse
import difflib
import hashlib
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402

SRC = U.REPO + r'\forge-combo29'
WORK = U.JOB + r'\out\work'
PATCHES = U.REPO + r'\fable_cpu_speed\patches'
GIT = r'C:\Program Files\Git\cmd\git.exe'
BASE_MANIFEST = '3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645'


def rel_files(root):
    out = []
    for top in ('include', 'src'):
        for d, _dirs, files in os.walk(os.path.join(root, top)):
            for f in files:
                out.append(os.path.relpath(os.path.join(d, f), root).replace('\\', '/'))
    return sorted(out)       # ordinal order, as in QA's manifest


def manifest_sha(root):
    text = ''.join('%s  %s\n' % (hashlib.sha256(open(os.path.join(root, r), 'rb').read()).hexdigest(), r) for r in rel_files(root))
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def git(args):
    env = dict(os.environ)
    env.update(GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
    p = U.spawn([GIT] + args, U.self_affinity(), cwd=U.REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    so, se = p.communicate()
    return p.returncode, so.decode('utf-8', 'replace').strip(), se.decode('utf-8', 'replace').strip()


def copy_tree(src, dst):
    for top in ('include', 'src'):
        shutil.copytree(os.path.join(src, top), os.path.join(dst, top))


def prepare(a):
    root = os.path.join(WORK, a.name)
    if os.path.exists(root):
        raise SystemExit('refusing: %s exists' % root)
    m = manifest_sha(SRC)
    if m != BASE_MANIFEST:
        raise SystemExit('the clone is not the lock source (manifest %s)' % m)
    copy_tree(SRC, os.path.join(root, 'a'))
    copy_tree(SRC, os.path.join(root, 'b'))
    print('prepared %s (a = baseline, b = to edit); baseline manifest %s' % (root, m))
    return 0


def patch(a):
    root = os.path.join(WORK, a.name)
    ra, rb = os.path.join(root, 'a'), os.path.join(root, 'b')
    if manifest_sha(ra) != BASE_MANIFEST:
        raise SystemExit('work copy a is not the baseline any more')
    out = []
    for r in sorted(set(rel_files(ra)) | set(rel_files(rb))):
        pa, pb = os.path.join(ra, r), os.path.join(rb, r)
        da = open(pa, 'rb').read() if os.path.exists(pa) else b''
        db = open(pb, 'rb').read() if os.path.exists(pb) else b''
        if da == db:
            continue
        for d in (da, db):
            if d and (not d.endswith(b'\n') or b'\r' in d):
                raise SystemExit('%s: needs LF line ends and a final newline for this simple diff writer' % r)
        la = da.decode('latin-1').splitlines(keepends=True)
        lb = db.decode('latin-1').splitlines(keepends=True)
        out.extend(difflib.unified_diff(la, lb, 'a/forge-combo29/' + r, 'b/forge-combo29/' + r, n=3))
    if not out:
        raise SystemExit('a and b are identical: no patch')
    os.makedirs(PATCHES, exist_ok=True)
    pf = os.path.join(PATCHES, a.name + '.patch')
    with open(pf, 'w', encoding='latin-1', newline='') as f:
        f.write(''.join(out))
    print('wrote %s (%d bytes, md5 %s)' % (pf, os.path.getsize(pf), U.hashes(pf)[0]))
    return 0


def verify(a):
    root = os.path.join(WORK, a.name)
    pf = os.path.join(PATCHES, a.name + '.patch')
    rp = os.path.join(root, 'p')
    if os.path.exists(rp):
        raise SystemExit('refusing: %s exists (a changed patch needs a new candidate name)' % rp)
    md5, sha = U.hashes(pf)
    L = U.header('PATCH APPLY PROOF %s' % a.name, [os.path.abspath(__file__), U.__file__], [], [
        'patch %s bytes %d md5 %s sha256 %s' % (pf, os.path.getsize(pf), md5, sha),
        'base: clone at HEAD-tree of %s, folder forge-combo29' % U.SOURCE_REV])
    bad = []

    def check(what, ok, detail=''):
        L.append('%s  %s %s' % ('OK  ' if ok else 'DIFF', what, detail))
        if not ok:
            bad.append(what)

    rc, so, _ = git(['status', '--porcelain', '--', 'forge-combo29'])
    check('clone has no change under forge-combo29 before the test', rc == 0 and so == '')
    rc, so, _ = git(['diff', '--quiet', U.SOURCE_REV, '--', 'forge-combo29'])
    check('git diff --quiet %s -- forge-combo29 (work tree equals the lock commit)' % U.SOURCE_REV[:8], rc == 0)
    check('clone source manifest equals the lock receipt', manifest_sha(SRC) == BASE_MANIFEST)
    rel = os.path.relpath(pf, U.REPO).replace('\\', '/')
    rc, so, se = git(['apply', '--check', '--verbose', rel])
    check('git apply --check', rc == 0, '| ' + (se or so).replace('\n', ' | ')[:300])
    rc, so, se = git(['apply', '--numstat', rel])
    L.append('numstat: ' + so.replace('\n', ' | '))
    applied = False
    if not bad:
        rc, so, se = git(['apply', rel])
        applied = (rc == 0)
        check('git apply', applied, se[:200])
        if applied:
            try:
                copy_tree(SRC, rp)
            finally:
                rc, so, se = git(['apply', '-R', rel])
                check('git apply -R (clone restored)', rc == 0, se[:200])
    rc, so, _ = git(['status', '--porcelain', '--', 'forge-combo29'])
    check('clone has no change under forge-combo29 after the test', rc == 0 and so == '')
    check('clone source manifest equals the lock receipt after the test', manifest_sha(SRC) == BASE_MANIFEST)
    if applied:
        rb = os.path.join(root, 'b')
        fa, fb = rel_files(rp), rel_files(rb)
        same = (fa == fb) and all(open(os.path.join(rp, r), 'rb').read() == open(os.path.join(rb, r), 'rb').read() for r in fa)
        check('patched tree p equals the edited tree b byte for byte (%d files)' % len(fa), same)
        L.append('patched tree %s manifest sha256 %s' % (rp, manifest_sha(rp)))
    L.append('VERDICT PATCH %s; end %s' % ('PASS' if (applied and not bad) else 'FAIL', U.vienna_now()))
    U.write_log(os.path.join(U.LOGS, 'patch_%s_apply.log' % a.name), L)
    print('\n'.join(L))
    return 0 if (applied and not bad) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['prepare', 'patch', 'verify'])
    ap.add_argument('name')
    a = ap.parse_args()
    U.require_lane()
    return {'prepare': prepare, 'patch': patch, 'verify': verify}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
