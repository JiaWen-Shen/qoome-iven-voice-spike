# Rationale → Principle 映射（批次 1 / A1）

14 條 Iven rationale（v0 訪談 4 + v1 盲測 3 + v2 盲測 3 + v3 盲測 4）精讀拆解，抽出 30 條 principle。
用途：`style_pack.json` v1 校準依據（A2）、`training_data/principle_signals.jsonl` 未來輸出源（B3）。

不重跑決策：本檔只做映射，不重新評估「real vs naive_prof 哪個贏」——結論已在 `FINDINGS.md` §B5/§B6 定案。

---

## R-index（14 條 rationale 原始出處）

| ID | 版本 | 來源 | 檔案 |
|---|---|---|---|
| R1 | v0-A | 2026-07-18 訪談，商業模式/專利分潤題 | `qoome-edge-share/iven-eval-answers.json` `A2-1-note` |
| R2 | v0-B | 訪談，AI agent workspace hub 題 | 同上 `B2-1-note` |
| R3 | v0-C | 訪談，信任機制題 | 同上 `C2-1-note` |
| R4 | v0-D | 訪談，兩性關係投射題 | 同上 `D2-1-note` |
| R5 | v1-p1 | 2026-08-01 盲測第一輪，利益對齊×AI產品失敗 | `FINDINGS.md` §B5 |
| R6 | v1-p2 | 同輪，重組式機會×過剩市場 | 同上 |
| R7 | v1-p3 | 同輪，HITL分工律×agent熱潮 | 同上 |
| R8 | v2-p1 | 2026-08-01 盲測第二輪 | `qoome-edge-share/iven-voice-blind-test-v2-answers.json` |
| R9 | v2-p2 | 同輪 | 同上 |
| R10 | v2-p3 | 同輪 | 同上 |
| R11 | v3-p1 | 2026-08-02/03 盲測第三輪，商業/專業資產化題（dual rubric） | `qoome-edge-share/iven-voice-blind-test-v3-answers.json` |
| R12 | v3-p2 | 同輪，商業模式題 | 同上 |
| R13 | v3-p3 | 同輪，判斷力題 | 同上 |
| R14 | v3-p4 | 同輪，生活觀察題 | 同上 |

v3 order_map 已解出 A/B 對應 real/naive_prof（v3 rationale 引用時一律標明哪邊是 real）：
R11 A=real／R12 B=real／R13 B=real／R14 A=real。

---

## 敘事結構（P01–P07）

### P01: 層層推導非快速斷言
- 出處：v1 p1（R5）+ v2 p1（R8）
- Iven 原話：「我比較會層層推導，甚至用故事、舉例來說明，不會很快就斷言結論。」（R5）／「A的敘事邏輯比較像我這樣一層一層講下來」（R8）
- Chosen behavior：前提→中介→結論 3+ 層推理鏈才給出斷言
- Rejected behavior：開頭就丟結論句、無推導過程——跟現有 `short_assertive` dim（短句斷言化）直接矛盾
- 可量化？：是；metric = 推理鏈層數 ≥3（llm judge 計數，非純字數）
- 適用 register：全 register（已建 dim：`layered_reasoning`）

### P02: 故事、舉例具體場景非條列論證
- 出處：v1 p1（R5）+ v1 p3（R7）+ v3 p3（R13）
- Iven 原話：「甚至用故事、舉例來說明」（R5）／「比較欣賞C（naive_threads）的輕鬆說故事的敘事寫法」（R7）／「B更生動的故事寫法，雖然張力還不夠，但確實是我欣賞的方向」（R13）
- Chosen behavior：含具體 case/scenario/人物動作，非抽象概念堆疊
- Rejected behavior：純條列點、純抽象論證無場景
- 可量化？：否（llm judge 判斷是否含 case/scenario）
- 適用 register：全 register（已建 dim：`narrative_examples`）

### P03: 貫穿主軸洞見非套版拼湊
- 出處：v1 p1（R5）
- Iven 原話：「這三個都比較像是套版的文字，缺少一個貫穿主軸洞見或視角。」
- Chosen behavior：一個 non-obvious 主軸洞見貫穿全文
- Rejected behavior：拼湊 3-4 個不相關 point，各自獨立無串連
- 可量化？：否
- 適用 register：全 register（已建 dim：`throughline_insight`）

