"""Live wire audit, or replay compact published match evidence offline without engines."""
from replay29 import stage
from score29 import collect
from common29 import *
import argparse,time
p=argparse.ArgumentParser(description=__doc__);p.add_argument('blocks',type=Path);p.add_argument('book',type=Path);p.add_argument('out',type=Path)
p.add_argument('--live',type=Path);p.add_argument('--watch',action='store_true');a=p.parse_args()
raw=a.book.read_bytes();check(sha(raw)==BOOK_SHA,'book');book=raw.decode().splitlines()
check(len(book)==434 and chess.__version__=='1.11.2','book/chess')
cache_dir=a.out/'verified';cache_dir.mkdir(parents=True,exist_ok=True);last_count=-1
while True:
    changed=False
    for marker in sorted(a.blocks.glob('block*/*/receipt.json')):
        path=marker.parent;b=path.parent.name;m=path.name;dest=cache_dir/b/(m+'.json')
        if dest.exists():continue
        doc=stage(path,book,a.live/b/m if a.live else None)
        dump(dest,doc);changed=True
        print(datetime.now().astimezone().isoformat(),b,m,doc['finished'],'games independently verified from',sum(g['plies'] for g in doc['games']),'search rows',flush=True)
    status=(a.blocks/'schedule-end.json').exists();n=len(list(a.blocks.glob('block*/receipt.json')))
    if changed or n!=last_count or status:
        allstages=[json.loads(x.read_text()) for x in sorted(cache_dir.glob('block*/*.json'))]
        s=collect(a.out/('final' if status else 'latest'),allstages,a.blocks,status)
        print('common',s['common_complete_blocks'],'40',s['blocks_complete_by_minute40'],flush=True);last_count=n
    if status or not a.watch:break
    time.sleep(1)
