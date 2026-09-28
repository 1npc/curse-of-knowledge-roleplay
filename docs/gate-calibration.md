# 同源筛校准（规则 4）

由 `tools/calibrate_gate.py` 生成，数据在 `data/cognate_calibration.json`。
拒绝条件：任一转写与英文词的归一化 Levenshtein 相似度 ≥ 0.5，或前 3 个字母相同，或 Double Metaphone 主码相同。

- 同源或借词 59 对，拒绝 49 对，**召回率 0.83**；es 35/36，ja 6/8，zh 8/15
- 规则 3（ja 片假名禁令、zh 音译词表、es 借词表）与规则 4 合起来拒绝 58/59 对
- 非同源 50 对，误拒 0 对，**误拒率 0.00**

各判据单独的命中数（同源对）： Levenshtein 44，前缀 26，Metaphone 36。

## 漏掉的同源对

| 语种 | 形式 | 英文 | 最大相似度 | 转写 | 规则 3 拦下 |
|---|---|---|---|---|---|
| es | oficina | office | 0.43 | oficina | 否 |
| zh | 巧克力 | chocolate | 0.33 | chiao, chiaokoli, qiao, qiaokeli | 是 |
| zh | 汉堡 | hamburger | 0.33 | bao, han, hanbao, hanpao, pao | 是 |
| zh | 雷达 | radar | 0.20 | lei, leida, leita | 是 |
| zh | 马达 | motor | 0.40 | mada, mata | 是 |
| zh | 逻辑 | logic | 0.40 | chi, lochi, luo, luoji | 是 |
| zh | 巴士 | bus | 0.40 | bashi, pashih, shi, shih | 是 |
| zh | 的士 | taxi | 0.33 | dishi, shi, shih, tishih | 是 |
| ja | テーブル | table | 0.33 | teburu, teeburu | 是 |
| ja | コーヒー | coffee | 0.17 | kohi, koohii | 是 |

## 误拒的非同源对

| 语种 | 形式 | 英文 | 最大相似度 | 触发判据 |
|---|---|---|---|---|

漏掉的同源对由规则 9 的词形可猜性检验兜底；它们也说明这道闸不能单独当熟悉度筛。
