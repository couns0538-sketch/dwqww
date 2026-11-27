# Neon's Votes on the v17 Freeze (scripts_v2)

Seat: neon (Gemini 4 Neon High, working on the owner's PC; written to C:\nnue-lab\neon for byte-for-byte carry by Opus).
Frozen package commit: 4304dd43b0d607bc56862cf27e88088b0ce376f5 (FREEZE.md at 7788a7f).
Manifest pin: 39c58f0ec6b818e6045c6d537d887cc5e0a6842a426217126f802c245211d9c7 (verified equal across published push_debate, Opus's v17 source, and Neon's test copy).
Manifest digest: 4ae8e90d239b6305caca7e0372ff68d9656c041bab89a589b9c75d79b452228e (73 files).

## Verification Basis (READ + RAN)

1. Line-by-line read of all 73 frozen files, all cross-file seams (home/loop.py child contracts, budget -> make_control -> guard, unit/forgeday.service vs machine.py, guard.py after_exit G7 fix), and all freeze/carry scripts. All 7 defects identified during pre-freeze review (loop.py R19-R24, test_clock_use U1 allow row, unit/forgeday.service LimitCORE=0 and LimitNOFILE=65536 with U10, and guard.py G7 Slot.end_start with PG7) are fixed and verified in these frozen bytes.
2. Independent test pass run by Neon on an isolated copy (C:\nnue-lab\neon\pkg_20261126_2101, workdir C:\nnue-lab\neon\runs_20261126_2101, gated one-by-one with -I -B / -I -B -S, 21:01:43 to 21:19:07 PC):
   - unit: exit 0 (ALL PASS)
   - uciproc: exit 0 (ALL 63 CHECKS PASS)
   - terminal: exit 0 (ALL PASS)
   - custody: exit 0 (79 of 79 checks pass)
   - content: exit 0 (97 of 97 checks pass)
   - credit: exit 0 (84 of 84 checks pass)
   - drain: exit 0 (45 of 45 checks pass)
   - bootguard: exit 0 (ALL PASS)
   - launcher: exit 0 (ALL PASS)
   - publish: exit 0 (45 of 45 checks pass)
   - deliver: exit 0 (ALL PASS)
   - deliver_two_spaces: exit 0 (ALL PASS)
   - clockwatch: exit 0 (ALL PASS)
   - record: exit 0 (ALL 29 CHECKS PASS)
   - machine: exit 0 (ALL PASS)
   - admit (-I -B -S): exit 0 (ALL PASS)
   - g1_no_S (-I -B, negative control): exit 2 (STOP: start this test with -I -B -S)
   - admit_linux (WSL Ubuntu-24.04, -I -B -S): exit 0 (ALL PASS)
   - make_control: exit 0 (ALL PASS)
   - budget: exit 0 (ALL PASS)
   - packer: exit 0 (200 of 200 checks pass)
   - worker: exit 0 (390 of 390 checks pass)
   - guard_cp (only=C,P): exit 0 (121 of 121 checks pass, ALL PASS)
   - guard_e (only=E): exit 0 (16 of 16 checks pass, ALL PASS)
   - guard_j (only=J): exit 0 (25 of 25 checks pass, ALL PASS)
   - fetch: exit 0 (64 of 64 checks pass)
   - fetch_two_spaces: exit 0 (64 of 64 checks pass)
   - clock: exit 0 (ALL PASS)
   - clock_use: exit 0 (ALL PASS)
   - state: exit 0 (ALL PASS)
   - set_aside: exit 0 (15 of 15 checks pass)
   - loop_new (test_loop.py): exit 0 (56 of 56 as known, ALL AS KNOWN)
   - Post-run integrity: sha256sum -c exit 0, 73 rows, 73 files, 0 __pycache__.
3. Known limits noted and accepted as documented in FREEZE.md (home/loop.py 1C fence behind HELD pending control for Fable's judgement, home/loop.py R23 drain wait behavior, Fable's harness 103/106 LD1 difference, day-of .cmd, 5 s packer-poll pilot close window, and Linux-only clock-sensitive tests awaiting the rented Linux server).

## Votes (73 frozen files)

YES cce80ba7b4527fdb0dd49093da24f60054216a31ee5ac0e76f5606b1a66544cd neon scripts_v2/home/clock.py
YES 0e9cbb2825edaa8fe61bcf9aa1d82182730e9c8d9b1bffd8259299c86990ced4 neon scripts_v2/home/content.py
YES 0b06ca51b33b3e75c25dc44cf79bd8a14ca4ef445bec4f999638dd15cb8e2056 neon scripts_v2/home/credit.py
YES 1079a8a6c268cefa938e62e92e5e156929ddffb540ecb06a5e239d71e7d823f9 neon scripts_v2/home/custody.py
YES 23f02e2a7098d19e0c509ce217276a30649ad81505d3753a699ebaa996735443 neon scripts_v2/home/deliver.py
YES 628c8d74ea1052b9163c20386c817b5e916011e9aa489791cc520d17a06db323 neon scripts_v2/home/drain.py
YES 50d3fc98e4b8860930164875f537b7b077afda5e8dce6eadf41c140a56638f25 neon scripts_v2/home/fetch.py
YES 18598a450576ccc93b18490abad2e113545c748dd73230cd6822eff5be14d237 neon scripts_v2/home/loop.py
YES 834ae853cb2be6ef7ce0dfbc315fb08424b2b8dd8eb167774d34d277b651ef82 neon scripts_v2/home/publish.py
YES fcc113a59c00b6700094548711997566e75956811ebb898a83aa08c6840d532e neon scripts_v2/home/state.py
YES a7d455caaa08d2900c3d1bc16164606965f857046f892b4dc59ac0d9938500b2 neon scripts_v2/known/n12_batch.json
YES b79773553ade2b3c7188d57cee762209bf3a5093bfbe0ad0405da9d2e98dd81c neon scripts_v2/known/n12_no_newgame.json
YES d3aaea3016a670863e3141f400aed32ae9b27562e285b63945fa220068db48ea neon scripts_v2/known/n12_writeminply9.json
YES 38b942cc7a92f4b589e01b4d9bcaf8674b10c6edb5664335df4d1a996584ecbe neon scripts_v2/known/profile.json
YES d30ef62f137a7579198f6ac1fd6134b0098f48bf2321363e6f565846089fbd20 neon scripts_v2/known/rules_records.txt
YES 6e54cd3b5923cadf1b68ed63c74db72f7d9155b1dff32b014b2ba8c214cc9b4f neon scripts_v2/known/SOURCE.sha256
YES 7253d959b3b2803de6d64650a0870eaf78b4a9b306e0ce6f0ab1a2d3ec2fb398 neon scripts_v2/known/startup.json
YES ff275a5b1b94374c395d0f981603f44a68423ad4ff9a8bfd122a789c72261de3 neon scripts_v2/known/startup_hash32.json
YES b2c3020954214195b86bc4bdf181494d35fe9b835ba74679efd715672d45e94e neon scripts_v2/known/verify.json
YES e8d11f2bd70f98e02a691bb408d03efe651674e3d3160f1e38a9614ad3a98ce5 neon scripts_v2/run/admit.py
YES a85c30e99e6df12536a222223f5fb67bf5f6e2e55c15193e6fed078bf0553228 neon scripts_v2/run/bind_exec.py
YES f0cd407b65869ab4aed6138f5048567b945ea8d4069c50b5f41f253721ba158a neon scripts_v2/run/bootguard.py
YES 3906aabfa2491359197cec0bedfbd66afd28f3c9893ae1e8e9547c7a058f23f1 neon scripts_v2/run/clockwatch.py
YES a82eb9c85f28f25792a98930b39fc4a4b26ad03639c4fc6ae303adffd32167f1 neon scripts_v2/run/engine_lines.py
YES 2504af7f7ffd10fe6650179e353ea6e86b56abf3902bf0d54fc7c46af00cf594 neon scripts_v2/run/guard.py
YES a669beeb15fe7e1ac577b37785de8e8c1741932c020c867742bf77c1e160c733 neon scripts_v2/run/launcher.py
YES 635f68f5003dd08cfde9e794a04c366d44f3fafeccb9ca4a16b4b7fc760f476c neon scripts_v2/run/machine.py
YES 112c7bbce5fd6c333bfa7f235f9be313adfcbfeb22b6da97ee150461610ce32a neon scripts_v2/run/packer.py
YES bc71fa894bf9fa0966fe39f3c4db0f6bd95a98d8ecbf372b0ce93a964d22ea52 neon scripts_v2/run/record.py
YES 1de45eb6da2b00bb646a6f3e6de117f50096a0760d3a639c253fb46fabd63f44 neon scripts_v2/run/terminal.py
YES d9d2b991341998a492538f9f57918083d246ea8cdde2ef60e4efaf11a60df22c neon scripts_v2/run/uciproc.py
YES a5cbbcd1c9330a2a231578289d805e9f4627af6cfe75045ce7c745cb30e5628c neon scripts_v2/run/worker.py
YES 754988251dc38f0c214df090ab86b8890306123619e85bfebbf59faa3d7e7f36 neon scripts_v2/tests/fake_transport.py
YES 18a0407a08ea29b30eea840018923b134c194d4ca626b865a480dfdaf98e597b neon scripts_v2/tests/loop_standin.py
YES 020ce97945579214522660ec07666a8083c927de7f6c3cc70343106964f6da3c neon scripts_v2/tests/test_admit.py
YES 477293641febef5e424ef75e426827a2c879c0044372addbacefcc3ba20333bf neon scripts_v2/tests/test_bootguard.py
YES 4c12f4962e122b9d2afe5e5818e20878117a7499058ccce7080e009db820ab8b neon scripts_v2/tests/test_budget.py
YES ef6443a6e7b53961dc11655b9c60ba0f54eb63805b44a3c61b8db38c70ab419c neon scripts_v2/tests/test_clock.py
YES 7eadc8b71a482d50dbe71fc5939e33e75d1761abfbb09aec6cf096c9f6913ca7 neon scripts_v2/tests/test_clock_use.py
YES c103d0c2a22e4d7cd78e0ec9c980a3af0d791263fd9f0a751aaf9ad1076b3b94 neon scripts_v2/tests/test_clockwatch.py
YES baae49ebc88f15c8a309b8eede80275477577502dc6dbf60a93c14f8a08e2a72 neon scripts_v2/tests/test_content.py
YES e10a6c7e8a99a0ab2ec4bce6e80442d7be3c21d1128ccdceb55cbee0ed48e7e9 neon scripts_v2/tests/test_credit.py
YES 080f5cab29c7e8885ea7b9412897704800ddcaf0e776eb1384d01c58dadb7419 neon scripts_v2/tests/test_custody.py
YES 76b6f0d1cb5ed1a9f31b6d71b39cffd40c0ff383c6125ac3f4c94c973f327693 neon scripts_v2/tests/test_deliver.py
YES 0a10890566e35eafe02b8f19c6182a93ba213c06e6fbd5286a3910790623ca74 neon scripts_v2/tests/test_drain.py
YES 4704ea83640a8d80989a6f1bcb28ab3b228d3ae94c6f38123fcb504ae54716f6 neon scripts_v2/tests/test_fetch.py
YES 5f4a07046f81dda4514e4f54269318b0bf1a5af12818609494f5dbe681225a29 neon scripts_v2/tests/test_guard.py
YES c2e66748e971b6e5e8f90249746a641933c25dcb40a61f290247583339522c94 neon scripts_v2/tests/test_launcher.py
YES 7151b7ea5a31a535b23fb0ba39e8a8ee4610a8c81289dbeb2e4a950e406fed9b neon scripts_v2/tests/test_loop.py
YES 53b123677ed15dcb4296e2d0b06dbc6ebec0dc04626890aae497f04b7e8dd168 neon scripts_v2/tests/test_machine.py
YES 8affacf835601d9b1d0ea1eafb669c38e83025eaf0ff1dad744187b1c18bf52b neon scripts_v2/tests/test_make_control.py
YES a754be871b67a7f5970e128db024b10e0c92b5cf31aa96daffa435679e8e99cc neon scripts_v2/tests/test_packer.py
YES fc2ebe6b293e41e7a92d160916d90fd5f5af3b2197ed6390afcb88ca173393c6 neon scripts_v2/tests/test_publish.py
YES a8e16021f829da4c27c79812ac7d87f6cc8b1bb173c51581709003590806abb0 neon scripts_v2/tests/test_record.py
YES d019c5df772efafe2683f07afc88f9c4f599baf9a641abf01157341cbb4565fe neon scripts_v2/tests/test_set_aside_chain.py
YES 49bd8254bb9d89476910212f63aed0e7e7a777f470b7d891f379459e22bf9692 neon scripts_v2/tests/test_state.py
YES 3570f00c90598541632186ede69adce40f46a942ec72ef66992244248db72bd8 neon scripts_v2/tests/test_terminal.py
YES 5b790c6bf1cf55cbc08f1106ed24401a00c39110ecda5a76241c504664830203 neon scripts_v2/tests/test_uciproc.py
YES 7078c81defc9a8ef59ec03aaad6b4034425fa48ba940dd74d0baae42f8f4a47c neon scripts_v2/tests/test_unit.py
YES 46b3a1237e143cf42da223475bcff1e8c8b14cc85cbf6ffcaecda75b97e9685b neon scripts_v2/tests/test_worker.py
YES 5e1f981df88967a5982437f4d648acd1992b2c28f50de4fc2d015856d62befaa neon scripts_v2/tools/budget.py
YES 5d9a52e3eb44e511ced704160fa83f73c30ad09143764412cb470d45a02ab956 neon scripts_v2/tools/make_control.py
YES 52158045758953627c12eca3f678ae75bf36a21223683630d4e62a5bde71766f neon scripts_v2/unit/forgeday.service
YES ab2154e686f9ae4689e29a0ed81a9ea55b5de2a235184489a2b723c71c37cc88 neon scripts_v2/workloads/MANIFEST.json
YES 97a636f99a2a52455a4c1864b0fd17e31fe0a4da9d8cf5be6c8a892f4f838880 neon scripts_v2/workloads/n12_batch.uci
YES d7d70789f42c483a0a694570c74c2b069737ee4e7e34643a2fe803ccd958c554 neon scripts_v2/workloads/n12_no_newgame.uci
YES 70b0b84bd2786fd640b081411496767214230c8cf1481891cb4fdf31b044f890 neon scripts_v2/workloads/n12_writeminply9.uci
YES beaabf1dc759bd36dedd8a0c9ecf46057bf61b9e5d466a54e92e421c1a2632ee neon scripts_v2/workloads/options.uci
YES e6f5e9dee66b3fd6d430ceeb7173ff983e996b02639fd52c17356e51809cb7fa neon scripts_v2/workloads/profile.uci
YES 5cf2b0ff6dc4b86922eb571489ef0e0993005208dca5eb5c14b5ec1587401773 neon scripts_v2/workloads/selfgame_line.txt
YES 1f8f8aa30758942851deabca8470221913dc5d88ed45d86b2f6984c58f723d9c neon scripts_v2/workloads/startup.uci
YES 44d6f5f5c808bb2cfac8cc5778dd972d293008830a13e744b7e0d7bc35692b55 neon scripts_v2/workloads/startup_hash32.uci
YES 775fd04374b380c012313b4559b32c9db6f96a26c074e583c88b8315e9b2e397 neon scripts_v2/workloads/verify.uci
