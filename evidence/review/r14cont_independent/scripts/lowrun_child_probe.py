import ctypes,os,psutil
p=psutil.Process()
print("affinity",p.cpu_affinity(),"nice",int(p.nice()),"cuda",os.environ.get("CUDA_VISIBLE_DEVICES"),"hip",os.environ.get("HIP_VISIBLE_DEVICES"))
