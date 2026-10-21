from pathlib import Path
import os,signal,time

def group_members(pgid):
    result=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            raw=(p/'stat').read_text();end=raw.rfind(')');fields=raw[end+2:].split()
            if int(fields[2])==pgid:result.append({'pid':int(p.name),'state':fields[0]})
        except (OSError,ValueError,IndexError):pass
    return result

def cleanup(pgid):
    before=group_members(pgid);actions=[];reaped=[]
    def reap():
        while True:
            try:pid,status=os.waitpid(-1,os.WNOHANG)
            except ChildProcessError:break
            if pid==0:break
            reaped.append({'pid':pid,'wait_status':status})
    live=lambda:[r for r in group_members(pgid) if r['state']!='Z']
    for sig in [signal.SIGTERM,signal.SIGKILL]:
        if not live():break
        try:os.killpg(pgid,sig);actions.append(signal.Signals(sig).name)
        except ProcessLookupError:pass
        until=time.monotonic()+2
        while time.monotonic()<until and live():reap();time.sleep(.02)
    reap();after=group_members(pgid)
    return {'group_id':pgid,'before':before,'actions':actions,'reaped_children':reaped,'after':after,'no_live_owned_processes':not any(r['state']!='Z' for r in after),'unexpected_live_members_after_command':any(r['state']!='Z' for r in before)}
