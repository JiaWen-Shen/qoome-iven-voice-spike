# Iven-Voice 核心迴圈 — 旁路 spike

離線驗證「改寫 → gate → 退件重寫 → 回收」決策迴圈，證明回灌管線會動。
**不碰 n8n、不碰編輯台 UI、不接 production。** 對齊 Iven PR#1 comment：LangGraph 重構 + 編輯檯分工。

## 這支證明什麼

| | stub（免 key）| real（需 key）|
|---|---|---|
| 迴圈控制流（draft→gate→redo→pass）| ✅ | ✅ |
| L1 管線：退件理由進下一輪 prompt | ✅ deterministic | ✅ |
| L2 行為：v1≠v2 | ✅ | ✅ |
| L3 分數：回灌提升 & 過噪音地板 | ⚠️ 構造性（stub 是 feedback-sensitive）| ✅ 真判定 |
| L4 遷移：規則套 unseen 題升分 | ⚠️ 構造性 | ✅ 真判定 |
| L5 語意：像不像 Iven | ❌ 需 Iven 盲測 | ❌ 需 Iven |

> stub 用 deterministic 假模型 + heuristic 評分，只證**管線串得起來**（L1/L2 + 控制流）。
> L3/L4 的「真的變準」要 `--real` 跑真 LLM（真噪音地板 + judge 打分）。
> L5「像不像本人」prompt-only 有 ceiling（EMNLP 2025 ~30-40%），最終需 Iven，未來考慮 LoRA/activation steering。

## 跑

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install langgraph anthropic

python run.py --stub                        # 免 key，驗管線
export ANTHROPIC_API_KEY=sk-...
python run.py --real --model claude-sonnet-5   # 真 LLM，驗 L3/L4
```

輸出：`results/results.json` + `results/summary.md`

## 檔案

| 檔 | 作用 |
|---|---|
| `style_pack.json` | Iven 文風 rubric（10 維，顯性 heuristic + 隱性 llm-only；含 AI slop 負向偵測）|
| `seeds/seeds.json` | 舊心法×新題材配對 + 真 Iven 定版 exemplar |
| `iven_voice_graph.py` | LangGraph 狀態機（draft/gate node + conditional redo + stub/real LLM）|
| `run.py` | 驗證階梯 runner（噪音地板 + L1–L4）|
| `results/` | 跑出來的證據 |

## 目前結果（stub）

首稿 0.348（長句、connective 過用、無重定義）→ 退件 → 末稿 0.877（短句、不是X而是Y、中英夾雜）。
lift 0.529 > 噪音地板。規則從 p1 遷移到 unseen p2 也升分。**管線全綠。**

## 下一步

1. `--real` 跑真 LLM（Karen 提供 key）→ 拿真 L3/L4 數字
2. 結果 + code push 個人 research repo（spike 標籤，非 content-factory）
3. 給 Iven：plan 連結 + summary.md + 「PR#1 關掉改走這個」
4. Iven 認同 → Phase 2 真 Iven 盲測 L5 → Phase 3 接編輯台 UI + n8n（一個 node）

## 已知限制（誠實）

- stub 噪音地板 = 0（deterministic），真噪音要 `--real`
- stub 的 L3/L4 是構造性通過（feedback-sensitive 假模型），只證管線非證品質
- 隱性維度（coined_terms/register/flat_tone…）prompt-only ceiling，heuristic 測不到，靠 judge/Iven
- judge 與 draft 目前同家模型；`--real` 建議 judge 換一支避免自我圈選（TODO）
