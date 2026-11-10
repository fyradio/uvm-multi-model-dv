---
name: uvm-multi-model-dv
description: 用多個 AI 模型分工寫 UVM/SystemVerilog 驗證環境（VCS）時用：vplan 唯一依據、凍結介面合約、只傳檔案、open question 裁決、gate.py 用模擬結果與覆蓋率把關防止發散。
---

# UVM 多模型分工（防發散版）

目標：分工之後不偏題。做法借鏡 ESCAPEMENT：一本聖經、凍結的共用工具、清楚的接縫、導演用工具當裁判。範本在本 repo 的 `template/`。

## 0. 開工前（角色 A：最強的模型或使用者）
1. 和使用者一起把 spec 轉成 `vplan.json`。每條需求要有 `id`（REQ-001）、`spec_ref`、`desc`、`check`（scoreboard 或 sva）、`covergroups`、`tests`、`owner`；另外再填 `coverage_goal`、`frozen_files`、`open_questions`。
2. 寫凍結檔 `tb_contract_pkg.sv`：唯一的 transaction class、參數、`ref_model_base`（pure virtual 的 `predict()` 和 `reset()`），以及下面兩個 macro：
   ```systemverilog
   `define REQ_PASS(id,msg) `uvm_info("REQCHK",$sformatf("%s PASS %s",id,msg),UVM_LOW)
   `define REQ_FAIL(id,msg) `uvm_error("REQCHK",$sformatf("%s FAIL %s",id,msg))
   ```
   再加上 interface、env 骨架和 filelist.f。之後只有 A 能修改這些檔案，每改一次就把 CONTRACT_VERSION 加 1。

## 1. 分工：按元件分，3–4 個角色就好
- B：agent（driver、monitor、sequencer）加 sequences。
- C：ref model 加 scoreboard，只看 spec，不看 RTL。
- D：SVA 加 coverage。建議用和 C 不同家的模型；也可以讓 D 獨立寫第二份 ref model 和 C 交叉比對，兩份不一致代表 spec 模糊或 RTL 有 bug。
- E：審查（導演），不寫程式。

## 2. 傳遞規則（最重要）
- 每個模型只拿四樣東西：vplan（標出它負責的 REQ）、凍結檔、相關的 spec 段落、角色卡。**不要轉傳其他模型的對話或說明**。
- 交付內容只有完整檔案，加上最多 5 行摘要。
- 共同規則：
  - 只做指派給你的 REQ，不新增需求，不改凍結檔。
  - 每個檢查點都用 REQ_PASS 或 REQ_FAIL 回報。
  - spec 不清楚時，在回覆最後寫 `OPEN_QUESTION: REQ-xxx <問題>`，先用最保守的寫法，並標上 `// TODO Q-n`，**不要自己決定**。
- A 每一輪統一裁決 open questions，寫回 vplan.json 後再發下一輪。

## 3. 把關（VCS）
- 編譯：`vcs -full64 -sverilog -ntb_opts uvm-1.2 -timescale=1ns/1ps +lint=TFIPC-L -cm line+cond+fsm+tgl+branch+assert -f filelist.f -l logs/compile.log -o simv`
- 跑 vplan 裡所有 test，每個 test 跑多個 seed：`./simv +UVM_TESTNAME=$t +ntb_random_seed=$seed -cm ... -cm_name ${t}_${seed} -l logs/${t}_${seed}.log`
- 合併覆蓋率：`urg -dir simv.vdb -format text -report urgReport`
- `gate.py` 判定結果，並輸出 gate_report.json：
  1. 每個 log 都有 report summary，且 UVM_ERROR 和 UVM_FATAL 都是 0。
  2. 每個 REQ 至少有一次 REQ_PASS。
  3. log 或原始碼出現 vplan 沒有的 REQ，判為 FAIL（偏題偵測）。
  4. 凍結檔的 hash 變了，判為 FAIL。
  5. vplan 列出的 covergroup 要達到 coverage_goal（讀 urgReport/groups.txt，regex 依 VCS 版本調整）。
  6. open question 還沒裁決，判為 WARN。

## 4. 修正迴圈
E 只讀 gate_report.json、vplan 和失敗 test 的 log 片段，輸出格式固定為 `FAIL 項 → 負責角色 → 一句修正指示（引用 REQ）`，不能提出 vplan 以外的建議。每張修正單只轉給它所屬的角色。重複這個迴圈，直到 GATE PASS。

## 5. 常見的發散原因（遇到就回頭檢查）
- 介面沒有先凍結，每個模型各自定義一套 transaction。
- 分得太細（超過 5 個角色），接縫比工作還多。
- 讓模型自己決定 spec 模糊的地方，偏差一層層累積。
- 用 AI 的意見當驗收標準，應該改用模擬結果和覆蓋率數字。
