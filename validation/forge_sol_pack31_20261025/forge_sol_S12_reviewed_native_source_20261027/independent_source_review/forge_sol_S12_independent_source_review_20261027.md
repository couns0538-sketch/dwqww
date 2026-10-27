# S12 native-prep independent source review

Source preparation is reviewable **with the separate reviewed ON-framing successor**; no demonstrated must-fix remains in that successor. The frozen original44 packet still contains the ON bench observer bug and must not be used unchanged for that stage.

Found and reproduced: normal OFF S25 rejects the required ON active+8stats prefix. A source-framed synthetic raw fixture produced bench_prefix_bytes951 despite correct nodes/diagnostics. The separate parser now validates every original byte, exact diagnostics/order/terminal, raw hashes and closed EOF. A second requested closure fix now pins/records/postchecks parser and runner source. OFF S25 remains strict.

Reviewed successor pins: parser023508d16cf5d5468a45b2a0706975f82f06deb2aca96a162dc4488ba3ecb586; runner2d5bbf131766201ce02d3e8d6739a2f56d12ae0bf55b7f66f20f7ff5a41e8433; tool diff869db8452fa37b26ab649e20ba80a32528285c4b06f6d4f6aebb85dc8ece14e1.

Verified44 frozen payloads unchanged; actual LP/B Release+ASAN baseline bindings; complete v2 source maps from pristine+six patched files; exact ABI/core/link-map gates; baseline17-failure RED policy; one-Worker8192-root/1024-transition oracle source704dadab. Compiler4GiB AS caps are in separate processes; ASAN runtime entrypoints explicitly require unlimited AS and leak/UB halt settings. No stale v1 candidate map is used.

Independently ran34 original +27 successor pure tests on CPU4nice19: PASS. These are tools/fixtures only. C++ compile, native FIRST/current Std/ASAN/ON, actual RED/counter/alias/parity, speed, Elo, Windows and adoption remain UNVERIFIED. No compiler/engine/native/Git or agent spawn, no frozen-file edits. Root retains ordered S11 publication/native lease control.

Detailed review JSON SHA256: `009d0cbb220d6713458eb0669e060e8148dea63a0843149a5dd20fc949a98b89`.
