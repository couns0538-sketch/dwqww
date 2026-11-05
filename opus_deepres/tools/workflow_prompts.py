#!/usr/bin/env python3
"""workflow_prompts.py - save the exact task text each workflow agent received (for audit and resume).

usage: python -I -B workflow_prompts.py <workflow transcript dir> <out dir>
Reads agent-*.meta.json (label) and the agent's transcript (the "computed task" user message = the script's prompt)
and writes <out dir>/<label>.md with that text. Refuses to overwrite an existing file.
"""
import glob
import json
import os
import sys


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for meta in sorted(glob.glob(os.path.join(src, 'agent-*.meta.json'))):
        label = json.load(open(meta, encoding='utf-8')).get('description', 'unknown').replace(':', '_')
        tr = meta.replace('.meta.json', '.jsonl')
        task = None
        for line in open(tr, encoding='utf-8'):
            d = json.loads(line)
            m = d.get('message') or {}
            c = m.get('content')
            if m.get('role') == 'user' and isinstance(c, str) and 'computed task' in c[:200]:
                task = c
                break
        if task is None:
            print(f'{label}: no computed-task message found in {tr}')
            continue
        dst = os.path.join(out, f'{label}.md')
        if os.path.exists(dst):
            print(f'{label}: exists, kept {dst}')
            continue
        with open(dst, 'w', encoding='utf-8', newline='\n') as f:
            f.write(task.replace('\r\n', '\n'))
        print(f'{label}: {len(task)} chars -> {dst}')


if __name__ == '__main__':
    main()
