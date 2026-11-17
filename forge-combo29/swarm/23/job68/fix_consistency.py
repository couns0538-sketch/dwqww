import io

p = 'consistency_check.py'
s = io.open(p, encoding='utf-8').read()

old = '''    # 2. corrected phrases appearing without a nearby correction marker
    for phrase, why in CORRECTED:
        for m in re.finditer(re.escape(phrase), text, re.I):
            ctx = text[max(0, m.start() - 220):m.start() + 220].lower()
            marked = any(k in ctx for k in ("refut", "supersed", "withdrawn", "retract", "correct", "not a",
                                            "wrong", "replaced", "does not hold"))
            if not marked:
                line = text[:m.start()].count("\\n") + 1
                problems.append((f, "line %d: %r unqualified — %s" % (line, phrase, why)))'''

new = '''    # 2. corrected phrases appearing without a nearby correction marker.
    # SCOPED after the first run produced 8 false positives: "0 info lines" is the CORRECT description of 19-F12 (the
    # abort path) and appears legitimately wherever that defect is discussed, and "scope limit" appears legitimately in
    # 23-F112's own row. A check that fires on correct usage teaches people to ignore it (23-F165), so each phrase now
    # carries an exemption list of contexts in which it is right.
    EXEMPT = {
        "0 info lines": ("19-f12", "23-f8", "23-f19", "quit", "eof", "abort", "fabricated", "a2a3", "per depth"),
        "zero info lines": ("19-f12", "23-f8", "quit", "eof", "abort", "per depth"),
        "scope limit": ("23-f112", "withdraw"),
    }
    for phrase, why in CORRECTED:
        for m in re.finditer(re.escape(phrase), text, re.I):
            ctx = text[max(0, m.start() - 300):m.start() + 300].lower()
            marked = any(k in ctx for k in ("refut", "supersed", "withdrawn", "retract", "correct", "not a",
                                            "wrong", "replaced", "does not hold"))
            exempt = any(k in ctx for k in EXEMPT.get(phrase, ()))
            if not marked and not exempt:
                line = text[:m.start()].count("\\n") + 1
                problems.append((f, "line %d: %r unqualified — %s" % (line, phrase, why)))'''

assert old in s
s = s.replace(old, new, 1)

# also normalise the en-dash/hyphen duplicate in the tracked figure
old2 = '''    for label, pat in TRACKED.items():
        vals = set()
        for m in re.finditer(pat, text):
            v = next((g for g in m.groups() if g), None)
            if v:
                vals.add(v.strip())'''
new2 = '''    for label, pat in TRACKED.items():
        vals = set()
        for m in re.finditer(pat, text):
            v = next((g for g in m.groups() if g), None)
            if v:
                # normalise en-dash to hyphen: the same range written two ways is not a contradiction
                vals.add(v.strip().replace("\\u2013", "-"))'''
assert old2 in s
s = s.replace(old2, new2, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print("scoped the phrase check and normalised dashes")
