---
name: iven-voice-generator
description: >
  用 Iven aspirational voice（他想成為的樣子，非現在平均聲音）生成 Threads 短文或長文草稿。
  吃 style_pack v1（22 維 rubric）+ aspirational exemplar pool v4（8 段真實 Iven Tier-A/B 語料）
  單次生成、不走 gate/redo loop（v3 教訓：gate rubric 是 present metric，跟 aspirational 目標不對齊）。
  觸發：「幫 Iven 寫 Threads」「iven-voice」「用 Iven 聲音寫」「/iven-voice-generator」。
---

# Iven Voice Generator — aspirational-self draft 生成器

## ⚠️ 早期測試版，還沒正式包裝

這是 `qoome-iven-voice-spike`（v0→v3 盲測，score2 real 3/4 命中 success 門檻）的第一版產物外化。先讓 Iven 拉下來試用，測過可以的話，再一起討論要包成 Claude Code plugin / MCP server 還是其他形式。目前只是「能跑」的狀態，不是最終交付形態。

## 背景（動手前必讀）

- 完整方法論：`../../CLAUDE.md`（本 repo 根目錄，4 學術基礎）
- 14 rationale → 30 principle 映射：`references/principles.md`（原檔 `../../rationale_to_principles.md`）
- v0-v3 盲測歷程與結論：`../../FINDINGS.md` §B5/§B6/§B7
- **核心轉向**：v0-v2 追 present-self（clone 現在的 Iven）；v3 起追 aspirational-self（Iven 想成為的樣子）。v2 時 Karen+Iven 100% 覺得 baseline 才像 Iven、但 3/3 都欣賞 aspirational 版——present 跟 aspirational 是分開兩件事，本 skill 只做 aspirational。

## 用法

```bash
git clone <this repo>
cd qoome-iven-voice-spike/skills/iven-voice-generator
python3 scripts/gen.py --topic "<題材錨點>" --register Threads   # or 長文
python3 scripts/gen.py --topic "<題材>" --gist "<可選：舊心法一句話>" --register 長文
python3 scripts/gen.py --topic "<題材>" --register Threads --dry-run   # 只印組出來的 prompt，不呼叫 API
```

`gen.py` 只依賴 `anthropic` 這個 Python package（`pip install anthropic`），其他都是標準函式庫。

需要 `ANTHROPIC_API_KEY`（環境變數或 `.env`）。`--dry-run` 不需要 key，可先檢查 prompt 組裝是否符合預期。

### 參數

| 參數 | 必填 | 說明 |
|---|---|---|
| `--topic` | 是 | 題材錨點（例：「AI agent 熱潮下的 HITL 分工律」） |
| `--gist` | 否 | 舊心法/既有觀點一句話，作為 seed（無則純題材發散） |
| `--register` | 否，預設 `Threads` | `Threads`（175字 hook、短平快+誘因）／`長文`（可承載高資訊密度、全篇層層推導） |
| `--pillar` | 否 | 標籤用（商業／HTP專業／私域／生活觀察），不影響生成邏輯 |
| `--dry-run` | 否 | 只印 system+user prompt，不呼叫 API |

## 方法（見 `references/method.md` 完整版）

單次生成，**不走 draft→gate→redo 迴圈**。原因：v3 已證明 present-metric gate 會反噬 aspirational 目標（gate 判準是「像不像現在的 Iven」，跟「想不想成為這樣」是兩件事，硬跑會把 aspirational draft 判假陽性 fail）。

生成邏輯：
1. 依 `--register` 從 `references/style_pack_v1.json` 篩出適用 dim（Threads 走 hook/argument_tension/register_playful；長文走 layered_reasoning/structure_density_hybrid/daishi_narrative_style）
2. 把 `references/exemplar_pool_v4.json` 8 段真實 Iven 語料全部塞進 system prompt 當 few-shot 錨點（pool 小，不篩）
3. 單次呼叫 `claude-sonnet-5`，`max_tokens=8192`（⚠️ 沿用 spike 教訓：extended thinking 會吃光 4096，見 spike commit `aee8017`）

## 已知限制（誠實記錄，不要自欺）

- **prompt-only ceiling**：本 skill 純 prompt-engineering，spike FINDINGS 已證實 prompt-only 隱性層 ceiling ~30-40%（EMNLP 2025）。不會產出完美 Iven 聲音，只是目前可行的最佳近似。
- **golden-set 仍是 0/15**：`daishi_narrative_style` dim 目前只能給中性分，Iven 自己的敘事範例待冷啟填 `wiki/soul/golden-set.md`（personal-wiki repo）。
- **未過 embedding gate 驗證**：`training_data/` + `embedding_gate/`（軌道 B/C）尚未執行，本 skill 的輸出品質目前只能靠人工盲測把關，無自動化 gate。
- **只在 v3 測過的 4 pillar** 有 exemplar/prompt 調校過的把握（商業/HTP專業/私域/生活觀察），其他主題類型未驗證。
- **本輪未做 live API 測試**（見 `scripts/gen.py` 完成筆記）——`--dry-run` 已驗證 prompt 組裝邏輯正確，但實際生成品質未經人工複核。

## Source of truth（避免版本漂移）

**現況**：`references/` 是從這個 repo 根目錄的 `style_pack.json`／`seeds/aspirational_exemplar_pool_v4.json`／`rationale_to_principles.md` 複製的快照。若根目錄那幾份檔案之後更新，這裡的 `references/` 要記得手動同步一次，不然會對不上——這是已知的技術債，還沒有自動化機制。

**未來**：等 personal-wiki 那邊的 `soul/dist/` 編譯出正式版本（目前卡在 golden-set 還沒填），這裡的 `references/` 應該改成直接引用那邊，不再手動複製。
