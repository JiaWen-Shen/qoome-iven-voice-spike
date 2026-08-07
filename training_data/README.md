# training_data/ — weight-opt 原料累積（軌道 B）

目標：把 14 rationale + Iven 既有 Tier-A 整成標準 training data schema，供未來 DPO/LoRA 使用。
**現況：schema 已立，12-20 pair 門檻已達（實際 10 preference pair + 5 tier annotation + 30 principle signal）**，
距重量版門檻（5K-50K pair）還差 3 個 order of magnitude——見 Vault plan `24-*.md`「未來（重量版觸發前提 checklist）」。

## 檔案

| 檔案 | 內容 | 產生方式 |
|---|---|---|
| `preference_pairs.jsonl` | 10 條 DPO-ready pair（v1 2 + v2 3 + v3 5） | `python3 build_pairs.py > preference_pairs.jsonl`（從盲測 draft/answer JSON 直接抓字，不手動轉錄） |
| `tier_annotations.jsonl` | 5 條 tier 標註（2 explicit + 3 inferred） | `python3 build_tiers.py > tier_annotations.jsonl` |
| `principle_signals.jsonl` | P01-P30 全量匯出（26 style_dim + 4 methodology） | `python3 build_principle_signals.py > principle_signals.jsonl` |
| `tier_a_corpus/iven_v0_interviews.md` | v0 4 條訪談 raw corpus | 手動整理自 `qoome-edge-share/iven-eval-answers.json` |
| `tier_a_corpus/iven_rationales_v1-v3.md` | v1-v3 10 條 rationale raw corpus | 手動整理，含 v1 p3 勘誤（見下方「已知問題」） |
| `negative_corpus/slop_examples.md` | 3 類負例（AI 模仿稿/企業模板/拗口執行失敗） | 手動整理自 `seeds/eval_set.json` slop + v3 p1 real draft |

Schema 三份 jsonl 皆由 `build_*.py` 腳本生成（非手動維護）——若上游來源（rationale_to_principles.md / 盲測 answer JSON）修改，重跑對應腳本即可同步，避免手動轉錄漂移。

## preference_pairs.jsonl schema

```jsonl
{"prompt": "...", "chosen": "...", "rejected": "...", "rationale": "...", "source": "iven_v3_p2", "dimensions_scored": ["argument_tension"], "confidence": "strong|medium|weak", "confidence_note": "..."}
```

`confidence` 三級：
- **strong**：v3 dual-rubric 明確 score2 差距 + rationale 直接對應
- **medium**：v2 present-round，chosen 取「欣賞」方向非「pick」方向（P27），或 v3 中 rationale 稍隱晦
- **weak**：v1 present-round，三方皆非強偏好，或訊號 narrow-scope（只在單一維度成立）

## 已知問題

**v1 p3 標籤勘誤**：`FINDINGS.md` §B5 把 Iven p3 rationale 引用中的「C」標註為「naive_threads」，但查 Iven 當輪原始 `order_map`（`qoome-edge-share/iven-voice-blind-test-answers.json`），實際對應是 A=naive_prof／B=naive_threads／C=**real**。`build_pairs.py`/`iven_rationales_v1-v3.md` 已用正確標籤；`FINDINGS.md` 本體本輪未動，是否回頭訂正留給 Karen 決定（這處誤標其實讓原結論更成立——Iven 在 v1 就已對 real 的敘事寫法有正面訊號，比 v2 才浮現的 pick≠欣賞 分裂訊號更早，不是削弱原結論）。

**v3 p4 pair 方向與 Vault plan 原草稿不同**：`24-Iven-Voice-Spike-Shutdown-and-Next-Steps-2026-08-05.md` 批次 3 checklist 原寫「Pair-1：骨架維度 chosen=B, rejected=A／Pair-2：密度維度 chosen=B, rejected=A」——這是 plan 撰寫時（order_map 尚未反解）用 A/B 泛指語意角色（A=real 類、B=naive 類）的占位寫法，非本題實際字母。`build_pairs.py` 已用反解後的正確方向：骨架 pair chosen=real／密度 pair chosen=naive_prof（兩者互為鏡像，正是 P07 hybrid 訊號的資料來源）。

## 3 個 append 觸發規則（Layer 2，見 Vault plan「記憶機制」段）

- **觸發 A**：Iven 對任何生成內容給 feedback（含 Threads 留言、soul 討論、editorial-desk pick）→ **當天 append** 到 `preference_pairs.jsonl`（用 `build_pairs.py` 同款 schema手動加一行，或擴充腳本讀新來源）
- **觸發 B**：每季末 lint（掃當季 Iven 相關 commit + commit msg 找漏掉的 signal）
- **觸發 C**：case-4 editorial-desk 每次 op session → append 該 session 產生的 preference signal

## 下一步

- 軌道 C（`embedding_gate/`，批次 4，需 GPU/雲）：吃本目錄 `preference_pairs.jsonl` + `tier_a_corpus/` + `negative_corpus/` 做 contrastive fine-tune 語料
- 每次新增 pair，`principle_signals.jsonl` 不需重跑（除非 rationale_to_principles.md 本身有新 principle）
