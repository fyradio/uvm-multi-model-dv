# uvm-multi-model-dv

用多個 AI 模型分工撰寫 **UVM / SystemVerilog 驗證環境（Synopsys VCS）**，而且**不發散**的工作流程與範本。

這套做法借鏡 [ESCAPEMENT](https://github.com/Leonxlnx/escapement)：一部用多個 AI 代理分工完成的程式化短片。研究筆記見 [`docs/escapement-research.md`](docs/escapement-research.md)。

## 核心原則
1. **一份唯一依據**：`vplan.json`，每條需求都有一個 REQ 編號。
2. **先凍結介面再分工**：`tb_contract_pkg.sv`、`my_if.sv`。
3. **按元件分 3–4 個角色**，不要切得太細。
4. **只傳檔案，不傳對話**。
5. **spec 模糊不自己決定**：寫成 `OPEN_QUESTION`，交給人裁決。
6. **用工具當裁判**：`gate.py` 檢查模擬結果、REQ 追蹤、偏題、凍結檔和覆蓋率。

## 目錄
```
template/
  AGENT_BRIEF.md      各角色任務單與一輪的流程（先看這份）
  vplan.json          驗證計畫：REQ、test、covergroup、owner、open_questions
  tb/tb_contract_pkg.sv  凍結：transaction、ref_model_base、REQ_PASS/REQ_FAIL
  tb/my_if.sv         凍結：DUT interface（範例）
  filelist.f          VCS filelist
  run_regress.sh      VCS 編譯 → 多 seed 回歸 → urg → gate.py
  gate.py             自動把關，輸出 gate_report.json
skills/uvm-multi-model-dv/SKILL.md   可給 AI 助理載入的 skill
docs/escapement-research.md          研究筆記
```

## 快速開始
```bash
cp -r template my_block_dv && cd my_block_dv
# 1. 依 spec 填 vplan.json，修改 tb/my_if.sv 與 tb_contract_pkg.sv 後凍結
# 2. 依 AGENT_BRIEF.md 把角色卡發給各模型（每個只拿自己的 REQ）
# 3. 收回檔案，加進 filelist.f
./run_regress.sh 5        # 每個 test 跑 5 個 seed
cat gate_report.json      # 交給審查角色 E，派修正單
```

## gate.py 檢查項目
| # | 檢查 | 結果 |
|---|---|---|
| 1 | 每個 log 都有 UVM report summary，且 UVM_ERROR / UVM_FATAL = 0 | FAIL |
| 2 | 每個 REQ 至少有一次 `REQ_PASS` | FAIL |
| 3 | log 或原始碼出現 vplan 沒有的 REQ（偏題） | FAIL |
| 4 | 凍結檔的 hash 和 `.contract_hash` 不同 | FAIL |
| 5 | covergroup 沒有達到 `coverage_goal` | FAIL |
| 6 | open question 還沒裁決 | WARN |

## 注意
- `gate.py` 只用 Python 標準函式庫（3.8 以上）。
- 不同版本 VCS 的 `urgReport/groups.txt` 格式略有差異，第一次使用時要確認覆蓋率的 regex。
- `run_regress.sh` 預設使用 `-ntb_opts uvm-1.2`，請依你們的 UVM 版本調整。
- `.contract_hash` 會在第一次執行時建立；介面合法改版後，刪掉它重新建立。

