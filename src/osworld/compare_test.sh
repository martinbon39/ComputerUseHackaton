#!/usr/bin/env bash
# Test-split report (GitHub Actions arms, ~/osw/results_test_gh_{expo125,prompt,orig}/): the 3 pairs on test, then
# pooled with the orbit confirm arms (stratified bootstrap by split). Usage: bash osworld/compare_test.sh [--out f.json]
set -euo pipefail
cd "$(dirname "$0")/.."
T=~/osw/results_test_gh; C=~/osw/results_val
echo "== TEST split (3 arms, pairs expo125-prompt, expo125-orig, prompt-orig)"
PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py --origin other --subsets all "$@" \
  expo125=${T}_expo125 prompt=${T}_prompt orig=${T}_orig
echo "== POOLED confirm + test (stratified by split)"
PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py --origin other --strata confirm,test \
  --subsets split:confirm,split:test,pooled \
  expo125=${C}_patched_eager_m40,${T}_expo125 prompt=${C}_prompt_eager_m40,${T}_prompt orig=${C}_orig_eager_m40,${T}_orig
