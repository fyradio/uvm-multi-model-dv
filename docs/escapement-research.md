# 研究筆記：ESCAPEMENT 是怎麼用多個 AI 做出來的

研究對象：<https://github.com/Leonxlnx/escapement>（MIT，研究日期 2026-11-10）
閱讀範圍：README、`BRIEF.md`、`lib/common.py`、`tools/mix.py`、`tools/make_cues.py`、`audio/manifest.json`。

## 1. 專案在做什麼
一部 36 秒的程式化 3D 短片。由 Claude Code（Opus 5.5）寫 Python，以 headless 模式驅動 Blender 5.2（EEVEE）完成，全片沒有下載任何 3D 模型或貼圖。
執行環境只是一台內建 AMD Radeon 780M 的筆電。作者給了一個提示，之後回饋修改了幾輪。

## 2. 多 AI 分工為什麼沒有發散
| 機制 | ESCAPEMENT 的做法 | 對應到 DV |
|---|---|---|
| 唯一依據 | `BRIEF.md`（製作聖經）＋`shotlist.json`（唯一權威時間表） | `vplan.json` |
| 凍結共用工具 | `lib/common.py`、`tools/rb.py` 規定不准修改，helper 只能寫在自己的模組 | `tb_contract_pkg.sv`、`my_if.sv` |
| 清楚的接縫 | T1–T5 轉場交接點寫在 BRIEF，相鄰兩幕都要遵守 | transaction／ref model 簽名、REQ 編號 |
| 分工粒度 | 一幕一個建造代理，共 5 個 | 一個元件一個角色，共 3–4 個 |
| 導演與製作分開 | 另派導演代理看成品批評，再跑第二輪修正 | 角色 E 只讀 gate_report |
| 工具當裁判 | `exposure_check.py` 給畫面打分，不通過就要修 | `gate.py`：UVM 錯誤數、REQ_PASS、覆蓋率 |
| 中途的新要求 | 寫回 BRIEF 的「Client Rules」區 | 寫回 vplan 的 `open_questions` |
| 資源保護 | 用全域 GPU 鎖，一次只跑一個渲染（共用 iGPU 曾經藍屏） | 回歸腳本統一跑模擬 |

## 3. 音樂與音效的做法
- **拍點網格**：24fps 搭配 120BPM，一拍 12 幀、一小節 48 幀。用 `T0`（片頭對應曲子的秒數）把重拍對齊畫面。
- **cue 掛在鏡頭上**：用 `at(shot, i)` 表示「某個鏡頭的第 i 幀」。畫面重剪之後，聲音會自己跟著移動。
- **對齊方式**：`start`（從該幀開始）、`peak`（最大聲的一刻落在該幀，用於撞擊聲）、`end`（在該幀結束，用於 riser）。
- **重點時刻疊多層**：例如五下金屬撞擊，每一下疊上 sub-bass knock 和焊接火花，音量逐下遞增。
- **混音**：用 numpy 加 ffmpeg 離線處理。音樂 ducking、FFT 濾波、合成 IR 做 reverb、look-ahead limiter（上限 -1 dBFS、tanh 軟膝），輸出 24-bit WAV。
- **剪音樂只按整小節**：用 assert 檢查重複或跳過的長度是 48 幀的倍數，避免後面的拍點錯開。
- **素材 manifest**：每個檔案記錄來源、授權、裁切、峰值／RMS、頻譜重心和 sha256。Mixkit 的檔案不放進 repo，只留下載連結。

## 4. 套到 IC 數位驗證時的教訓
1. 分工越細，接縫就越多，發散通常就出在接縫上。
2. 不要把各模型的對話互相轉傳，只交換檔案。
3. spec 模糊的地方不能讓模型自己決定，要變成 open question 由人裁決。
4. 驗收看模擬結果和覆蓋率數字，不看 AI 怎麼說。
5. 不同模型最好的用法是 N-version：各自只看 spec 寫 ref model，再互相比對。這種用法分得越開越好。
