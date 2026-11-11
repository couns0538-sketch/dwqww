#!/usr/bin/env python3
"""Temporary guarded prototype, source-only extraction; no searches or timings."""
import difflib, hashlib, json, pathlib, re, subprocess, tempfile
repo=pathlib.Path(__file__).resolve().parents[2]; out=pathlib.Path(__file__).resolve().parent
lock='16833ecc03b425586f91f4c8834dea8807bf4c22'
def git(*x): return subprocess.check_output(['git','-C',str(repo),*x])
def sha(x): return hashlib.sha256(x).hexdigest()
receipt=json.loads((out/'check_square_calls_results.json').read_text()); flags=receipt['flags']; records=[]; dumps=[]
with tempfile.TemporaryDirectory(prefix='forge-check-square-codegen-') as tmp:
 root=pathlib.Path(tmp)
 for name in git('ls-tree','-r','--name-only',lock,'forge-combo29/src','forge-combo29/include').decode().splitlines():
  assert pathlib.Path(name).suffix in ('.cpp','.hpp','.h','.inc')
  data=git('show',f'{lock}:{name}'); assert sha(data)==receipt['source_manifest'][name]
  dest=root/pathlib.Path(name).relative_to('forge-combo29'); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(data)
 src=root/'src/search.cpp'; original=src.read_text()
 old='''        check_squares_[Bishop] = attacks::bishop(enemy_king, occupancy);
        check_squares_[Rook] = attacks::rook(enemy_king, occupancy);'''
 new='''#ifndef FORGE_SPD_CHECK_SQUARE_PRESENCE
#define FORGE_SPD_CHECK_SQUARE_PRESENCE 0
#endif
#if FORGE_SPD_CHECK_SQUARE_PRESENCE
        const Color us = board_.side_to_move();
        const Bitboard queens = board_.pieces(us, Queen);
        check_squares_[Bishop] = (board_.pieces(us, Bishop) | queens) != 0
            ? attacks::bishop(enemy_king, occupancy) : 0;
        check_squares_[Rook] = (board_.pieces(us, Rook) | queens) != 0
            ? attacks::rook(enemy_king, occupancy) : 0;
#else
'''+old+'''
#endif'''
 assert original.count(old)==1; candidate=original.replace(old,new)
 (out/'check_square_prototype.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),candidate.splitlines(True),fromfile='a/forge-combo29/src/search.cpp',tofile='b/forge-combo29/src/search.cpp')))
 for speed in (0,1):
  for variant,content,on in [('lock',original,0),('off',candidate,0),('on',candidate,1)]:
   src.write_text(content); obj=root/'search.o'; command=['g++',*flags,f'-DFORGE_SEARCH_SPEED2={speed}',f'-DFORGE_SPD_CHECK_SQUARE_PRESENCE={on}','-I'+str(root/'include'),'-c',str(src),'-o',str(obj)]
   subprocess.run(command,check=True,timeout=180)
   dis=subprocess.check_output(['objdump','-drC',str(obj)]).decode(); parts=re.split(r'(?=^[0-9a-f]+ <)',dis,flags=re.M); picker=''.join(s for s in parts if 'forge::MovePicker::next(bool)>' in s.split('\n',1)[0])
   dumps.append(f'SPEED2={speed} variant={variant}\n'+picker)
   symbols=subprocess.check_output(['nm','-CS',str(obj)]).decode(); match=re.search(r'^[0-9a-f]+ ([0-9a-f]+) . forge::MovePicker::next\(bool\)$',symbols,re.M); assert match
   records.append(dict(speed2=speed,variant=variant,sha256=sha(obj.read_bytes()),picker_text_bytes=int(match[1],16),pext_count=picker.count('\tpext '),command=command))
 for speed in (0,1):
  rows=[r for r in records if r['speed2']==speed]; assert rows[0]['sha256']==rows[1]['sha256']
(out/'check_square_codegen_prototype.txt').write_text('\n'.join(dumps))
(out/'check_square_codegen_results.json').write_text(json.dumps(dict(lock=lock,script_sha256=sha(pathlib.Path(__file__).read_bytes()),records=records),indent=2)+'\n')
print(json.dumps(records,indent=2))
