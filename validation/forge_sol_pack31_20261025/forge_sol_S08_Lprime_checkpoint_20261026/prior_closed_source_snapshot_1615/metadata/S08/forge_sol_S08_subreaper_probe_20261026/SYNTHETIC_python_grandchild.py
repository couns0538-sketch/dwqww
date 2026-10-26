import subprocess,sys,time
p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(20)"])
print(p.pid,flush=True)
time.sleep(20)
