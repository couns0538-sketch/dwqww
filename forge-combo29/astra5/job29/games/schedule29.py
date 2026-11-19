"""Play Job 29 in matched 50-opening blocks and freeze each arm and common-block receipt."""
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
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"runner"))
from game29 import play, GAME_COLS
from pack_arm29 import pack_arm, save_json, sha

CLOSE=datetime.fromisoformat("2026-11-19T23:28:09+00:00").timestamp()
OPTIONAL=datetime.fromisoformat("2026-11-19T23:18:09+00:00").timestamp()
HARD=datetime.fromisoformat("2026-11-19T23:33:09+00:00").timestamp()
NC="9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3"
L27="271cea0cd131935998b72aeee5e6bda336f8bea8f48bcf060088895f1765b21c"
PHASES={"primary":("D1","D2","E"),"additional":("D3","D4")}
STANDING={"standing":("F1","F2")}


def utc(): return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Schedule:
    def __init__(self,exe,book,root,prediction,standing_start=None):
        self.phases=STANDING if standing_start else PHASES
        self.close=standing_start+35*60 if standing_start else CLOSE
        self.hard=standing_start+45*60 if standing_start else HARD
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
        self.completed=[]; self.by_close=[];self.partial=None
        self.by_phase={phase:[] for phase in self.phases}
        self.optional_eligible=None
        self.prediction=prediction
        save_json(self.blocks/"run.json",{"utc_start":utc(),"pid":os.getpid(),"prediction_commit":prediction,
                  "binary_sha256":sha(self.exe),"L27_sha256":sha(self.book),"openings":len(self.fens),
                  "max_active_games":self.width,"available_logical_cpus":sorted(os.sched_getaffinity(0)),
                  "new_block_cutoff_utc":datetime.fromtimestamp(self.close,timezone.utc).isoformat(),
                  "optional_primary_finish_before":None if standing_start else datetime.fromtimestamp(OPTIONAL,timezone.utc).isoformat(),
                  "hard_stop_utc":datetime.fromtimestamp(self.hard,timezone.utc).isoformat(),"phase_stages":self.phases,
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
                if time.time()>=self.hard:
                    reason="hard_stop";break
                while nextgame<=last and len(active)<self.width and time.time()<self.hard:
                    gid=nextgame; nextgame+=1; op=(gid+1)//2
                    task=asyncio.create_task(play(self.exe,stage,live,gid,op,self.fens[op-1]))
                    active[task]=gid
                if not active: break
                finished,_=await asyncio.wait(active,timeout=max(0,self.hard-time.time()),return_when=asyncio.FIRST_COMPLETED)
                if not finished:
                    reason="hard_stop";break
                for task in finished:
                    gid=active.pop(task)
                    rest=task.result()
                    if int(rest[GAME_COLS.index("game")])!=gid or rest[GAME_COLS.index("match")]!=stage: raise ValueError(f"game ID mismatch {gid}")
                    done.add(gid)
                    self.event("game_end",block=b,stage=stage,game=gid,ending=rest[GAME_COLS.index("ending")],ended_utc=rest[GAME_COLS.index("ended_utc")])
                for mark in (20,40):
                    until=lo+mark-1
                    if until<hi and mark not in checked and all(g in done for g in range(first,2*until+1)):
                        cp=self.checkpoints/label/stage/f"p{mark:03d}"
                        rec=await asyncio.to_thread(pack_arm,live,cp,b,stage,lo,until,self.hard,"checkpoint")
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
        rec=await asyncio.to_thread(pack_arm,live,out,b,stage,lo,hi,self.hard,reason)
        self.event("arm_end",block=b,stage=stage,reason=reason,path=str(out),complete=rec["complete"],
                   finished_games=rec["finished_games"],unfinished_games=rec["unfinished_game_ids"],
                   final_pairs=rec["finished_pairs"],finished_searches=rec["searches"])
        return rec,error

    async def block(self,b,phase,local,lo,hi):
        import csv
        stages=self.phases[phase]
        self.partial=b
        (self.blocks/f"block{b:03d}").mkdir()
        self.event("block_start",block=b,phase=phase,phase_block=local,first=lo,last=hi,stages=stages)
        receipts=[]
        reason="complete"
        error=None
        for stage in stages:
            if time.time()>=self.hard:
                reason="hard_stop";break
            row,error=await self.arm(b,stage,lo,hi)
            receipts.append(row)
            if error or not row["complete"]:
                reason=row["reason"];break
        complete=len(receipts)==len(stages) and all(r["complete"] for r in receipts)
        ends=[]
        for r in receipts:
            with (self.blocks/f"block{b:03d}"/r["stage"]/"games.tsv").open() as f:
                ends.extend(g["ended_utc"] for g in csv.DictReader(f,delimiter="\t"))
        last=max(ends,default=None)
        if complete:
            self.completed.append(b); self.by_phase[phase].append(b); self.partial=None
            if datetime.fromisoformat(last).timestamp()<=self.close:self.by_close.append(b)
        completed_stages=[r["stage"] for r in receipts if r["complete"]]
        started_stages=[r["stage"] for r in receipts]
        summary={"block":b,"phase":phase,"phase_block":local,"stages":list(stages),"opening_first":lo,"opening_last":hi,
                 "complete":complete,"last_game_end_utc":last,"finished_by_block_cutoff":b in self.by_close,
                 "completed_stages":completed_stages,"not_started_stages":[s for s in stages if s not in started_stages],
                 "arms":{r["stage"]:{"finished_games":r["finished_games"],"finished_pairs":r["finished_pairs"],
                                      "unfinished_game_ids":r["unfinished_game_ids"],"receipt":r["stage"]+"/receipt.json"} for r in receipts},
                 "sealed_utc":utc()}
        save_json(self.blocks/f"block{b:03d}"/"receipt.json",summary)
        self.event("block_end",**summary)
        return complete,last,reason,error

    async def run(self):
        last_block=None
        reason="all_eligible_phases_complete"; failure=None
        nblocks=(len(self.fens)+49)//50
        phase_bounds={}
        for i,phase in enumerate(self.phases):
            phase_bounds[phase]=list(range(i*nblocks+1,(i+1)*nblocks+1))
        try:
            for phase,global_ids in phase_bounds.items():
                if phase=="additional" and not self.optional_eligible:
                    reason="primary_completed_after_optional_deadline";break
                last=None
                for idx,b in enumerate(global_ids):
                    if time.time()>=self.close:
                        reason="no_new_block_cutoff";break
                    lo=50*idx+1; hi=min(lo+49,len(self.fens)); last_block=b
                    complete,last,why,failure=await self.block(b,phase,idx+1,lo,hi)
                    if not complete or failure:
                        reason=why;break
                if len(self.by_phase[phase])!=nblocks or failure:
                    if phase=="primary": self.optional_eligible=False
                    break
                if phase=="primary":
                    self.optional_eligible=datetime.fromisoformat(last).timestamp()<OPTIONAL
                    self.event("optional_gate",primary_last_game_utc=last,eligible=self.optional_eligible,
                               deadline=datetime.fromtimestamp(OPTIONAL,timezone.utc).isoformat())
        except BaseException as ex:
            failure=ex;reason="scheduler_error"
        finally:
            planned=[b for ids in phase_bounds.values() for b in ids]
            end={"utc":utc(),"reason":reason,"common_complete_blocks":self.completed,"complete_by_phase":self.by_phase,
                 "blocks_complete_by_minute40":self.by_close if "primary" in self.phases else None,
                 "blocks_complete_before_admission_cutoff":self.by_close,"phase_plan":phase_bounds,
                 "additional_phase_eligible":self.optional_eligible,"partial_block":self.partial,
                 "last_started_block":last_block,"not_started_blocks":[b for b in planned if b>(last_block or 0)],
                 "error":repr(failure) if failure else None}
            save_json(self.blocks/"schedule-end.json",end)
            self.event("schedule_end",**{k:v for k,v in end.items() if k!="utc"})
            self.events.close()
        if failure:raise failure


async def main(args):
    task=asyncio.current_task();loop=asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM,task.cancel)
    standing=None
    if args.standing_start:
        dt=datetime.fromisoformat(args.standing_start)
        if dt.tzinfo is None:raise ValueError("Standing job start requires a timezone")
        standing=dt.timestamp()
    runner=Schedule(args.exe,args.book,args.root,args.prediction,standing)
    await runner.run()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("exe",type=Path);p.add_argument("book",type=Path);p.add_argument("root",type=Path)
    p.add_argument("--prediction",required=True,help="Published prediction-only commit")
    p.add_argument("--standing-start",help="Only for S1; explicit authorized standing-job anchor with timezone")
    asyncio.run(main(p.parse_args()))
