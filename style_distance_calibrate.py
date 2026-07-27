"""B3 補測 —— embedding-based（非 LLM judge）風格距離，零依賴版。

動機：contrastive LLM judge（calibrate.py）分不開 iven_tier_a 跟 slop（gap=-0.1）。
問題是「LLM judge 這個方法論本身有結構性問題」還是「s1/s2 這兩篇 slop 統計特徵上真的很像」？
用字元 n-gram 頻率向量（跟 StyleDistance 同一類「風格向量距離」，但用統計 n-gram 代替
訓練過的 neural embedding——網路裝不了 sentence-transformers/torch 時的零依賴替代）算
cosine similarity，leave-one-out 對每篇算「離 iven 群心近還是離 slop 群心近」。

用法：python style_distance_calibrate.py（無需 API key、無需額外套件）
輸出：results/style_distance_calibration.json
"""
import json, math, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL_SET = json.load(open(os.path.join(HERE, "seeds/eval_set.json"), encoding="utf-8"))


def ngram_vec(text: str, ns=(2, 3)) -> Counter:
    v = Counter()
    t = "".join(text.split())  # 去空白/換行，只看字元序列
    for n in ns:
        for i in range(len(t) - n + 1):
            v[t[i:i + n]] += 1
    total = sum(v.values()) or 1
    return Counter({k: c / total for k, c in v.items()})  # 正規化成頻率分布


def cosine(a: Counter, b: Counter) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def centroid(vecs) -> Counter:
    c = Counter()
    for v in vecs:
        for k, val in v.items():
            c[k] += val
    n = len(vecs) or 1
    return Counter({k: val / n for k, val in c.items()})


def main():
    items = ([dict(e, label="iven_tier_a") for e in EVAL_SET["iven_tier_a"]]
              + [dict(e, label="slop") for e in EVAL_SET["slop"]])
    vecs = {e["id"]: ngram_vec(e["text"]) for e in items}
    iven_ids = [e["id"] for e in items if e["label"] == "iven_tier_a"]
    slop_ids = [e["id"] for e in items if e["label"] == "slop"]

    rows = []
    for e in items:
        # leave-one-out centroid：自己那組排除自己，避免自己算自己分數虛高
        own_ids = iven_ids if e["label"] == "iven_tier_a" else slop_ids
        other_label_ids = slop_ids if e["label"] == "iven_tier_a" else iven_ids
        loo_own = [vecs[i] for i in own_ids if i != e["id"]]
        iven_c = centroid(loo_own) if e["label"] == "iven_tier_a" else centroid([vecs[i] for i in iven_ids])
        slop_c = centroid(loo_own) if e["label"] == "slop" else centroid([vecs[i] for i in slop_ids])
        sim_iven = cosine(vecs[e["id"]], iven_c)
        sim_slop = cosine(vecs[e["id"]], slop_c)
        # 正規化成 0-1，跟 calibrate.py 的 contrastive_fit 同刻度方便對照
        score = round(sim_iven / (sim_iven + sim_slop), 3) if (sim_iven + sim_slop) > 0 else 0.5
        rows.append({"id": e["id"], "label": e["label"], "score": score,
                     "sim_iven": round(sim_iven, 4), "sim_slop": round(sim_slop, 4),
                     "text": e["text"][:60]})

    iven_scores = [r["score"] for r in rows if r["label"] == "iven_tier_a"]
    slop_scores = [r["score"] for r in rows if r["label"] == "slop"]
    gap = round(min(iven_scores) - max(slop_scores), 3)
    report = {"method": "char-ngram(2,3) cosine, leave-one-out centroid", "rows": rows,
              "iven_min": min(iven_scores), "iven_max": max(iven_scores),
              "slop_min": min(slop_scores), "slop_max": max(slop_scores),
              "gap": gap, "separated": gap > 0}

    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump(report, open(os.path.join(HERE, "results/style_distance_calibration.json"), "w", encoding="utf-8"),
               ensure_ascii=False, indent=2)

    for r in sorted(rows, key=lambda r: -r["score"]):
        print(f'{r["label"]:12} {r["id"]:4} {r["score"]:.3f}  {r["text"]}')
    print(f'\nIven range: [{report["iven_min"]}, {report["iven_max"]}]')
    print(f'Slop range: [{report["slop_min"]}, {report["slop_max"]}]')
    print(f'Gap (iven_min - slop_max): {gap}  ->  {"分得開 ✅" if report["separated"] else "分不開 ❌"}')


if __name__ == "__main__":
    main()
