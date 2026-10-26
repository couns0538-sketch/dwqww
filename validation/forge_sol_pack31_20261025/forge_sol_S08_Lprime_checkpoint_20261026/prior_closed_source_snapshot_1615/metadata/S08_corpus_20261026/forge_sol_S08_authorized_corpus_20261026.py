#!/usr/bin/env python3
"""Build source-pinned profile-only corpus; no engine invocation or best moves."""
import argparse, collections, hashlib, json, pathlib, re
import chess

DATE='20261026'
F=pathlib.Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')
L=F/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src'
PINS={
 'wac':('9bfb7b42cf5bbc7f3d60ff767ca3be460e0ae4d9110ef9a71ddf0bd7071d4d46',pathlib.Path('/workspace/forge-sol-next-20261024/int16-review/wac300.epd')),
 'epd':('de36a48f856a5a0c10d0865747965a7b2f5d89149078923ba2d766979238bf6c',L/'tools/openings/forge-10000.epd'),
 'moves':('7516f1bf1da95530f762cd77b8c2de7f4910f8c15f918dd1af5eaa8f6b332058',L/'tools/openings/forge-10000.moves'),
 'source':('13c7c87a377ec30616f9a733bc5d74072c697c6e48db9eb39d751409f3cc0f97',L/'src/uci.cpp'),
 'authority':('11e1be8ac83c6ce78d7e609059c4a96ec4b002ae923d44683077a0df038862b2',F/'MISSING_INPUTS_20261025.md'),
 'opening_manifest':('b3bc1840a87765f8ff70c01fe9a1697f3fb3a3a3d20298d19f24ad1dbf1aabb7',L/'tools/openings/manifest.json'),
}

def sha(data):return hashlib.sha256(data).hexdigest()
def fen4(fen):return ' '.join(fen.split()[:4])
def new_directory(path):path.mkdir(parents=False,exist_ok=False)

def select_unique(rows,count):
    seen=set(); selected=[]; duplicate=0
    for row in rows:
        key=fen4(row['fen'])
        if key in seen:duplicate+=1;continue
        seen.add(key);selected.append(row)
        if len(selected)==count:return selected,duplicate
    raise ValueError(f'need {count} distinct boards, found {len(selected)}; no padding')

def replay_opening(line):
    fields=line.split('\t')
    if len(fields)!=3:raise ValueError('opening move record needs id, FEN and UCI moves')
    number,expected,moves=fields; board=chess.Board()
    for token in moves.split():
        move=chess.Move.from_uci(token)
        if move not in board.legal_moves:raise ValueError('illegal opening move '+token)
        board.push(move)
    supplied=chess.Board(expected)
    # Both exact source clocks and the legal en-passant meaning are checked.
    if board.fen()!=supplied.fen():raise ValueError('replayed opening final board differs from supplied FEN')
    if not supplied.is_valid():raise ValueError('invalid supplied opening board')
    return {'id':'Forge-'+number,'fen':expected,'source':'OPENING','plies':len(moves.split())}

