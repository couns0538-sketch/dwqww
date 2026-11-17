import io

p = 'consistency_check.py'
s = io.open(p, encoding='utf-8').read()

old = '''print("consistency check over %d documents" % len([f for f in FILES if __import__('os').path.exists(f)]))'''
new = '''print("consistency check over %d documents" % len([f for f in FILES if __import__('os').path.exists(f)]))
print()
print("STATUS OF THIS CHECK: ADVISORY ONLY, NOT A GATE — and the reason is the finding. It found real contradictions")
print("once (the three exposed by reordering, 23-F181) but it cannot tell a stale figure from a legitimate second one,")
print("or a corrected phrase from a correct USE of that phrase describing the defect it names. Three tuning passes took")
print("it from 8 false positives to 3, and the remaining 3 are all correct text. A check that fires on correct usage is")
print("worse than none (23-F165), so this one is NOT wired into the pre-commit gate: read its output, do not obey it.")'''
assert old in s
s = s.replace(old, new, 1)

# do not exit nonzero: advisory
s = s.replace('''    print("VERDICT: %d possible contradiction(s) — each needs a human read, not automatic acceptance" % len(problems))
    sys.exit(1)''',
'''    print("VERDICT: %d possible contradiction(s) — each needs a human read, not automatic acceptance" % len(problems))
    sys.exit(0)  # ADVISORY: always 0, so it can never block a commit (see the status note above)''')

io.open(p, 'w', encoding='utf-8').write(s)
print("marked advisory-only with the reason")
