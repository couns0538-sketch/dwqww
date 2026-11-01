import ctypes as C,datetime,json,pathlib,platform,struct,sys
sys.path.insert(0,'D:/a9/pydeps')
import psutil
k=C.WinDLL('kernel32',use_last_error=True)
fn=k.GetLogicalProcessorInformationEx
fn.argtypes=[C.c_int,C.c_void_p,C.POINTER(C.c_uint32)]
n=C.c_uint32(); fn(0,None,C.byref(n)); buf=C.create_string_buffer(n.value)
if not fn(0,buf,C.byref(n)): raise C.WinError(C.get_last_error())
cores=[]; offset=0
while offset<n.value:
    relation,size=struct.unpack_from('<II',buf.raw,offset)
    flags,eff=struct.unpack_from('<BB',buf.raw,offset+8)
    groups=struct.unpack_from('<H',buf.raw,offset+30)[0]
    for j in range(groups):
        mask,group=struct.unpack_from('<QH',buf.raw,offset+32+16*j)
        cores.append({'group':group,'mask':hex(mask),'logical_cpus':[i for i in range(64) if mask>>i&1],
                      'smt':bool(flags&1),'efficiency':eff})
    offset+=size
assert any(c['logical_cpus']==[2,3] for c in cores),'chosen CPUs are not one physical core'
data={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'platform':platform.platform(),
      'physical_cores':cores,'disk_free':{d:psutil.disk_usage(d+':/').free for d in ['C','D']}}
path=pathlib.Path(__file__).parents[1]/'evidence/host.json'
with path.open('x') as f:json.dump(data,f,indent=2)
print(json.dumps(data,indent=2))
