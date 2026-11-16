#!/usr/bin/env bash
# build sanitizer engines in their own folders (nothing committed)
set -u
SRC=/agent/repos/base/forge-combo29
for k in asan tsan; do
  if [ $k = asan ]; then
    FLAGS="-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer"
  else
    FLAGS="-fsanitize=thread -fno-omit-frame-pointer"
  fi
  cmake -S "$SRC" -B ~/b/$k -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER=/usr/bin/g++-13 \
    -DCMAKE_CXX_FLAGS="$FLAGS" -DFORGE_MARCH=native > ~/b/$k.cmake.log 2>&1 || { echo "$k cmake FAIL"; continue; }
  make -C ~/b/$k -j4 > ~/b/$k.make.log 2>&1 || { echo "$k make FAIL"; continue; }
  echo "$k built: $(ls -la ~/b/$k/forge | awk '{print $5}') bytes, __asan_=$(nm -C ~/b/$k/forge | grep -c __asan_) __ubsan_=$(nm -C ~/b/$k/forge | grep -c __ubsan_) __tsan_=$(nm -C ~/b/$k/forge | grep -c __tsan_)"
done
