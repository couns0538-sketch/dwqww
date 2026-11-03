"""Owned negative fixture: the launcher must reject this source mutation."""
from pathlib import Path
from run_policy import free_guard
free_guard(16384)
with Path(__file__).open('a',encoding='utf-8') as stream:
    stream.write('\n# Intentional mutation by the launcher negative fixture.\n')
print('Fixture changed its own source; successful qualification must be refused.',flush=True)

# Intentional mutation by the launcher negative fixture.
