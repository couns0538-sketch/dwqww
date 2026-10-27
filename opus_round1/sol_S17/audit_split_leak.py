"""Independent leak audit of an S17 split (Opus 5.5, 2026-10-27). Own code; trusts nothing the split tool wrote except
its row-selection ledger, which it checks against the sources and the outputs. Read-only on every input.
  1. game groups are recomputed from the ORIGINAL ordered sources with Sol's rule (fullmove decrease, piece-count
     increase or WHITE-result change starts a group; no reset at file boundaries); leak = a group with kept rows in
     both parts; the recomputed partition is compared with the ledger's group labels;
  2. position leak = an exact position (board32 + side to move) present in both output POS files (64-bit candidates,
     every candidate confirmed on all 33 bytes); duplicates inside each output are counted too;
  3. round trip: every output row (POS board/score/meta, HCE, text line) equals its source row, in ledger order;
  4. accounting: input rows = kept train + kept validation + dropped;
  5. SHA256 of every split output file and of every source input, written with the report to a NEW directory.
Usage: <python with numpy> -I -B audit_split_leak.py <split config.json> <split out dir> <NEW audit dir>"""
import hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
import numpy as np
U64=np.uint64;DATE='20261026';PARTS=('train','validation');RES={'0.0':0,'0.5':1,'1.0':2}

def fpos(path):
    raw=np.fromfile(path,np.uint8);n=int.from_bytes(raw[8:16].tobytes(),'little')
    assert raw[:4].tobytes()==b'FPOS' and len(raw)==16+35*n,path
    return raw[16:16+32*n].reshape(n,32),raw[16+32*n:16+34*n].view('<i2'),raw[16+34*n:16+35*n]
def fhce(path):
    raw=np.fromfile(path,np.uint8);n=int.from_bytes(raw[8:16].tobytes(),'little');assert raw[:4].tobytes()==b'FHCE' and len(raw)==16+2*n;return raw[16:].view('<i2')
def keys(boards,metas):
    with np.errstate(over='ignore'):
        w=np.ascontiguousarray(boards).view('<u8').reshape(-1,4);h=w[:,0]*U64(0x9e3779b97f4a7c15)
        for j in (1,2,3):h=(h^(h>>U64(29)))*U64(0xbf58476d1ce4e5b9)^w[:,j]
        h^=(metas&1).astype(U64)*U64(0x94d049bb133111eb);return (h^(h>>U64(31)))*U64(0xff51afd7ed558ccd)
def ident(boards,metas):return np.concatenate([boards,(metas&1).reshape(-1,1)],axis=1)
def lines(path):
    with open(path,'rb') as f:return f.read().splitlines(keepends=True)
def fullmoves(text_lines):return np.array([int(l.split(b'|',1)[0].split()[5]) for l in text_lines],np.int32)
def pieces(boards):return ((boards&15)!=0).sum(1)+((boards>>4)!=0).sum(1)
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<24),b''):h.update(b)
    return h.hexdigest()
def cross_positions(a_b,a_m,b_b,b_m):
    """Exact positions present in both sets, and duplicates inside each set."""
    ka,kb=keys(a_b,a_m),keys(b_b,b_m);both=np.intersect1d(ka,kb);exact=0
    for k in both:
        ia=np.flatnonzero(ka==k);ib=np.flatnonzero(kb==k);A={bytes(x) for x in ident(a_b[ia],a_m[ia])};B={bytes(x) for x in ident(b_b[ib],b_m[ib])};exact+=len(A&B)
    def dups(b,m,k):
        o=np.argsort(k,kind='stable');s=k[o];eq=np.flatnonzero(s[1:]==s[:-1]);d=0
        for i in eq:d+=bytes(ident(b[o[i]:o[i]+1],m[o[i]:o[i]+1])[0])==bytes(ident(b[o[i+1]:o[i+1]+1],m[o[i+1]:o[i+1]+1])[0])
        return int(d)
    return exact,len(both),dups(a_b,a_m,ka),dups(b_b,b_m,kb)

def free_ram_gib():
    import ctypes,os
    if os.name!='nt':return None
    class St(ctypes.Structure):_fields_=[('l',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(f,ctypes.c_ulonglong) for f in ('tp','ap','tpf','apf','tv','av','ae')]
    s=St();s.l=ctypes.sizeof(St);return s.ap/2**30 if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s)) else None

