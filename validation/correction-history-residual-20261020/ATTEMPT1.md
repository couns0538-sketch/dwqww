# First preparation attempt

The first script invocation exported both core sources and recorded compiler/history queries, then failed before CMake configuration with FileNotFoundError for cmake. No compile, probe execution or engine search ran. The inherited PATH lacked the installed CMake wrapper. Original command records are in attempt1-commands.json; the untouched first source exports remain under /workspace/.cloud-setup/correction-history-residual-20261020/.

The second attempt pins /workspace/.cloud-setup/venv/bin/cmake and /usr/bin/g++-14, uses a fresh outside-checkout directory, and expresses the history search's literal plus as [+]. This is an environment/setup failure, not an arithmetic result.
