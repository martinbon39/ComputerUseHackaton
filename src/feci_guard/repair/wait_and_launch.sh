#!/usr/bin/env bash
# Launch the guard arm only when >= 10 GB are available (ares 08:0x: my own VM already runs, ~5 GB floor remains), re-checked twice 30 s apart.
until a=$(free -g | awk '/Mem:/{print $7}'); [ "$a" -ge 10 ] && sleep 30 && [ "$(free -g | awk '/Mem:/{print $7}')" -ge 10 ]; do
  echo "$(date -u +%H:%M:%S) waiting, available ${a} GB"; sleep 60; done
echo "$(date -u +%H:%M:%S) launching guard arm"
exec bash /home/orbit/projects/ComputerUseHackaton/holo-neurochir/feci_guard/run_repair.sh guard $HOME/osw/feci_repair/guard /home/orbit/projects/ComputerUseHackaton/holo-neurochir/feci_guard/repair/episodes.txt 2
