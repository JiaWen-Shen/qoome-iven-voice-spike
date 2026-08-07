"""C2 — pretrained sentence-transformers cosine baseline（輕量版技術，免費/CPU），
先跑這個確認「值不值得做中量版 contrastive fine-tune」，避免沒必要就燒錢燒時間。

⚠️ 中量版 fine-tune 本身需要「幾百 pair 起跳」（見 Vault plan 24-*.md 決策4），
現況 training_data/preference_pairs.jsonl 只有 10 pair，即使這支 baseline 沒過門檻，
也不代表現在該衝去 fine-tune——pair 量本身就不夠，是獨立的 blocker。

方法（避開 Karen round 1 陷阱 B3.5→B3.6 教訓，見 FINDINGS.md）：
- Positive/negative corpus 沿用既有校準過的 seeds/eval_set.json（iven_tier_a / slop），
  跟 B2/B3/B3.5/B3.6 歷史結果同一份語料，可比較。
- Held-out 測試集：v1/v2/v3 blind test 全部 10 組 real vs naive_prof pair（20 篇），
  topic 跟 eval_set.json 完全不重疊（忘機哲學 vs AI/商業評論兩個不同語料池）——
  比 B3.6 原本 n=2 held-out 大很多，且天生跨題材，是比「同一題材」更嚴格的測試
  （模型要是抓 topic word 而非 style，在完全不同題材域之間會直接崩潰）。
- Metric：AUROC（real=1 / naive_prof=0），用 positive-centroid 相似度 - negative-centroid 相似度 當 score。
- Exit criterion：AUROC > 0.75 → 換裝進 skill；沒過 → 誠實記錄，不硬做。

Usage: .venv/bin/python3 embedding_gate/baseline_test.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

HERE = Path(__file__).parent.parent.resolve()

EVAL_SET = json.loads((HERE / "seeds/eval_set.json").read_text(encoding="utf-8"))
POS_TEXTS = [x["text"] for x in EVAL_SET["iven_tier_a"]]
NEG_TEXTS = [x["text"] for x in EVAL_SET["slop"]]


def load_draft_json(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))["drafts"]


def collect_held_out_pairs():
    """v1/v2/v3 全部 real vs naive_prof pair，topic 跟 eval_set.json 不重疊。"""
    pairs = []
    for fname, version in [("blind_test_drafts.json", "v1"), ("blind_test_drafts_v2.json", "v2"), ("blind_test_drafts_v3.json", "v3")]:
        for d in load_draft_json(fname):
            tid = d.get("topic_id") or d.get("id")
            modes = d["modes"]
            if "real" in modes and "naive_prof" in modes:
                pairs.append({
                    "topic_id": tid, "version": version,
                    "real": modes["real"]["draft"],
                    "naive_prof": modes["naive_prof"]["draft"],
                })
    return pairs


def auroc_from_scores(labels, scores):
    """Mann-Whitney U based AUROC，不依賴 sklearn。labels: 1=positive class."""
    pos_scores = [s for l, s in zip(labels, scores) if l == 1]
    neg_scores = [s for l, s in zip(labels, scores) if l == 0]
    n_pos, n_neg = len(pos_scores), len(neg_scores)
    if n_pos == 0 or n_neg == 0:
        return None
    count = 0.0
    for ps in pos_scores:
        for ns in neg_scores:
            if ps > ns:
                count += 1.0
            elif ps == ns:
                count += 0.5
    return count / (n_pos * n_neg)


def main():
    model_name = sys.argv[1] if len(sys.argv) > 1 else "sentence-transformers/all-MiniLM-L6-v2"
    print(f"loading model {model_name}...", file=sys.stderr)
    model = SentenceTransformer(model_name)

    pos_emb = model.encode(POS_TEXTS, normalize_embeddings=True)
    neg_emb = model.encode(NEG_TEXTS, normalize_embeddings=True)
    pos_centroid = pos_emb.mean(axis=0)
    neg_centroid = neg_emb.mean(axis=0)
    pos_centroid /= np.linalg.norm(pos_centroid)
    neg_centroid /= np.linalg.norm(neg_centroid)

    held_out = collect_held_out_pairs()
    print(f"held-out pairs: {len(held_out)} (topics: {[p['topic_id'] for p in held_out]})", file=sys.stderr)

    labels, scores, rows = [], [], []
    for p in held_out:
        for mode, label in [("real", 1), ("naive_prof", 0)]:
            text = p[mode]
            emb = model.encode([text], normalize_embeddings=True)[0]
            sim_pos = float(np.dot(emb, pos_centroid))
            sim_neg = float(np.dot(emb, neg_centroid))
            score = sim_pos - sim_neg
            labels.append(label)
            scores.append(score)
            rows.append({
                "topic_id": p["topic_id"], "version": p["version"], "mode": mode,
                "sim_to_iven_tier_a": round(sim_pos, 4),
                "sim_to_slop": round(sim_neg, 4),
                "score": round(score, 4),
            })

    auroc = auroc_from_scores(labels, scores)

    out = {
        "meta": {
            "model": model_name,
            "technique": "輕量版（pretrained cosine，no fine-tuning）",
            "positive_corpus": f"seeds/eval_set.json iven_tier_a (n={len(POS_TEXTS)})",
            "negative_corpus": f"seeds/eval_set.json slop (n={len(NEG_TEXTS)})",
            "held_out_n_pairs": len(held_out),
            "held_out_n_texts": len(labels),
            "held_out_topics_overlap_with_corpus": False,
            "exit_criterion": "AUROC > 0.75",
            "auroc": round(auroc, 4) if auroc is not None else None,
            "passed": bool(auroc is not None and auroc > 0.75),
        },
        "per_item": rows,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
