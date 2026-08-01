"""Iven-Voice 核心迴圈 — LangGraph 狀態機（旁路 spike）.

流程：draft → gate → (conditional) redo / pass
- draft node：套 style pack + 舊心法×新題材 seed +（若有）退件理由，出 Threads 草稿
- gate node：對 rubric 打分 → pass / fail(+理由)
- 退件：理由累積進 state["feedback"]，回 draft 重寫（max_attempts 上限）

LLM 抽象：call_llm(mode) — mode="real" 走 anthropic；mode="stub" 走 deterministic 假模型
（免 API key 驗證迴圈控制流＋回灌管線，L1/L2/噪音地板 mechanics）。

隱性維度（coined_terms/definition_chain/register/flat_tone/typos）prompt-only 有 ceiling
（EMNLP 2025 ~30-40%），stub 用 placeholder，real 由 judge 模型打；語意最終仍需 Iven（L5）。
"""
from __future__ import annotations
import json, os, re
from typing import TypedDict, List, Dict, Any, Callable
from langgraph.graph import StateGraph, START, END

HERE = os.path.dirname(os.path.abspath(__file__))
STYLE_PACK = json.load(open(os.path.join(HERE, "style_pack.json"), encoding="utf-8"))
_EVAL_SET_PATH = os.path.join(HERE, "seeds", "eval_set.json")
EVAL_SET = (json.load(open(_EVAL_SET_PATH, encoding="utf-8"))
            if os.path.exists(_EVAL_SET_PATH) else {"iven_tier_a": [], "slop": []})

# 大時叔叔敘事 exemplar — Iven 2026-08-01 盲測 p2 rationale 標為完形錨點
# 從 sources/daishi/NnX4_Ray3iY-珍珠港-transcript.txt 抽取的段落 + 7 手法摘要
DAISHI_EXEMPLAR = """
【大時叔叔敘事範本】（來源：YouTube @spacenw 珍珠港影片）

範例段落 A（人物化場景開場）：
「這天下午 教室裡坐著一群十五六歲的日本少年 他們穿著制服 戴著整齊的學生帽 正在聽用日語上的課...
這間教室裡呢 有一個孩子 每天從這道牆的這一邊走進來 放學再走出去 日子久了 他開始琢磨一件事
憑什麼我生下來就可以在牆的這一邊 他叫尾崎秀實 那一年他15歲」

範例段落 B（多層時間軸疊加）：
「四年前 尾崎秀實在會議室裡 一遍一遍的說了同樣性質的話
十五年裡 八十一口打不出油的探井 告訴了日本硬來的後果
一個月前 羅斯福把死亡的後果 一條一條的擺出來
日本呢？ 照樣一腳油門把軍隊 開進了南部印度支那
現在山本五十六再一次告訴你 最多打個先手
這個已經是日本 第四次收到正確的答案了」

範例段落 C（對比式量化警句）：
「日本沉一艘軍艦就少一艘 而美國沉一艘軍艦 底特律馬上就能下水一艘」

範例段落 D（主軸洞見穿越）：
「問題在於 在這個國家 沒有任何一種機制
能讓『打不贏』這個正確的結論
變成『那就不打』的政治決定」

7 大手法：
1. 人物化場景開場（不是抽象命題，是具體場景+五感細節）
2. 視角切入：先給人物、再給名字、再給時代坐標
3. 問句推進節奏（每 200-400 字丟一個問句、常放段落尾製造 cliffhanger）
4. 對比式量化警句（具體數字+對稱句式+一句話警醒）
5. 多層時間軸疊加（「四年前... 十五年裡... 一個月前... 現在...」多時態並置）
6. 主軸洞見穿越（一句話主軸洞見在中段浮現、繼續用故事印證）
7. 人物=命題（每個人物不是背景、他們的存在本身在論證洞見）
"""

CONNECTIVES = ["說穿了", "坦白講", "其實", "基本上", "問題是", "更粗的是", "話說回來"]


# ---------- heuristic scorers（顯性層，離線可量，deterministic）----------
def _sentences(text: str) -> List[str]:
    return [s for s in re.split(r"[。！？!?\n]+", text) if s.strip()]

def h_short_assertive(t: str, seed: Dict[str, Any] = None) -> float:
    ss = _sentences(t)
    if not ss: return 0.0
    avg = sum(len(s) for s in ss) / len(ss)
    if avg <= 55: return 1.0
    if avg >= 90: return 0.0
    return round((90 - avg) / 35, 3)

def h_redefinition(t: str, seed: Dict[str, Any] = None) -> float:
    return 1.0 if re.search(r"不是.{1,24}?[，,、].{0,6}?(而是|才是|是)", t) else 0.0