### P04: 大時叔叔敘事結構錨點
- 出處：v1 p2（R6）
- Iven 原話：「我內容自己的完形卻是像「大時叔叔」那樣的敘事結構和方法。」
- Chosen behavior：人物化場景開場 + 視角切入 + 多層時間軸疊加 + 對比式量化警句（見 `sources/daishi/narrative-analysis.md` 7 手法）
- Rejected behavior：無人物/場景，純論述開場
- 可量化？：部分；heuristic proxy = 開場是否含具體場景/人物詞，敘事節奏仍需 llm 判斷
- 適用 register：長文（已建 dim：`daishi_narrative_style`；golden-set 待補，暫給中性分）

### P05: 特殊視角/情境切入非泛泛而談
- 出處：v2 p1（R8）+ v3 p4（R14）
- Iven 原話：「我比較欣賞B的寫法，從一個特殊視角或情境切入，帶重點帶數字。」（R8）
- Chosen behavior：開場即鎖定一個具體視角/情境（非通用開場句），並帶重點/數字支撐
- Rejected behavior：泛用開場、無具體切入點
- 可量化？：否（llm 判斷開場是否有具體視角）
- 適用 register：全 register（**NEW dim**：`vantage_point_entry`）

### P06: 反覆辯證 + 反直覺洞察
- 出處：v3 p1（R11）
- Iven 原話：「我更欣賞的其實會更是那種反覆辯證，且敘事更深挖進一個「之前沒想到」或「和直覺相反」的敘事模式，會更顯得具有「反直覺」洞察的專業感。」
- Chosen behavior：先立常識/直覺 thesis → 反轉 antithesis → 新洞見 synthesis（真實範例見下方 A3 exemplar：`卷六-財散民聚`「財聚則民散」→「財散則民聚」結構）
- Rejected behavior：單向論述，無 thesis-antithesis 轉折
- 可量化？：否（llm 判斷是否有明確轉折句「但其實/然而/反而」+ 反轉後新結論）
- 適用 register：全 register（**NEW dim**：`dialectic_counterintuitive`）

### P07: real 骨架 + naive 資訊密度 hybrid
- 出處：v3 p4（R14）
- Iven 原話：「如果是系列議題或是更長文的反覆辯證引導，用A的手法但B的資訊密度，會是我更欣賞的類型。」（A=real 敘事手法，B=naive_prof 資訊密度）
- Chosen behavior：real 的敘事骨架（層層推導+故事化）承載 naive_prof 等級的資訊密度（數據/術語/具體機制）
- Rejected behavior：骨架對但內容空（real 常見弱點）或密度夠但變技術白皮書無骨架（naive_prof 常見弱點）
- 可量化？：否（需雙軸同時判斷，llm）
- 適用 register：長文/系列議題（**NEW dim**：`structure_density_hybrid`——這是 v3 aspirational-shift 核心新訊號，對應 `personal-wiki/wiki/soul/candidate-mental-models/aspirational-shift.md`）

---

## 可量化 constraint（P08–P14）

### P08: 口讀感（順口非拗口）
- 出處：v2 p3（R10）+ v3 p1（R11）+ v3 p3（R13）
- Iven 原話：「敘事的口氣實在是拗口，不像是人在講話。」（R10）／「以我這種心中默唸口讀型的人來說，一個句子要讀懂需要反覆看好幾次。」（R11）／「文筆還稍硬一點（口讀上不符合我自己的慣性，但不代表不好）」（R13）
- Chosen behavior：句子唸出聲順口，無需反覆看即可讀懂
- Rejected behavior：堆疊修飾語/從句嵌套過深導致要重讀
- 可量化？：部分；heuristic proxy = 每句逗號數 ≤3 或從句嵌套層 ≤2 當警戒線，但最終判準需 llm 唸讀模擬（純 heuristic 會誤判正常長句）
- 適用 register：全 register（**NEW dim**：`vocalization_ease`；⚠️ 與 `short_assertive` 部分重疊但焦點不同——`short_assertive` 管句長，`vocalization_ease` 管唸讀順暢度）

### P09: short_assertive vs layered_reasoning 張力界線
- 出處：既有 style_pack `known_tension` + v1 p1（R5）
- Iven 原話：見 P01
- Chosen behavior：register 條件化——Threads 開場/結尾可短句斷言，中段論證走層層推導；長文全篇走層層推導
- Rejected behavior：全篇短句斷言（現況 `short_assertive` weight 2 未條件化，已知衝突）
- 可量化？：是；metric = 短句斷言只允許出現在開場 hook 或結尾金句位置，中段比例應 <20%
- 適用 register：Threads（允許開場/結尾短句）／長文（全篇層層推導）

