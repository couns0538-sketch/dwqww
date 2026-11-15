#include <pthread.h>
#include <cstdio>
int g = 0;
static void* writer(void*) { for (int i = 0; i < 100000; ++i) g = i; return nullptr; }
static void* reader(void*) { int s = 0; for (int i = 0; i < 100000; ++i) s += g; printf("%d\n", s); return nullptr; }
int main() {
  pthread_t a, b;
  pthread_create(&a, nullptr, writer, nullptr);
  pthread_create(&b, nullptr, reader, nullptr);
  pthread_join(a, nullptr);
  pthread_join(b, nullptr);
  return 0;
}
