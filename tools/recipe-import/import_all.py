# -*- coding: utf-8 -*-
"""全量导入：只保留中式日常菜 + 1-2星->快手菜"""
import json, sqlite3, sys, os, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import converter as C

DB = os.environ.get(
    "NINIMENU_DB",
    str(pathlib.Path(__file__).resolve().parents[2] / "dist-win" / "data" / "ninimenu.db"),
)


def map_category(cat, diff):
    if cat == "主食":
        return "主食"
    if cat == "汤羹":
        return "汤品"
    return "快手菜" if diff <= 2 else "家常菜"


C.map_category = map_category

# 非中式日常菜的排除关键词
EXCLUDE_KW = [
    # 西式 / 烘焙 / 早餐
    "意式", "印度", "韩式", "韩国", "苏格兰", "澳门", "美式", "奶酪", "培根", "通心粉",
    "意大利面", "吐司", "面包", "蛋糕", "三明治", "燕麦", "牛奶", "果酱", "北非蛋",
    "免治", "红芸豆", "鲣鱼", "太阳蛋", "完美水煮蛋", "温泉蛋", "溏心蛋", "茶叶蛋",
    "蒸花卷", "手抓饼", "蛋煎糍粑", "桂圆红枣粥", "水煮玉米",
    # 海鲜大菜 / 猎奇
    "海参", "蟹", "鳝", "鱔", "蛏", "螺蛳", "鳜鱼", "红虾", "罗氏虾", "黑鳕鱼",
    "生蚝", "阿根廷", "猪皮冻",
    # 地方小吃 / 甜品
    "热干面", "油泼面", "蕨根粉", "老友", "炒馍", "芝麻烧饼", "凉粉", "醪糟", "十八酿",
]


def build():
    conv = C.load()
    kept = [c for c in conv if not any(k in c["name"] for k in EXCLUDE_KW)]
    removed = [c["name"] for c in conv if any(k in c["name"] for k in EXCLUDE_KW)]
    return kept, removed


def main(commit=False):
    kept, removed = build()
    con = sqlite3.connect(DB, timeout=20)
    con.execute("PRAGMA busy_timeout=15000")
    exist = {r[0] for r in con.execute("SELECT name FROM dishes WHERE deleted_at IS NULL")}

    def norm(n):
        return n.replace("西红柿", "番茄").replace("鸡蛋", "蛋")

    exist_norm = {norm(n) for n in exist}
    todo = [c for c in kept if c["name"] not in exist and norm(c["name"]) not in exist_norm]
    dup = [c["name"] for c in kept if c["name"] in exist or norm(c["name"]) in exist_norm]

    from collections import Counter
    print(f"原始 176 道 -> 排除非日常 {len(removed)} 道 -> 保留 {len(kept)} 道")
    print(f"其中与现有库重名/近义跳过 {len(dup)} 道 -> 实际新增 {len(todo)} 道")
    print("\n新增分类分布:", dict(Counter(c["category"] for c in todo)))
    print("新增难度分布:", dict(Counter(c["difficulty"] for c in todo)))
    print(f"\n导入后预计启用总数: {len(exist) + len(todo)}")

    print("\n--- 排除清单 ---")
    print("、".join(removed))
    print("\n--- 待新增样例(前25) ---")
    print("、".join(c["name"] for c in todo[:25]))

    if not commit:
        print("\n[dry-run] 未写入数据库")
        return

    sql = """INSERT INTO dishes
      (name,image_url,images,video_url,category,meal_type,taste,ingredients,seasonings,
       steps,cook_time,difficulty,remark,favorite,enabled,tags,sort_order,created_at,updated_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"""
    n = 0
    for c in todo:
        tags = json.loads(c["tags"])
        if "HowToCook" not in tags:
            tags.append("HowToCook")
        con.execute(sql, (
            c["name"], c["image_url"], json.dumps([]), "", c["category"], c["meal_type"],
            c["taste"], c["ingredients"], c["seasonings"], c["steps"], c["cook_time"],
            c["difficulty"], c["remark"], 0, 1,
            json.dumps(tags, ensure_ascii=False), 100,
        ))
        n += 1
    con.commit()
    print(f"\n✅ 已导入 {n} 道")
    print("\n--- 全库分类统计（启用） ---")
    for r in con.execute(
        "SELECT category, COUNT(*) FROM dishes WHERE deleted_at IS NULL AND enabled=1 "
        "GROUP BY category ORDER BY COUNT(*) DESC"
    ):
        print(f"  {r[0]}: {r[1]}")
    total = con.execute("SELECT COUNT(*) FROM dishes WHERE deleted_at IS NULL AND enabled=1").fetchone()[0]
    print(f"  合计: {total}")
    con.close()


if __name__ == "__main__":
    main(commit="--commit" in sys.argv)
