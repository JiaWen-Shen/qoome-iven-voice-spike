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

---

## §B5 盲測第一輪：Iven 主判 + Karen 補充（2026-08-01）

B3.6 之後 Plan B 決策卡在 Iven 未表態。2026-08-01 Karen 直接把 blind test ship 出來（`qoome-edge-share/eval-iven-voice-blind-test-v0.html`，3 題 × 3 mode = 9 draft、`gen_blind_test_drafts.py` 產出），Karen 跟 Iven 各盲測一輪。**回饋以 Iven 為主、Karen 為補充觀察**。

### 測試設置

- **3 題目**（seeds/seeds.json p1/p2/p3 沿用）：利益對齊 × AI 產品失敗 / 重組式機會 × 過剩市場 / HITL 分工律 × agent 熱潮
- **3 mode**：real（spike full loop、B2 gate default、naive_first=False）/ naive_prof（Baseline #2：「以商業專家身份寫」無 Iven persona）/ naive_threads（Baseline #5：Threads 高互動格式但無特定 persona）
- **draft data**：`blind_test_drafts.json`（都是 claude-sonnet-5 產出）
- **rater**：Karen、Iven 具名盲測、A/B/C 順序前端 seeded shuffle（不同 rater 看不同順序）

### 結果矩陣

| Mode | Karen 平均 | Iven 平均 |
|---|---:|---:|
| naive_prof（Baseline #2） | 4.33 | 3.67 |
| naive_threads（Baseline #5） | 3.00 | 3.33 |
| **real**（spike full loop） | **2.67** | **3.00** |

**兩人 pick real 為「最像」的次數**：Karen 0/3、Iven 1/3（p1，且打分僅 3、不 confident）
**兩人一致**：**都未強偏 real**

### Iven 3 題 rationale 摘要（主 signal）

**p1**：「三個都是**論點像**，推論法確實可能會是我的邏輯路徑，但**在文筆上比較不像**，我比較會**層層推導**，甚至**用故事、舉例**來說明，**不會很快就斷言結論**。這三個都比較像是**套版的文字，缺少一個貫穿主軸洞見或視角**。」

**p2**：「論點上都像是我會推導的，連我自己都被吸引，覺得很有洞察力。A（naive_prof）的寫法夠粗暴吸睛，但我反而不太擅長。B（naive_threads）這種**娓娓道來的模式，比較像我會寫的，但拿來做社群貼文會太軟**。C（real）的寫法不是我欣賞的，也不是我擅長的寫法。**這裡有個很有意思的自我觀察**：**我自己雖然像 B 這型，但我內容自己的完形卻是像「大時叔叔」那樣的敘事結構和方法**。」

**p3**：「論點都像，文筆部份 A（naive_prof）雖然最像，但**其實我比較欣賞 C（naive_threads）的輕鬆說故事的敘事寫法**。」

### Iven 4 個核心 signal（主結論）

Iven 3 題都指向同一個結構性 gap——**論點層 gate 通過但文筆層沒過**：

1. **層層推導**（非快速斷言）：Iven 明訂反對「太快斷言結論」；spike 現有 style_pack `short_assertive`（短句斷言化）weight 2 反而是**加分項**、跟 Iven 判準相反
2. **故事、舉例**（非條列論證）：Iven p1/p3 都提到偏好敘事寫法、spike 現有 dim 無此軸
3. **貫穿主軸洞見/視角**（非套版）：Iven p1「三個都缺主軸洞見」= 三個 draft 都達不到；spike gate 現有 dim 無此高階判準
4. **大時叔叔敘事結構**：Iven p2 自我承認的敘事風格錨點；**這是 wiki 未捕捉的關鍵語料 gap**——是 golden-set 該優先補的錨點

### 意義（對 Plan B (a) vs (b) 決策）

- **(a) 人工盲測可行性低**：Iven 自己承認判準飄（「我像 B、但完形像大時叔叔」）+ Karen/Iven 判準不對稱（Karen 嚴 spread 2-5、Iven 寬集中 3-5）→ 兩個 rater 都測不出穩定 signal
- **(b) training-level 支持強**：三題都出現「論點像但文筆不夠好」= 完全對齊 B3.6「prompt-only 天花板」結論
- **spike 現有 style_pack 校準方向錯**：`short_assertive` 加分項跟 Iven「層層推導」判準相反、`redefinition` 招牌斷言句式 Iven 也標「太快斷言不像我」

**決策方向**：走 (b) training-level、但**新錨點 = 大時叔叔敘事**，golden-set 該優先補這條、不再冷啟從零

### Karen 5 個補充觀察（次要 signal、可作為 spike gate 早期過濾）

Karen 判斷嚴、抓到 Iven rationale 未提的表面 pattern。作為 **spike gate 早期過濾**用（篩 obvious bad output）、不作為主判準：

1. **self-note 括號**（p1 real「（我剛發明的詞，先收下）」）：Iven 不會用旁白 flag 自己造詞
2. **內文提到自己名字舉例**（p1 real 用 Iven/Qoome 舉例）：Iven 是觀察者位置、不是示範者
3. **AI 味濃**（p2/p3）：Iven 沒明說「AI 味」但 rationale 說「套版」＝概念重疊
4. **問題開場**（Karen p2 加分點）：對齊 spike `hook_175`
5. **混合 signal**（real 有 Iven 元素但同時踩反模式）

**Karen signal 跟 Iven signal 的關係**：Karen 抓「這稿有明顯 AI 印子」；Iven 抓「這稿沒到我的完形」。**Karen 適合當 pre-filter、Iven 判準是 gold standard**——但 Iven gold standard 靠盲測不 scalable（判準飄+成本高），該轉 training-level。

