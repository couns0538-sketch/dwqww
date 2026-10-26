# Wave 14 measured cache proposal

Proposal only: originals retained. Reuses the unchanged wave 13 audit logic with a new output folder, completed wave 13 map collisions, current-day cache exclusion and S08/validation exclusions.

560 source-proven closed external cache groups, 865 complete hardlink aliases: 130,186,874 raw bytes, 48,288,921 measured deterministic gzip6 bytes, 81,897,953 net payload bytes. Projected allocated gain is 82,223,104 bytes (78.41 MiB); the 100 MiB target is explicitly unmet. No remaining eligible external groups were left unmeasured. Largest projected archive is 340,336 bytes.

Scope is only regular historical Forge CMake .o and libforge_core.a cache in explicitly mapped /workspace/.cloud-setup build roots. Preserve repository/source/evidence originals, data, nets, all main/test/helper executables, all existing archives/maps, and active S08. Full alias closure and fresh preserved-source bindings are recorded. A broader delimiter-aware S08-name check over every selected alias passes; frozen audit source and original proposal remain unchanged.

Root must freshly review closure/leases, archive each group sequentially, fsync, verify raw bytes/SHA using Python and GNU gzip decoders, persist all alias metadata in a durable restore map/journal, then retire all aliases with exact link-count accounting. This subagent performed no unlink or archive creation.

The inherited 6 MiB pending-packet projection is an arithmetic scenario, not a prediction of S08 build growth. Proc denials limit any global reference-absence claim.