### P10: 論點張力非平鋪直訴
- 出處：v3 p2（R12）
- Iven 原話：「不過B對我來說，還缺乏一種「論點的張力」。」
- Chosen behavior：論點需有反差/衝突/風險堆疊製造張力（非平舖陳述事實）
- Rejected behavior：觀點正確但語氣平淡、無衝突感
- 可量化？：否（llm 判斷）
- 適用 register：Threads/社群（**NEW dim**：`argument_tension`）

### P11: 吸引力/hook 非說教
- 出處：v3 p2（R12）
- Iven 原話：「觀點可能很好，但會偏說教，缺乏吸引人不自覺一直想往下看的誘因。」
- Chosen behavior：開場製造「想往下看」的誘因（懸念/反常識/具體數字）
- Rejected behavior：說教語氣開場（「我認為…」「大家應該…」）
- 可量化？：是；沿用既有 `hook_175` dim，補充「非說教語氣」判準
- 適用 register：Threads（擴充既有 dim）

### P12: 社群 register 要容易入口但不失張力
- 出處：v3 p2（R12）+ v3 p4（R14）
- Iven 原話：「B這種比較口語、人性的短文，是我覺得更「容易入口」的方式，但我不擅長。」（R12）／「A的寫法還是更容易入口」（R14）
- Chosen behavior：Threads 版本優先「容易入口」（口語/短句/具體）+ P10 論點張力，兩者缺一不可
- Rejected behavior：只有容易入口沒張力（淪為 naive_threads baseline 問題）或只有張力沒入口（淪為 real 拗口問題）
- 可量化？：否（需綜合判斷）
- 適用 register：Threads（擴充 `register_playful` dim）

### P13: 長文/系列議題 register 允許高資訊密度
- 出處：v3 p4（R14）
- Iven 原話：見 P07
- Chosen behavior：長文版本可承載 naive_prof 等級的技術細節/數據密度，只要骨架維持敘事化（P07）
- Rejected behavior：短文（Threads）塞入高密度技術細節（會變成 P16 技術白皮書負例）
- 可量化？：否
- 適用 register：長文/系列議題（新增 register 判準，對應 `structure_density_hybrid` dim）

### P14: 娓娓道來型敘事適合長文不適合社群
- 出處：v1 p2（R6）
- Iven 原話：「B這種娓娓道來的模式，比較像我會寫的，但拿來做社群貼文會太軟。」
- Chosen behavior：娓娓道來/舖陳型敘事保留給長文，社群貼文需更快進入張力/hook
- Rejected behavior：社群貼文用長文節奏開場（太軟、無法在 175 字內勾住）
- 可量化？：是；沿用 `hook_175` metric，補充 register 條件（娓娓道來節奏只允許長文）
- 適用 register：Threads（禁）／長文（允許）

---

## Register 切換（已併入 P12–P14，此段補一條總結）

### P29: register 判準總結——Threads 短平快+誘因，長文/系列反覆辯證引導
- 出處：v3 p4（R14）綜合 P12/P13
- Iven 原話：見 P14（R14）
- Chosen behavior：依 register 切兩套 profile——Threads（P10+P11+P12）vs 長文（P07+P13+P01 全篇）
- Rejected behavior：同一套 profile 套用所有 register（現況 `style_pack` v0 未分 register，已知盲點）
- 可量化？：否（schema 層規則，style_pack v1 起需標 register 欄位）
- 適用 register：全 register（元規則）

（P29 編號沿用原批次規劃順序，置於此處避免打斷 P08-P14 可量化段落連貫性；下方 P15-P28、P30 依序接續。）

---

## 硬性 negative（P15–P20）

### P15: 拗口/生硬（負向，非口語）
- 出處：v2 p3（R10）+ v3 p1（R11）+ v3 p3（R13）
- Iven 原話：見 P08
- Chosen behavior：（反向）避免
- Rejected behavior：句子需反覆看才懂、書面語堆疊（如「透過…之機制以達成…之目的」型公文腔）
- 可量化？：部分；heuristic proxy 同 P08
- 適用 register：全 register（P08 的負向鏡像。⚠️ 建議：若 `vocalization_ease` 判定嚴重拗口，比照 `no_seed_leak` 走硬性扣分而非加權稀釋——B3 已證明加權平均會被稀釋掉，見 FINDINGS §B3）

### P16: 技術白皮書腔（負向，除非長文 register 且骨架敘事化）
- 出處：v3 p4（R14）
- Iven 原話：「B的敘事結構像，但更像是在寫技術白皮書。」
- Chosen behavior：（反向）避免
- Rejected behavior：純技術規格條列、無敘事骨架承載
- 可量化？：否（llm 判斷「有無敘事骨架承載技術細節」）
- 適用 register：全 register（Threads 絕對禁止；長文需搭配 P07 hybrid 才允許密度）

