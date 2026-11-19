"""Play Job 28 in matched 50-opening blocks and freeze each arm and common-block receipt."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode=True
from game28 import play
from pack_arm28 import pack_arm, save_json, sha

CLOSE=datetime.fromisoformat("2026-11-19T22:59:52+00:00").timestamp()
HARD=datetime.fromisoformat("2026-11-19T23:04:52+00:00").timestamp()
NC="9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3"
L27="271cea0cd131935998b72aeee5e6bda336f8bea8f48bcf060088895f1765b21c"
STAGES=("M4","M5","M6")


def utc(): return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Schedule:
    def __init__(self,exe,book,root,prediction):
        self.exe=exe.resolve(strict=True)
        self.book=book.resolve(strict=True)
        self.root=root.resolve()
        if sha(self.exe)!=NC or sha(self.book)!=L27: raise ValueError("executable or L27 identity mismatch")
        self.fens=[line for line in self.book.read_text().splitlines()]
        if len(self.fens)!=434 or any(len(fen.split())!=6 or not fen.endswith(" 0 1") for fen in self.fens):
            raise ValueError("wrong L27 line count or FEN normalization")
        self.width=min(4,int(subprocess.check_output(["nproc"],text=True))-1)
        if self.width<1: raise ValueError("insufficient CPUs for the declared game limit")
        self.blocks=root/"blocks"; self.live=root/"live"; self.checkpoints=root/"checkpoints"
        for p in (self.blocks,self.live,self.checkpoints):p.mkdir(exist_ok=False,parents=True)
        self.events=(self.blocks/"events.jsonl").open("x",buffering=1)
        self.completed=[]; self.by45=[];self.partial=None
        self.prediction=prediction
        save_json(self.blocks/"run.json",{"utc_start":utc(),"pid":os.getpid(),"prediction_commit":prediction,
                  "binary_sha256":sha(self.exe),"L27_sha256":sha(self.book),"openings":len(self.fens),
                  "max_active_games":self.width,"available_logical_cpus":sorted(os.sched_getaffinity(0)),
                  "minute45_utc":datetime.fromtimestamp(CLOSE,timezone.utc).isoformat(),
                  "minute50_utc":datetime.fromtimestamp(HARD,timezone.utc).isoformat(),
                  "cpu_rule":"Unpinned games share the available CPUs. Only one side searches at a time in each game."})

    def event(self,kind,**kwargs):
        rec={"utc":utc(),"event":kind,**kwargs}
        msg=json.dumps(rec,separators=(",",":"))
        print(msg,file=self.events,flush=True)
        if kind!="game_end":
            os.fsync(self.events.fileno())
            print(msg,flush=True)

    async def arm(self,b,stage,lo,hi):
        label=f"block{b:03d}"
        live=self.live/label/stage
        out=self.blocks/label/stage
        live.mkdir(parents=True)
        first,last=2*lo-1,2*hi
        nextgame=first; active={}; done=set();checked=set();error=None;reason="complete"
        self.event("arm_start",block=b,stage=stage,first=lo,last=hi)
        try:
            while nextgame<=last or active:
                if time.time()>=HARD:
                    reason="minute50";break
                while nextgame<=last and len(active)<self.width and time.time()<HARD:
                    gid=nextgame; nextgame+=1; op=(gid+1)//2
                    task=asyncio.create_task(play(self.exe,stage,live,gid,op,self.fens[op-1]))
                    active[task]=gid
                if not active: break
                finished,_=await asyncio.wait(active,timeout=max(0,HARD-time.time()),return_when=asyncio.FIRST_COMPLETED)
                if not finished:
                    reason="minute50";break
                for task in finished:
                    gid=active.pop(task)
                    rest=task.result()
                    if int(rest[0])!=gid: raise ValueError(f"game ID mismatch {gid}")
                    done.add(gid)
                    self.event("game_end",block=b,stage=stage,game=gid,ending=rest[5],ended_utc=rest[-1])
                for mark in (20,40):
                    until=lo+mark-1
                    if until<hi and mark not in checked and all(g in done for g in range(first,2*until+1)):
                        cp=self.checkpoints/label/stage/f"p{mark:03d}"
                        rec=await asyncio.to_thread(pack_arm,live,cp,b,stage,lo,until,HARD,"checkpoint")
                        checked.add(mark)
                        self.event("checkpoint",block=b,stage=stage,through_opening=until,path=str(cp),
                                   completed_games=rec["finished_games"])
        except BaseException as exc:
            error=exc;reason="game_error" if not isinstance(exc,asyncio.CancelledError) else "scheduler_cancelled"
            self.event(reason,block=b,stage=stage,error=repr(exc))
        finally:
            for task in active:
                if not task.done(): task.cancel()
            await asyncio.gather(*active,return_exceptions=True)
        rec=await asyncio.to_thread(pack_arm,live,out,b,stage,lo,hi,HARD,reason)
        self.event("arm_end",block=b,stage=stage,reason=reason,path=str(out),complete=rec["complete"],
                   finished_games=rec["finished_games"],unfinished_games=rec["unfinished_game_ids"],
                   final_pairs=rec["finished_pairs"],finished_searches=rec["searches"])
        return rec,error

    async def run(self):
        reason="L27_complete";failure=None
        current_block=None
        try:
            for b,lo in enumerate(range(1,len(self.fens)+1,50),1):
                if time.time()>=CLOSE:
                    reason="minute45_no_new_block";break
                hi=min(lo+49,len(self.fens));self.partial=b;current_block=b
                self.event("block_start",block=b,first=lo,last=hi)
                receipts=[]
                for stage in STAGES:
                    if time.time()>=HARD:
                        reason="minute50";break
                    r,err=await self.arm(b,stage,lo,hi)
                    receipts.append(r)
                    if err or not r["complete"]:
                        reason=r["reason"];failure=err;break
                is_complete=len(receipts)==3 and all(r["complete"] for r in receipts)
                last_game_end=None
                if is_complete:
                    self.completed.append(b);self.partial=None
                    ends=[]
                    for stage in STAGES:
                        import csv
                        with (self.blocks/f"block{b:03d}"/stage/"games.tsv").open() as f:
                            ends.extend(row["ended_utc"] for row in csv.DictReader(f,delimiter="\t"))
                    last_game_end=max(ends)
                    if datetime.fromisoformat(last_game_end).timestamp()<=CLOSE:self.by45.append(b)
                summary={"block":b,"opening_first":lo,"opening_last":hi,"complete":is_complete,
                         "last_game_end_utc":last_game_end,"finished_by_minute45":b in self.by45,
                         "completed_stages":[r["stage"] for r in receipts if r["complete"]],
                         "arms":{r["stage"]:{"finished_games":r["finished_games"],"finished_pairs":r["finished_pairs"],
                                             "unfinished_game_ids":r["unfinished_game_ids"],"receipt":r["stage"]+"/receipt.json"} for r in receipts},
                         "not_started_stages":[s for s in STAGES if s not in [r["stage"] for r in receipts]],
                         "sealed_utc":utc()}
                save_json(self.blocks/f"block{b:03d}"/"receipt.json",summary)
                self.event("block_end",**summary)
                if not is_complete or failure:break
        except BaseException as ex:
            failure=ex;reason="scheduler_error"
        finally:
            end={"utc":utc(),"reason":reason,"common_complete_blocks":self.completed,"blocks_complete_by_minute45":self.by45,
                 "partial_block":self.partial,"last_started_block":current_block,
                 "not_started_blocks":list(range((current_block or 0)+1,(len(self.fens)+49)//50+1)),
                 "error":repr(failure) if failure else None}
            save_json(self.blocks/"schedule-end.json",end)
            self.event("schedule_end",**{k:v for k,v in end.items() if k!="utc"})
            self.events.close()
        if failure: raise failure


async def main(args):
    task=asyncio.current_task();loop=asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM,task.cancel)
    runner=Schedule(args.exe,args.book,args.root,args.prediction)
    await runner.run()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("exe",type=Path);p.add_argument("book",type=Path);p.add_argument("root",type=Path)
    p.add_argument("--prediction",required=True,help="Published prediction-only commit")
    args=p.parse_args()
    asyncio.run(main(args))
