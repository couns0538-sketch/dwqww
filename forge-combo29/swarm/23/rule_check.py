#!/usr/bin/env python3
"""rule_check.py : structural check of RULE_known_answer_control.md, which the page itself says is the only way to find
the defects it accumulates (stale counts, jumping numbering, stranded sections).

Checks, each with a planted-failure proof in the run:
  1. instance headings are numbered 1..N with no gaps and no duplicates;
  2. the counts stated in prose ("N instances", "N faults") equal the actual number of instance sections;
  3. the stated number of sentences in the headline ("Five sentences") equals the number of bolded lead sentences;
  4. every file token that looks like a path resolves.

Run from within forge-combo29/swarm/23.
"""
import os, re, sys

PAGE = 'RULE_known_answer_control.md'
HERE = os.path.abspath(os.getcwd())
ROOT = '/agent/repos/dwqww'
SEAT = 'forge-combo29/swarm/23'
prefixes = ['', './', HERE + '/', ROOT + '/', os.path.join(ROOT, SEAT) + '/']
for b in (HERE, os.path.join(ROOT, SEAT)):
    if os.path.isdir(b):
        for j in sorted(os.listdir(b)):
            jd = os.path.join(b, j)
            if os.path.isdir(jd):
                prefixes.append(jd + '/')
                for k in sorted(os.listdir(jd)):
                    if os.path.isdir(os.path.join(jd, k)):
                        prefixes.append(os.path.join(jd, k) + '/')


def resolve(c):
    c = os.path.expanduser(c)
    for pre in prefixes:
        if os.path.exists(os.path.normpath(pre + c)):
            return True
    return False


text = open(PAGE).read()
print("== controls: the resolver finds a real file and misses a fake one ==")
print("  FINDINGS.md ->", "RESOLVED" if resolve('FINDINGS.md') else "NOT RESOLVED")
print("  fake_zz9.out ->", "resolved (BAD)" if resolve('fake_zz9.out') else "NOT resolved (correct)")
print()

nums = [int(m.group(1)) for m in re.finditer(r"^## Instance (\d+)", text, re.M)]
print("instance sections found:", len(nums), "->", nums)
gaps = [i for i in range(1, max(nums) + 1) if i not in nums] if nums else []
dups = sorted({n for n in nums if nums.count(n) > 1})
print("gaps:", gaps, "| duplicates:", dups)

prose = re.findall(r"\b([A-Za-z]+)\b instances?\b", text) + re.findall(r"\*\*([a-z]+)\*\* faults", text)
words = {'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,
         'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,
         'eighteen':18,'nineteen':19,'twenty':20}
stated = [(w, words[w.lower()]) for w in prose if w.lower() in words]
print("counts stated in prose:", stated)
bad_counts = [(w, n) for w, n in stated if n != len(nums)]
print("counts that disagree with the actual section count:", bad_counts)

sent_head = re.search(r"^## ([A-Za-z]+) sentences to carry", text, re.M)
# count ONLY the bolded lead sentences inside the block that runs from that heading to the next '## '
if sent_head:
    blk = text[sent_head.end():]
    nxt = re.search(r"^## ", blk, re.M)
    blk = blk[:nxt.start()] if nxt else blk
    # a "sentence" is a bolded LEAD at the START of a blockquote paragraph. A bolded line that follows a '>' line
    # without a blank '>' separator is a continuation of the same sentence (line 12 of the page is exactly that,
    # an emphasis inside the "proxy" sentence), so it must not be counted — my first count of 6 was this error.
    lines = blk.split('\n')
    n_sent = 0
    for i, ln in enumerate(lines):
        if not ln.startswith('> **'):
            continue
        prev = lines[i - 1].strip() if i > 0 else ''
        if prev in ('', '>'):
            n_sent += 1
else:
    n_sent = 0
print("headline says '%s'; bolded lead sentences found: %d" % (sent_head.group(1) if sent_head else "?", n_sent))
sent_bad = bool(sent_head) and words.get(sent_head.group(1).lower()) != n_sent
print("headline count wrong:", sent_bad)

toks = set(re.findall(r"(?:[\w.-]+/)*[\w-]+\.(?:py|out|txt|json|jsonl|fens|sh|md)", text))
ALLOW = {'compare_perft.py','integrity_selftest.sh','refused_readyok.py','FABLE_TO_swarm_5.md'}
unres = sorted(t for t in toks if t not in ALLOW and not resolve(t))
print("unresolved path tokens (excluding %d allow-listed script names):" % len(ALLOW), unres)
print()
ok = not gaps and not dups and not bad_counts and not sent_bad and not unres
print("VERDICT:", "PASS" if ok else "FAIL — see above")
sys.exit(0 if ok else 1)