### P17: 套版文字/缺主軸洞見（負向）
- 出處：v1 p1（R5）
- Iven 原話：見 P03
- Chosen behavior：（反向）
- Rejected behavior：拼湊業界常見 point、無獨特視角
- 可量化？：否（既有 dim `throughline_insight` 負向情境）
- 適用 register：全 register

### P18: 說教感/無誘因（負向）
- 出處：v3 p2（R12）
- Iven 原話：見 P11
- Chosen behavior：（反向）
- Rejected behavior：「我認為/大家應該/我們需要」開場的說教句式
- 可量化？：是；heuristic 可偵測開場是否為說教句型 → 出現即扣分
- 適用 register：Threads（擴充既有 dim `hook_175` 負向）

### P19: AI slop 概念重疊（負向，Karen pre-filter，非 Iven 主判準）
- 出處：FINDINGS §B5 Karen 補充觀察 3（交叉引用 R5「套版」概念重疊）
- Iven 原話（交叉引用）：「都比較像是套版的文字」（R5）
- Chosen behavior：（反向）
- Rejected behavior：connective 過用（說穿了/坦白講/其實/基本上/問題是 ≥4次）、tone 無起伏
- 可量化？：是；沿用既有 dim `connective_overuse`（heuristic，≥4次扣分）
- 適用 register：全 register（既有 dim，不需新增）

### P20: self-note 括號/內文自我舉例（負向，Karen pre-filter）
- 出處：FINDINGS §B5 Karen 補充觀察 1-2（非 Iven 直接 rationale，Karen 判斷，標記為次要 signal）
- Iven 原話：無（Karen 觀察）
- Chosen behavior：（反向）不用旁白 flag 自造詞、不用自己/Qoome 名字舉例
- Rejected behavior：「（我剛發明的詞，先收下）」型 self-note；內文出現「Iven」「Qoome」自我指涉舉例
- 可量化？：是；heuristic = regex 偵測自陳新詞 pattern + 內文出現作者本名
- 適用 register：全 register（**NEW dim**：`no_self_reference`，weight 建議 1，Karen pre-filter 非 gold standard）

---

## Quality tier annotation（P21, P30）+ 方法論 principle（P22–P28）

### P21: 「及格標準」tier 下限定義
- 出處：v3 p3（R13）
- Iven 原話：「我自覺A這篇文章就是我認為的「及格標準」，寫到這程度，其實就不輸人了。」
- Chosen behavior：tier=passing 下限 = 敘事骨架對（P01+P05）+ 文筆稍硬可接受（不要求完美 P08）
- Rejected behavior：敘事骨架都不對 → 不到 passing
- 可量化？：是（`training_data/tier_annotations.jsonl` schema 用此當 passing 錨點）
- 適用 register：全 register

### P22: 具名概念持久性優於通用內容
- 出處：v0-D（R4）
- Iven 原話：「像是「便宜多巴胺機制」也是我常會提到的名詞，但先前餵入的內容只有一份有提到，有被抓出來用，確實很厲害。」
- Chosen behavior：exemplar/corpus 中反覆出現的命名詞彙（即使只出現一次於少量語料）比通用內容更該被 retrieve/複用
- Rejected behavior：忽略語料中低頻但具名的專屬詞彙、只抓高頻通用字
- 可量化？：是；retrieval/prompt 建構時應對「命名詞」加權（非純 tf-idf 頻率）
- 適用 register：全 register（影響 exemplar pool 選材策略，非文字風格 dim）

### P23: 先建框架/公理再推參數（商業模式敘事順序）
- 出處：v0-A（R1）
- Iven 原話：「我自己在商業模式的設計上，都會先把利害關係人間的交互、框架及模式做一個深度構建及確認，然後把參數的推演，當做是真正能否落地的最重要一步。」
- Chosen behavior：商業/機制類主題先講框架與角色關係，參數/細節放後段
- Rejected behavior：開場就跳進參數/數字細節，未先建立關係框架
- 可量化？：否（llm 判斷段落順序）
- 適用 register：長文/商業主題

### P24: 找到未被說出的悖論是加分
- 出處：v0-C（R3）
- Iven 原話：「我直覺在寫這命題時，確實有發現這是個悖論，AI確實也有找到我沒看到的悖論。」
- Chosen behavior：主動點出主題內隱含的悖論/矛盾（呼應 P06 反直覺洞察）
- Rejected behavior：只講表面共識，未挖出深層矛盾
- 可量化？：否
- 適用 register：全 register（與 P06 交叉引用，非獨立 dim，為 `dialectic_counterintuitive` 的子案例）

