# 写作计划（9/29）

按 ARR 长文准备：正文 8 页，另加 Limitations、Ethics 和参考文献，附录不限。主线见 `storyline.md`。正文用英文，本文件的说明用中文，英文草稿句只是起点。

## 1. 读者读完要记住的三件事

1. 角色扮演模型会说出角色**感知不到**的内容：角色听不懂的外语，或根本听不见的话。
2. 边界写进**结构化状态**几乎没用，写成一句话也只对部分模型有用；模型读得懂状态，只是生成时不用。
3. 先让模型**列出角色能感知和理解的内容**再作答，多数模型能修好；修不好的，问题出在这张清单。

全文每一节都要回到这三点之一。与这三点无关的结果（翻译器离线、否认却使用、规模曲线）一律放附录。

## 2. 题目与摘要

**题目**（推荐）：Role-Playing Language Models Use What Their Characters Cannot Perceive

**摘要草稿**（约 180 词，数字待主实验）：

> Role-playing language models increasingly voice characters in games and agent simulations, where
> the system tracks what each character can hear and which languages it understands. We ask whether
> models respect these perceptual boundaries. We present speech that the character hears but cannot
> understand, or cannot hear at all, and measure whether the reply uses its content, with a
> counterfactual canary design that separates use from guessing within the same reply. Across [11]
> open models from [9] families, characters routinely act on speech they cannot perceive: [X–Y]% of
> replies use content in a language the character does not speak, and [X–Y]% use speech marked as
> inaudible. Contrary to the intuition that comprehension is the fragile case, a bare inaudibility
> flag is ignored at least as often. Boundaries given as structured state barely constrain
> generation, and a sentence of prose helps only some models, even though the models answer
> questions about the state correctly. A two-step perspective filter, which first lists what the
> character can perceive, removes most use in [k] of [K] models without suppressing content the
> character should understand; where it fails, the list itself already leaks.

## 3. 章节与页数

| 节 | 页数 | 内容 | 图表 |
|---|---|---|---|
| 1 Introduction | 1.25 | 见第 4 节 | 图 1 |
| 2 Related Work | 0.5 | 三段：角色知识边界；心智理论中"知道却不用"；视角过滤类方法 | 无 |
| 3 Measuring perceptual use | 1.5 | 任务、状态格式、各格设计、金丝雀对换、计分 | 表 1 |
| 4 Setup | 0.5 | 条目与语言、11 个模型、解码、能力门、统计方法 | 无 |
| 5 Results | 3.25 | 5.1 到 5.5，对应三件事 | 图 2、图 3、表 2 |
| 6 Discussion | 0.75 | 对状态驱动系统的建议；为什么状态不起作用（只作假设） | 无 |
| 7 Conclusion | 0.25 | | |
| Limitations | 不计页 | 见第 7 节 | |

## 4. 引言的段落结构

1. **开场例子**：一个不会日语的角色，被人用日语告知东西藏在哪里，下一句就去那里取（图 1）。讲人类读者一眼能看出的错误，不用术语。
2. **为什么重要**：游戏 NPC 和多智能体仿真把"谁听得到、谁懂哪种语言"写在状态里，指望模型照做；做不到，信息不对称、剧情悬念、社会仿真的有效性都会失效。
3. **难点**：内容就在输入里，模型自己完全理解，要它"装作没理解"。已有工作测的是参数知识或时间边界（CHARM、TimeChara），或第三人称问答（FANToM、SimpleToM），没有测开放生成里、由感知状态决定的边界。
4. **本文做法**：两种边界（听不懂、听不见）× 三种表达方式（结构化状态、逐句标记、一句文字），同一条回复内的金丝雀对换，规则计分。
5. **发现**：四条，每条一句，带主实验数字。第二条明写"与直觉相反，语言并不特殊"。
6. **贡献**：测量方法与数据；跨 9 个家族的发现；修复的检验与失败定位。

## 5. 结果节怎么写

