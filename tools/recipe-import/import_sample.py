# -*- coding: utf-8 -*-
"""导入 HowToCook 菜品到 NiniMenu 数据库"""
import json, sqlite3, sys, time, os, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from converter import load

DB = os.environ.get(
    "NINIMENU_DB",
    str(pathlib.Path(__file__).resolve().parents[2] / "dist-win" / "data" / "ninimenu.db"),
)

# 10 道样本：全是日常中式家常菜，覆盖 4 分类 / 2 难度
SAMPLE = [
    "酸辣土豆丝", "手撕包菜", "小炒肉", "香干肉丝",
    "凉拌黄瓜", "凉拌油麦菜",
    "蛋炒饭", "西红柿鸡蛋挂面",
    "西红柿鸡蛋汤", "玉米排骨汤",
]

def main(dry=False, names=None, all_new=False):
    conv = load()
    if all_new:
        picks = conv
    else:
        want = names or SAMPLE
        by_name = {c["name"]: c for c in conv}
        picks = [by_name[n] for n in want if n in by_name]
        miss = [n for n in want if n not in by_name]
        if miss:
            print("!! 未找到:", miss)

    con = sqlite3.connect(DB, timeout=20)
    con.execute("PRAGMA busy_timeout=15000")
    exist = {r[0] for r in con.execute("SELECT name FROM dishes WHERE deleted_at IS NULL")}
    todo = [c for c in picks if c["name"] not in exist]
    print(f"待导入 {len(todo)} 道（跳过重名 {len(picks)-len(todo)} 道）")
    if dry:
        for c in todo:
            print("  +", c["name"], c["category"], c["difficulty"], c["cook_time"], "分")
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
    print(f"✅ 已导入 {n} 道")
    # 验证
    rows = con.execute(
        "SELECT id,name,category,difficulty,cook_time,length(ingredients),length(steps) "
        "FROM dishes WHERE deleted_at IS NULL AND tags LIKE '%HowToCook%' ORDER BY id"
    ).fetchall()
    print(f"\n库中 HowToCook 标记菜品 {len(rows)} 道:")
    for r in rows:
        print(f"  #{r[0]:<4} {r[1]:<12} {r[2]:<5} {r[3]:<7} {r[4]:>3}分  食材{r[5]:>4}B 步骤{r[6]:>4}B")
    con.close()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(dry="--dry" in args, all_new="--all" in args)
