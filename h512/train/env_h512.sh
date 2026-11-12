# source me: JOB E environment (ROCm venv read-only; caches and temp inside the job folder)
export H512_ROOT="D:/forge_jobs_20261111/h512E"
export PY="/f/nnue_pytorch/venv/Scripts/python.exe"
export PATH="/f/nnue_pytorch/venv/Scripts:$PATH"
export TMP="$H512_ROOT/_work/cache/tmp" TEMP="$H512_ROOT/_work/cache/tmp"
export TRITON_CACHE_DIR="$H512_ROOT/_work/cache/triton"
export TORCHINDUCTOR_CACHE_DIR="$H512_ROOT/_work/cache/inductor"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
