# 生成方法

## 為什麼不走 gate/redo 迴圈

`qoome-iven-voice-spike` v0-v2 用 LangGraph `draft → gate →(conditional) redo / pass` 迴圈（見 `iven_voice_graph.py`）。v3 起改追 aspirational-self 後，這個迴圈**主動停用**：

- gate rubric（`contrastive_fit` 對照 `eval_set.json`）量的是「像不像 Iven 現在的平均聲音」——present metric
- aspirational 目標是「像不像 Iven 想成為的聲音」——跟 present metric 是兩個不同的軸（見 `principles.md` P27）
- 若硬跑 present-metric gate 去判 aspirational draft，會把「往好的方向偏移」誤判成「退步」而觸發 redo，越 redo 越退回 present 平均值——這正是 v2「real 全輸」表面結論被誤讀的根因（FINDINGS §B6）

所以本 skill 是**單次生成**，品質把關留給人工盲測（Iven 本人），不用自動 gate。

## Prompt 組裝邏輯

1. **Register 判定**：`--register Threads` 或 `長文`，決定從 `style_pack_v1.json` 篩哪些 dim 進 system prompt 的「寫作原則」清單（見 `style_pack_v1.json` 每個 dim 的 `register` 欄位）。
2. **Exemplar 注入**：`exemplar_pool_v4.json` 8 段全部塞進 system prompt（pool 小，不用再篩選）。這是 few-shot 錨點，不是抄襲來源——system prompt 明確要求「不要提到大時叔叔/尾崎秀實/Iven/忘機這些名字本身，只採用敘事骨架與精神」（沿用 spike `gen_blind_test_drafts_v3.py` 的 no-name-leak 守則）。
3. **命名式概念 + 重定義結構 + 層層推導 + 具體故事**：四個核心指令，來自 `principles.md` P01/P02/P06/P22（見 spike v3 `gen_real()` 系統 prompt 原文）。
4. **Register 專屬指令**：
   - `Threads`：175 字內 hook（P11/P14）+ 容易入口但保留論點張力（P10/P12）+ 短句斷言限開場/結尾（P09）
   - `長文`：可承載高資訊密度、real 骨架 + naive 密度 hybrid（P07/P13）、娓娓道來節奏允許（P14）

## 跟未來 editorial loop 的關係

- exemplar pool 本身是「發散蒐集多種手法」階段的產物（4→8 段涵蓋不同寫法），本 skill 生成時是「收斂成一篇具體草稿」的應用端
- 本 skill 目前不含「蒐集你的退件回饋、回頭調整規則」的機制——那是未來 case-4 Editorial Desk 的職責（尚未實作）
- 本 skill **不是** editorial loop 的替代品，是它的上游草稿產生器：先有稿子，你 pick/退件，回饋才餵得回來

## 已知失敗模式（複測前必看）

- **max_tokens 太低 → 首稿全空**：spike 曾撞到 model 開 extended thinking 吃光 max_tokens=4096，拉到 8192 才解（commit `aee8017`）。本 skill `gen.py` 已固定用 8192。
- **seed leak**：若有帶 `--gist`，草稿不應逐字複製 gist 原文——這是抄提示不是轉譯（`style_pack_v1.json` 的 `no_seed_leak` dim，veto 級別）。
- **拗口/技術白皮書腔**：`vocalization_ease` 與 `structure_density_hybrid` 兩個新 dim 是 v1 才加的，尚未經過任何一輪盲測驗證有效——生成結果若偏拗口或偏白皮書，是已知風險，不是意外。