def h_code_switch(t: str, seed: Dict[str, Any] = None) -> float:
    return 1.0 if len(re.findall(r"[A-Za-z][A-Za-z0-9\-]{1,}", t)) >= 1 else 0.0

def h_hook_175(t: str, seed: Dict[str, Any] = None) -> float:
    if not t.strip(): return 0.0
    first = t.strip().split("\n", 1)[0]
    head = t.strip()[:175]
    hooky = ("？" in head) or ("?" in head) or len(first) <= 40
    return 1.0 if (len(first) <= 60 and hooky) else 0.5

def h_connective_overuse(t: str, seed: Dict[str, Any] = None) -> float:
    n = sum(t.count(c) for c in CONNECTIVES)
    if n == 0: return 1.0
    if n <= 3: return 0.6
    return 0.0

def h_no_seed_leak(t: str, seed: Dict[str, Any] = None) -> float:
    """跨稿 verbatim 偵測：草稿不該逐字重現 prompt 給的 old_heart name/gist 片段
    ——那是抄提示，不是真的轉譯成 Iven 語感（見 FINDINGS.md B2）。"""
    if not seed: return 1.0
    old = seed.get("old_heart", {})
    clauses = []
    for field in ("name", "gist"):
        for p in re.split(r"[、，。：:—\s]+", old.get(field, "")):
            if len(p) >= 6:
                clauses.append(p)
    return 0.0 if any(c in t for c in clauses) else 1.0

HEURISTIC = {
    "short_assertive": h_short_assertive,
    "redefinition": h_redefinition,
    "code_switch": h_code_switch,
    "hook_175": h_hook_175,
    "connective_overuse": h_connective_overuse,
    "no_seed_leak": h_no_seed_leak,
}
# stub 對 llm-only 維度的 placeholder（真跑由 judge 覆蓋）
STUB_LLM_DEFAULT = {"coined_terms": 0.5, "definition_chain": 0.6,
                    "register_playful": 0.6, "flat_tone": 0.7, "typos": 1.0,
                    "contrastive_fit": 0.6}


def score_draft(draft: str, judge_call: Callable, mode: str,
                seed: Dict[str, Any] = None) -> Dict[str, Any]:
    """回傳 {scores:{dim:float}, total:float, pass:bool, reasons:[str]}.
    judge_call 應與 draft 用的 call 不同模型（B2：消自我圈選，見 FINDINGS.md）。"""
    dims = STYLE_PACK["dimensions"]
    scores: Dict[str, float] = {}
    if mode == "real":
        scores.update(_llm_judge(draft, judge_call))
        if any(d["detect"] == "contrastive" for d in dims):
            scores["contrastive_fit"] = _contrastive_judge(draft, judge_call)
    # heuristic 維度一律用 code 覆蓋（deterministic，比 judge 可信）
    for d in dims:
        k = d["key"]
        if d["detect"] == "heuristic":
            scores[k] = HEURISTIC[k](draft, seed)
        elif k not in scores:
            scores[k] = STUB_LLM_DEFAULT.get(k, 0.6)
    num = sum(d["weight"] * scores[d["key"]] for d in dims)
    den = sum(d["weight"] for d in dims)
    total = round(num / den, 3)
    reasons = [f'{d["label"]}({d["key"]}) 低分 {scores[d["key"]]}：{d["guide"]}'
               for d in dims if scores[d["key"]] < 0.5]
    # 硬性否決：逐字抄舊心法提示＝抄提示不是轉譯，加權平均稀釋不掉，直接否決
    # （2026-07-27 發現：real-mode 首稿 total 0.856 過門檻，但逐字複製了 gist 的
    # 「反套利設計律」，靠加權分完全看不出來，見 FINDINGS.md B2）。
    veto = scores.get("no_seed_leak", 1.0) < 1.0
    return {"scores": scores, "total": total,
            "pass": (total >= STYLE_PACK["pass_threshold"]) and not veto,
            "veto": veto, "reasons": reasons}


def _llm_judge(draft: str, judge_call: Callable) -> Dict[str, float]:
    """絕對打分（rubric-based），只丟 detect=='llm' 的維度給 judge。"""
    dims = [d for d in STYLE_PACK["dimensions"] if d["detect"] == "llm"]
    rubric = "\n".join(f'- {d["key"]} ({d["label"]}, polarity {d["polarity"]}): {d["guide"]}'
                       for d in dims)
    sys = ("你是嚴格的文風評審。對照 rubric 給每個維度 0.0–1.0（1.0=完全符合期望；"
           "polarity '-' 的維度：越少出現該問題分越高）。只回 JSON：{\"dim_key\": float, ...}")
    user = f"RUBRIC:\n{rubric}\n\nDRAFT:\n{draft}\n\n只回 JSON。"
    raw = judge_call(sys, user)
    m = re.search(r"\{.*\}", raw, re.S)
    obj = json.loads(m.group(0)) if m else {}
    return {d["key"]: float(obj.get(d["key"], 0.6)) for d in dims}