### Plan B 修正結論（2026-08-01 收斂）

- **確認走 (b) training-level**、放棄 (a) 人工盲測（Iven 判準飄+成本高）
- **新錨點 = 大時叔叔敘事**（golden-set 冷啟卡的 blocker 找到破口）
- **style_pack 需重新校準**：`short_assertive` / `redefinition` 這些現有 dim 跟 Iven 主 signal 相反，需新增 `layered_reasoning` / `narrative_examples` / `throughline_insight` / `daishi-narrative-style` 4 dim 覆蓋 Iven 主判準

### 下次動作

1. `style_pack.json` 加 4 新 dim（本次 PR 一起做）
2. `personal-wiki/wiki/soul/golden-set.md` 補「大時叔叔敘事」題目模板 3-5 題（Karen 提名 schema、Iven 冷啟填 body）
3. 走 (b) training-level 路線正式啟動、golden-set 累到 15 題後跑 LoRA baseline 試驗

---

## §B6 盲測第二輪 v2 結果（2026-08-01 傍晚）+ v3 目標系統性轉向（2026-08-02）

### v2 盲測結果（2026-08-01 22:55 Iven 提交後定稿）

3 題 × 2 mode（real / naive_prof）× 2 rater（Karen / Iven）。表面結論：**naive_prof 完勝、real 全輸**——兩人 6/6 都覺得 naive_prof 才像 Iven。

若只看 pick，會誤判 v2 的 4 新 dim（layered_reasoning / narrative_examples / throughline_insight / daishi_narrative_style）+ 大時叔叔錨點方向錯了。

### v2 隱藏 signal（改寫全部結論）

Iven 三題 rationale 都自揭 **pick（像現在）跟欣賞（想成為）分離**：

| 題 | Iven pick（像我） | Iven 欣賞（我要的手法） |
|---|---|---|
| p1 專業資產化 | A = naive_prof | B = **real** |
| p2 商業模式 | B = naive_prof | A = **real** |
| p3 判斷力 | B = naive_prof | A = **real** |

Iven 原話（p3）：「A 的視角及情境切入法是我欣賞的，但敘事的口氣實在是拗口，不像是人在講話。」

**3/3 都欣賞 real（吃大時叔叔錨點的版本）**——他心裡想成為的聲音就是 real 這條線、只是覺得 v2 real 稿本身「拗口」執行沒到位。

### 目標系統性轉向（Karen 2026-08-02 決策）

**v0-v2**：追 present-self（clone 現在的 Iven）——metric =「像不像現在」
**v3 起**：追 aspirational-self（Iven 想成為的樣子）——metric =「你想不想寫成這樣」

為什麼轉向：
- 若 Iven 現況已夠好、就不需要 spike。spike 存在意義本來就是幫他長成想成為的樣子
- v2 real 全輸不代表方法錯、代表**評分維度錯**（拿 present metric 判 aspirational method）
- 大時叔叔錨點方向 confirmed 對——3/3 都欣賞，只需修 executor 品質

### v3 setup

- **4 題 × 4 pillar**（p1 商業/p2 HTP 專業/p3 私域/p4 生活觀察）—— 覆蓋度 up、測跨題材穩定性
- **real mode**：吃 aspirational_exemplar_pool_v3.json 4 條 exemplar（Karen 代挑：忘機卷八「向善的機巧」/ 卷二「大惑易性」/ SCM book / 大時叔叔敘事）+ 保留大時叔叔錨點；**不走 gate loop**（gate rubric 是 present metric、跟 aspirational 目標不對齊）
- **naive_prof mode**：完全同 v2（baseline 不動）
- **雙評分 rubric**：每題 score1（像現在）+ score2（想成為）+ pick sanity check + rationale。**主 metric = score2**、score1 只當觀察

### v3 hypothesis

- **success**：score2 real 勝 naive_prof ≥ 3/4 題 → (b) training-level + 大時叔叔錨點方向確認、收工去 personal-wiki golden set / Threads Editorial Desk Phase 0
- **partial**：score2 real 勝 2/4 → 方向對但 exemplar 挑得沒對到位、v4 換 Iven 更點名的段落
- **fail**：score2 real 未穩勝 → 錨點素材迭代 or 承認 aspirational 假設本身有問題
- **score1 依然 naive_prof 全勝** → **正常，不算 fail**（想成為 ≠ 現在，這正是 spike 存在的原因）
- ⛔ **反面警訊**：若 Iven rationale 說「real 型的我也不想寫」→ aspirational 假設本身有問題，錨點方向偏離他真實嚮往

### v3 ship 狀態（2026-08-02）

- Spike repo `3f985eb` seeds + exemplar pool + gen script、`aee8017` max_tokens 4096→8192
- Edge-share repo `30fc17c` HTML + workflow + answers stub、`7bdd494` 8 個 draft
- 頁面：https://jiawen-shen.github.io/qoome-edge-share/eval-iven-voice-blind-test-v3.html
- 4 題 real 命名式概念全命中：「解牛式解耦」/「多巴胺義肢」/「暗轉介，明分潤」/「半鎖陳列」，無「大時叔叔/Iven/忘機」名字 leak
- 待 Karen 自測 → DM Iven

### v3 開放問題（待 Iven 確認）

1. Iven 願自選 3-5 段 aspirational reference 取代 Karen 代挑？
2. 4 題題材覆蓋度夠？有想加的 pillar？
3. 雙評分 rubric 負擔可接受？（v2 是單 pick + 單分，v3 變 pick + 兩分 + rationale）
