#!/usr/bin/env python3
"""test_cleanroom_lint.py OUT_DIR - self-test of cleanroom_lint.py with planted bad patches and messages.

The planted names are taken from the tool's own encoded lists at run time, so this file carries no names either.
Exit 0 = every case as expected.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cleanroom_lint as cl  # noqa: E402

out = sys.argv[1]
if os.path.exists(out):
    sys.exit(f'refusing existing {out}')
os.makedirs(out)
name0 = cl.terms(cl.NAMES_B64)[0]
lic0 = cl.terms(cl.LICENCE_B64)[0]
HDR = 'diff --git a/src/search.cpp b/src/search.cpp\n--- a/src/search.cpp\n+++ b/src/search.cpp\n@@ -1,2 +1,3 @@\n'


def write(name, text, binary=False):
    p = os.path.join(out, name)
    with open(p, 'wb') as f:
        f.write(text if binary else text.encode('utf-8'))
    return p


cases = [
    ('clean_patch', ['--patch', write('clean.patch', HDR + ' int a = 0;\n+int b = 1; // own idea\n')], 0),
    ('word_inside_other_word', ['--patch', write('egypt.patch', HDR + '+// the egypt / regpt words are not names\n')], 0),
    ('name_in_comment', ['--patch', write('name.patch', HDR + f'+// idea from {name0.title()}\n')], 1),
    ('licence_header', ['--patch', write('lic.patch', HDR + f'+// {lic0.title()} 2026 somebody\n')], 1),
    ('license_file', ['--patch', write('licfile.patch', 'diff --git a/LICENSE b/LICENSE\n--- a/LICENSE\n+++ b/LICENSE\n@@ -1 +1 @@\n-x\n+y\n')], 1),
    ('openings_file', ['--patch', write('open.patch', 'diff --git a/tools/openings/a.epd b/tools/openings/a.epd\n--- a/tools/openings/a.epd\n+++ b/tools/openings/a.epd\n@@ -1 +1 @@\n-x\n+y\n')], 1),
    ('id_author', ['--patch', write('author.patch', 'diff --git a/src/uci.cpp b/src/uci.cpp\n--- a/src/uci.cpp\n+++ b/src/uci.cpp\n@@ -1 +1 @@\n-  "id author X\\n"\n+  "id author Y\\n"\n')], 1),
    ('crlf_patch', ['--patch', write('crlf.patch', (HDR + '+int b = 1;\n').replace('\n', '\r\n'))], 1),
    ('non_ascii', ['--patch', write('utf.patch', HDR + '+// café\n')], 1),
    ('not_a_patch', ['--patch', write('none.patch', 'just text\n')], 1),
    ('message_with_name', ['--message-file', write('msg.txt', f'R15: tuned like {name0}\n')], 1),
    ('message_clean', ['--message-file', write('msg_ok.txt', 'R15: candidate C1 - pruning depth uses the LMR history term\n')], 0),
    ('nothing_to_check', [], 2),
    ('missing_patch', ['--patch', os.path.join(out, 'no_such.patch')], 2),
]
real = os.path.join(os.path.dirname(HERE), 'cands', 'c1_prunelmrhist', 'c1_prunelmrhist.patch')
if os.path.exists(real):
    cases.append(('real_c1_patch', ['--patch', real], 0))
fails = 0
for name, args, want in cases:
    r = subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'cleanroom_lint.py')] + args,
                       capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or [''])[-1]
    if r.returncode == want:
        print(f'PASS {name} (exit {r.returncode}): {last[:110]}')
    else:
        fails += 1
        print(f'FAIL {name}: exit {r.returncode}, want {want}: {r.stdout.strip()[:200]} {r.stderr.strip()[:200]}')
print(f'{len(cases) - fails} / {len(cases)} cases as expected')
print('ALL PASS' if fails == 0 else f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