def main():
    free=free_ram_gib()  # the audit holds about 0.8 GB for a 3M-row window: keep the PC above its 6 GiB floor
    if free is not None and free<7.0:raise SystemExit(f'STOPPED_LOW_RAM: {free:.2f} GiB free, need 7.0')
    cfg_path,split,out=pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve(),pathlib.Path(sys.argv[3]).resolve()
    out.mkdir(parents=False,exist_ok=False);cfg=json.loads(cfg_path.read_text(encoding='utf-8-sig'));base=cfg_path.parent
    srcs=[{'name':s['name'],'pos':(base/s['pos']).resolve(),'text':(base/s['text']).resolve()} for s in cfg['sources']];rep={'split_out':str(split),'config':str(cfg_path)}
    rep['input_sha256']={str(p):sha(p) for s in srcs for p in (s['pos'],s['pos'].with_suffix('.hce'),s['text'])}
    # sources, concatenated in chronological order
    B=[];S=[];M=[];Hc=[];T=[];off={};n=0
    for s in srcs:
        b,sc,m=fpos(s['pos']);h=fhce(s['pos'].with_suffix('.hce'));t=lines(s['text']);assert len(t)==len(b)==len(h),s['name']
        off[s['name']]=n;n+=len(b);B.append(b);S.append(sc);M.append(m);Hc.append(h);T.extend(t)
    B=np.concatenate(B);S=np.concatenate(S);M=np.concatenate(M);Hc=np.concatenate(Hc)
    fm=fullmoves(T);res=M>>1;pc=pieces(B)
    textres=np.array([RES[l.rsplit(b'|',1)[1].strip().decode()] for l in T],np.uint8);assert np.array_equal(textres,res),'text/POS result mismatch'
    gid=np.concatenate([[0],np.cumsum((fm[1:]<fm[:-1])|(pc[1:]>pc[:-1])|(res[1:]!=res[:-1]))])
    # ledger
    led=[json.loads(l) for l in open(split/f'forge_sol_S17_row_selection_{DATE}.jsonl',encoding='utf-8')]
    assert len(led)==n,('ledger rows',len(led),n)
    glob=np.array([off[r['source']]+r['row'] for r in led],np.int64);assert np.array_equal(np.sort(glob),np.arange(n)),'ledger must cover every source row once'
    kept=np.array([r['status']=='kept' for r in led]);part=np.array([PARTS.index(r['assigned_split']) for r in led],np.int8)
    labels=np.array([int(r['group'].split(':')[1]) for r in led],np.int64)
    mygid=gid[glob]
    # 1. group leak (own groups) and agreement with the ledger's labels
    k=kept;g2p={};leak_groups=0
    pairs=set(zip(mygid[k].tolist(),part[k].tolist()));per={}
    for g,p in pairs:per.setdefault(g,set()).add(p)
    leak_groups=sum(1 for v in per.values() if len(v)>1)
    same_partition=len(set(zip(mygid.tolist(),labels.tolist())))==len(set(mygid.tolist()))==len(set(labels.tolist()))
    rep['groups']={'recomputed_groups':int(gid[-1])+1,'ledger_groups':len(set(labels.tolist())),'same_partition_as_ledger':bool(same_partition),'groups_with_kept_rows_in_both_parts':int(leak_groups)}
    # 2. position leak between the two outputs
    ob={p:fpos(split/f'forge_sol_S17_{p}_{DATE}.pos') for p in PARTS}
    exact,cands,dup_t,dup_v=cross_positions(ob['train'][0],ob['train'][2],ob['validation'][0],ob['validation'][2])
    rep['positions']={'train_rows':len(ob['train'][0]),'validation_rows':len(ob['validation'][0]),'exact_positions_in_both_parts':int(exact),'64bit_candidates_checked':int(cands),'duplicate_positions_inside_train':dup_t,'duplicate_positions_inside_validation':dup_v}
    # 3. round trip of every output row
    rt={}
    for pi,p in enumerate(PARTS):
        sel=glob[kept&(part==pi)];b,sc,m=ob[p];h=fhce(split/f'forge_sol_S17_{p}_{DATE}.hce');t=lines(split/f'forge_sol_S17_{p}_{DATE}.txt')
        ok=len(sel)==len(b)==len(h)==len(t) and np.array_equal(B[sel],b) and np.array_equal(S[sel],sc) and np.array_equal(M[sel],m) and np.array_equal(Hc[sel],h) and all(T[i]==x or T[i]+b'\n'==x for i,x in zip(sel.tolist(),t))
        rt[p]={'rows':int(len(sel)),'pos_hce_text_equal_to_source_rows':bool(ok)}
    rep['round_trip']=rt
    # 4. accounting
    rep['accounting']={'input_rows':n,'kept_train':int((kept&(part==0)).sum()),'kept_validation':int((kept&(part==1)).sum()),'dropped':int((~kept).sum()),
                       'dropped_reasons':{r:sum(1 for x in led if x['status']!='kept' and x['reason']==r) for r in sorted({x['reason'] for x in led if x['status']!='kept'})}}
    a=rep['accounting'];a['balanced']=a['input_rows']==a['kept_train']+a['kept_validation']+a['dropped']
    rep['leak_count']=int(leak_groups+exact)
    rep['verdict']='PASS' if rep['leak_count']==0 and same_partition and a['balanced'] and all(v['pos_hce_text_equal_to_source_rows'] for v in rt.values()) and dup_t==dup_v==0 else 'FAIL'
    sums=''.join(f'{sha(p)}  {p.name}\n' for p in sorted(split.iterdir()) if p.is_file())
    (out/'split_outputs_SHA256SUMS').write_bytes(sums.encode())
    (out/'leak_audit.json').write_bytes((json.dumps(rep,indent=2,sort_keys=True)+'\n').encode())
    (out/'SHA256SUMS').write_bytes(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS').encode())
    print(json.dumps({k:rep[k] for k in ('verdict','leak_count','groups','positions','round_trip','accounting')},sort_keys=True))
    return 0 if rep['verdict']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
