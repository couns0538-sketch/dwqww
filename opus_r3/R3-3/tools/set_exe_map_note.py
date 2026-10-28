"""Set the provenance note of exe_map.json (written as a file to avoid shell backslash mangling).

Usage: python -I -B set_exe_map_note.py <exe_map.json>
"""
import json
import sys

p = sys.argv[1]
m = json.load(open(p, encoding='utf-8'))
m['note'] = (r"Filled by tools/fill_exe_map.py from the main session's final F:\opus_scratch\r3\exe\EXES.txt "
             r"(copy: pc_copies/EXES_final_330237f3.txt), all built from opus-r3-stack 330237f3 (contains the HardDeadline "
             r"fix 5792074a and the S-A2/S-A4 merges); forge_r3_stack.exe is a byte copy of forge_r3_base.exe; h512 stays "
             r"null (no H512 net). An earlier set built from c3d774d2 (21:25-21:33) was superseded.")
with open(p, 'w', newline='\n', encoding='utf-8') as fh:
    fh.write(json.dumps(m, indent=1) + '\n')
assert '\r' not in open(p, encoding='utf-8', newline='').read()
print(m['note'])
