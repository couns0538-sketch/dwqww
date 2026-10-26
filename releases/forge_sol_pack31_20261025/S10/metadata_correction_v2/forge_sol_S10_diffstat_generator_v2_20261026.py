#!/usr/bin/env python3
"""Correct sealed S10 diffstat metadata using read-only git apply --numstat.

No engine/source patch, native evidence, original report or checkpoint is changed.
All outputs are new files; original closed manifest and members are reverified.
"""
from pathlib import Path
import argparse,copy,hashlib,json,shutil,subprocess

PARENT=Path('/workspace/forge-pack24-20261026/S10_delivery_20261026')
PATCHES=Path('/workspace/forge-pack24-20261026/S10')
ORIGINAL_MANIFEST='forge_sol_S10_SHA256SUMS_CLOSED_20261026.txt'
ORIGINAL_RESULTS='forge_sol_S10_consolidated_results_20261026.json'
ORIGINAL_REPORT='forge_sol_S10_closed_report_20261026.md'
EXPECTED_FILES={'CMakeLists.txt','include/forge/search.hpp','src/search.cpp','src/uci.cpp','IDEA_SOURCE.md','README.md'}
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def create(p,data):
    with p.open('xb') as stream:stream.write(data)

def create_json(p,data):create(p,(json.dumps(data,indent=2)+'\n').encode())

