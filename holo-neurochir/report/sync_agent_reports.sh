#!/bin/bash
# Copie toutes les 15 min les REPORT.md, budget et verdicts des agents (pod) vers le repo, pour le papier.
D=/home/orbit/projects/ComputerUseHackaton/holo-neurochir/report/agent_reports
while true; do
  for a in $(ssh $POD_SSH 'cd /workspace/astra && ls -d */ | tr -d /'); do
    mkdir -p $D/$a
    rsync -q -e "ssh $POD_SSH_OPTS" --include='*/' --include='REPORT*.md' --include='*VERDICT*' --include='budget.jsonl' --include='*_check.json' --include='summary*.json' --include='OWNER.md' --exclude='*' -m -r $POD_HOST:/workspace/astra/$a/ $D/$a/ 2>/dev/null
  done
  date -u +%H:%M > $D/LAST_SYNC
  sleep 900
done
