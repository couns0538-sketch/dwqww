#!/usr/bin/env bash
# Wait for the opus-ci run of <sha> on branch opus-r3-port-c and print its result (gh must run inside the worktree).
SHA=$1
cd /f/opus_scratch/worktrees/opus_r3_port_c || exit 2
id=""
for i in $(seq 1 60); do
  id=$(gh run list --branch opus-r3-port-c --limit 10 --json databaseId,headSha,workflowName \
       --jq ".[] | select(.headSha==\"$SHA\" and .workflowName==\"opus-ci\") | .databaseId" 2>/dev/null | head -1)
  [ -n "$id" ] && break
  sleep 20
done
[ -z "$id" ] && { echo "no opus-ci run found for $SHA"; exit 1; }
echo "run $id"
while true; do
  st=$(gh run view "$id" --json status --jq .status 2>/dev/null || echo unknown)
  [ "$st" = "completed" ] && break
  sleep 60
done
gh run view "$id" --json conclusion,jobs --jq '"conclusion " + .conclusion, (.jobs[] | "job \(.databaseId) \(.name) \(.conclusion)")'
