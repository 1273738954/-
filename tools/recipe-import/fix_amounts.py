# -*- coding: utf-8 -*-
"""修正 HowToCook 导入菜的用量异常"""
import sqlite3, json, re, os, pathlib

DB = os.environ.get(
    "NINIMENU_DB",
    str(pathlib.Path(__file__).resolve().parents[2] / "dist-win" / "data" / "ninimenu.db"),
)

# 主料缺量补全；None 表示删除该条目（占位词）
FIX_MAIN = {
    "油麦菜": "250克", "方便面": "1包", "泡面": "1包", "三文鱼": "200克", "面": "150克",
    "米粉": "150克", "荞麦面": "150克", "麻油": "10毫升", "饺子": "10个",
    "剑骨鱼或鲤鱼": "1条", "鳊鱼": "1条", "白蘑菇": "200克", "小米": "100克",
    "米": "150克", "叶菜类蔬菜": "300克", "青菜": "300克", "茶树菇": "100克",
    "毛豆": "300克", "皮蛋": "2个", "卤料包": "1包", "肋排": "500克", "鸡": "半只",
    "生鸡肝": "200克", "小米辣": "5个", "鸡全翅": "6个", "瘦肉": "250克",
    "茭白": "200克", "黔式腊肠": "2根", "原料": None, "菜类": "200克",
    "蔬菜": "300克", "肉类": "200克", "配料": "50克",
}

# 调料上限（超过则夹到该值）
CLAMP = {"盐": 5, "食盐": 5, "味精": 3, "鸡精": 3, "食用油": 30, "植物油": 30,
         "油": 30, "生抽": 20, "酱油": 20, "老抽": 15, "糖": 10, "白糖": 10, "醋": 20,
         "陈醋": 20, "香醋": 20, "料酒": 20, "蚝油": 15, "淀粉": 10, "生粉": 10,
         "香油": 10, "花椒": 5, "干辣椒": 10, "豆瓣酱": 20, "黄油": 20}

# 菜名/食材名清洁
NAME_FIX = {
    "闽星茶树菇": "茶树菇", "纯瘦肉": "瘦肉", "猪五花肉：约": "五花肉",
    "带皮五花肉": "五花肉", "五花肉条": "五花肉", "生菜": "生菜",
}

WHOLE_UNITS = ("根", "个", "颗", "瓣", "只", "条", "片", "棵", "盒", "袋", "把", "枚")


def num(a):
    m = re.match(r"^(\d+(?:\.\d+)?)", a or "")
    return float(m.group(1)) if m else None


def unit(a):
    m = re.match(r"^\d+(?:\.\d+)?\s*(\D+)$", a or "")
    return m.group(1).strip() if m else ""


def fix_amount(a):
    """小数取整 / 0.5X -> 半X"""
    v = num(a)
    if v is None:
        return a
    u = unit(a)
    if abs(v - round(v)) < 1e-9:
        return a
    if v < 1 and u in WHOLE_UNITS:
        return f"半{u}"
    r = round(v)
    if r == 0:
        r = 1
    return f"{r}{u}"


def fix_name(n):
    n = NAME_FIX.get(n, n)
    n = re.sub(r"[：:].*$", "", n)
    return n.strip()


def main(dry=False):
    con = sqlite3.connect(DB, timeout=20)
    con.execute("PRAGMA busy_timeout=15000")
    rows = con.execute(
        "SELECT id,name,ingredients,seasonings FROM dishes "
        "WHERE deleted_at IS NULL AND tags LIKE '%HowToCook%'"
    ).fetchall()
    log = []
    for did, dname, ing_s, sea_s in rows:
        ings = json.loads(ing_s or "[]")
        seas = json.loads(sea_s or "[]")
        new_ings, new_seas = [], []
        for i in ings:
            nm = fix_name(i["name"])
            amt = i["amount"]
            if nm in FIX_MAIN:
                v = FIX_MAIN[nm]
                if v is None:
                    log.append(f"  删除占位食材: {dname} / {nm}")
                    continue
                if amt == "适量":
                    log.append(f"  主料补量: {dname} / {nm} {amt} -> {v}")
                    amt = v
            amt2 = fix_amount(amt)
            v = num(amt2)
            if v is not None and nm in CLAMP and v > CLAMP[nm]:
                old = amt2
                amt2 = f"{CLAMP[nm]}{unit(amt2) or '克'}"
                log.append(f"  调料夹值: {dname} / {nm} {old} -> {amt2}")
            elif amt2 != amt:
                log.append(f"  小数取整: {dname} / {nm} {amt} -> {amt2}")
            if nm != i["name"]:
                log.append(f"  名称清洗: {dname} / {i['name']} -> {nm}")
            new_ings.append({"name": nm, "amount": amt2})
        for i in seas:
            nm = fix_name(i["name"])
            amt = i["amount"]
            v = num(amt)
            if v is not None and nm in CLAMP and v > CLAMP[nm]:
                old = amt
                amt = f"{CLAMP[nm]}{unit(amt) or '克'}"
                log.append(f"  调料夹值: {dname} / {nm} {old} -> {amt}")
            amt2 = fix_amount(amt)
            if amt2 != amt:
                log.append(f"  小数取整: {dname} / {nm} {amt} -> {amt2}")
            new_seas.append({"name": nm, "amount": amt2})
        if not dry:
            con.execute("UPDATE dishes SET ingredients=?, seasonings=? WHERE id=?",
                        (json.dumps(new_ings, ensure_ascii=False),
                         json.dumps(new_seas, ensure_ascii=False), did))
    if not dry:
        con.commit()
    print("\n".join(log[:40]))
    print(f"\n共 {len(log)} 处修正{'（dry-run 未写入）' if dry else '，已写入'}")
    con.close()


if __name__ == "__main__":
    import sys
    main(dry="--dry" in sys.argv)
