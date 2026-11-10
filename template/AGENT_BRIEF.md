# DV 多模型分工：任務單範本

原則：**只傳檔案，不傳對話**。每個模型只會拿到下面這幾樣東西，不會看到其他模型的討論。

給每個模型的輸入固定四樣：
1. `vplan.json`（只標出它負責的 REQ）
2. `tb/tb_contract_pkg.sv`、`tb/my_if.sv`（凍結，只能用不能改）
3. spec 中對應的章節（只給相關段落，不給整本）
4. 下面的角色卡

---

## 共同規則（每張卡都要貼）
- 只實作指派給你的 REQ 編號，**不得新增需求、不得改凍結檔案**。
- 每個檢查點都要用 `` `REQ_PASS("REQ-xxx", ...) `` / `` `REQ_FAIL(...) `` 回報。
- spec 不清楚時**不要自己決定**，在回覆最後加上：
  `OPEN_QUESTION: <REQ 編號> <問題>`，並用最保守的寫法暫時實作，加上 `// TODO Q-?` 註解。
- 只交檔案（完整檔案內容），不要長篇說明；最多 5 行摘要。

## 角色 A：架構／整合（最強的模型，或你自己）
- 分工前寫好凍結檔案、env 骨架、filelist.f。
- 收集所有 OPEN_QUESTION → 裁決 → 寫回 vplan.json。
- 唯一能改凍結檔案的人；改了就把 CONTRACT_VERSION +1，通知所有人重拿。

## 角色 B：Agent（driver / monitor / sequencer）＋ sequences
- 負責：REQ-…（激勵相關）
- 交付：`tb/agent/*.sv`、`tb/seq/*.sv`

## 角色 C：Reference model ＋ scoreboard
- 繼承 `ref_model_base`，只看 spec 寫，**不准看 RTL**。
- 交付：`tb/env/ref_model_c.sv`、`tb/env/scoreboard.sv`

## 角色 D：SVA ＋ coverage（建議用和 C 不同家的模型）
- 交付：`tb/sva/*.sv`、`tb/cov/*.sv`
- 選配：也獨立寫一份 `ref_model_d.sv`，和 C 的模型交叉比對（N-version）。
  兩份不一致的地方 = spec 模糊或 RTL bug，列進 open_questions。

## 角色 E：審查（導演）——不寫程式
輸入只有：`gate_report.json`、vplan.json、失敗 test 的 log 片段。
輸出固定格式：
```
FAIL 項 → 負責角色 → 一句話修正指示（引用 REQ 編號）
```
不得提出 vplan 以外的新功能建議。

---

## 一輪的流程
1. A 凍結介面 → 2. B/C/D 平行實作 → 3. `./run_regress.sh`
4. E 讀 gate_report.json 派修正單 → 5. 只把「該角色的修正單」轉給該角色
6. 重複 3–5 到 `GATE PASS`；OPEN_QUESTION 由 A 每輪統一裁決
