# EXE IDENTITIES — every binary I ran, so any number can be tied to an executable

Written 2026-11-17T00:13:36Z after S-F63 (a behavioural claim needs the
binary, not just the settings). Jobs before job73 predate the rule and carry no stamp of their own; **this file is
their stamp** — a legacy job's numbers come from one of the builds below, and any job that named its build now has
that build's hash here.

| build | sha256 | id name |
|---|---|---|
| base 6b98f217 (release) | `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83` | Chess Engine Forge 6.4.24 candidate |
| base 6b98f217 (ASan+UBSan) | `7af51a7f90cbf32b214c3fc35d7410ff037430bc4ce1d4a8c59619db418b835c` | Chess Engine Forge 6.4.24 candidate |
| PC r15 (release, file5 patch) | `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4` | Chess Engine Forge 6.4.24 candidate |
| PC r15 + seat30 ttclear repair | `4d0a268bd1ca88de265fd898844b57baf0ef5a59dfea404c01f08d661f45c25d` | Chess Engine Forge 6.4.24 candidate |
| PC r15 + alt-table 64MB cap | `863617ba237a5c15c3614048f3173544db97e3c134ec93e8ca0322690f4e21e5` | Chess Engine Forge 6.4.24 candidate |
| PC r15 + shared table | `82f30eeebd86362efe19ee681e86423e33a0d2438d39c5be9d9c81671aa52ca6` | Chess Engine Forge 6.4.24 candidate |
| PC r15 + alt-table 8MB own | `c8775c0998e4f3c82786940e36f329b1c3234c4ebb310c2243eccff3222fff60` | Chess Engine Forge 6.4.24 candidate |

Both release builds report the same `id name`; only the **sha256** distinguishes them, which is exactly why the
rule is about the hash and not the banner.

Honesty pins, all four builds that can be built clean: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920,
perft 5 = 4865609 (default options). See HONESTY.txt for the base run.
