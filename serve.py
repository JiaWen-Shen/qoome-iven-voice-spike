"""本機 sidecar —— 讓 iven_voice_graph.run_once() 可以被 HTTP 呼叫。

用途：fork 出來的 qoome-content-factory 副本，讓「產生文章」按鈕改打這裡，
繞過 gateway/n8n，直接跑 draft→gate→退件重寫 迴圈。純本機測試用，不對外。

用法：
  export ANTHROPIC_API_KEY=sk-ant-...
  uvicorn serve:app --port 8899
"""
import json, os
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from iven_voice_graph import run_once

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = json.load(open(os.path.join(HERE, "seeds/seeds.json"), encoding="utf-8"))["pairings"]

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class DraftGateRequest(BaseModel):
    topic: str
    editorial_intent: Optional[str] = None


def pick_seed(topic: str, editorial_intent: Optional[str]) -> dict:
    """demo 用簡單挑選：關鍵字對到哪個 pairing 的 pillar/anchor 就用哪組，
    對不到就用第一組（p1）。不做複雜比對邏輯，符合 spike 一貫的最小可行原則。"""
    hay = f"{topic} {editorial_intent or ''}"
    for p in SEEDS:
        if p["new_topic"]["pillar"] in hay or p["old_heart"]["name"] in hay:
            return p
    seed = dict(SEEDS[0])
    seed["new_topic"] = dict(seed["new_topic"], anchor=topic)
    return seed


@app.post("/draft-gate")
def draft_gate(req: DraftGateRequest):
    seed = pick_seed(req.topic, req.editorial_intent)
    result = run_once(seed, mode="real", max_attempts=3, naive_first=False)
    return {
        "draft": result["history"][-1]["draft"],
        "total": result["final_total"],
        "pass": result["final_pass"],
        "attempts": result["attempts"],
        "history": [{"attempt": h["attempt"], "total": h["total"], "pass": h["pass"]}
                    for h in result["history"]],
        "seed_used": {"old_heart": seed["old_heart"]["name"], "topic": req.topic},
    }


@app.get("/health")
def health():
    return {"ok": True}
