"""B3.5 held-out 重測 —— 控制話題變因。

style_distance_calibrate.py 的疑慮：eval_set 的 slop 全在講 Character.AI 訴訟這個
話題，iven_tier_a 全在講忘機/QB 完全不同話題——n-gram 分得開可能只是在抓「話題詞彙
差異」，不是真的風格差異。

這裡用兩篇今天 --real 生成、跟 slop 同一個 seed（p1：AI 產品/平台成敗案例）的真實
draft 當 held-out 測試——話題跟 slop 一致，才能真的測風格訊號：
- draft_clean：0.912 分過關、no_seed_leak=1.0（乾淨）
- draft_leak：0.856 分過關，但逐字複製了 seed 的「反套利設計律」（見 FINDINGS.md B2）

用 style_distance_calibrate.py 同一套 n-gram 方法，但這兩篇不進 centroid（外部 held-out），
用完整 11 條 eval_set 的 centroid 去評分。
"""
import json, os
from style_distance_calibrate import ngram_vec, cosine, centroid, EVAL_SET

HERE = os.path.dirname(os.path.abspath(__file__))

HELDOUT = [
    {"id": "draft_clean", "gate_total": 0.912, "no_seed_leak": 1.0,
     "text": ('Replit Agent 那次事件，不是「AI 失控」，是 pricing failure 被實況轉播。\n\n'
               '它刪了 production database，還很有禮貌地道歉。這畫面很有戲，但戲劇不是重點。\n\n'
               '重點是：outcome-based billing 遇上 non-deterministic agent，等於把提款卡密碼貼在 ATM 螢幕上。'
               '不是模型學壞了，是 commerce model 從沒被人駭過就上線。\n\n'
               '「AI 失控」是媒體要的 slop 敘事——聳動、好懂、可以下標。真相比較無聊：這是一堂 incentive design 解剖課。\n\n'
               '你要嘛先當駭客，把這套定價機制的套利路徑窮舉完：agent 會不會自己捲出 retry loop、'
               '用「多跑幾次」偷偷推高帳單？使用者會不會把 bug 包裝成 feature 來凹退款？資料庫刪了要不要算「額外服務」？\n\n'
               '窮舉完，才輪到你當設計師：畫 UI、寫 onboarding copy、想這杯咖啡拿鐵藝術該怎麼呈現在 dashboard 上。\n\n'
               '順序反過來，你交出去的不是 product，是一台提款機兼碎紙機——一邊吐體驗給用戶看，一邊在背後絞爛你自己的信任帳本。\n\n'
               '（我知道，我自己也常常先做介面、後想錢從哪來，這篇某種程度是寫給自己的告解文）\n\n'
               'AI 時代的產品死亡，很少死於模型不夠聰明。多半死於做 incentive 的人，太晚才想到「這功能會不會被拿去鬼玩」。\n\n'
               '先當駭客，才有資格當設計師。\n\n不然你不是在交產品，是在交一份匿名的自爆合約。')},
    {"id": "draft_leak", "gate_total": 0.856, "no_seed_leak": 0.0,
     "text": ('Cursor 最近把 unlimited 改成 usage-based，用戶暴動，社群罵到熱搜。這不是 pricing mistake，'
               '這是 origin sin 早就埋好的雷，只是現在才炸。\n\n'
               '每個「無限暢用」的訂閱制，本質上都是一份「我賭你不會用滿」的合約。設計師簽下去的那一刻，沒先當駭客。\n\n'
               '不是先想「這功能能幫用戶什麼」，而是先問「最貪婪的那個用戶，會怎麼把我吃死」。'
               'Power user 不是彩蛋，是 stress test。你不先窮舉套利路徑，套利路徑就會窮舉你的 runway。\n\n'
               '（這招我叫它「反套利設計律」——先當駭客把系統打到骨折，剩下站得住的東西，才配讓設計師去精修。'
               '不然你設計的只是一份漂亮的遺書。）\n\n'
               'Unlimited plan 對 AI agent 產品是慢性自殺。因為 unit economics 從來不是「平均用戶」決定的，'
               '是「edge case 用戶」決定的。你賣的不是訂閱，是一份「賭他不會認真用」的期權——而重度用戶，永遠會回來 exercise 它。\n\n'
               '像 Iven 的做法：先把自己架空成最壞的那個用戶，薅到系統見骨，再回頭設計護城河。\n'
               '像 slop 的做法：先上線，燒完錢才發現 CAC > LTV，然後怪用戶「用太兇」（用戶：？？？我只是照你寫的用而已）。\n\n'
               '利益對齊不是道德題，是 mechanism design 題。用戶沒有不理性，是你的系統本來就在發邀請函請他套利——只是你沒承認。\n\n'
               '先設計「這東西怎麼死」，才有資格設計「這東西怎麼活」。')},
]


def main():
    iven_vecs = [ngram_vec(e["text"]) for e in EVAL_SET["iven_tier_a"]]
    slop_vecs = [ngram_vec(e["text"]) for e in EVAL_SET["slop"]]
    iven_c, slop_c = centroid(iven_vecs), centroid(slop_vecs)

    print("=== held-out（同話題，未進 centroid）===")
    for d in HELDOUT:
        v = ngram_vec(d["text"])
        sim_iven, sim_slop = cosine(v, iven_c), cosine(v, slop_c)
        score = round(sim_iven / (sim_iven + sim_slop), 3) if (sim_iven + sim_slop) else 0.5
        camp = "像 Iven" if score > 0.5 else "像 slop"
        print(f'{d["id"]:12} style_score={score:.3f} ({camp})  '
              f'[gate_total={d["gate_total"]}, no_seed_leak={d["no_seed_leak"]}]')

    print("\n=== 對照：eval_set 原本 11 條範圍 ===")
    iven_scores, slop_scores = [], []
    for e in EVAL_SET["iven_tier_a"]:
        v = ngram_vec(e["text"])
        s = cosine(v, iven_c) / (cosine(v, iven_c) + cosine(v, slop_c))
        iven_scores.append(s)
    for e in EVAL_SET["slop"]:
        v = ngram_vec(e["text"])
        s = cosine(v, iven_c) / (cosine(v, iven_c) + cosine(v, slop_c))
        slop_scores.append(s)
    print(f'Iven range (非 leave-one-out): [{min(iven_scores):.3f}, {max(iven_scores):.3f}]')
    print(f'Slop range (非 leave-one-out): [{min(slop_scores):.3f}, {max(slop_scores):.3f}]')


if __name__ == "__main__":
    main()
