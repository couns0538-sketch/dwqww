#!/usr/bin/env bash
set -euo pipefail
cd /workspace/dwqww
setup_root=/workspace/.cloud-setup
mkdir -p "$setup_root/toolchains"
if [ ! -x "$setup_root/venv/bin/python" ]; then python3 -m venv "$setup_root/venv"; fi
"$setup_root/venv/bin/python" -m pip install --no-cache-dir --disable-pip-version-check cmake==3.31.6
"$setup_root/venv/bin/cmake" -S . -B "$setup_root/forge-avx2-build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS='-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off'
"$setup_root/venv/bin/cmake" --build "$setup_root/forge-avx2-build" --parallel 2
PYTHONDONTWRITEBYTECODE=1 "$setup_root/venv/bin/ctest" --test-dir "$setup_root/forge-avx2-build" --output-on-failure
export LLVM_MINGW_ROOT="$setup_root/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64"
if [ ! -x "$LLVM_MINGW_ROOT/bin/x86_64-w64-mingw32-clang++" ]; then
  archive_path="$setup_root/toolchains/llvm-mingw-20261006.tar.xz"
  curl --fail --location --retry 2 --max-time 240 --silent --show-error https://github.com/mstorsjo/llvm-mingw/releases/download/20261006/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64.tar.xz -o "$archive_path"
  printf '%s  %s\n' 5f9c6ed95b2d4bdb2869a488c5fd5857fbdabcf288a0aa3eb1da43f6a08d8ab4 "$archive_path" | sha256sum -c -
  tar -xf "$archive_path" -C "$setup_root/toolchains"
fi
"$setup_root/venv/bin/cmake" -S . -B "$setup_root/forge-windows-zen5" -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=/workspace/dwqww/tools/windows-zen5.cmake
"$setup_root/venv/bin/cmake" --build "$setup_root/forge-windows-zen5" --parallel 2
python3 tools/check_nnue_simd.py "$setup_root/forge-avx2-build/forge"
python3 tools/check_nnue_simd.py "$setup_root/forge-windows-zen5/forge.exe"
# Reproduce the headless Wine runtime without system-directory writes.
python3 - <<'PY'
from pathlib import Path
import hashlib,os,shutil,subprocess,urllib.request
root=Path('/workspace/.cloud-setup');wine=root/'wine';packages=root/'wine-packages'
if not (wine/'usr/lib/wine/wine64').is_file():
    packages.mkdir(exist_ok=True)
    pinned=[
      ('pool/main/w/wine/libwine_10.0~repack-6_amd64.deb','702c99d2fbaef2a4966667e0cdabd477ed1754c1b3b5d4476606eaf5fd6e1444'),
      ('pool/main/w/wine/wine64_10.0~repack-6_amd64.deb','4cdf8319d873c13210815c1aac18859a56ea21b0b2d35a3388dab881464ed488'),
      ('pool/main/libz/libz-mingw-w64/libz-mingw-w64_1.3.1+dfsg-2_all.deb','c4e6d6bfabe8b6d12c797736a3d762d83513b49f488d1aaf61d4526387a2dd3e')]
    for url,digest in pinned:
        archive=packages/Path(url).name
        if not archive.is_file():urllib.request.urlretrieve('https://deb.debian.org/debian/'+url,archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=digest:raise RuntimeError('Wine package checksum mismatch: '+archive.name)
        subprocess.run(['dpkg-deb','-x',str(archive),str(wine)],check=True)
server=wine/'usr/lib/wine/wineserver'
if not server.is_symlink():
    backup=server.with_name('wineserver-debian-wrapper')
    if backup.exists():raise RuntimeError('Preserving existing Wine server wrapper; inspect setup manually')
    server.rename(backup);server.symlink_to('wineserver64')
data=wine/'usr/share/wine/wine'
if not os.path.lexists(data):data.symlink_to('.')
zlib=wine/'usr/lib/x86_64-linux-gnu/wine/x86_64-windows/zlib1.dll'
if not os.path.lexists(zlib):shutil.copyfile(wine/'usr/x86_64-w64-mingw32/lib/zlib1.dll',zlib)
for name,build in [('forge-wine','forge-windows-zen5'),('forge-wine-baseline','forge-windows-baseline')]:
    wrapper=root/name
    if not wrapper.exists():
        wrapper.write_text('#!/usr/bin/env bash\nset -o pipefail\nexport WINEPREFIX=/workspace/.cloud-setup/wine-prefix-ready\nexport WINEDEBUG=-all\nexport XDG_CACHE_HOME=/workspace/.cloud-setup/font-cache\n/workspace/.cloud-setup/wine/usr/lib/wine/wine64 /workspace/.cloud-setup/'+build+'/forge.exe "$@" | stdbuf -oL tr -d "\\r"\n')
        wrapper.chmod(0o755)
PY
mkdir -p "$setup_root/font-cache"
export WINEPREFIX="$setup_root/wine-prefix-ready" WINEDEBUG=-all XDG_CACHE_HOME="$setup_root/font-cache"
"$setup_root/wine/usr/lib/wine/wine64" "$setup_root/forge-windows-zen5/forge_tests.exe"
PYTHONDONTWRITEBYTECODE=1 python3 tools/uci_regression.py "$setup_root/forge-wine" --log "$setup_root/uci-wine-setup.log"
PYTHONDONTWRITEBYTECODE=1 python3 tools/ponder_regression.py "$setup_root/forge-wine"
