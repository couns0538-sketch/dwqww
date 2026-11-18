"""Run and audit HistRework controls first, then the two isolated level-2 arms."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

CONTROL = {
    'both_on': (['HistReworkQuiet=2','HistReworkCorrection=2'], 'B4'),
    'both_off': (['HistRework=2','HistReworkQuiet=0','HistReworkCorrection=0'], 'S14'),
    'follow_on': (['HistRework=2'], 'B4'),
    'follow_off': ([], 'S14'),
}
ARMS = {
    'quiet_only': (['HistReworkQuiet=2','HistReworkCorrection=0'], None),
    'correction_only': (['HistReworkQuiet=0','HistReworkCorrection=2'], None),
}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('exe',type=Path)
    p.add_argument('lab',type=Path,help='directory containing jobs 1, 3 and 4')
    p.add_argument('out',type=Path)
    args=p.parse_args()
    lab=args.lab.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(lab/'job3'))
    from read_ladders import audit
    for label,(options,ref) in {**CONTROL,**ARMS}.items():
        cmd=[sys.executable, lab/'job3/ladder.py',args.exe.resolve(),'S14',out/label,'--last','20']
        for setting in options:
            cmd+=['--set',setting]
        subprocess.run(cmd,check=True,env=dict(os.environ,ASTRA5_JOB1=str(lab/'job1')))
        data,hits,_,settings=audit(out,label,20)
        baseline,_,_,baseline_settings=audit(lab/'job4/B','S14',20)
        sent=baseline_settings+['setoption name '+s.replace('=',' value ') for s in options]
        if settings!=sent: raise ValueError(f'{label}: sent {settings}, expected {sent}')
        if ref:
            reference=audit(lab/'job4/B',ref,20)[0]
            for first,second in zip(data,reference,strict=True):
                if first[:7]!=second[:7]: raise ValueError(f'{label} differs first at D{first[0]}: observed {first[:7]}, reference {second[:7]}')
        first=f'D{hits[0][0]} {hits[0][2]} {hits[0][3]} {hits[0][4]} {hits[0][5]} nodes' if hits else 'not by D20'
        print(f'{label}: raw transcript equals all {len(data)} TSV rows; first mate {first}; D20 {data[-1][2]} {data[-1][3]} {data[-1][4]} {data[-1][5]} nodes'+(f'; all 20 equal job4/B/{ref}' if ref else ''),flush=True)


if __name__=='__main__': main()
