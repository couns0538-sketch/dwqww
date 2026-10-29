# source me: R6 environment for the nnue-pytorch ROCm venv (read-only use of the venv)
export VENV=/f/nnue_pytorch/venv
export PY="$VENV/Scripts/python.exe"
export PATH="$VENV/Scripts:$PATH"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export TMP="F:/opus_scratch/r6/tmp" TEMP="F:/opus_scratch/r6/tmp"
export TRITON_CACHE_DIR="F:/opus_scratch/r6/triton_cache"
export TORCHINDUCTOR_CACHE_DIR="F:/opus_scratch/r6/inductor_cache"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUTF8=1
