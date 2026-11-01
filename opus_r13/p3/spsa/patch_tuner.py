"""R13: patch the scratch copy of R9's r9_spsa.py so the fixed engine options come from the config (fixed_options)."""
p = 'C:/o13/p3/spsa_tool/r9_spsa.py'
s = open(p, 'rb').read().decode()
old = 'f"cmd={c[\'engine\']}", "option.R9Tune=true"] + \\'
assert s.count(old) == 1, 'anchor'
s = s.replace(old, 'f"cmd={c[\'engine\']}"] + list(c.get("fixed_options", ["option.R9Tune=true"])) + \\')
s = s.replace('"""R9: SPSA tuner', '"""R13 copy (fixed_options from the config instead of option.R9Tune=true; otherwise unchanged). R9: SPSA tuner', 1)
open(p, 'wb').write(s.encode())
print('tuner copy patched')
