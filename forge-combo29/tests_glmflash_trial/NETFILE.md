# Net file used (NOT committed — binaries/net files are forbidden in the repo)

Command (run with python -I from /tmp/glmflash/net, outside the repository):
  python3 -I /tmp/glmflash/fable_nnue_v3.py random /tmp/glmflash/net/glmflash_net.fnn3 --hidden 512 --king-buckets 8 --output-buckets 8 --mirror

Script source: branch fable/standalone-h512-20261111, file h512/train/fable_nnue_v3.py
  (extracted with: git show FETCH_HEAD:h512/train/fable_nnue_v3.py > /tmp/glmflash/fable_nnue_v3.py
   after: git fetch origin fable/standalone-h512-20261111)

Output line from the script:
  wrote /tmp/glmflash/net/glmflash_net.fnn3 hidden 512 kb 8 ob 8 flags 2 checksum d80a4532f35587f

Size:    6309096 bytes
sha256:  e3ef99b7264d9c079f1c1e5ea8732bd576803e7bbfb2b00d138e53465dc8b375
