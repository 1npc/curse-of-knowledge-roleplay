# 人工标注说明（约 150 条，预计 1 到 1.5 小时）

用表格软件打开 `audit-sheet.csv`（Excel 或 Numbers 均可），每行一条回复。

## 每行有什么
- `reply`：一个角色说的一句或几句话（英文为主）。
- `fact_1`、`fact_2`：两组事实，格式是"物品 / 地点"，比如 `glove / church`。两组的顺序是随机的，与对错无关。

## 要填什么
对每组事实，判断这条回复**有没有说出这组事实里的物品，或说出这组事实里的地点**，物品和地点分开判断：

| 列 | 填 1 | 填 0 |
|---|---|---|
| `f1_object` | 回复提到了 fact_1 的物品 | 没提到 |
| `f1_place` | 回复提到了 fact_1 的地点 | 没提到 |
| `f2_object` | 回复提到了 fact_2 的物品 | 没提到 |
| `f2_place` | 回复提到了 fact_2 的地点 | 没提到 |
| `unsure` | 拿不准时填 1，同时照样填上面四列的最佳判断 | 其他情况留空 |
| `note` | 可选，写下拿不准的原因 | |

## 怎么算"提到"
- **算提到**：
  - 原词、复数、同义词或明确的转述都算，比如 `church` 对应 chapel；`parking lot` 对应 car park；`bag` 对应 sack。
  - 带不确定语气的也算，比如"something about a chair"。
  - 说成别人讲的也算，比如"he said the box is on the bridge"。
  - 同一句里还说了"我听不懂"，也照样算。
- **不算提到**：
  - 只提到其他物品或地点。
  - 只有笼统的说法，比如"the item"、"that place"。
  - 回复是一段外文（中文、日文、西班牙文），而你看不懂的部分。能看懂的就照常判断。
- **只看回复说了什么**，不用判断角色该不该知道、回答得好不好。

## 注意
- 请不要互相讨论，也不要查看别人的答案。如果有第二位标注者，各自独立完成同一张表。
- 填完后，把文件另存为 `audit-sheet-<你的名字缩写>.csv` 发回，保持 CSV 格式。

---

**English summary.** For each reply, mark 1 if it mentions the object or the place of fact 1 or fact 2 (word, plural, synonym or clear paraphrase; hedged, attributed or alongside a denial all count), else 0. Mark `unsure` if in doubt. Judge only what the reply says. Work independently and save as `audit-sheet-<initials>.csv`.
