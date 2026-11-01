"""CR C0005114 boundary admission policy; no process suspension or timing subtraction.

Original implementation matching the supplied review patch. Windows API semantics:
https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getsystemtimes
https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-globalmemorystatusex
GetSystemTimes includes idle in kernel time; >64 CPUs fail closed because it then
reports only the calling thread's processor group. This PC has 16 logical CPUs.
"""
from __future__ import annotations

import ctypes
import json
import math
import os
from pathlib import Path
import sys
import threading
import time

START_CPU = 80.0
ONGOING_CPU = 90.0
WAIT_SECONDS = 60
MIN_FREE = 8 * 1024 ** 3  # The supplied CR patch uses 8 GiB available physical RAM.
MAX_AGE = 1.5
PATCH_MD5 = 'C0005114DE753177DE0EB7ECE944B438'


def percent_from_times(previous, current):
    idle = current[0] - previous[0]
    total = current[1] - previous[1]
    if total <= 0 or idle < 0 or idle > total:
        raise RuntimeError('Invalid GetSystemTimes delta; refusing work')
    return 100.0 * (1.0 - idle / total)


class WindowsMetrics:
    class FileTime(ctypes.Structure):
        _fields_ = [('low',ctypes.c_uint32),('high',ctypes.c_uint32)]
    class MemoryStatus(ctypes.Structure):
        _fields_ = [('length',ctypes.c_uint32),('load',ctypes.c_uint32)] + [
            (name,ctypes.c_uint64) for name in ('total_phys','available_phys','total_page',
                                               'available_page','total_virtual','available_virtual','extended')]

    def __init__(self):
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.GetSystemTimes.argtypes=[ctypes.POINTER(self.FileTime)]*3
        self.kernel.GetSystemTimes.restype=ctypes.c_int
        self.kernel.GlobalMemoryStatusEx.argtypes=[ctypes.POINTER(self.MemoryStatus)]
        self.kernel.GlobalMemoryStatusEx.restype=ctypes.c_int
        self.kernel.GetActiveProcessorCount.argtypes=[ctypes.c_ushort]
        self.kernel.GetActiveProcessorCount.restype=ctypes.c_uint32
        count=self.kernel.GetActiveProcessorCount(0xffff)
        if not count or count>64:
            raise RuntimeError('GetSystemTimes cannot cover this processor topology; refusing work')
        self.cpu_count=count

    def cpu_times(self):
        idle,kernel,user=self.FileTime(),self.FileTime(),self.FileTime()
        if not self.kernel.GetSystemTimes(ctypes.byref(idle),ctypes.byref(kernel),ctypes.byref(user)):
            raise ctypes.WinError(ctypes.get_last_error())
        number=lambda value:(value.high<<32)|value.low
        return number(idle),number(kernel)+number(user)

    def free_ram(self):
        value=self.MemoryStatus()
        value.length=ctypes.sizeof(value)
        if not self.kernel.GlobalMemoryStatusEx(ctypes.byref(value)):
            raise ctypes.WinError(ctypes.get_last_error())
        return value.available_phys


class CachedSampler:
    """One-second system samples; retain peak since the preceding admission boundary."""
    def __init__(self,metrics):
        self.metrics=metrics
        self.lock=threading.Lock()
        self.ready=threading.Event()
        self.stop=threading.Event()
        self.latest=None
        self.peak=0.0
        self.error=None
        self.thread=threading.Thread(target=self._run,daemon=True,name='tmfit-resource-sampler')
        self.thread.start()

    def _run(self):
        try:
            previous=self.metrics.cpu_times()
            while not self.stop.wait(1.0):
                current=self.metrics.cpu_times()
                value=percent_from_times(previous,current)
                previous=current
                with self.lock:
                    self.latest=(value,time.monotonic())
                    self.peak=max(self.peak,value)
                self.ready.set()
        except BaseException as error:
            with self.lock:self.error=error
            self.ready.set()

    def read(self):
        if not self.ready.wait(2.0):
            raise RuntimeError('CPU sampler did not produce a fresh metric; refusing work')
        with self.lock:
            if self.error is not None:
                raise RuntimeError('CPU sampler failed; refusing work') from self.error
            if self.latest is None:
                raise RuntimeError('Missing CPU metric; refusing work')
            value,stamp=self.latest
            peak=self.peak
            self.peak=value
            return value,peak,stamp

    def close(self):
        self.stop.set()
        self.thread.join(timeout=2.0)


