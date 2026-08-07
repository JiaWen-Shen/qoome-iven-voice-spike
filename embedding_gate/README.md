# 軌道 C — Route 3 Embedding Gate（批次 4）

目標（Vault plan `24-*.md` 決策 4）：pretrained cosine baseline 先跑，過門檻就直接用；沒過 → contrastive fine-tune（中量版）。

## C1 — Corpus 準備 ✅

沿用既有校準過語料，不重造：
- Positive：`seeds/eval_set.json` `iven_tier_a`（6 篇，忘機書稿/QB 語料）
- Negative：`seeds/eval_set.json` `slop`（5 篇，AI 模仿稿 + 通用企業模板）
- 這兩份語料是 B2/B3/B3.5/B3.6 一路沿用的同一份校準集，本輪結果可跟歷史結果直接比較

## C2 — Pretrained cosine baseline ✅ 跑了，**沒過門檻**

`embedding_gate/baseline_test.py`（`sentence-transformers/all-MiniLM-L6-v2`，CPU，免費，本機跑）：

- Held-out 測試集：v1+v2+v3 全部 10 組 real vs naive_prof pair（20 篇），topic 跟 eval_set.json **完全不重疊**（忘機哲學 vs AI/商業評論兩個語料池）——比 B3.6 原本 n=2 held-out 大很多，且是跨語料域測試，比「同題材」更嚴格：若模型只是抓 topic word 而非風格，在完全不同題材域之間會直接崩潰。
- Metric：AUROC（real=1／naive_prof=0），score = `sim(text, positive_centroid) - sim(text, negative_centroid)`
- **結果：AUROC = 0.47**（0.5 = 純隨機，本測試比隨機還略差）——完全沒有辨識力
- 細看 per-item：多個 topic（p3／p3_v3／p4_v3）naive_prof 的 `sim_to_iven_tier_a` 反而**高於** real，方向錯誤，不只是噪音
- 完整輸出：`baseline_result.json`

**誠實結論**：`all-MiniLM-L6-v2` 這種泛用英文為主的 pretrained embedding，對中文商業寫作的「風格」維度幾乎沒有辨識力（絕對相似度全擠在 0.35-0.65 窄帶，語意層面可能還行，但抓不到 Iven 特有的語感/句式）。這**印證** Vault plan 決策 4 原本判斷「輕量版做 PoC 太淺」——不是猜錯方向，是**empirically 驗證**了這個判斷。

**跟 B3.5 的差異（重要，避免誤讀成同一種失敗）**：B3.5 的錯誤是「沒控制話題」導致 n-gram 抓到假訊號（看似分得開，實則是話題詞彙差異）。本輪 C2**已經控制話題**（held-out 跨語料域）、用的是真訓練過的 neural embedding（非統計 n-gram），依然分不開——這是一個**更嚴謹測試下的真負面結果**，不是重蹈覆轍。

### 追加測試：換中文原生 base model（`BAAI/bge-small-zh-v1.5`），排除「model 選錯」的可能性

`all-MiniLM-L6-v2` 是英文為主訓練的 model，用在中文任務上本來就吃虧——在下結論前先排除這個混淆因子，換一個中文原生 embedding model 重跑同一套 held-out 測試（同樣免費、CPU、不需 fine-tune）：

- **`BAAI/bge-small-zh-v1.5`：AUROC = 0.55**（仍未過 0.75，但比 `all-MiniLM-L6-v2` 的 0.47 好、且方向正確——略優於隨機）
- 完整輸出：`baseline_result_bge-zh.json`

**結論收斂**：換中文原生 model 後數字有改善方向但幅度很小（0.47→0.55，離 0.75 門檻還差一大截）。這排除了「純粹選錯 model」的解釋——兩個 pretrained model 都抓不到 Iven 風格的核心訊號，問題不在 base model 選擇，是**風格訊號本身需要針對 Iven corpus 做過 fine-tune 才抓得到**，這正是 Vault plan 決策 4 原本判斷中量版必要性的理由，現在有兩組獨立 baseline 數字撐住這個判斷。

## C2 下一步（contrastive fine-tune）—— ⛔ **blocked，非跳過**

Baseline 沒過門檻，照 plan 該進中量版 contrastive fine-tune。但：

- Vault plan 決策 4 表訂中量版門檻：「需要 pair 量：**幾百 pair 起跳**」
- 現況 `training_data/preference_pairs.jsonl`：**10 pair**
- 10 << 幾百，即使現在有 GPU/預算，拿 10 pair 去 fine-tune 一個 embedding model **必然只是 memorize 這 10 個樣本、不會學到可泛化的風格訊號**——這正是 spike 一路秉持的原則（`FINDINGS.md`：「硬調到 real L3 變綠＝自欺，不做」）

**本輪判斷**：不做 fine-tune。不是「跳過」，是**資料量不足以支撐這一步**，跟 GPU/預算無關——就算現在給錢給 GPU，10 pair 也做不出有意義的 fine-tune。

## C3 — 落地位置 ✅

本目錄即落地位置（`qoome-iven-voice-spike/embedding_gate/`），跟計畫一致（選項 X，延續 spike、共用 corpus 檔案）。

## Exit criterion 對照（批次 4 完成筆記用）

- [x] baseline 有跑（2 個 model：`all-MiniLM-L6-v2` AUROC=0.47、`BAAI/bge-small-zh-v1.5` AUROC=0.55），數字誠實記錄，皆未過 0.75
- [x] 已排除「model 選錯」的混淆因子（換中文原生 model 只小幅改善，非決定性差異）
- [ ] 中量版 fine-tune —— **blocked**（pair 量 10 << 門檻幾百），非本輪範圍，需先回批次 3/Layer 2 觸發規則累積更多 preference pair
- **後續換裝進 skill？否**——baseline 沒過、fine-tune 未做，`iven-voice-generator` skill 仍然沒有自動化 style gate，繼續依賴人工盲測把關（跟 SKILL.md 已知限制段一致）

## 重新啟動條件

累積到「幾百 pair」門檻後（見 `training_data/README.md` 3 個 append 觸發規則）重跑本目錄：
1. 重新產生 `training_data/preference_pairs.jsonl`（含新累積的 pair）
2. 用 `sentence-transformers` 的 `losses.ContrastiveLoss` 或 `MultipleNegativesRankingLoss` fine-tune `BAAI/bge-small-zh-v1.5`（本輪 2 個 baseline 中中文原生 model 分數較高，優先選它當 fine-tune 起點，非 `all-MiniLM-L6-v2`）
3. 用同一套 `baseline_test.py` held-out 測試方法論（跨語料域、topic 不重疊）驗證 fine-tune 後是否真的改善 AUROC，而非只看 training loss 下降
