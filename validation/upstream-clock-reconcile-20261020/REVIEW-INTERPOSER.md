# Follow-up review of helper-observation correction

The production review in REVIEW.md remains against frozen source
cecf0b9e3af5602053bcaf5c5d16ffc09f58850d. Its recorded diagnostic hash refers
to the original unexecuted GNU-wrap version, now preserved byte-for-byte in
witnesses-release-attempt1/automatic-origin-api-attempt1.cpp.

The corrected diagnostic exports pthread_create from its executable and delegates
to the next ELF definition with dlsym(RTLD_NEXT). It records actual successful
creation boundaries without delays or failure injection. This reaches the
libstdc++ shared-library calls that GNU --wrap did not observe. Missing resolution
aborts; a zero/missing helper count still fails the validity gate. This change is
only in the diagnostic and is absent from all production engine/core builds.

Root reviewed the symbol/delegation logic and checked saved PASS summaries for
Release attempt2 and ASan attempt1, including unchanged input hashes. The old
886 core yields the expected five failing untimed/ponder modes and two passing
timed modes; the new core yields seven passing main-worker origin modes. Each
valid row observes three actual helper creations. Production full CTest executes
separately without this interposer. TSan results must remain pending until its
own instrumented build and witness finish; no detector option may be disabled.

The main-worker-only and direct-API limitations in REVIEW.md still apply. This
review establishes neither every-helper timing observation nor speed, Elo or a
remedy for the separate hosted baseline forfeit.

Corrected diagnostic SHA256: f17a3444e7be71dd3443c294d27c92b5b380933471fb9b63cd66c6ccf33174a5
