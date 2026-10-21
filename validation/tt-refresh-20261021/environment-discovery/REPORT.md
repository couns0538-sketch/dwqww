# Workspace repository discovery

Retain exactly one project repository: `/workspace/dwqww`, real Git root `/workspace/dwqww`, sanitized origin `github.com/couns0538-sketch/dwqww`, full local HEAD `da8af7c0473e7b85b8be3ce59150ed9f32803134`. HEAD matched at the beginning and end of local Git inspection. This is a local checkpoint observation, not a claim that this particular HEAD was published; the root owns the subsequent onboarding-draft update and publication verification.

A complete physical traversal of `/workspace` ran from03:16:24.267876 to03:16:28.548606UTC on2026-10-21. It scanned10,812 directories and93,169 entries without depth limits or directory exclusions, including hidden paths, Git object stores, toolchain/package caches, source/build exports and archive trees. DIRECTORIES.jsonl retains every directory observation. Five `.git` markers were found; no Git pointer files or additional custom/bare/linked-worktree Git metadata were found. All four nonempty Git metadata directories were independently validated. No traversal errors, inaccessible targets, broken symlinks or unresolved repository candidates occurred.

Repository classifications are explicit:

- `/workspace/dwqww`: the sole retained project.
- `/workspace/.cloud-setup/fastchess`: pinned dependency, HEAD `60d7a7a26c6b0582a15c112fb29a1829bef2adb3`; no origin configured, not a project.
- `/workspace/.cloud-setup/strength-openings-research-20261019/books`: opening-book dependency, HEAD `a804a97e709f40aa75a00f9d19e84915b7a3a45c`; sanitized origin `github.com/official-stockfish/books`.
- `/workspace/.cloud-setup/hosted-strength-pilot/provenance/git-preservation-smoke/throwaway-repo`: provenance fixture, HEAD `0f8718db46e70e70ecff4f9f8fbad9fdad9bf254`; no origin configured.
- `/workspace/.git`: empty platform marker, not a repository.

All266 symlinks are listed without truncation in SYMLINKS.json. Internal directory aliases are covered through their physical targets. The only external directory aliases are the two Wine `dosdevices/z:` links to `/`; they are explicitly outside the physical workspace scope and were not recursively traversed. No claim is made about external repositories elsewhere in `/`. The scan is a bounded observation of a live workspace, not an atomic filesystem snapshot.

Previous discovery receipts were read and hashed; their marker checks were reused and extended with full physical traversal and custom HEAD/objects/commondir detection. Previous receipts are unchanged. Git operations were local read-only rev-parse, remote-name listing and config --get, with optional locks disabled; no status/index refresh, fetch, config or ref mutation occurred. Only sanitized remote host/repository paths are persisted. No network, engine, build, onboarding-draft or source change was performed.

No blocker to retaining the single project was found. The new evidence is confined to this environment-discovery namespace; prior native/trial archives and their original snapshots remain unchanged.
