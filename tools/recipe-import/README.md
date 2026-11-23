# 菜谱数据导入工具

把 [HowToCook（程序员做饭指南）](https://github.com/Anduin2017/HowToCook) 的开源菜谱批量导入 NiniMenu 的 `dishes` 表。

## 数据来源与许可

- 原始项目：[Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)
- 本目录 `all_recipes.json` 取自社区 fork [SzeMeng76/HowToCook](https://github.com/SzeMeng76/HowToCook) 自动生成的结构化产物（366 条）
- 许可：**Unlicense**（公共领域，可自由使用、修改、分发，无需署名）

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `all_recipes.json` | 原始菜谱数据（366 条） |
| `converter.py` | 字段转换：HowToCook → NiniMenu `dishes` 表结构 |
| `import_all.py` | 全量导入（含范围过滤、非日常菜排除、与现有库去重） |
| `import_sample.py` | 只导 10 道样本，用于先看效果 |
| `fix_amounts.py` | 用量修正：调料夹值、小数取整、占位词清理、名称清洗 |

## 用法

```bash
cd tools/recipe-import

# 1. 预览（不写库，只打印将要导入的清单和统计）
python import_all.py

# 2. 确认后执行导入
python import_all.py --commit

# 3. 修正用量异常（建议导入后执行一次）
python fix_amounts.py

# 只看改动不写入
python fix_amounts.py --dry

# 只导 10 道样本
python import_sample.py
```

数据库默认路径为 `../../dist-win/data/ninimenu.db`，可用环境变量覆盖：

```bash
NINIMENU_DB=/path/to/ninimenu.db python import_all.py --commit
```

## 转换规则

- **范围**：难度 1–3 星（4–5 星为烤鸭、佛跳墙等，不适合日常）
- **分类映射**：1–2 星 → 快手菜，3 星 → 家常菜；原「主食」→ 主食，「汤羹」→ 汤品
- **排除**：饮品、甜品、调料、半成品加工四个分类整体排除；再按关键词排除西式、海鲜大菜、地方小吃（黑名单见 `import_all.py` 的 `EXCLUDE_KW`）
- **去重**：与库中已有菜名完全同名或近义（西红柿≈番茄、鸡蛋≈蛋）的跳过，保留原有数据
- **用量**：优先从原文提取（支持 `500g`、`2个`、`两瓣`、`10-15ml` 等写法）；缺失时按 2 人份常识补全（`converter.py` 的 `STD_AMOUNT`）
- **标记**：导入的菜 `tags` 含 `HowToCook`，便于后台筛选与回滚

## 幂等性

重复执行不会产生重复菜品（按菜名去重），可以安全地多次运行。

## 注意

- 导入的菜 `image_url` 为空，需在管理后台上传图片
- 执行前建议备份数据库：
  ```bash
  cp dist-win/data/ninimenu.db dist-win/data/ninimenu.db.bak
  ```
- 部分食材名带品牌或修饰词（如「漓泉啤酒」），可按需在后台手工调整
