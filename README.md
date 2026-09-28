# Over-Comprehension（十月 ARR 投稿）

研究问题：角色扮演语言模型扮演一个听不懂某种语言、又没有翻译通道的角色时，会不会照样理解并用上这段外语的内容（过度理解）。执行计划见 NPCBank 仓库 `docs/proposals/2026-10-arr-over-comprehension.zh-CN.md`（下称 proposal）。

## 规矩

- 本机只用系统 Python 标准库（`python3`），不建 venv、不 pip 安装；需要第三方包的步骤（vLLM 推理、MeCab 词典核验、GEE、作图）都在远端跑。
- NPCBank 仓库只读；不碰 v1.0.1 冻结 worktree。
- 任何付费调用都要用户逐笔授权并给美元上限；登录 Snellius 或 H200 要用户明确授权。
- 游戏台词受版权保护：仓库里只放计数、定位和意译，不抄原句。

## 目录

| 路径 | 内容 |
|---|---|
| `oc/translit.py` | 假名转罗马字（wapuro、Hepburn、训令式），拼音转威妥玛，西语去重音 |
| `oc/phon.py` | 归一化 Levenshtein 与 Double Metaphone |
| `oc/gate.py` | 刺激筛选闸（proposal 5.4 规则 1 到 8，A/B 逐字一致，配对混淆，非金丝雀位置不含值集词） |
| `oc/noise.py` | 噪声刺激 N1、N2 |
| `oc/build.py` | 按条件矩阵展开提示（每题 112 个主体提示加 13 个探针；试点另加 20 个 N2） |
| `oc/patterns.py`、`oc/langid.py`、`oc/score.py` | 规则评分器：语用标记、回复语言、金丝雀严格命中与命中方式 |
| `data/valueset.json` | 32 个候选取值（PLACE、OBJECT 各 16）的英文别名与日中西形式 |
| `data/mask.json` | 匹配前遮蔽的习语与专名 |
| `data/personas.json` | 9 张 Cyberpunk 人设卡（草稿，待用户审） |
| `data/cognate_calibration.json` | 同源筛校准对 |
| `items/pilot/skeletons.json` | 试点骨架 P01 到 P10 × zh/ja/es × A/B |
| `tests/` | 单元测试；`tests/fixtures/scorer_cases.jsonl` 是 120 条手写实判用例 |
| `tools/` | 资格检索、闸校准、提示生成、可猜性问卷、核对表 |
| `docs/` | 资格表、闸校准报告、决定与偏离、进度日志、核对表、问卷 |

## 常用命令

```bash
python3 -m unittest discover -s tests -v
python3 tools/calibrate_gate.py
python3 tools/build_prompts.py items/pilot/skeletons.json items/pilot/prompts.jsonl --pilot
python3 tools/make_scorer_cases.py
python3 tools/make_guessability.py
python3 tools/make_review_packet.py items/pilot/skeletons.json pilot
```

提示文件（`items/**/prompts.jsonl`）可由条目和代码复现，不进 git；清单（`*.manifest.json`）记录条数和 SHA-256。
