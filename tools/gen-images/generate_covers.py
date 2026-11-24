# -*- coding: utf-8 -*-
"""为无图菜品批量生成菜名封面（SVG，零依赖）

用法:
    python generate_covers.py            # 生成并写库
    python generate_covers.py --dry      # 只看会生成多少张
"""
import os
import re
import sqlite3
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DB = os.environ.get("NINIMENU_DB", str(ROOT / "dist-win" / "data" / "ninimenu.db"))
OUT_DIRS = [ROOT / "dist-win" / "uploads" / "generated",
            ROOT / "backend" / "uploads" / "generated"]

# 分类配色: (起始色, 结束色, 文字色, 副标题色)
PALETTE = {
    "家常菜": ("#FFE8CC", "#FFB069", "#5A3A20", "#8A6242"),
    "快手菜": ("#D8F0D5", "#6FBF73", "#1F4B23", "#3E6B42"),
    "主食":   ("#FFF2DC", "#F3C169", "#5A4220", "#8A6B3A"),
    "汤品":   ("#D9EEFB", "#5FB4E8", "#12405F", "#356A8C"),
}
DEFAULT_PALETTE = ("#EDEDED", "#BDBDBD", "#333333", "#666666")
DIFF_LABEL = {"easy": "简单", "medium": "中等", "hard": "较难"}


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def font_size(name: str) -> int:
    n = len(name)
    if n <= 3:
        return 76
    if n <= 4:
        return 68
    if n <= 5:
        return 58
    if n <= 7:
        return 48
    return 40


def make_svg(name: str, category: str, difficulty: str, cook_time: int) -> str:
    c1, c2, tc, sc = PALETTE.get(category, DEFAULT_PALETTE)
    fs = font_size(name)
    sub = " · ".join(x for x in [category, DIFF_LABEL.get(difficulty, ""),
                                 f"{cook_time}分钟" if cook_time else ""] if x)
    # 长菜名按每行 7 字折行
    lines = [name[i:i + 7] for i in range(0, len(name), 7)] or [name]
    start_y = 240 - (len(lines) - 1) * (fs * 0.6)
    texts = "".join(
        f'<text x="320" y="{start_y + i * fs * 1.18:.0f}" text-anchor="middle" '
        f'font-family="Microsoft YaHei, PingFang SC, sans-serif" font-size="{fs}" '
        f'font-weight="700" fill="{tc}">{esc(line)}</text>'
        for i, line in enumerate(lines)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
  </defs>
  <rect width="640" height="480" fill="url(#bg)"/>
  <circle cx="548" cy="62" r="132" fill="#ffffff" opacity="0.18"/>
  <circle cx="72" cy="418" r="96" fill="#ffffff" opacity="0.13"/>
  <circle cx="600" cy="392" r="30" fill="#ffffff" opacity="0.16"/>
  {texts}
  <text x="320" y="{start_y + (len(lines) - 1) * fs * 1.18 + 62:.0f}" text-anchor="middle"
        font-family="Microsoft YaHei, PingFang SC, sans-serif" font-size="24"
        fill="{sc}" opacity="0.85">{esc(sub)}</text>
</svg>
'''


def main(dry=False):
    con = sqlite3.connect(DB, timeout=20)
    con.execute("PRAGMA busy_timeout=15000")
    rows = con.execute(
        "SELECT id,name,category,difficulty,cook_time FROM dishes "
        "WHERE deleted_at IS NULL AND enabled=1 "
        "AND (images IS NULL OR images='' OR images='[]')"
    ).fetchall()
    print(f"无图菜品 {len(rows)} 道")
    if dry:
        for r in rows[:8]:
            print("  -", r[1], r[2])
        return

    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)

    for did, name, cat, diff, ct in rows:
        svg = make_svg(name, cat, diff or "easy", ct or 0)
        fn = f"gen_{did}.svg"
        for d in OUT_DIRS:
            (d / fn).write_text(svg, encoding="utf-8")
        url = f"/uploads/generated/{fn}"
        con.execute("UPDATE dishes SET image_url=?, images=? WHERE id=?",
                    (url, f'["{url}"]', did))
    con.commit()
    print(f"✅ 已生成 {len(rows)} 张封面，写入 {len(OUT_DIRS)} 个目录，并更新数据库")
    left = con.execute(
        "SELECT COUNT(*) FROM dishes WHERE deleted_at IS NULL AND enabled=1 "
        "AND (images IS NULL OR images='' OR images='[]')"
    ).fetchone()[0]
    print("剩余无图:", left)
    con.close()


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
