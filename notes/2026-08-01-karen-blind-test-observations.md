# Karen 盲測觀察草稿 — 2026-08-01

> **Status**：Karen n=1 rater 觀察筆記。**不是結論**、**不 push**。
> Iven 提交盲測後才根據決策樹分流去向（見 §分流決策樹）。
> Source data：`https://raw.githubusercontent.com/JiaWen-Shen/qoome-edge-share/main/iven-voice-blind-test-answers.json` submissions[0]（rater=karen、submitted_at=2026-08-01T04:24:05Z）

## 1. 三題判斷解碼

盲測頁 A/B/C 順序前端 seeded shuffle by rater name，Karen 看到的實際 mode：

| 題 | Karen pick | 實際 mode 對應（用 order_map 解碼） | 打分 |
|---|---|---|---|
| p1（利益對齊 × AI 產品失敗案例） | A（=`naive_prof`）| A=naive_prof、B=naive_threads、**C=real** | naive_prof=5、naive_threads=2、**real=2** |
| p2（重組式機會 × 過剩市場） | C（=`naive_prof`）| A=naive_threads、B=real、**C=naive_prof** | naive_prof=5、naive_threads=2、**real=3** |
| p3（HITL 分工律 × agent 熱潮） | B（=`naive_threads`）| **A=real**、B=naive_threads、C=naive_prof | naive_prof=3、naive_threads=5、**real=3** |

**平均分**：naive_prof **4.33**、naive_threads **3.00**、real **2.67**

**結論（單 rater n=3、preliminary）**：Karen 三題全沒選 real、real 平均分墊底。

## 2. Karen rationale 摘出的 pattern

從 submissions[0].answers 摘 Karen 具體字句（原文引號內）：

**Pattern P1：「self-note 括號」**
- 出處：p1 real draft 有「（我剛發明的詞，先收下）」
- Karen 判：「感覺 Iven 似乎不會這樣用」
- 具體性：Iven 造詞是內化到句子裡（命名式隱喻——AI 校正稅／數位外骨骼／玄德值），不會加 self-note 括號旁白 flag「這是我剛發明的」
- Style_pack dimension 對應：**無**。style_pack `coined_terms` 只判「有沒有命名式隱喻」、不判「命名手法」——現有 dimension 抓不到這個
- 分類：**新 dim 候選** — 「命名手法自然性」（有命名式隱喻但用 self-note 旗標 = 反 Iven）

**Pattern P2：「內文提到自己的名字舉例」**
- 出處：p1 real draft 內文用 Iven/Qoome 舉例（Karen 沒引具體字句、但 rationale 說「C 的開頭很像，但 Iven 應該不會在內文裡提到自己的名字作為舉例」）
- Karen 判：Iven 招牌是「用 case 講原理」但**不會拿自己當 case**
- 具體性：Iven 對外語域 = 觀察者/評論家立場，不是「我來示範」立場（跟他 SCM 2002「權威引用後即重構」的作者位置一致）
- Style_pack dimension 對應：**無**。style_pack 完全沒有「敘事人稱/位置」dim
- 分類：**新 dim 候選** — 「作者位置：觀察者 vs 示範者」

**Pattern P3：p2/p3 real「AI 味濃」**
- 出處：p2 real（A=naive_threads「AI 味很濃」）、p3 real（A=real「很 AI 味」）
- Karen 判：兩題都用「AI 味」形容—— style_pack 有 `flat_tone`、`connective_overuse`、`typos` 三個 AI slop 負向 dim，Karen 選詞卻是「AI 味」不是具體「tone 平」或「連接詞多」
- 具體性不足：Karen rationale 沒細分「AI 味」是**哪一味**——是連接詞、tone、還是其他？
- Style_pack dimension 對應：**可能已覆蓋**（flat_tone / connective_overuse）—— gate 沒攔下說明校準閾值不夠嚴，或 heuristic 偵測不到
- 分類：**gate 校準問題**（不是缺 dim、是 dim 閾值太鬆）

**Pattern P4：「用問題開場」= 加分**
- 出處：p2 C（=naive_prof）「C 用問題開場」→ Karen 打 5 分挑最像
- Karen 判：Iven 常用問題開場、hook 型
- 具體性：對應 style_pack `hook_175`（「前 175 字要有 hook」weight 1）——但 dim 是量「有沒有 hook」、沒量「hook 是問句還是斷言」
- Style_pack dimension 對應：**部分覆蓋**（hook_175 有但不夠細）
- 分類：**gate 校準問題**（可能可以拆 sub-dim「hook 類型：問句 / 斷言 / 逆向共識」）

