#!/bin/bash
cd /tmp/wall/vo
for i in $(seq 1 60); do curl -s -m 3 http://127.0.0.1:8767/health | grep -q ok && break; sleep 3; done
python3 -c "import json;[print(a+'\t'+b) for a,b in json.load(open('lines.json'))]" | while IFS=$'\t' read id txt; do
  [ -s $id.wav ] && continue
  VOICE_API_URL=http://127.0.0.1:8767 ~/.claude/skills/voix-martin/scripts/voix.sh "$txt" -f wav -o /tmp/wall/vo/$id.wav
done
echo ALLDONE
