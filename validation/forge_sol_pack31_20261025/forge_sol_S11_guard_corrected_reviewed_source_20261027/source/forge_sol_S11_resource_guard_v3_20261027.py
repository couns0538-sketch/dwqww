"""Source-only S11 resource observer v3; never launches or signals a process.

The existing owned controller supplies child_start events/new-session groups and
retains its full cleanup scans. Aggregate RSS is sampled, not continuously
enforced: new descendants may await the next1s membership refresh plus observer
work/loop latency. Known-member RSS is sampled at50ms; threshold stays4GiB.
"""
from pathlib import Path
import json
import os
import shutil
import time

CAP=4*1024**3
RSS_INTERVAL=.05
GROUP_INTERVAL=1.0
DISK_FLOOR=64*1048576


class OwnedResourceGuard:
    def __init__(self,out,deadline,owned,result):
        self.out=Path(out);self.events=self.out/'events.jsonl';self.deadline=deadline
        self.owned=owned;self.result=result;self.self_pid=os.getpid()
        self.owner=self._pid_stat(self.self_pid)
        if self.owner is None:raise ValueError('controller identity unavailable')
        self.event_token=None;self.event_cache_token=None;self.event_cache=None
        self.group=None;self.leader=None;self.leader_present=False;self.stage_closed=True
        self.cached={self.self_pid:self.owner};self.next_group=0.;self.next_rss=0.
        self.maximum_rss=0;self.last_reason=None;self.first_sample=None;self.last_sample=None
        self.counts={key:0 for key in ('calls','clock_checks','stop_checks','owner_identity_checks','leader_identity_checks','event_reads','membership_scans','stage_changes','exit_refreshes','RSS_samples','RSS_identity_checks','RSS_status_reads','final_scans')}

    def _clock(self):return time.monotonic()

    def _disk_free(self):return shutil.disk_usage(self.out).free

    def _pid_stat(self,pid):
        try:
            raw=Path('/proc',str(pid),'stat').read_text();tail=raw[raw.rfind(')')+2:].split()
            return {'pid':pid,'start_ticks':int(tail[19]),'pgrp':int(tail[2]),'ppid':int(tail[1]),'state':tail[0]}
        except FileNotFoundError:return None

    def _read_rss(self,pid):
        try:
            lines=Path('/proc',str(pid),'status').read_text().splitlines()
            values=[int(line.split()[1])*1024 for line in lines if line.startswith('VmRSS:')]
            return values[0] if values else 0  # A zombie has no VmRSS entry.
        except FileNotFoundError:return None

    @staticmethod
    def _same(a,b):
        return a is not None and b is not None and all(a[key]==b[key] for key in ('pid','start_ticks','pgrp'))

    def _event(self):
        try:stat=self.events.stat()
        except FileNotFoundError:return None
        token=(stat.st_mtime_ns,stat.st_size)
        if token!=self.event_cache_token:
            self.counts['event_reads']+=1;lines=self.events.read_text().splitlines()
            if not lines:raise ValueError('empty child event log')
            value=json.loads(lines[-1])
            if value.get('event')!='child_start' or type(value.get('pid')) is not int or value['pid']<=0:raise ValueError('invalid registered child event')
            self.event_cache={'token':token,'pid':value['pid']};self.event_cache_token=token
        return self.event_cache

    def _scan(self,group):
        self.counts['membership_scans']+=1
        return self.owned._all_members(group)

    def _sync_event(self):
        event=self._event()
        if event is None:
            return 'OWNED_EVENT_MISSING' if self.event_token is not None else None
        if event['token']==self.event_token:return None
        new_group=event['pid']
        if self.group==new_group and not self.stage_closed and self.leader is not None:
            current=self._pid_stat(new_group)
            if current is not None and not self._same(current,self.leader):return 'OWNED_STAGE_IDENTITY_CHANGED'
        if self.group is not None and new_group!=self.group:
            # Completed stages must already have been reaped by the unchanged
            # owned runner before a new child is registered.
            if self._scan(self.group):return 'PREVIOUS_OWNED_GROUP_OPEN'
        current=self._pid_stat(new_group)
        if current is not None and (current['pgrp']!=new_group or current['ppid']!=self.self_pid):return 'OWNED_STAGE_IDENTITY_CHANGED'
        self.event_token=event['token'];self.group=new_group;self.leader=current
        self.leader_present=current is not None;self.stage_closed=False
        self.cached={self.self_pid:self.owner};self.next_group=0.;self.next_rss=0.
        self.counts['stage_changes']+=1
        return None

    def _refresh_members(self,final=False):
        if self.group is None:return None
        rows=self._scan(self.group);new={self.self_pid:self.owner}
        for row in rows:
            current=self._pid_stat(row['pid'])
            if current is None:continue  # Exit between scan and identity read.
            if current['start_ticks']!=row['start_ticks'] or current['pgrp']!=self.group:return 'OWNED_MEMBER_IDENTITY_CHANGED'
            previous=self.cached.get(row['pid'])
            if previous is not None and not self._same(current,previous):return 'OWNED_MEMBER_IDENTITY_CHANGED'
            if row['pid']==self.group and (self.leader is None or not self._same(current,self.leader)):return 'OWNED_STAGE_IDENTITY_CHANGED'
            new[row['pid']]=current
        self.cached=new
        self.stage_closed=not self.leader_present and len(new)==1
        self.next_group=self._clock()+GROUP_INTERVAL;self.next_rss=0.
        if final:self.counts['final_scans']+=1
        return None

    def _sample_rss(self):
        rss=0
        for pid,expected in list(self.cached.items()):
            self.counts['RSS_identity_checks']+=1;before=self._pid_stat(pid)
            if before is None:
                if pid==self.self_pid:return 'CONTROLLER_IDENTITY_MISSING'
                del self.cached[pid];self.next_group=0.;continue
            if not self._same(before,expected):return 'OWNED_MEMBER_IDENTITY_CHANGED'
            self.counts['RSS_status_reads']+=1;value=self._read_rss(pid);after=self._pid_stat(pid)
            if after is None:
                if pid==self.self_pid:return 'CONTROLLER_IDENTITY_MISSING'
                del self.cached[pid];self.next_group=0.;continue
            if value is None or value<0:return 'OWNED_RSS_UNREADABLE'
            if not self._same(after,expected):return 'OWNED_MEMBER_IDENTITY_CHANGED'
            rss+=value
        self.counts['RSS_samples']+=1;self.maximum_rss=max(self.maximum_rss,rss)
        self.result['maximum_observed_owned_RSS_bytes']=max(self.result.get('maximum_observed_owned_RSS_bytes',0),rss)
        sample={'monotonic':self._clock(),'RSS_bytes':rss,'known_PID_count':len(self.cached),'group':self.group}
        if self.first_sample is None:self.first_sample=sample
        self.last_sample=sample;self.next_rss=self._clock()+RSS_INTERVAL
        return 'OWNED_RSS_LIMIT' if rss>CAP else None

    def reason(self,_job=None,end=None):
        self.counts['calls']+=1
        try:
            limit=min(self.deadline,end if end is not None else self.deadline)
            self.counts['clock_checks']+=1
            if self._clock()>=limit:return self._stop('OWNED_DEADLINE')
            self.counts['stop_checks']+=1
            if self.owned._STOP_REQUESTED:return self._stop('EXTERNAL_STOP')
            self.counts['owner_identity_checks']+=1
            if not self._same(self._pid_stat(self.self_pid),self.owner):return self._stop('CONTROLLER_IDENTITY_CHANGED')
            if self._disk_free()<DISK_FLOOR:return self._stop('DISK_FREE_FLOOR')
            stop=self._sync_event()
            if stop:return self._stop(stop)
            if self.group is not None and not self.stage_closed:
                self.counts['leader_identity_checks']+=1;current=self._pid_stat(self.group)
                if current is not None:
                    if self.leader is None or not self._same(current,self.leader):return self._stop('OWNED_STAGE_IDENTITY_CHANGED')
                elif self.leader_present:
                    self.leader_present=False;self.next_group=0.;self.counts['exit_refreshes']+=1
                if self._clock()>=self.next_group:
                    stop=self._refresh_members()
                    if stop:return self._stop(stop)
            if self._clock()>=self.next_rss:
                stop=self._sample_rss()
                if stop:return self._stop(stop)
            # A membership/status scan must not hide a deadline or stop arriving
            # while it ran. Cleanup remains the original owned controller's job.
            self.counts['clock_checks']+=1
            if self._clock()>=limit:return self._stop('OWNED_DEADLINE')
            self.counts['stop_checks']+=1
            if self.owned._STOP_REQUESTED:return self._stop('EXTERNAL_STOP')
            return None
        except (OSError,ValueError,KeyError,IndexError,TypeError):return self._stop('OWNED_RESOURCE_OBSERVER_ERROR')

    def _stop(self,reason):
        self.last_reason=reason;return reason

    def finalize(self):
        """Full end observation, even after a failed deadline; never signals."""
        try:
            if self.group is not None:
                current=self._pid_stat(self.group)
                if current is not None and self.leader is not None and not self._same(current,self.leader):return self._stop('OWNED_STAGE_IDENTITY_CHANGED')
                self.leader_present=current is not None
                stop=self._refresh_members(final=True)
                if stop:return self._stop(stop)
            stop=self._sample_rss()
            return self._stop(stop) if stop else None
        except (OSError,ValueError,KeyError,IndexError,TypeError):return self._stop('OWNED_RESOURCE_OBSERVER_ERROR')

    def snapshot(self):
        return {'policy_version':3,'RSS_cap_bytes':CAP,'known_PID_RSS_interval_seconds':RSS_INTERVAL,'complete_group_refresh_interval_seconds':GROUP_INTERVAL,
            'scope':'controller plus cached verified members of current registered new-session child group; clock/stop and controller/active-leader identity every loop',
            'visibility_gap':'new descendants may await next1s membership refresh plus loop/scan work; aggregate RSS is sampled, not continuous',
            'full_start_end_cleanup':'stage registration refresh, finalization refresh, plus unchanged owned runner full end/reap scans',
            'counts':dict(self.counts),'maximum_observed_owned_RSS_bytes':self.maximum_rss,'first_sample':self.first_sample,'last_sample':self.last_sample,'last_reason':self.last_reason,
            'guard_launches_or_signals_processes':False}
