"""建 principle_signals.jsonl（B3）——rationale_to_principles.md 30 條 P01-P30 直接匯出。

機械轉換，內容需與 rationale_to_principles.md 保持一致；若該檔案未來修改，本檔案需同步重跑。
type 分兩類：
- style_dim：文字風格判準，未來可餵 constitutional DPO / RLAIF
- methodology：評測方法論規則（非文字內容判準），供 training_data schema 設計參考，不直接進 style reward model

Usage: python3 training_data/build_principle_signals.py > training_data/principle_signals.jsonl
"""
import json

METHODOLOGY_IDS = {"P21", "P27", "P28", "P30"}

# (id, name, source, chosen, rejected, quantifiable, register)
PRINCIPLES = [
    ("P01", "層層推導非快速斷言", "v1 p1（R5）+ v2 p1（R8）",
     "前提→中介→結論 3+ 層推理鏈才給出斷言", "開頭就丟結論句、無推導過程", "是；推理鏈層數 ≥3（llm judge）", "全 register"),
    ("P02", "故事、舉例具體場景非條列論證", "v1 p1（R5）+ v1 p3（R7）+ v3 p3（R13）",
     "含具體 case/scenario/人物動作", "純條列點、純抽象論證無場景", "否", "全 register"),
    ("P03", "貫穿主軸洞見非套版拼湊", "v1 p1（R5）",
     "一個 non-obvious 主軸洞見貫穿全文", "拼湊 3-4 個不相關 point", "否", "全 register"),
    ("P04", "大時叔叔敘事結構錨點", "v1 p2（R6）",
     "人物化場景開場+視角切入+多層時間軸疊加+對比式量化警句", "無人物/場景，純論述開場", "部分；開場是否含具體場景/人物詞", "長文"),
    ("P05", "特殊視角/情境切入非泛泛而談", "v2 p1（R8）+ v3 p4（R14）",
     "開場鎖定具體視角/情境並帶重點/數字", "泛用開場、無具體切入點", "否", "全 register"),
    ("P06", "反覆辯證 + 反直覺洞察", "v3 p1（R11）",
     "thesis（常識）→ antithesis（反轉）→ synthesis（新洞見）", "單向論述，無轉折", "否；判斷是否有明確轉折句+新結論", "全 register"),
    ("P07", "real 骨架 + naive 資訊密度 hybrid", "v3 p4（R14）",
     "real 敘事骨架承載 naive_prof 等級資訊密度", "骨架對內容空 或 密度夠但變白皮書", "否", "長文/系列議題"),
    ("P08", "口讀感（順口非拗口）", "v2 p3（R10）+ v3 p1（R11）+ v3 p3（R13）",
     "句子唸出聲順口、無需反覆看即可讀懂", "堆疊修飾語/從句嵌套過深", "部分；每句逗號數≤3或從句嵌套層≤2 當警戒線", "全 register"),
    ("P09", "short_assertive vs layered_reasoning 張力界線", "既有 known_tension + v1 p1（R5）",
     "Threads 開場/結尾可短句斷言，中段走層層推導；長文全篇層層推導", "全篇短句斷言", "是；中段短句斷言比例 <20%", "Threads(部分)/長文(全篇)"),
    ("P10", "論點張力非平鋪直訴", "v3 p2（R12）",
     "論點有反差/衝突/風險堆疊", "觀點正確但語氣平淡", "否", "Threads/社群"),
    ("P11", "吸引力/hook非說教", "v3 p2（R12）",
     "開場製造想往下看的誘因（懸念/反常識/數字）", "說教語氣開場（我認為/大家應該）", "是；沿用 hook_175 + 說教句型偵測", "Threads"),
    ("P12", "社群 register 要容易入口但不失張力", "v3 p2（R12）+ v3 p4（R14）",
     "容易入口(口語/短句/具體) + 論點張力兩者兼具", "只有其一", "否", "Threads"),
    ("P13", "長文/系列議題 register 允許高資訊密度", "v3 p4（R14）",
     "承載 naive_prof 等級技術細節，骨架維持敘事化", "短文塞高密度技術細節", "否", "長文/系列議題"),
    ("P14", "娓娓道來型敘事適合長文不適合社群", "v1 p2（R6）",
     "舖陳型敘事保留給長文", "社群貼文用長文節奏開場", "是；沿用 hook_175 metric + register 條件", "Threads(禁)/長文(允許)"),
    ("P15", "拗口/生硬（負向）", "v2 p3（R10）+ v3 p1（R11）+ v3 p3（R13）",
     "（反向）避免", "句子需反覆看才懂、書面公文腔", "部分；同 P08 proxy，建議 veto 非加權", "全 register"),
    ("P16", "技術白皮書腔（負向）", "v3 p4（R14）",
     "（反向）避免，除非長文+骨架敘事化", "純技術規格條列、無敘事骨架", "否", "全 register"),
    ("P17", "套版文字/缺主軸洞見（負向）", "v1 p1（R5）",
     "（反向）", "拼湊業界常見 point、無獨特視角", "否", "全 register"),
    ("P18", "說教感/無誘因（負向）", "v3 p2（R12）",
     "（反向）", "我認為/大家應該/我們需要 開場句式", "是；說教句型偵測", "Threads"),
    ("P19", "AI slop 概念重疊（負向，Karen pre-filter）", "FINDINGS §B5（交叉引用 R5）",
     "（反向）", "connective 過用（≥4次）、tone 無起伏", "是；沿用既有 connective_overuse dim", "全 register"),
    ("P20", "self-note 括號/內文自我舉例（負向，Karen pre-filter）", "FINDINGS §B5 Karen 觀察1-2",
     "（反向）不用旁白 flag 自造詞、不用自己/Qoome 名字舉例", "「（我剛發明的詞，先收下）」型 self-note；內文出現作者本名", "是；regex 偵測", "全 register"),
    ("P21", "「及格標準」tier 下限定義", "v3 p3（R13）",
     "骨架對（P01+P05）+ 文筆稍硬可接受", "敘事骨架都不對", "是；tier_annotations schema 用此當 passing 錨點", "全 register"),
    ("P22", "具名概念持久性優於通用內容", "v0-D（R4）",
     "反覆出現的命名詞彙比通用內容更該被 retrieve", "忽略低頻但具名的專屬詞彙", "是；retrieval 應對命名詞加權", "全 register"),
    ("P23", "先建框架/公理再推參數", "v0-A（R1）",
     "商業/機制主題先講框架與角色關係，參數放後段", "開場就跳進參數/數字細節", "否", "長文/商業主題"),
    ("P24", "找到未被說出的悖論是加分", "v0-C（R3）",
     "主動點出主題內隱含的悖論/矛盾", "只講表面共識", "否", "全 register"),
    ("P25", "洞見需比讀者初見更深一層", "v0-B（R2）",
     "second-order insight", "停在讀者一看就懂的表層觀點", "否", "全 register"),
    ("P26", "特殊視角情境切入是欣賞點但非現況（訓練資料優先序）", "v2 p1（R8）",
     "aspirational 訓練優先強化視角切入+數字佐證（現況弱項）", "只重複現況強項（層層推導）", "否；方法論層", "全 register"),
    ("P27", "pick（像現在）與 score2（想成為）需分開追蹤", "v2 hidden signal（R8-R10）+ v3 dual rubric",
     "評測/訓練標註拆兩欄，不合併成單一分數", "單一 pick/單一分數評測", "是；schema 層規則", "全 register"),
    ("P28", "反面警訊守則", "v3 hypothesis 設計守則（FINDINGS §B6 v3 setup）",
     "持續追蹤 rationale 是否出現「real 型的我也不想寫」", "出現此語句未觸發重新檢視", "是；schema 層規則", "全 register"),
    ("P29", "register 判準總結", "v3 p4（R14）綜合 P12/P13",
     "Threads（P10+P11+P12）vs 長文（P07+P13+P01全篇）兩套 profile", "同一套 profile 套用所有 register", "否；schema 層規則", "全 register"),
    ("P30", "「不輸人」量化門檻", "v3 p3（R13）+ P08/P21 綜合",
     "pass 下限=骨架對+文筆稍硬可接受；tier A=骨架對+順口雙滿足", "用完美文筆當唯一 pass 門檻", "是；tier_annotations schema 核心規則", "全 register"),
]

for pid, name, source, chosen, rejected, quant, register in PRINCIPLES:
    row = {
        "id": pid,
        "name": name,
        "type": "methodology" if pid in METHODOLOGY_IDS else "style_dim",
        "source": source,
        "chosen_behavior": chosen,
        "rejected_behavior": rejected,
        "quantifiable": quant,
        "register": register,
        "full_detail_ref": f"rationale_to_principles.md#{pid.lower()}",
    }
    print(json.dumps(row, ensure_ascii=False))