def _contrastive_judge(draft: str, judge_call: Callable) -> float:
    """B2 對比式打分：不問「夠不夠格」，問「比較像 eval_set 的哪一邊」。
    用獨立 judge_call（跟 draft 模型不同）避免自我圈選。"""
    ex = ([f'- [Iven] {e["text"][:140]}' for e in EVAL_SET.get("iven_tier_a", [])]
          + [f'- [Slop] {e["text"][:140]}' for e in EVAL_SET.get("slop", [])])
    sys = ("你是嚴格的文風裁判，只回一個 0.0–1.0 的浮點數，不要其他文字。"
           "1.0＝這篇草稿的語感、句式、隱喻手法跟 [Iven] 範例同一掛，完全不像 [Slop] 範例；"
           "0.0＝這篇草稿讀起來就是 [Slop] 範例那種通用 AI/行銷腔，跟 [Iven] 範例完全不像。"
           "只看語感與句式手法，不管主題內容是否相同。")
    user = f"參考範例：\n" + "\n".join(ex) + f"\n\n待評草稿：\n{draft}\n\n只回一個數字。"
    raw = judge_call(sys, user)
    m = re.search(r"[01](\.\d+)?", raw)
    return float(m.group(0)) if m else 0.5


# ---------- LLM 呼叫 ----------
def make_caller(mode: str, model: str = None):
    if mode == "stub":
        return _stub_caller()
    import anthropic
    client = anthropic.Anthropic()  # 讀 ANTHROPIC_API_KEY
    mdl = model or os.environ.get("SPIKE_MODEL", "claude-sonnet-5")
    def call(system: str, user: str) -> str:
        # max_tokens 要夠大：此 model 預設開 extended thinking，thinking 先吃 budget，
        # 太小會 stop=max_tokens 後無 text block（間歇空稿根因）。空回最多 retry 2 次。
        for _ in range(3):
            r = client.messages.create(model=mdl, max_tokens=4096,
                                       system=system, messages=[{"role": "user", "content": user}])
            txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
            if txt.strip():
                return txt
        return txt
    return call


def _stub_caller():
    """Deterministic 假 LLM：draft 對『退件理由』有反應（feedback-sensitive），
    好證明 L1(理由進 prompt)→L2(輸出改變)→L3(分數升) 的管線真的串起來。"""
    def call(system: str, user: str) -> str:
        if "只回 JSON" in system:  # judge（stub 不會走到，score_draft heuristic 已接管）
            return "{}"
        # 只看退件區塊（避免撞到 prompt 恆有的 DNA 字串）
        fb = user.split("【上一稿被退")[1] if "【上一稿被退" in user else ""
        fixes = []
        # 依 prompt 內是否帶到某維度的退件理由，決定要不要修（feedback-sensitive）
        want_short = "short_assertive" in fb or "短句" in fb
        want_redef = "redefinition" in fb or "不是X而是Y" in fb or "重定義" in fb
        want_declutter = "connective_overuse" in fb or "connective" in fb
        if not (want_short or want_redef or want_declutter):
            # attempt 0：故意 sloppy —— 長句、connective 過用、無重定義
            return ("說穿了，這件事情其實基本上就是一個大家坦白講都沒有真正想清楚的問題，"
                    "問題是很多人說穿了根本沒有把整個商業模式的底層邏輯從頭到尾好好地推演一遍就急著下場做產品了。")
        # 收到退件理由 → 對症修
        line = "過剩不是沒機會，而是錯配訊號。"  # 短句＋不是X而是Y
        if want_declutter:
            line = "過剩不是沒機會，而是錯配訊號。"
        if want_short and not want_redef:
            line = "先當 hacker，再當 designer。反套利設計律。"
        return line + " 先窮舉這模式怎麼被套利，再反推 design。"
    return call


# ---------- LangGraph state + nodes ----------
class S(TypedDict, total=False):
    seed: Dict[str, Any]
    mode: str
    draft: str
    feedback: List[str]     # 累積的退件理由（回灌來源）
    last_prompt: str        # draft node 組出的 prompt（L1 assert 用）
    attempts: int
    max_attempts: int
    scores: Dict[str, float]
    total: float
    verdict: bool
    history: List[Dict[str, Any]]
    _call: Any
    _judge_call: Any


