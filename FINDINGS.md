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

1. **B1** ✅ 建有標籤 eval-set（`seeds/eval_set.json`，2026-07-27）：6 真 Iven Tier-A（撈自 personal-wiki 忘機書稿 + QB 2021-22 語料，非 `_export/` 那兩份大 HTML）+ 5 slop 負例（3 個是 real-mode 跑出來的 AI 模仿稿、2 個是通用企業模板）。⚠️ 暫代語料——`personal-wiki/wiki/soul/golden-set.md`（Iven 手寫 15 題，目前 0/15）填完後才是最終真值，屆時要重跑 B2/B3 校準。
2. **B2** ✅ code 完成（2026-07-27，stub 跑過確認 pipeline 沒壞）：
   - `_contrastive_judge()`（`iven_voice_graph.py`）新增 `contrastive_fit` 維度（weight 3）：不問「這篇夠不夠格」，問「比較像 `eval_set.json` 的 Iven 範例還是 slop 範例」，直接對照真實 exemplar 而非抽象 rubric。
   - judge 模型與 draft 模型分離（`run_once(judge_model=...)`，預設 `SPIKE_JUDGE_MODEL=claude-haiku-4-5-20251001`，跟 draft 預設 `claude-sonnet-5` 不同支），消自我圈選。
   - `h_no_seed_leak()` 新增 `no_seed_leak` 維度（heuristic，weight 1）；2026-07-27 real-mode 實測抓到一次真 leak（draft 逐字複製 gist 的「反套利設計律」），但當時只是加權平均一個維度，稀釋不掉，0.856 照樣過門檻——**後補硬性否決**：leak 出現直接 `pass=False`（不管加權總分多高），見 `score_draft()` 的 `veto` 邏輯。已用 `--real` 重跑一次驗證沒有 leak 時不會誤判（no_seed_leak=1.0 時正常過關）。
3. **B3** ✅ 跑了（`calibrate.py`，2026-07-27，judge=claude-haiku-4-5-20251001，真 API）——**分不開 ❌**：
   - Iven 範圍 [0.85, 0.95]；Slop 範圍 [0.0, 0.95]；gap = -0.1（負值＝重疊）
   - 6 個真 Iven 全過 0.85，但 slop 裡 s1/s2（兩篇 AI 模仿稿，其中 s1 還是簡體字）也打到 0.85/0.95，跟真 Iven 分不開
   - 反而 s3（原本設計成「最容易誤判成 Iven 的難負例」）跟 s4/s5（通用企業模板）都準確判 0.0——**gate 挑得出「明顯不像」，但挑不出「表面規則對、細節不對」的那種**
   - **這就是 FINDINGS 一直講的天花板，contrastive 包裝也沒繞過去**：判斷依據還是 prompt-only judge，跟舊絕對打分同一個 ceiling，只是換了問法。**觸發 training-level（LoRA/Persona Vectors）決策數據**，純 prompt-engineering 這條路線該停損了
   - 已知限制（誠實記錄，未修）：只跑 1 次/題（無重複投票去噪）、只測 1 支 judge 模型（haiku）、few-shot 範例截斷到 140 字——這些都可能是雜訊來源，但即使如此，s1 被打 0.85/0.95 這麼高，落差大到不太可能純粹是雜訊
   - 結果存 `results/calibration.json`
4. **B4** ⛔ 卡住——原計畫「用校準過 gate 重跑回灌」的前提（gate 校準過）沒成立（B3 分不開）。硬跑 B4 沒有意義，會是在沒校準的 gate 上重跑回灌，跟 spike 一開始 real-mode 撞到的天花板同一個問題，換個包裝而已。

## B3.5：embedding-based 補測（`style_distance_calibrate.py`，2026-07-27，零依賴）

在判定「路線停損」之前，先測一個更便宜的問題：s1/s2 被 LLM judge 打高分，是「LLM judge 方法論本身有問題」，還是「這些 slop 語料在表面特徵上真的很像 Iven」？

用字元 n-gram(2,3) 頻率向量 + cosine similarity（跟 StyleDistance 同類「風格向量距離」，但用統計 n-gram 代替訓練過的 neural embedding——網路裝不了 sentence-transformers/torch 時的零依賴替代），對 eval_set.json 同一批 11 條重跑：

- **分得開 ✅**：Iven range [0.264, 1.0]，Slop range [0.08, 0.191]，**gap = +0.073，完全沒重疊**
- s1（簡體字模仿稿）跟 s2/s3（繁體模仿稿）都在最低分區，跟通用企業模板 s4/s5 同一群，沒有任何一篇 slop 混進 Iven 的分數範圍
- **這推翻了「表面特徵層級也分不開」的假設**——純統計層級的風格向量清楚分得開，代表 B3 的「分不開」問題更可能出在 LLM judge 這個判斷機制本身，不是語料真的無法區分

⚠️ 誠實限制：n=11 樣本量小；字元 n-gram 會混到內容/主題訊號（不是純風格），不是真正訓練過的 style-only embedding；只跑一次沒有交叉驗證。

## B3.6：held-out 重測，推翻 B3.5（`style_distance_heldout.py`，2026-07-27）

B3.5 有個沒控制的變因：`iven_tier_a` 全講忘機/QB，`slop` 全講 Character.AI 訴訟——n-gram 分得開可能只是在抓「話題詞彙」不是「風格」。用兩篇今天 `--real` 生成、跟 slop 同一個 seed（同話題：AI 產品/平台成敗案例）的 held-out draft 重測：

- `draft_clean`（gate 打 0.912、no_seed_leak=1.0，乾淨過關）→ style_score = **0.150（像 slop）**
- `draft_leak`（gate 打 0.856、有逐字複製 leak）→ style_score = **0.213（像 slop）**
- 對照：非 leave-one-out 的 Iven range [0.904, 1.000]，Slop range [0.017, 0.061]——兩篇 held-out 都貼著 slop 那端，離 Iven 範圍很遠

**推翻 B3.5 的結論**：控制話題之後，n-gram 方法連「同話題下、人工判定寫得不錯的稿子」都判不出來，暴露它分得開純粹是話題詞彙差異，跟風格無關——這個零依賴統計代用品比 LLM judge 更不可靠，不能拿來替代判斷機制。

## Plan B 結論（2026-07-27，B3.6 後）

B1→B3 的原始結論站得住：**prompt-only judge（絕對打分或 contrastive）分不清真 Iven 跟表面規則對的 AI 模仿稿**，而且今天測試的「零成本替代方案」（字元 n-gram 風格距離）並沒有真的解決這個問題——它在無控制變因時看似分得開，控制話題後立刻現形是話題詞彙的假訊號。**決策點回到原本的位置，交給 Iven**：要嘛接受 L5 只能靠人工盲測把關、要嘛評估上 training-level（LoRA/Persona Vectors 或真正訓練過的 embedding model，golden-set.md 填完是起點）。如果還想再測一輪更嚴謹的 embedding 方法（真的裝 sentence-transformers/StyleDistance，非統計代用品），要記得**同時控制話題**才是有效測試，不然會重蹈今天 B3.5 的錯。

L5「像不像本人」最終需 Iven 盲測，B 無法取代。

## 跑法

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install langgraph anthropic
cp env.sample .env     # 填入 ANTHROPIC_API_KEY（見 iven-keys.md）
python run.py --stub   # 免 key，驗管線
python run.py --real --model claude-sonnet-5   # 真 LLM
```