def original_snapshot():
    m=PARENT/ORIGINAL_MANIFEST
    rows={}
    for line in m.read_text().splitlines():
        sha,name=line.split('  ',1)
        assert Path(name).name==name and len(sha)==64 and name not in rows
        q=PARENT/name;assert H(q)==sha
        rows[name]={'sha256':sha,'bytes':q.stat().st_size}
    assert len(rows)==13
    rows[m.name]={'sha256':H(m),'bytes':m.stat().st_size}
    return rows

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    out=args.out.resolve();assert out.is_dir() and out!=PARENT
    before=original_snapshot();original=json.loads((PARENT/ORIGINAL_RESULTS).read_text());corrected=copy.deepcopy(original)
    git=Path(shutil.which('git')).resolve();receipts=[];red=[];table=[]
    for feature in corrected['features']:
        p=PATCHES/feature['patch']['name'];assert H(p)==feature['patch']['sha256']
        argv=[str(git),'apply','--numstat',str(p)]
        r=subprocess.run(argv,cwd='/tmp',capture_output=True,check=False)
        stem='forge_sol_S10_'+feature['key']+'_numstat_v2_20261026'
        stdout=out/(stem+'.stdout');stderr=out/(stem+'.stderr');create(stdout,r.stdout);create(stderr,r.stderr)
        assert r.returncode==0 and r.stderr==b''
        records=[]
        for line in r.stdout.decode('utf-8').splitlines():
            add,delete,name=line.split('\t',2)
            assert add.isdigit() and delete.isdigit() and name in EXPECTED_FILES
            records.append({'path':name,'insertions':int(add),'deletions':int(delete)})
        assert len(records)==6 and {row['path'] for row in records}==EXPECTED_FILES
        counts={'files':len(records),'insertions':sum(row['insertions'] for row in records),'deletions':sum(row['deletions'] for row in records)}
        old=next(row for row in original['features'] if row['key']==feature['key'])['patch']
        wrong=any(old[name]!=value for name,value in counts.items())
        assert wrong and old['files']==0
        red.append({'feature':feature['key'],'status':'REJECTED_ORIGINAL_BAD_DIFFSTAT','original':{k:old[k] for k in counts},'actual':counts})
        receipt={'feature':feature['key'],'argv':argv,'cwd':'/tmp','returncode':r.returncode,'git_sha256':H(git),'patch_sha256':H(p),'stdout':{'path':stdout.name,'sha256':H(stdout),'bytes':stdout.stat().st_size},'stderr':{'path':stderr.name,'sha256':H(stderr),'bytes':stderr.stat().st_size},'per_file':records,**counts}
        receipts.append(receipt);feature['patch'].update(counts)
        table.append((feature['patch']['name'],old,counts))
    # This check permits exactly the three diffstat scalar fields to change.
    restored=copy.deepcopy(corrected)
    for feature in restored['features']:
        old=next(row for row in original['features'] if row['key']==feature['key'])
        for key in ('files','insertions','deletions'):feature['patch'][key]=old['patch'][key]
    assert restored==original
    verification={'scope':'S10 metadata only; no native, source-patch or original-report mutation','original_closed_files_before':before,'git':{'path':str(git),'sha256':H(git)},'read_only_commands':receipts,'red_controls':red,'green_controls':'PASS: corrected counts equal all four actual git apply --numstat outputs','non_diffstat_JSON_fields':'UNCHANGED_EXACT_EQUALITY','engine_runs':0,'source_patch_changes':0,'archive_changes':0,'original_closed_files_after':original_snapshot()}
    assert verification['original_closed_files_after']==before
    jp=out/'forge_sol_S10_consolidated_results_v2_20261026.json';create_json(jp,corrected)
    md=(PARENT/ORIGINAL_REPORT).read_text()
    md=md.replace('# Forge Sol S10 closed report — 2026-10-26','# Forge Sol S10 closed report v2 — 2026-10-26',1)
    for name,old,counts in table:
        oldrow=f"|{name}|`{old['sha256']}`|{old['files']} files,+{old['insertions']}/−{old['deletions']}|"
        newrow=f"|{name}|`{old['sha256']}`|{counts['files']} files,+{counts['insertions']}/−{counts['deletions']}|"
        assert md.count(oldrow)==1;md=md.replace(oldrow,newrow,1)
    md=md.replace(ORIGINAL_RESULTS,jp.name).replace(H(PARENT/ORIGINAL_RESULTS),H(jp))
    md+='\nMetadata correction v2: each diffstat above comes from the actual frozen patch via read-only `git apply --numstat`. The original generator counted Git-style headers even though these are plain unified patches, incorrectly reporting0 files. The original14 closed files and manifest are retained byte-for-byte. Only three diffstat scalar fields per patch differ in the v2 machine results; all native outcomes, original evidence references and hashes are unchanged. See `forge_sol_S10_diffstat_correction_v2_20261026.md` and the verification JSON.\n'
    mp=out/'forge_sol_S10_closed_report_v2_20261026.md';create(mp,md.encode())
    note='# S10 diffstat correction v2 — 2026-10-26\n\nThe sealed v1 aggregate incorrectly reported0 files for every patch because its generator counted only `diff --git` headers. The four unchanged patches use plain unified diff headers. This metadata defect does not alter any source patch, native result, archive, trial decision or engine baseline. V1 reports/generator/results and their original14-file sealed set remain intact.\n\n'
    note+='|Patch|Verified files|Insertions|Deletions|\n|---|---:|---:|---:|\n'
    for name,old,c in table:note+=f"|{name}|{c['files']}|{c['insertions']}|{c['deletions']}|\n"
    note+='\nFour red controls reject the original0-file metadata against actual Git numstat output. Four green comparisons pass for v2. Non-diffstat JSON fields compare exactly with v1, including202 CTest executions,1200 legal WAC positions, all original result/archive/source hashes, rejection decisions and unverified checks. Git commands are read-only; original stdout/stderr, per-file counts and tool/patch hashes are retained in the verification JSON. No native process was run.\n\n'
    note+=f'Corrected machine results SHA256 `{H(jp)}`. Corrected report SHA256 `{H(mp)}`.\n'
    np=out/'forge_sol_S10_diffstat_correction_v2_20261026.md';create(np,note.encode())
    vp=out/'forge_sol_S10_diffstat_verification_v2_20261026.json';create_json(vp,verification)
    # Verify all14 originals once more after writes; output folder is separate.
    assert original_snapshot()==before
    manifest=out/'forge_sol_S10_SHA256SUMS_METADATA_V2_20261026.txt'
    create(manifest,''.join(f'{H(p)}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file()).encode())
    for line in manifest.read_text().splitlines():sha,name=line.split('  ',1);assert H(out/name)==sha
    print(json.dumps({'status':'PASS_METADATA_CORRECTION_ONLY','original_closed_files_unchanged':len(before),'native_runs':0,'new_files':[{'name':p.name,'sha256':H(p),'bytes':p.stat().st_size} for p in (jp,mp,np,vp,manifest)],'counts':[{**c,'patch':name} for name,old,c in table]},indent=2))
if __name__=='__main__':main()