### P25: 洞見需比讀者初見更深一層
- 出處：v0-B（R2）
- Iven 原話：「像我會寫的，而且比我猛一看才去想還深入洞察。」
- Chosen behavior：second-order insight——不是讀者第一眼就能想到的層次
- Rejected behavior：停在讀者一看就懂的表層觀點（呼應 P03 throughline_insight 的「非 obvious」要求）
- 可量化？：否
- 適用 register：全 register（與 `throughline_insight` 交叉引用）

### P26: 特殊視角情境切入是欣賞點但非現況（訓練資料優先序 principle）
- 出處：v2 p1（R8）
- Iven 原話：見 P05
- Chosen behavior：aspirational 訓練應優先強化「視角切入+數字佐證」（現況弱項），而非只固化現有層層推導能力
- Rejected behavior：只重複現況強項（層層推導）、不練習現況弱項（視角切入）
- 可量化？：否（方法論層 principle，非單篇評分 dim；影響 exemplar pool 選材與訓練資料標註優先序）
- 適用 register：全 register

### P27: pick（像現在）與 score2（想成為）需分開追蹤（評測方法論 principle）
- 出處：v2 全題 hidden signal（R8-R10）+ v3 dual rubric 設計依據
- Iven 原話：「A敘事手法不像，但我欣賞。」（R9，v2 p2）
- Chosen behavior：任何未來評測/訓練資料標註都要拆兩欄——「像不像現在」與「想不想成為這樣」不能合併成單一分數，合併會把 aspirational signal 稀釋掉（v2 表面結論「real 全輸」就是被稀釋的例子，見 FINDINGS §B6）
- Rejected behavior：單一 pick/單一分數評測（v0-v2 的作法，已證明會誤判方向）
- 可量化？：是（schema 層規則，非文字內容 metric）
- 適用 register：全 register（評測方法論，非 style dim；已落實於 v3 dual-score schema，未來 training_data pair 標註要延續）

### P28: 反面警訊守則——若欣賞方向本身被否定，需重新檢視 aspirational 假設
- 出處：v3 hypothesis 設計時的守則（FINDINGS §B6 v3 setup 段），非直接單一 rationale；R11（v3 p1）「B我不擅長這樣寫」仍保留「欣賞」不觸發此警訊，特此區分
- Iven 原話（對照，非觸發案例）：「B就是我欣賞的敘事類型之一，但我不擅長這樣寫」（R11）← 不算警訊（仍欣賞，只是不擅長）
- Chosen behavior：持續追蹤 rationale 中是否出現「real 型的我也不想寫」等語句
- Rejected behavior：若出現此類語句而未觸發重新檢視，會導致方向偏離仍被誤判為 success
- 可量化？：是（schema 層規則：rationale 需標注是否命中此 veto 語句 pattern）
- 適用 register：全 register（評測方法論）

### P30: 「不輸人」量化門檻——骨架對+文筆稍硬=pass下限，骨架對+順口=tier A
- 出處：v3 p3（R13）+ P08/P21 綜合
- Iven 原話：見 P21
- Chosen behavior：`tier_annotations` 標註規則——pass 下限只要求骨架（P01+P03），不要求完美口讀感（P08 可稍硬）；tier A 才要求骨架+順口雙滿足
- Rejected behavior：用完美文筆當唯一 pass 門檻（過嚴，會把「稍硬但不輸人」誤判為 fail）
- 可量化？：是（`training_data/tier_annotations.jsonl` 標註 schema 的核心規則）
- 適用 register：全 register

---

## 下游用途

- **A2**（`style_pack.json` v1）：6 個 NEW dim（`vantage_point_entry` / `dialectic_counterintuitive` / `structure_density_hybrid` / `vocalization_ease` / `argument_tension` / `no_self_reference`）+ register 欄位 + known_tension 更新，全部可回溯到本檔 P05/P06/P07/P08/P10/P20。
- **A3**（exemplar pool v4）：P06（反覆辯證+反直覺）+ P02/P04（生動故事寫法）補洞方向，實際段落見 `seeds/aspirational_exemplar_pool_v4.json`。
- **批次 3**（`training_data/principle_signals.jsonl`）：本檔 30 條 principle 直接匯出，P21/P27/P28/P30 為 schema 層規則、非文字 dim，匯出時需標記 `type: "methodology"` 與其他 `type: "style_dim"` 區分。
