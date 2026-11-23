# -*- coding: utf-8 -*-
"""HowToCook -> NiniMenu dishes 转换器 v3（最终版）"""
import json, re, pathlib

SRC = str(pathlib.Path(__file__).parent / "all_recipes.json")
EXCLUDE_CATS = {"饮品", "甜品", "调料", "半成品加工"}

SEASONING_KEYS = [
    "盐", "糖", "酱油", "生抽", "老抽", "醋", "料酒", "蚝油", "味精", "鸡精", "鸡粉",
    "胡椒", "花椒", "八角", "桂皮", "香叶", "孜然", "五香粉", "十三香", "淀粉", "生粉",
    "食用油", "植物油", "花生油", "香油", "芝麻油", "辣椒油", "豆瓣酱", "甜面酱", "黄豆酱",
    "番茄酱", "沙拉酱", "蜂蜜", "芝麻", "辣椒粉", "干辣椒", "小米椒", "泡椒", "剁椒",
    "蒜蓉辣酱", "小苏打", "酵母", "泡打粉", "咖喱", "芥末", "腐乳", "豆豉", "冰糖",
]

SEASONING_DEFAULT = {
    "食用油": "20毫升", "植物油": "20毫升", "花生油": "20毫升", "盐": "3克", "食盐": "3克",
    "生抽": "15毫升", "老抽": "5毫升", "酱油": "15毫升", "糖": "5克", "白糖": "5克",
    "冰糖": "10克", "醋": "10毫升", "陈醋": "10毫升", "香醋": "10毫升", "白醋": "10毫升",
    "料酒": "10毫升", "黄酒": "10毫升", "蚝油": "10毫升", "淀粉": "5克", "生粉": "5克",
    "玉米淀粉": "5克", "胡椒粉": "1克", "白胡椒粉": "1克", "黑胡椒粉": "1克",
    "鸡精": "2克", "味精": "2克", "鸡粉": "2克", "花椒": "2克", "干辣椒": "5克",
    "小米椒": "3个", "八角": "1个", "桂皮": "1小块", "香叶": "2片", "豆瓣酱": "15克",
    "甜面酱": "15克", "黄豆酱": "15克", "番茄酱": "20克", "辣椒油": "10毫升",
    "香油": "5毫升", "芝麻油": "5毫升", "芝麻": "3克", "白芝麻": "3克", "孜然": "3克",
    "五香粉": "2克", "十三香": "2克", "蒜蓉辣酱": "15克", "香辣酱": "15克",
    "辣椒粉": "3克", "蜂蜜": "10克", "小苏打": "1克", "泡椒": "5个", "剁椒": "15克",
    "豆豉": "10克", "腐乳": "1块",
}

TOOL_WORDS = [
    "刀", "碗", "锅", "铲", "勺", "盘", "碟", "筷", "案板", "砧板", "保鲜膜", "保鲜袋",
    "微波炉", "电饭煲", "烤箱", "空气炸锅", "锡纸", "油纸", "刷子", "温度计", "厨房纸",
    "蒸架", "蒸屉", "漏勺", "擀面杖", "模具", "量杯", "电子秤", "密封袋", "手套",
    "打蛋器", "滤网", "砂锅", "高压锅", "炒锅", "平底锅", "汤锅", "奶锅", "烤盘", "烤架",
    "牙签", "锅盖", "屉布", "夹子", "剪刀",
]

STD_AMOUNT = {
    "西红柿": "2个", "番茄": "2个", "鸡蛋": "3个", "土豆": "1个", "青椒": "2个", "尖椒": "2个",
    "黄瓜": "1根", "茄子": "1个", "白菜": "300克", "大白菜": "300克", "娃娃菜": "1棵",
    "包菜": "250克", "卷心菜": "250克", "胡萝卜": "1根", "白萝卜": "300克", "洋葱": "1个",
    "蒜": "3瓣", "大蒜": "3瓣", "蒜头": "3瓣", "蒜苗": "2根", "姜": "10克", "生姜": "10克",
    "葱": "1根", "小葱": "1根", "大葱": "半根", "香葱": "1根", "香菜": "1小把",
    "韭菜": "250克", "菠菜": "250克", "生菜": "200克", "芹菜": "200克", "豆角": "250克",
    "四季豆": "250克", "西兰花": "1棵", "花菜": "半棵", "莲藕": "1节", "山药": "1根",
    "冬瓜": "300克", "南瓜": "300克", "丝瓜": "1根", "苦瓜": "1根", "莴笋": "1根",
    "木耳": "20克", "香菇": "6朵", "金针菇": "1把", "豆腐": "1块", "嫩豆腐": "1盒",
    "内酯豆腐": "1盒", "内脂豆腐": "1盒", "豆干": "150克", "腐竹": "50克",
    "猪肉": "300克", "五花肉": "300克", "带皮五花肉": "300克", "猪里脊": "250克",
    "里脊肉": "250克", "肉末": "200克", "肉沫": "200克", "牛肉": "300克", "牛腩": "500克",
    "牛柳": "300克", "羊肉": "300克", "鸡肉": "400克", "鸡胸肉": "300克", "鸡腿": "2个",
    "鸡翅": "8个", "鸡翅中": "8个", "鸡中翅": "8个", "排骨": "400克", "猪蹄": "1只",
    "虾": "300克", "虾仁": "250克", "鲈鱼": "1条", "带鱼": "300克", "蛤蜊": "500克",
    "米饭": "2碗", "冷饭": "2碗", "大米": "200克", "面条": "200克", "挂面": "150克",
    "面粉": "300克", "粉丝": "1把", "粉条": "100克", "年糕": "200克", "馒头": "2个",
    "饺子皮": "300克", "牛奶": "250毫升", "可乐": "330毫升", "啤酒": "300毫升",
    "紫菜": "10克", "火腿": "100克", "火腿肠": "2根", "玉米粒": "100克", "青豆": "50克",
    "红椒": "1个", "葱花": "1小把", "蒜末": "3瓣", "姜片": "3片", "咸鸭蛋": "1个",
    "水": "适量", "开水": "适量", "清水": "适量", "温水": "适量", "高汤": "适量",
}

