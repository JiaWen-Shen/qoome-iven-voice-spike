<!-- Auto-generated from CLAUDE.md by scripts/claude-to-agents.mjs on 2026-08-24. -->
<!-- Hook-triggered sections removed (no Codex equivalent) -- see below if any were stripped. Review before relying on it. -->
# qoome-iven-voice-spike — Project Context

離線 spike：驗證「改寫 → gate → 退件重寫 → 回收」核心迴圈，探索 Iven voice 的可 clone 邊界。**不碰 n8n、不碰編輯台 UI、不接 production**。

上層 context 見 [`../CLAUDE.md`](../CLAUDE.md)。完整運行說明見 `README.md`；結論累積於 `FINDINGS.md`。

**⚠️ 動手前必讀**：本 spike 不是獨立探索——Karen 在 `~/Vaults/JW_cloud/02_Projects/Personalized_content/` 已建成熟框架（9 檔），且 `04-案例二-qoome-iven-soul.md` + `08-weight-optimization-when-prompt-ceiling.md` header 明標「triggered by iven-voice-spike B2/B3」。**這個 spike 是那份框架的第一個實作場**，不是平行研究。方法選擇要對接、不要重造。

---

## 學術基礎（voice cloning / persona fidelity）

本 spike 的方法論選擇建立在**三個公開研究成果 + 一份 Karen 自建框架**上，動手前必讀對應條目、不要憑 intuition 重造輪子。

### 1. TwinVoice split（cognition ↔ expression）+ StyliTruth 反面 nuance

Voice 有兩層：**「how someone thinks」（認知層）** vs **「how they talk」（表達層）**。評測時要**分開測**、訓練時要**分開訓**。

⚠️ **關鍵 caveat（StyliTruth 2025，Karen 04-案例二 引用）**：thought 與 voice 在模型內**編碼在同一批 attention heads**，**not independently separable**——只是**measurably distinguishable**（可分軸打分）、不是**architecturally extractable**（不能純粹抽出來單獨改）。

所以 TwinVoice split 的正確用法：**評測維度**（rubric 拆兩軸）、**不是** 生成架構（不能設計「只改 voice 不動 thought」的 gate）。

- **KB**: `~/Vaults/JW_cloud/10_KB/ai-llm/wiki/techniques/evaluation-driven-creative-work.md` 2026-07-17 persona 段
- **對應 spike 證據**：v3 Iven rationale 跨題自揭「real 敘事骨架（cognition）+ naive 資訊密度（expression）」= TwinVoice split 實例
- **對應 Karen 案例二**：dr-ben 四格 delta 測試（baseline / thought-only / voice-only / both）驗證兩軸**可分軸打分**（voice 16/16、thought 3.5/4），但底層仍共享 attention heads
- **落到方法**：v4 rubric 顯性拆這兩軸打分，**不要**設計「乾淨切開 thought/voice」的 pipeline

### 2. Route 3：Swap the judge（含 LLM-as-judge 結構性不可靠論證）

**根本原因（Kim & Jurgens 2026）**：LLM 這個東西本身當 fine-grained style judge 就結構性不行——不是 prompt 沒寫好、不是 judge model 選錯，是 LLM 在細粒度風格判斷上有 architectural ceiling。這對應 Karen 04-案例二 明講的「Claude as interviewer + interviewee + judge simultaneously = 左手審右手 structural bias」。

**方法解**：當 LLM-as-judge 分不開「真 voice」與「表面模仿」時（v2 B2/B3 撞牆），**不是繼續調 prompt、加更多 exemplar、換更大 judge model，而是換 judge 本身**（換 kind、不是換 model）。

Karen 已在 `08-weight-optimization-when-prompt-ceiling.md` 完成四選項比較 + Qoome context 優先排序，**不要重跑此決策**：

| 選項 | Karen 排序 | Qoome context 判定 |
|---|---|---|
| **Embedding-based style classifier**（StyleDistance / sentence-transformers）| **#1 優先** | 今天可測、CP 最高、zero-cost；限制：只處理 voice 層（統計指紋），不能當唯一 gate |
| **DPO reward classifier** | #2（中低）| 最對齊原則、但 preference pair 量現階段不夠；先累積 slop 當 negatives、等 case-4 editorial loop 跑起再訓 |
| **LoRA fine-tuning** | #3（中期）| 現在 corpus 太小、大概率只 memorize 表面 feature、撞同樣 wall；等 golden-set 填完 + case-4 執行 + corpus 到幾十筆再說 |
| **Persona Vectors / Activation Steering** | ❌ 不推薦 | 學術驗證全是粗粒度 trait（evil / sycophancy），沒有 fine-grained 真人語感驗證 |

