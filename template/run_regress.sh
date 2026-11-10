#!/usr/bin/env bash
# VCS + UVM 回歸：編譯 -> 依 vplan 的 tests 跑多個 seed -> urg 合併覆蓋率 -> gate.py 判定
# 用法: ./run_regress.sh [seed 數量，預設 3]
set -u
SEEDS=${1:-3}
COV="line+cond+fsm+tgl+branch+assert"
mkdir -p logs

# 1) 編譯（lint 也看這份 log）
vcs -full64 -sverilog -ntb_opts uvm-1.2 -timescale=1ns/1ps \
    +lint=TFIPC-L -cm "$COV" -f filelist.f -l logs/compile.log -o simv
if [ $? -ne 0 ]; then echo "COMPILE FAIL"; exit 1; fi

# 2) 從 vplan.json 取出所有 test（用 python，不需要 jq）
TESTS=$(python3 -c "import json;print(' '.join(sorted({t for r in json.load(open('vplan.json'))['requirements'] for t in r['tests']})))")

for t in $TESTS; do
  for i in $(seq 1 "$SEEDS"); do
    seed=$RANDOM
    ./simv +UVM_TESTNAME="$t" +ntb_random_seed="$seed" +UVM_VERBOSITY=UVM_LOW \
      -cm "$COV" -cm_name "${t}_${seed}" -l "logs/${t}_${seed}.log" > /dev/null
  done
done

# 3) 合併覆蓋率成文字報告
urg -dir simv.vdb -format text -report urgReport > logs/urg.log 2>&1

# 4) 自動把關
python3 gate.py --vplan vplan.json --logs logs --urg urgReport --src tb