CN_NUM = {"半": .5, "一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
UNIT = r"(?:g|G|克|kg|KG|千克|ml|mL|ML|毫升|L|升|个|根|瓣|片|勺|汤匙|茶匙|颗|只|条|把|斤|袋|盒|块|串|朵|节|棵|碗|杯|张|滴|枚|小把|小块|小勺)"
CN = r"[半一两二三四五六七八九十]"
AMT_POST = re.compile(r"(\d+(?:\.\d+)?)\s*(" + UNIT + r")\s*$")
AMT_RANGE = re.compile(r"(\d+(?:\.\d+)?)\s*[-~～至]\s*(\d+(?:\.\d+)?)\s*(" + UNIT + r")\s*$")
AMT_PRE = re.compile(r"^(\d+(?:\.\d+)?)\s*(" + UNIT + r")\s*(.+)$")
CN_PRE = re.compile(r"^(" + CN + r")\s*(" + UNIT + r")\s*(.+)$")
CN_POST = re.compile(r"(" + CN + r")\s*(" + UNIT + r")\s*$")

BAD_PAT = re.compile(r"[=＝]|/人|每人|份数|用量为|\*|～|~|，|,|、|/|\.\.\.")
MODIFIER = ("带皮", "去皮", "新鲜", "冷冻", "熟的", "煮熟的", "生的", "挽成结", "切好的")

def clean_text(s):
    s = (s or "").strip()
    s = re.sub(r"^[\*\-•\s]+", "", s)
    s = re.sub(r"【[^】]*】|\[[^\]]*\]", "", s)          # 去图注
    s = re.sub(r"（[^）]*）|\([^)]*\)", "", s)
    s = re.sub(r"[`\"“”]", "", s)
    s = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]", "", s)
    return s.replace("的做法", "").strip()

def is_tool(n):
    return any(w in n for w in TOOL_WORDS) and len(n) <= 12

def norm_key(n):
    k = re.sub(r"\s|的|适量", "", n)
    for m in MODIFIER:
        k = k.replace(m, "")
    return k

def parse_one(text):
    s = clean_text(text)
    if not s or len(s) > 14:
        return None, None
    m = AMT_RANGE.search(s)
    if m:
        nm = s[:m.start()].strip(" :：,、")
        if nm:
            avg = (float(m.group(1)) + float(m.group(2))) / 2
            return nm, f"{avg:g}{m.group(3)}"
    m = AMT_PRE.match(s)
    if m:
        return m.group(3).strip(), m.group(1) + m.group(2)
    m = CN_PRE.match(s)
    if m:
        return m.group(3).strip(), f"{CN_NUM[m.group(1)]:g}{m.group(2)}"
    m = AMT_POST.search(s)
    if m:
        nm = s[:m.start()].strip(" :：,、")
        if nm:
            return nm, m.group(1) + m.group(2)
    m = CN_POST.search(s)
    if m:
        nm = s[:m.start()].strip(" :：,、")
        if nm:
            return nm, f"{CN_NUM[m.group(1)]:g}{m.group(2)}"
    return s, None

def is_seasoning(n):
    return any(k in n for k in SEASONING_KEYS)

def guess_taste(name, ings):
    blob = name + "".join(i["name"] for i in ings)
    if any(k in blob for k in ("辣椒", "花椒", "豆瓣", "辣", "剁椒", "泡椒")):
        return "辣"
    if any(k in blob for k in ("醋", "糖", "番茄", "西红柿", "酸甜")):
        return "酸甜"
    if any(k in blob for k in ("蒸", "白灼", "清炒", "汤", "粥", "羹")):
        return "清淡"
    return "咸鲜"

def guess_time(desc, diff):
    m = re.search(r"(\d+)\s*(?:小时|h)", desc or "")
    if m: return int(m.group(1)) * 60
    m = re.search(r"(\d+)\s*分钟", desc or "")
    if m: return int(m.group(1))
    return {1: 15, 2: 25, 3: 40}.get(diff, 30)