⚠️ **重要教訓（Karen round 1→2 顛覆）**：Karen 已試過 zero-dependency character n-gram(2,3) cosine 當替代 judge——round 1 看起來能分（Iven [0.264, 1.0] vs slop [0.08, 0.191]），round 2 hold topic 常數後**顛覆**——n-gram 抓到的是 topic-word artifact、不是 style。

**下一輪 embedding 測試強制要求**：
- 用 **trained style-embedding**（sentence-transformers / StyleDistance），**不用** n-gram proxy
- **hold topic 常數**（held-out same-topic draft，不是 fixed labeled corpus）
- **控制變數不全**時任何「看起來能分」都要視為 fake signal

- **KB**: `~/Vaults/JW_cloud/10_KB/ai-llm/wiki/concepts/model-training-adjustment-methods.md`

### 3. Persona Vectors / Activation Steering 限制 + DPO 門檻

**不要押 activation steering 是近期答案**。DPO 需要 5K–50K preference pair 才可訓，是**遠期正解、近期先累積**。

- **KB**: `~/Vaults/JW_cloud/10_KB/ai-llm/wiki/concepts/model-training-adjustment-methods.md`「Persona Vectors / Activation Steering」段
- **DPO 現況**：spike v3 累積 4 preference pair（16 分數點），距 DPO 訓練門檻 **3-4 個 order of magnitude**
- **意涵（每輪盲測都要對齊的三件事）**：
  1. 每輪盲測 answer JSON **產成 DPO-ready format**（`{prompt, chosen, rejected, rationale}`），慢慢累積
  2. 短期靠 Route 3（style classifier）補 LLM-judge ceiling
  3. 遠期累積夠 pair 才走 DPO / LoRA；activation steering 不押

### 4. Karen Personalized_content 框架（自建、直接上游）

三個公開研究是 KB 學術；這第四個是 Karen 自己在 `~/Vaults/JW_cloud/02_Projects/Personalized_content/` 建的 **9 檔完整框架**——**本 spike 是這份框架的第一個實作場**，不是平行研究。地位跟 KB 學術**同級**（甚至更高，因為它已對接本專案脈絡、跑過 4 個案例）。

- **位置**：`~/Vaults/JW_cloud/02_Projects/Personalized_content/`
- **本質**：Karen 從 4 個已完成案例（Karen-Tom voice / Qoome-Iven soul / ME-support TrendLife / Iven Threads Editorial Desk）萃取的**跨案例通用方法**，含決策樹、red-flag、四選項比較
- **必讀（依相關性排序）**：
  - `04-案例二-qoome-iven-soul.md`：header 明標「triggered by iven-voice-spike B2/B3」——**這份文件就是為本 spike 撞牆而寫**
  - `08-weight-optimization-when-prompt-ceiling.md`：header 也明標 spike B2/B3；含 4 選項比較 + Qoome 優先排序（本 CLAUDE.md §2 直接引用、不重跑）
  - `07-通用原則與checklist.md`：8 題決策樹 + 8 條 red-flag，v4+ 動手前必跑
  - `06-案例四-iven-threads-editorial-desk.md`：spike 的**下游消費者**設計；authenticity gate 落在 publish UI（field-empty = button disabled），**不落在 spike gate**
  - `01-核心方法論.md` + `02-編輯工作流框架.md`：divergent → convergent + frown → codify 原則
  - `03/05`：其他案例、參考
- **本 spike 對此框架的責任**：
  - **實作場**：驗證 case 二的方法在真 Iven corpus 上跑得動
  - **產訓練 substrate**：spike 每輪盲測 preference pair + rationale 就是 Karen 「eval-driven rubric 成為 fine-tune material」理論的實證資料
  - **驗證 Route 3**：Karen 08 檔排 embedding-based classifier #1 優先——spike 該走完這條 path，回報是否可行
- **核心對接原則**：spike 內任何方法選擇跟這 4 檔衝突時 → **服從 Karen 框架**、修 spike；不要自己另立分派

---

## Weight-Opt vs Prompt-Opt 分工（spike 自我定位）

