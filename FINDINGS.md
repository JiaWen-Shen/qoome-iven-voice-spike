# Iven-Voice 核心迴圈 spike — findings（2026-07-26）

離線驗證「改寫 → gate → 退件重寫 → 回收」決策迴圈。不碰 n8n、不碰編輯台 UI。
對齊 Iven PR#1 comment：**LangGraph 重構 + 編輯檯分工**。

## 建了什麼

LangGraph 狀態機：`draft → gate →(conditional) redo / pass`，回灌＝退件理由累積回 draft prompt。
`style_pack.json`（10 維 rubric，顯性 heuristic + 隱性 llm + AI slop 負向偵測）· `seeds/`（舊心法×新題材 + 真 Iven exemplar）· `iven_voice_graph.py` · `run.py`（驗證階梯）。

## 結果

### stub 模式（免 key，deterministic）— 全綠 ✅

| 層 | 結果 |
|---|---|
| L1 管線 | ✅ 退件理由真的進下一輪 prompt |
| L2 行為 | ✅ v1≠v2 |
| L3 分數 | ✅ 0.348→0.877，lift 0.529 > 噪音地板 0 |
| L4 遷移 | ✅ 規則從 p1 套到 unseen p2 也升分 |

**證明：迴圈控制流 + 回灌管線串得起來。**

### real 模式（Sonnet-5，Iven key）— 迴圈會跑，但揭 2 個真發現 ⚠️

修掉 2 個 bug 才跑起來：首稿全空（model 開 extended thinking 吃光 max_tokens → 拉 4096 + retry）；首稿太好直接過關（加 naive-first 製造失敗起點）。

**發現 1：rubric 太鬆、抓不到 Iven 獨特性。**
連 naive「一般小編」稿都常過 0.85（跑間飄 0.74–0.90）。中文商業寫作天生有英文術語、短句、少 connective——顯性 heuristic 量得到的 generic 稿也有。**印證 6/20 風格報告：顯性層 ~70% 容易，難在隱性層（prompt-only ceiling ~30-40%，EMNLP 2025）。**

**發現 2：prompt-level 回灌不穩，lift 常負。**
真跑 first 0.846 → final 0.735（回灌後反而變差），噪音地板跑間 0.015–0.42 亂飄。**印證 prompt-only ceiling：光回灌 prompt 無法穩定變準。**

## 結論

- 迴圈**機制成立**（stub 綠）
- prompt-level 回灌 + 顯性 rubric **撞天花板**（real）
- 這不是 bug，是**對齊 Iven LangGraph 方向 + 風格報告 rubric→frown corpus→評估升級訓練 路線**的實證
- 硬調到 real L3 變綠＝自欺，不做

## Next：Plan B（下個 session）

先修 gate 讓它會**區辨隱性層**，迴圈測試才有意義：

1. **B1** 建有標籤 eval-set（5–8 真 Iven Tier-A ex `personal-wiki/works/_export/` + 5–8 generic/slop 負例）
2. **B2** gate 改 contrastive（像 Iven 極 − 像 slop 極，judge 換模型消自我圈選）+ 跨稿比喻 verbatim 偵測
3. **B3** 校準——證明 gate 把真假分開（有 gap）。**分不開＝prompt-judge 也撞天花板 → 觸發上 training-level（LoRA/Persona Vectors）決策數據**
4. **B4** 用校準過 gate 重跑回灌，L3 lift 才有意義

L5「像不像本人」最終需 Iven 盲測，B 無法取代。

## 跑法

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install langgraph anthropic
cp env.sample .env     # 填入 ANTHROPIC_API_KEY（見 iven-keys.md）
python run.py --stub   # 免 key，驗管線
python run.py --real --model claude-sonnet-5   # 真 LLM
```
