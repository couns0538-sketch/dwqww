#!/usr/bin/env bash
# Proof that the ThreadSanitizer installed here REPORTS a race. Without this, a
# clean engine run means "no report" and not "no race" (brief rule 3).
set -u
mkdir -p /tmp/tsan-proof && cd /tmp/tsan-proof
cat > race.cpp <<'EOF'
#include <cstdio>
#include <thread>
int shared = 0;
int main() {
  std::thread a([]{ for (int i = 0; i < 100000; ++i) ++shared; });
  std::thread b([]{ for (int i = 0; i < 100000; ++i) ++shared; });
  a.join(); b.join();
  std::printf("%d\n", shared);
}
EOF
g++ -fsanitize=thread -g -O1 race.cpp -o race
./race > out.txt 2>&1
hits=$(grep -c 'ThreadSanitizer' out.txt || true)
echo "planted race: ThreadSanitizer mentions = $hits (expect > 0)"
grep -m1 'WARNING: ThreadSanitizer' out.txt || true
[ "$hits" -gt 0 ]