def map_category(cat, diff):
    if cat == "主食":  return "主食"
    if cat == "汤羹":  return "汤品"
    return "快手菜" if diff == 1 else "家常菜"

def merge_into(bucket, nm, amt):
    """名称包含关系合并：五花肉 ⊂ 带皮五花肉"""
    k = norm_key(nm)
    if not k:
        return
    for ek in list(bucket.keys()):
        if ek == k or ek in k or k in ek:
            onm, oamt = bucket[ek]
            # 保留更短更干净的名称 + 有量的用量
            best_name = onm if len(onm) <= len(nm) else nm
            best_amt = oamt if oamt is not None else amt
            bucket[ek] = (best_name, best_amt)
            return
    bucket[k] = (nm, amt)

def convert(rec):
    diff = rec["difficulty"]
    cat = map_category(rec["category"], diff)
    bucket = {}
    for i in rec.get("ingredients", []):
        raw = i.get("text_quantity") or i.get("name") or ""
        nm, amt = parse_one(raw)
        if not nm or BAD_PAT.search(nm) or is_tool(nm):
            continue
        if amt is None and i.get("quantity") is not None and i.get("unit"):
            amt = f"{i['quantity']:g}{i['unit']}"
        merge_into(bucket, nm, amt)

    ings, seas = [], []
    for nm, amt in bucket.values():
        sea = is_seasoning(nm)
        if amt is None:
            amt = (SEASONING_DEFAULT.get(nm) if sea else None) or STD_AMOUNT.get(nm) \
                  or next((v for k, v in STD_AMOUNT.items() if k in nm), None) or "适量"
        (seas if sea else ings).append({"name": nm, "amount": amt})
    if not ings:
        return None

    steps = []
    for s in rec.get("steps", []):
        t = re.sub(r"\s+", " ", clean_text(s.get("description") or "")).strip()
        if len(t) < 3:
            continue
        steps.append({"text": t})
    if not steps:
        return None
    total = guess_time(rec.get("description", ""), diff)
    per = max(1, min(6, round(total / max(len(steps), 1))))
    for idx, st in enumerate(steps):
        st["time"] = 2 if idx == 0 else per

    name = clean_text(rec["name"])
    return {
        "name": name, "category": cat, "meal_type": "all",
        "taste": guess_taste(name, ings),
        "ingredients": json.dumps(ings, ensure_ascii=False),
        "seasonings": json.dumps(seas, ensure_ascii=False),
        "steps": json.dumps(steps, ensure_ascii=False),
        "cook_time": total,
        "difficulty": "easy" if diff <= 2 else "medium",
        "tags": json.dumps([cat, rec["category"], {1: "简单", 2: "容易", 3: "中等"}[diff]], ensure_ascii=False),
        "image_url": "", "remark": "",
        "_d": diff, "_c": rec["category"],
    }

def load():
    data = json.load(open(SRC, encoding="utf-8"))
    pool = [r for r in data if isinstance(r.get("difficulty"), int) and 1 <= r["difficulty"] <= 3
            and r.get("category") not in EXCLUDE_CATS]
    out, seen = [], set()
    for r in pool:
        c = convert(r)
        if c and c["name"] not in seen:
            seen.add(c["name"]); out.append(c)
    return out

if __name__ == "__main__":
    conv = load()
    from collections import Counter
    print(f"转换成功 {len(conv)} 道")
    print("分类:", dict(Counter(c["category"] for c in conv)))
    print("难度:", dict(Counter(c["difficulty"] for c in conv)))
    tot = sum(len(json.loads(c["ingredients"])) + len(json.loads(c["seasonings"])) for c in conv)
    fill = sum(1 for c in conv for i in json.loads(c["ingredients"]) + json.loads(c["seasonings"]) if i["amount"] == "适量")
    print(f"用量为【适量】: {fill}/{tot} = {fill*100//max(tot,1)}%")

    famous = ["西红柿炒鸡蛋", "酸辣土豆丝", "可乐鸡翅", "红烧肉", "麻婆豆腐", "蛋炒饭",
              "紫菜蛋花汤", "蒸蛋", "手撕包菜", "鱼香肉丝"]
    picked, used = [], set()
    for kw in famous:
        for c in conv:
            if kw in c["name"] and c["name"] not in used:
                picked.append(c); used.add(c["name"]); break
    print("\n" + "=" * 62 + "\n样本预览\n" + "=" * 62)
    for c in picked:
        print(f"\n【{c['name']}】{c['_c']}{c['_d']}星 -> {c['category']}/{c['difficulty']}/{c['cook_time']}分/{c['taste']}")
        print("  食材:", "、".join(f"{i['name']} {i['amount']}" for i in json.loads(c["ingredients"])))
        print("  调料:", "、".join(f"{i['name']} {i['amount']}" for i in json.loads(c["seasonings"])) or "（无）")
        print("  步骤:", " / ".join(s["text"][:24] for s in json.loads(c["steps"])[:3]), f"...共{len(json.loads(c['steps']))}步")