| 小节 | 一句话结论（写成小节标题下第一句） | 主证据 |
|---|---|---|
| 5.1 Characters act on speech they cannot perceive | 所有模型都在两种边界上大量泄漏 | 图 2 的左两组；H1、H1i |
| 5.2 Comprehension is not the weak point | 两边都用逐句标记时，"听不见"漏得更多 | 图 2 的中间两组；H4 |
| 5.3 How the boundary is stated matters, but not enough | 语言清单不如直接标记；一句文字帮部分模型 | 图 2 的全部；H3、H2a、H2b |
| 5.4 Models know the state but do not apply it | 探针答对的条目上照样泄漏 | 表 2；H5a；一条"否认却使用"的例子放脚注 |
| 5.5 A perspective filter closes most of the gap | M1g 修好多数模型；修不好时清单本身就漏 | 图 3；H5b |

**图 1**：一个直接对话的例子，左边是给模型的状态（节选），右边是三种写法下的回复：只给状态时泄漏，写成一句话后守住，M1g 的两步。例子取自试点条目（不进确证分析），台词是自写的，不用游戏原文。

**图 2**（主图）：每个模型一行，点图。横轴是泄漏率，每行 5 个点：语言清单、逐句标记听不懂、逐句标记听不见、描述写明听不见、语言加一句文字；带骨架重抽的区间。模型按语言清单下的泄漏排序。一张图同时讲 5.1 到 5.3。

**图 3**：左边是 M1g 前后的泄漏（两种边界，每模型一对箭头）；右边是散点，横轴第一步清单的泄漏，纵轴第二步的泄漏，说明失败出在清单。

**表 1**：设计。行是各格（应理解、有翻译器、听不懂、逐句标记听不懂、应听见、听不见、逐句标记听不见），列是给模型的状态和描述写了什么、预期是否使用。

**表 2**：8 个确证检验的点估计、单侧下界、Holm 校正后的 p 值和结论。

## 6. 讨论节要说的

1. **给系统设计者的建议**：把感知边界写成叙述，不要只放在结构化字段里；生成前加一步视角清单；对清单本身做检查。
2. **为什么状态不起作用**（标明是假设）：模型把上下文当作读者可见的全部信息，像全知叙述者；小说里外语对白通常直接译给读者（翻译惯例），模型可能学到了"对白默认可懂"；结构化字段可能被当作元数据而不是剧情事实。本文不检验这些机制。
3. **对"语言特殊"直觉的交代**：原计划以此为主张，试点对齐后被否定，预注册前改了假设。正文用一句话如实写出，细节放附录。这也是论文的一个发现。

## 7. Limitations 要写的

- 三种语言、英文回复、主要是游戏角色（非 Cyberpunk 小臂只作佐证）；
- 只有 40B 以下的开放模型；托管模型若跑，只作参考；
- 贪心解码、关闭思考；
- 规则计分的漏检（人工审计给出校正后的估计）；
- 假设是看过试点后定的（试点条目不进确证分析，冻结版本在 OSF 登记）。

## 8. 附录清单

A 条目构造与闸门（同源词、猜测性测试）；B 全部提示模板；C 计分器与人工审计；D 能力门与各语种结果；E 探索性分析：否认却使用、翻译器离线、声明强度阶梯、规模曲线、直接对话与旁听；F 各模型完整表格；G FS 与 M1 的结果；H 偏离说明与试点描述。

## 9. 时间安排

| 日期 | 写作 | 实验 |
|---|---|---|
| 9/29 到 10/2 | 写第 2、3、4 节和附录 A、B（设计已定，不依赖结果）；画图脚本用试点数据先跑通 | 定 H5b 判据和模型集合；生成主集提示；人工核对 |
| 10/3 | | 冻结并在 OSF 登记 |
| 10/4 到 10/6 | 写引言和讨论的初稿 | 主实验与 M1g；人工审计 |
| 10/7 到 10/9 | 填结果，写第 5 节，定摘要数字 | 确证分析 |
| 10/10 到 10/11 | 通读、压页数、查引用 | |
| 10/12 | 用户提交 | |

## 10. 写作前需要你定的

1. H5b 的保留判据（见 `storyline.md` 第 6 节）。
2. 确证模型集合（拟 11 个）。
3. 题目。
4. 论文放在哪里写：本仓库的 `paper/`（ACL 模板）还是 Overleaf。
