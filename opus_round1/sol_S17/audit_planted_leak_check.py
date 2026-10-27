"""Planted-leak check for audit_split_leak.py: on writable copies of a finished split, the clean copy must PASS and each
planted leak must FAIL with leak_count >= 1. Writes only below the NEW scratch dir.
  group : one kept validation row is relabelled train in the ledger (that game now has rows in both parts)
  position : the first train output row gets the board and side to move of the first validation output row
Usage: <python with numpy> -I -B audit_planted_leak_check.py <split config.json> <split out dir> <NEW scratch dir>"""
import json,pathlib,shutil,stat,subprocess,sys
sys.dont_write_bytecode=True
cfg,split,root=pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve(),pathlib.Path(sys.argv[3]).resolve()
AUDIT=pathlib.Path(__file__).resolve().with_name('audit_split_leak.py');root.mkdir(parents=False,exist_ok=False);DATE='20261026'
def copy(name):
    d=root/name;shutil.copytree(split,d)
    for p in d.iterdir():p.chmod(stat.S_IREAD|stat.S_IWRITE)
    return d
def audit(d):
    r=subprocess.run([sys.executable,'-I','-B',str(AUDIT),str(cfg),str(d),str(root/(d.name+'_audit'))],capture_output=True,text=True)
    rep=json.loads((root/(d.name+'_audit')/'leak_audit.json').read_text())
    return r.returncode,rep['verdict'],rep['leak_count'],rep['groups']['groups_with_kept_rows_in_both_parts'],rep['positions']['exact_positions_in_both_parts']
ok=True
c=copy('clean');res=audit(c);good=res[:2]==(0,'PASS') and res[2]==0;ok&=good;print('clean copy:',res,'->','PASS' if good else 'FAIL')
g=copy('planted_group');led=g/f'forge_sol_S17_row_selection_{DATE}.jsonl';rows=[json.loads(l) for l in led.read_text(encoding='utf-8').splitlines()]
i=next(k for k,r in enumerate(rows) if r['status']=='kept' and r['assigned_split']=='validation');rows[i]['assigned_split']='train'
led.write_bytes(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows).encode())
res=audit(g);good=res[0]!=0 and res[1]=='FAIL' and res[3]>=1;ok&=good;print('planted group leak:',res,'->','caught' if good else 'MISSED')
p=copy('planted_position');t=bytearray((p/f'forge_sol_S17_train_{DATE}.pos').read_bytes());v=(p/f'forge_sol_S17_validation_{DATE}.pos').read_bytes()
nt=int.from_bytes(t[8:16],'little');nv=int.from_bytes(v[8:16],'little')
t[16:48]=v[16:48];t[16+34*nt]=(t[16+34*nt]&~1)|(v[16+34*nv]&1)  # board32 and side to move of validation row 0
(p/f'forge_sol_S17_train_{DATE}.pos').write_bytes(bytes(t))
res=audit(p);good=res[0]!=0 and res[1]=='FAIL' and res[4]>=1;ok&=good;print('planted position leak:',res,'->','caught' if good else 'MISSED')
print('planted-leak check:','PASS' if ok else 'FAIL');sys.exit(0 if ok else 1)