**Pattern P5：p3 real「XX 現在紅到什麼程度？」是像的部分**
- 出處：p3 real（A=real）Karen 引「A 很 AI 味」但矛盾是——real 開頭「Agent automation 現在紅到什麼程度？」其實**是問句 hook**（呼應 P4 加分）
- Karen 給 3 分（不算最低）、只是不到 5
- 解讀：real 有 Iven-like 元素但也踩到 P1/P2 反模式、pattern 疊加後 -1
- 分類：**mixed signal** — 不是「real 全糟」是「real 混合 signal」

## 3. Style_pack 對應總表

| Pattern | Karen 觀察 | Style_pack 現有 dim | Gap 類型 |
|---|---|---|---|
| P1 self-note 括號 | 反 Iven | 無 | 新 dim 候選 |
| P2 敘事位置 | 反 Iven | 無 | 新 dim 候選 |
| P3 AI 味（籠統） | 反 Iven | flat_tone / connective_overuse / typos | 校準太鬆 |
| P4 問題開場 | 像 Iven | hook_175（不夠細）| 拆 sub-dim 候選 |
| P5 混合 signal | 中間值 | — | mixed，非 pattern |

## 4. Iven 提交盲測後的分流決策樹

### 若 Iven 判準跟 Karen 一致（也全挑 baseline、real 分墊底）
→ pattern P1/P2/P4 進 `wiki/soul/萃取核對清單.md`「反向查核」段（Karen 主場、Karen 7/18 建立、schema HITL 允許）
→ pattern P3 走 spike gate 校準（修 style_pack.json 閾值、Karen 主場 spike repo）
→ pattern P5 進 spike FINDINGS.md 補記「混合 signal 現象」

**不做**：
- 不改 active `wiki/soul/表達dna-文筆基準.md`（HITL 紅線）
- 不建反模式段（P1/P2 是「Iven 不做的事」= soul 反面、仍屬 soul 疆界、要 Iven 升格）

### 若 Iven 判準跟 Karen 相反（挑 real 或亂選）
→ pattern P1-P5 進 `wiki/synthesis/karen-vs-iven-判準差異-2026-08-01.md`（新建 synthesis 頁、記錄 signal 但不定調）
→ FINDINGS.md 補記「rater 判準 divergence」現象
→ 觸發：Iven 拍板要走哪條路（真的相信自己選的 real 更像 → gate 校準要 flip、還是承認自己判準不穩 → 走 (b) training-level）

### 若 Iven 判準混亂（打分飄、pick 沒模式）
→ pattern 進候選池 `wiki/soul/心智模型-候選池.md` pattern（等收更多 data）
→ 觸發 (a) 人工盲測 = 不可行 → 走 (b) training-level 決策

## 5. Karen 觀察筆記的元問題

**元問題 1**：Karen 判準本身有多穩定？
- 若隔一週再測、判準會不會飄？
- 這輪 n=1 rep=1、無 retest data
- 若真要 ship (a) 人工盲測 → 需要「同 rater 隔時間 retest」的一致率當可信度

**元問題 2**：Karen 是「Iven 判準的 proxy」還是「另一種判準」？
- Karen 是 Iven 的合作者、看過大量 Iven 語料，但**不是 Iven 本人**
- 若 Karen ≠ Iven 判準，Karen 打分 low value 對 spike gate 校準

**元問題 3**：n=3 題目 sample size 太小
- 3 pillar 都是 Iven 招牌領域（利益對齊 / 重組式機會 / HITL）
- 若換到 Iven 較陌生領域（設計、育兒）可能 real vs baseline 差距不同
- 這輪只能得結論「Iven 熟悉的商業/AI 領域」spike real 不夠像

## 6. 下次動作條件觸發

- **等 Iven 提交後**（`curl` answers.json、submissions.length ≥ 2）→ 執行 §4 分流
- **若 3 天內 Iven 沒提交** → Karen Teams DM remind、順便問其他 3 件事（見 [[2026-07-summary]] Part 2 🚧 段）
- **若 Iven 提交後 pattern 有明顯分流** → 更新此 note 的「結論」段（本 note 保留作為觀察 log、不 delete）