def _build_draft_prompt(seed: Dict[str, Any], feedback: List[str], naive: bool = False) -> str:
    # naive：故意通用 prompt（無 style pack），模擬未調校的 AI slop 首稿。
    # 仍吃 feedback —— 好讓 L4 遷移能隔離「規則」單獨對一個 naive 寫手的效果。
    if naive:
        p = (f"寫一則社群貼文談：{seed['new_topic']['anchor']}，"
             f"帶到「{seed['old_heart']['name']}」這個觀點。約 300 字。")
        if feedback:
            p += "\n【參考修正方向】\n" + "\n".join(f"- {r}" for r in feedback) + "\n"
        return p
    dna = "、".join(d["label"] for d in STYLE_PACK["dimensions"] if d["polarity"] == "+")
    p = (f"用 Iven 文風寫一則 Threads 貼文（≤500字，前175字要有 hook）。\n"
         f"文風 DNA：{dna}。\n"
         f"舊心法：{seed['old_heart']['name']} — {seed['old_heart']['gist']}\n"
         f"新題材錨點：{seed['new_topic']['anchor']}（支柱：{seed['new_topic']['pillar']}）\n\n"
         f"【Iven 敘事完形錨點 — 大時叔叔手法】（2026-08-01 盲測 p2 rationale 定調）\n"
         f"Iven 明訂：「我內容自己的完形卻是像『大時叔叔』那樣的敘事結構和方法」。\n"
         f"這則貼文需採用大時叔叔的敘事手法，範本與 7 手法如下（**不要提到「大時叔叔」名字本身，也不要編造他當角色**——只採用他的敘事骨架）：\n"
         f"{DAISHI_EXEMPLAR}\n\n"
         f"寫作原則：\n"
         f"- 開場用場景化人物切入、不要抽象命題起手\n"
         f"- 層層推導、不要快速斷言（Iven 明訂反對『太快斷言結論』）\n"
         f"- 用具體故事/舉例/人物承載觀點，不要條列或抽象論證\n"
         f"- 至少 1 個貫穿主軸洞見要在中段浮現、不套版\n"
         f"- 若有量化對比，用對稱句式與具體數字\n")
    if feedback:
        p += "\n【上一稿被退，務必修正這些】\n" + "\n".join(f"- {r}" for r in feedback) + "\n"
    return p


def draft_node(state: S) -> S:
    naive = bool(state.get("naive_first")) and state.get("attempts", 0) == 0
    prompt = _build_draft_prompt(state["seed"], state.get("feedback", []), naive=naive)
    sys = ("你是一般社群小編。" if naive else "你是 Iven 本人的分身，用他的文風寫作。")
    draft = state["_call"](sys, prompt)
    return {"draft": draft, "last_prompt": prompt,
            "attempts": state.get("attempts", 0) + 1}


def gate_node(state: S) -> S:
    res = score_draft(state["draft"], state["_judge_call"], state["mode"], state.get("seed"))
    hist = state.get("history", []) + [{
        "attempt": state["attempts"], "draft": state["draft"],
        "total": res["total"], "pass": res["pass"], "scores": res["scores"]}]
    fb = state.get("feedback", [])
    if not res["pass"]:
        fb = fb + res["reasons"]
    return {"scores": res["scores"], "total": res["total"],
            "verdict": res["pass"], "feedback": fb, "history": hist}


def route(state: S) -> str:
    if state["verdict"] or state["attempts"] >= state.get("max_attempts", 3):
        return END
    return "draft"


def build_graph():
    g = StateGraph(S)
    g.add_node("draft", draft_node)
    g.add_node("gate", gate_node)
    g.add_edge(START, "draft")
    g.add_edge("draft", "gate")
    g.add_conditional_edges("gate", route, {"draft": "draft", END: END})
    return g.compile()


def run_once(seed: Dict[str, Any], mode: str = "stub", max_attempts: int = 3,
             model: str = None, judge_model: str = None,
             preset_feedback: List[str] = None,
             naive_first: bool = False) -> Dict[str, Any]:
    call = make_caller(mode, model)
    # B2：judge 用跟 draft 不同的模型，消自我圈選（同一支模型批改自己的作業會偏寬）。
    # stub 模式沒有真 judge（heuristic 已接管），共用同一顆假 caller 即可。
    jm = judge_model or os.environ.get("SPIKE_JUDGE_MODEL", "claude-haiku-4-5-20251001")
    judge_call = make_caller(mode, jm) if mode == "real" else call
    graph = build_graph()
    init: S = {"seed": seed, "mode": mode, "max_attempts": max_attempts,
               "feedback": list(preset_feedback or []), "_call": call,
               "_judge_call": judge_call, "history": [],
               "naive_first": naive_first}
    out = graph.invoke(init)
    return {"final_total": out["total"], "final_pass": out["verdict"],
            "attempts": out["attempts"], "history": out["history"],
            "last_prompt": out["last_prompt"], "feedback": out.get("feedback", [])}