def bench_rows(text):
    part=text.split('constexpr std::array<std::string_view, 8> fens{',1)[1].split('};',1)[0]
    if part.count('forge::Board::StandardStartFen')!=1:raise ValueError('unexpected bench start definition')
    values=[chess.STARTING_FEN]+re.findall(r'"([^"\n]+)"',part)
    if len(values)!=8:raise ValueError('expected exactly eight original bench boards')
    return [{'id':'ForgeBench.'+str(i),'fen':fen,'source':'BENCH','line':text[:text.index(part)].count('\n')+1} for i,fen in enumerate(values,1)]

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=pathlib.Path,required=True)
    args=parser.parse_args(argv)
    inputs={}
    for name,(expected,path) in PINS.items():
        data=path.read_bytes()
        if sha(data)!=expected:raise ValueError('source pin mismatch: '+name)
        inputs[name]={'path':str(path),'sha256':expected,'bytes':len(data)}
    authority=PINS['authority'][1].read_text()
    if 'use WAC300 (12_strength/h256tools) + bench positions + positions from tools/openings; say which you used' not in authority:raise ValueError('authorization text absent')
    wac=[]
    for number,line in enumerate(PINS['wac'][1].read_text().splitlines(),1):
        identity=re.search(r'\bid\s+"([^"]+)";',line)
        if identity is None:raise ValueError('missing WAC id')
        wac.append({'id':identity.group(1),'fen':fen4(line)+' 0 1','source':'WAC','line':number})
    bench=bench_rows(PINS['source'][1].read_text())
    epd_lines=PINS['epd'][1].read_text().splitlines()
    move_lines=PINS['moves'][1].read_text().splitlines()
    if len(epd_lines)!=10000 or len(move_lines)!=10000:raise ValueError('opening file count mismatch')
    initial,duplicate=select_unique(wac+bench,307)
    selected,seen=list(initial),{fen4(row['fen']) for row in initial}
    replayed=0
    for number,(epd,moves) in enumerate(zip(epd_lines,move_lines),1):
        row=replay_opening(moves);replayed+=1
        if row['id'] not in epd or fen4(epd)!=fen4(row['fen']):raise ValueError('opening EPD/moves mismatch')
        row['line']=number
        key=fen4(row['fen'])
        if key in seen:duplicate+=1;continue
        seen.add(key);selected.append(row)
        if len(selected)==2000:break
    if len(selected)!=2000:raise ValueError('not enough original distinct openings')
    for row in selected:
        if not chess.Board(row['fen']).is_valid():raise ValueError('invalid selected board '+row['id'])
    output=args.output.absolute();new_directory(output)
    names={kind:f'forge_sol_S08_{kind}_profile_corpus_{DATE}.epd' for kind in ('WAC','BENCH','OPENING')}
    (output/names['WAC']).write_bytes(PINS['wac'][1].read_bytes())
    for kind in ('BENCH','OPENING'):
        rows=bench if kind=='BENCH' else [row for row in selected if row['source']==kind]
        (output/names[kind]).write_text(''.join(f'{fen4(row["fen"])} id "{row["id"]}";\n' for row in rows))
    manifest={'authorization':{'kind':'handoff_S08_opening_substitution','sha256':PINS['authority'][0],'rule':'MISSING_INPUTS explicitly permits WAC300 + bench + tools/openings; no STS identity claimed'},'corpora':[]}
    for kind,name in names.items():
        manifest['corpora'].append({'path':name,'sha256':sha((output/name).read_bytes()),'kind':kind,'source':{'WAC':'canonical supplied WAC300','BENCH':'eight original lock bench boards; profiling only; no best moves claimed','OPENING':'original deterministic Forge synthetic quiet-development openings, seed20261003,12legalplies; profiling substitute, not WAC/STS'}[kind]})
    (output/f'forge_sol_S08_authorized_corpus_manifest_{DATE}.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    receipt={'status':'PASS_CORPUS_PREPARATION_NO_ENGINE','count':2000,'unique_fen4':len(seen),'counts_by_kind':dict(collections.Counter(row['source'] for row in selected)),'duplicate_rows_skipped':duplicate,'opening_records_replayed':replayed,'selected_opening_plies_replayed':sum(row.get('plies',0) for row in selected),'all_selected_python_chess_valid':True,'inputs':inputs,'selected':selected,'limitations':['Only300WAC; no STS supplied','Remaining1700profilepositions are authorized bench/opening substitutes, not tactics benchmarks','No native searches, timing, speed or strength results'],'chess_version':chess.__version__}
    (output/f'forge_sol_S08_authorized_corpus_provenance_{DATE}.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:receipt[k] for k in ('status','count','unique_fen4','counts_by_kind','duplicate_rows_skipped','opening_records_replayed')}))

if __name__=='__main__':main()
