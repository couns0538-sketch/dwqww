"""Direct package structure and local-link validation; no agent evaluation."""
from pathlib import Path
import re
from run_policy import Inputs, write_json, safe_path
import argparse

def validate(output):
    root=Path(__file__).resolve().parents[1]
    inputs=Inputs()
    packages=[]
    for name in ('relabel-data-qc','npt-data-holdout-check'):
        package=root/'.agents'/'skills'/name
        skill=package/'SKILL.md'
        text=inputs.get(skill).bytes().decode('utf-8')
        match=re.match(r'^---\nname: ([^\n]+)\ndescription: ([^\n]+)\n---\n',text.replace('\r\n','\n'))
        if not match or match[1]!=name or len(match[2])<30:
            raise ValueError('invalid skill frontmatter')
        links=[]
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
            if '://' in target:
                continue
            resolved=safe_path((package/target).resolve())
            if not resolved.is_file():
                raise ValueError('missing local link: '+target)
            inputs.get(resolved).digest()
            links.append(target)
        packages.append(dict(name=name,local_links=links,status='PASS'))
    examples=['tools/p5_qc.py','tools/qc_core.py','tools/run_policy.py','tests/test_p5_audit.py','tools/game_hash.py','tests/test_game_hash.py']
    for example in examples:
        inputs.get(root/example).digest()
    original=inputs.get(Path('C:/Users/Administrator/.codex/skills/npt-data-holdout-check/scripts/audit_exports.py')).digest()
    copied=inputs.get(root/'.agents/skills/npt-data-holdout-check/scripts/audit_exports.py').digest()
    if copied!=original:
        raise ValueError('copied legacy helper differs from installed helper')
    write_json(output,dict(status='PASS',packages=packages,examples=examples,legacy_helper='byte-identical; not executed for R13',
                           agent_pressure_evaluation='NOT_RUN: user prohibits subagents',inputs=inputs.receipts()))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--threads',required=True,type=int,choices=[1])
    args=parser.parse_args()
    validate(args.output)