class Governor:
    def __init__(self,sampler,free_ram,clock=time.monotonic,sleep=time.sleep,output=sys.stdout):
        self.sampler,self.free_ram=sampler,free_ram
        self.clock,self.sleep,self.output=clock,sleep,output
        self.started=False
        self.checks=self.waits=0
        self.max_cpu=0.0
        self.min_free=None
        self.pending=[]
        self.log=None
        self.closed=False
        self.errors=0

    def _record(self,row):
        row=dict(row,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
        line=json.dumps(row,sort_keys=True)+'\n'
        if self.log is None:self.pending.append(line)
        else:
            self.log.write(line)
            self.log.flush()

    def attach(self,directory):
        if self.log is not None:raise RuntimeError('Governor log already attached')
        self.log=(Path(directory)/'governor.jsonl').open('x',encoding='utf-8',newline='\n')
        self.log.writelines(self.pending)
        self.log.flush()
        self.pending.clear()

    def checkpoint(self,start=None):
        if self.closed:raise RuntimeError('Governor is closed')
        start=not self.started if start is None else start
        limit=START_CPU if start else ONGOING_CPU
        while True:
            try:
                cpu,peak,stamp=self.sampler.read()
                free=self.free_ram()  # Fresh physical availability at every admission attempt.
                if (not isinstance(cpu,(int,float)) or not isinstance(peak,(int,float)) or
                    not math.isfinite(cpu) or not math.isfinite(peak) or not 0<=cpu<=peak<=100 or
                    not isinstance(free,int) or isinstance(free,bool) or free<0 or
                    not isinstance(stamp,(int,float)) or not math.isfinite(stamp) or
                    not 0<=self.clock()-stamp<=MAX_AGE):
                    raise RuntimeError('Missing, invalid, or stale resource metric; refusing work')
            except BaseException as error:
                self.errors+=1
                self._record(dict(action='error',reason=str(error)))
                raise RuntimeError('Resource governor failed closed') from error
            self.checks+=1
            self.max_cpu=max(self.max_cpu,peak)
            self.min_free=free if self.min_free is None else min(self.min_free,free)
            allowed=peak<limit and free>=MIN_FREE
            self._record(dict(action='admit' if allowed else 'wait',start=start,cpu_percent=cpu,
                              peak_since_boundary=peak,limit_percent=limit,free_ram_bytes=free,
                              minimum_free_bytes=MIN_FREE,wait_seconds=0 if allowed else WAIT_SECONDS))
            if allowed:
                self.started=True
                return
            self.waits+=1
            print(f'governor: peak CPU {peak:.1f}% (limit <{limit:.0f}%), free RAM {free/1024**3:.2f} GiB; waiting 60s before work',
                  file=self.output,flush=True)
            self.sleep(WAIT_SECONDS)

    def snapshot(self):
        return dict(status='WINDOWS_BOUNDARY_ADMISSION',cr_patch_md5=PATCH_MD5,
                    start_cpu_below=START_CPU,ongoing_cpu_below=ONGOING_CPU,
                    minimum_free_physical_bytes=MIN_FREE,wait_seconds=WAIT_SECONDS,
                    max_sample_age_seconds=MAX_AGE,checks=self.checks,waits=self.waits,errors=self.errors,
                    maximum_observed_cpu_percent=self.max_cpu,minimum_observed_free_ram_bytes=self.min_free,
                    scope='Admission before work units; no instantaneous ceiling during an already-running unit',
                    active_process_suspension=False,active_timing_subtraction=False,
                    external_suspension_detection='not claimed')

    def close(self):
        if self.closed:return
        self.sampler.close()
        if self.log is not None:self.log.close()
        self.closed=True


_current=None


def current():
    global _current
    if _current is None and os.name=='nt':
        metrics=WindowsMetrics()
        _current=Governor(CachedSampler(metrics),metrics.free_ram)
    return _current


def load_governor(start=None):
    controller=current()
    if controller is not None:controller.checkpoint(start)


def attach(directory):
    controller=current()
    if controller is not None:controller.attach(directory)


def snapshot():
    controller=current()
    return controller.snapshot() if controller is not None else dict(
        status='NON_WINDOWS_NOT_APPLICABLE',cr_patch_md5=PATCH_MD5,
        scope='Windows PC governor is not claimed for Linux CI',active_process_suspension=False,
        active_timing_subtraction=False)


def finish(directory):
    controller=current()
    if controller is not None:controller.close()
    with (Path(directory)/'governor-receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(snapshot(),stream,indent=2,sort_keys=True)
        stream.write('\n')
