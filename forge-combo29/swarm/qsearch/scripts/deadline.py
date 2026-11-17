import subprocess, signal, time, json, sys
def run_with_deadline(argv, seconds):
    t0=time.time()
    p=subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out,err=p.communicate(timeout=seconds)
        return {"status":"returned","rc":p.returncode,"secs":round(time.time()-t0,3),
                "out":out.strip()[-4000:],"err":err.strip()[-800:]}
    except subprocess.TimeoutExpired:
        try: os.killpg(p.pid, signal.SIGKILL)
        except Exception: pass
        out,err=p.communicate()
        return {"status":"HANG","rc":None,"secs":round(time.time()-t0,3),
                "out":(out or '').strip()[-2000:],"err":(err or '').strip()[-800:]}