| 已做 | 類別 | 未來 weight-opt 用途 |
|---|---|---|
| style_pack rubric（10 維） | prompt | 可轉 constitutional principle set |
| Iven Tier-A exemplar + aspirational_exemplar_pool_v3 | prompt (few-shot) | ✅ SFT 訓練資料 |
| draft→gate→redo LangGraph 迴圈 | prompt (agentic) | ❌ orchestration 層、不進 weight |
| contrastive gate + judge 分離 + verbatim veto | prompt (eval-time) | ⚠️ 判定結果可作 reward-model 訊號 |
| labeled eval-set（v2 B1） | prompt (calibration) | ✅ held-out benchmark |
| embedding 補測 + sidecar（B3.5/B3.6，n-gram round 1）| 兩者之間 | ⚠️ round 2 顛覆、n-gram 不可靠；要升級到 trained style-embedding |
| 大時叔叔錨點 + 4 條 aspirational exemplar（v3） | prompt (few-shot) | ✅ SFT Tier-A 語料 |
| v3 盲測 4 preference pair + rationale | data collection | ✅✅ **DPO-ready format**、n 太小需累積 |

**結論**：spike v1-v3 是 **95% prompt-opt**、**5% weight-opt 可用原料累積**。README 自己已標明「prompt-only ceiling ~30-40%（EMNLP 2025）」——這條 ceiling 就是靠 Route 3（trained style-embedding, 非 n-gram）+ DPO 累積雙軌跨過去，**不要押 activation steering**。

---

## 職責分工

（Karen 框架各檔的角色見學術基礎 §4；此處只列跨資產分工。）

| 誰 | 做什麼 |
|---|---|
| **Karen 框架**（02_Projects/Personalized_content） | 方法、原則、案例庫、決策樹 |
| **本 spike**（qoome-iven-voice-spike） | 案例二的實作場、跑實驗、產訓練 substrate、驗證 Route 3 embedding path |
| **personal-wiki soul 層** | L2 distillation / L3 compiled product 落地地 |
| **case-4 Editorial Desk**（未實作）| spike 產物的實戰場、外部 feedback loop 收集 |

---

## Prior Art 對接位置

- **KB 全景**：`~/Vaults/JW_cloud/10_KB/ai-llm/wiki/concepts/model-training-adjustment-methods.md`、`wiki/techniques/evaluation-driven-creative-work.md`、`raw/series/evaluation-driven-creative-work/`、`raw/series/ai-editor-hub/`
- **Karen 框架**：`~/Vaults/JW_cloud/02_Projects/Personalized_content/`（9 檔，動手前必讀 `04`、`08`、`07`、`06`）
- **personal-wiki soul 層**：`~/Jottacloud/vibe/qoome/personal-wiki/wiki/soul/表達dna-文筆基準.md`（命名式隱喻演化、跟 v3 real 四題對齊）、`wiki/soul/golden-set.md`（E group Iven 待填答、v3 blind test 是外部佐證、**現況 0/15**）、`wiki/synthesis/soul-engine-設計.md`（L0-L3 pipeline）

## 落地位置（spike v3 產物該去哪）

不新建架構、對接既有：

- `personal-wiki/wiki/soul/表達dna-文筆基準.md`：append v3 命名式隱喻外部驗證段
- `personal-wiki/wiki/soul/golden-set.md`：append E group 外部佐證（不篡改 Iven 待填欄；也記錄「golden-set 0/15 = 目前最大 bottleneck、case-4 editorial loop 是解法」）
- `personal-wiki/soul/dist/style-pack.md`（若無則新建，L3 compiled product）：合併 style_pack.json + aspirational_exemplar_pool_v3.json + rewrite loop method
- `personal-wiki/wiki/soul/candidate-mental-models/aspirational-shift.md`（candidate）：「real 骨架 + naive 資訊密度」跨題訊號、跑 nuwa 3-way gate 驗證後才升 soul page

---

## 動手前 checklist

1. 讀 `../CLAUDE.md`（qoome 上層 context）
2. 讀 `README.md`（spike 定位 + 已知限制）
3. 讀 `FINDINGS.md`（歷次結論；§B6 v3 aspirational 轉向、§B7 收工結論）
4. 讀 `~/Vaults/JW_cloud/02_Projects/Personalized_content/04-案例二-qoome-iven-soul.md` + `07-通用原則與checklist.md` + `08-weight-optimization-when-prompt-ceiling.md`（Karen 上游框架，這 3 檔最相關）
5. 對應 KB 條目讀完（本檔上方四個學術基礎）
6. 才動 code / 才寫 v4+
