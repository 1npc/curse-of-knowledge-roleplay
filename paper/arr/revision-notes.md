# 当前四边界论文的修订与证据对应

当前标题为 **Role-Playing Language Models Use Information Their Characters Cannot Access**。全文围绕“生成器是否应接收角色无法访问的信息”组织，引言列出三项贡献，随后为相关工作、访问评估设计、角色视角编译、实验设置、五项结果、讨论与结论。旧 760,508 条研究单独保留，未与本轮 220,088 条生成记录合并。

| 修改要求 | 当前结果与处理 | 状态 |
|---|---|---|
| 以信息访问为核心，弱化外语独占叙事 | 听觉、理解、视觉和接收四边界统一组织；十一模型热图入正文，数值表保留附录 | 已落实 |
| 按 ACL 风格重组文章 | 去掉 RQ 问句式标题；补充四通道访问/事件壳说明表和 11/6/4 模型及匹配场景范围表；方法、测量、统计和结果分开 | 已落实 |
| 页数、匿名与图表排版 | 官方 review 模板四文件与当前上游逐字节一致；正文含图表满8页、全稿14页；Limitations从第9页开始；Figure 2在第7页并伴随结果讨论；附录末页表格靠上顺排 | 已编译及逐页检查 |
| 正文必须写满8页 | 四模型确证明细、自过滤实例、允许信息控制和词项块敏感性结论在正文；保留指标解释、编译示例、统计单位及方法调用成本。完整词项块CI及程序在附录E。第8页左右两栏末行分别到775.19pt及773.04pt，字号和官方页边距不变 | 已落实 |
| 根据最新意见收束写作 | 摘要从162词压到138词，保留判断/生成差距和编译器两项主要数值；引言和贡献减少重复；结果强调结论，能力资格/分母/重采样完整细节移至附录E。第3页测量列避免段距拉伸，附录允许3个宽表与正文共同排页，全稿仍14页 | 已落实，未新增实验 |
| 核查 85% 能力门槛 | 原计划明定无条件主分析、能力条件化次分析；三个日语单元不合格。次分析 D=50.98 [48.36,53.67]，1152 端点、9 单元；未新增逐条翻译筛选 | 已计算，主分析未替换 |
| 状态正确分解 | 四边界分别报告条件估计和分母；理解状态探针全部正确，能力合格后仍为50.98。额外 pooled 条件估计65.93 [64.82,67.14]保留为次分析 | 已落实 |
| 编译器对删除的事件保留优势 | +67.75 [65.36,70.05] 是冻结联合方法检验的原组件；100%限定为设计的事件壳及直接发生问答 | 已突出 |
| 双人响应审查 | 原832条、两套独立空白表保留；已有AI代理响应审查与真人分开 | 真实数据待填 |
| 中/日/西刺激核查 | 两位新AI代理各审24条，48次判断；3条意义标签分歧、11条至少一方不确定。两套真人表及6位评审槽位保持空白 | AI临时审查完成，真人待填 |
| foil 富集及单项准确率 | 192条诊断包含41条机器foil阳性普查及疑难/随机对照，类别可重叠。正文附录披露AI foil低召回；富集包不得作为总体F1 | 材料与分析接口完成，真实标签待填 |
| 检查选项顺序 | A/B配对内顺序与问题均一致，但32场景为18/14的确定性顺序。按顺序分解并补等权敏感性；全上下文49.11–63.00pp | 已核查并修正措辞 |
| 词形可猜性 | 既有96题覆盖48个活跃v2词项—语种单元，空白参与者表已打包 | 真实参与者数据待填 |
| 新增自然互动下游任务 | 未生成新实验；当前事件保留只支持有限直接问答，选择只支持文本中的提议 | 作为未来增强项，不伪造结果 |

新增统计位于 `analysis/h200-v2-20261002/revision-audit/results.json`，脚本为 `tools/audit_access_v2_revision.py`。它核对原始分数 SHA、复现原理解均值和状态正确估计/CI，并保持冻结生成、评分器与检验族不变。能力资格来自观察到的翻译诊断，条件 CI 不含资格门槛本身的估计不确定性。

`tools/prepare_access_v2_human_extension.py` 保护原审计文件，准备新表；`tools/evaluate_access_v2_human_extension.py` 分别核对foil、choice和occurrence标签。空白表只产生待填状态，不能产生虚构的人类金标。语义总体认证继续使用既有代表性样本及逆抽样权重。

主张检查已覆盖：多维边界差异、独立调用而非内部知识断言、提示效果依赖边界和模型组、自过滤允许事实损失、事件壳保留的任务范围、延迟时原事件仍在上下文、选择不是执行动作，以及AI评审不具备真人母语资格。没有新增接受概率或会议等级评估。

当前源文件使用官方 ACL review 样式，2026-10-03 核对 ARR 长文正文最多8页及匿名评审要求。摘要少于200词，正文11pt、双栏、A4，官方页边距不变。匿名版删除致谢标题，AI 使用披露保留在 Ethical Considerations；提交清单及最终作者披露仍待作者完成。

原四模型确证及六模型比较保持原值。当前源稿通过内置编译器，独立图源保留已验证的成功编译及不变SHA；PDF用既有本地pdfLaTeX导出并检查14页，正文严格8页、字体全部嵌入、无页外文字、无溢出框或未解析引用。正文不再出现单独占页的行为图。内置XeTeX预览的换行和分页不同，提交排版以pdfLaTeX导出为准；源文件保留预览提示、pdfLaTeX八页守卫及跨引擎图表宽度守卫。真实人工数据仍为0；AI代理的低foil召回已在实验设置正文披露，主分析和能力条件化次分析保持分开。

## Result-figure redesign

Both main result figures now use the full ACL text width. The eleven-model profile juxtaposes inaccessible net use, accessible target use, and equal-channel means (88 matrix values and 22 mean markers). Accessible target use is independently recovered from the SHA-bound frozen scores, with all 384 endpoints retained per cell. The behavior composite shows four delay small multiples, two-/four-turn paired changes with their saved intervals, and search-choice effects under full context and compilation. Colors, point shapes, grids, numeric labels, and typography share one geometry between editable TikZ and SVG. Deep-fill labels and green annotations were checked for readable contrast. The appendix confirmation plot uses the same style, exact numbers, and paired controls.

The detailed per-model confirmation table moved to Appendix A. The main conclusion and final appendix sensitivity paragraph were tightened while preserving cohort scope, every numeric interval, and frozen-test status. No generation, scoring, hypothesis, or scientific result changed. The main text remains exactly eight full pages under the unchanged official ACL typography.


## Final-tense human-study reporting template

Reorganized the human-study report into separate discovery and confirmation semantic audits, occurrence review, enriched foil/choice diagnostics, language double review and non-speaker word guessing. Two new tables hold confusion counts, weighted target/foil metrics, pre-adjudication agreement and language judgments. Ninety-six visible author-fill fields replace missing observations, qualifications, ethics information and interpretation. A main-text footnote and appendix convention identify these as a completion template; no human observations are manufactured or AI judgments relabeled. AI diagnostic metrics remain in a separate appendix subsection. Operational runtime details moved to Appendix A. The main retention interpretation now explicitly states that all partial-event scenes contain an occurrence and that always-positive answers can score 100%; broader interaction competence is unmeasured.

The source compiled successfully in the built-in editor and the existing pdfLaTeX export. All sixteen PDF pages were rendered and inspected. Main text remains eight full pages, Limitations starts at nine, both rich result composites remain on pages seven/eight, and official typography/margins are unchanged. Fonts are embedded, anonymous metadata is retained, references resolve, and no overfull boxes or page-boundary violations occur. Frozen inputs, scores, tests and figure data remain unchanged; actual human labels remain zero.

## Reporting revision from the latest review

Corrected the inventory to 24 sentences forming 12 reciprocal A/B pairs, verified against source/form mappings (8 sentences/4 pairs per language). Added both-state probe controls from all 6,144 saved confirmation replies, with separate error directions and the 50% always-No reference. Added exact messages and A/B/access substitutions, eight role replies and four independent probe answers for selected Qwen C001; all 12 score records independently reproduced from raw replies and frozen plans. Documented denial flags and multi-value scorer behavior. Human reports separate full/removal/view, both states, and the correct-probe full-inaccessible subgroup, with absolute automatic-minus-human bias and union disclosure. Actual human observations remain zero; all 231 fields are unsupplied. Bounded method claims by baseline and input-schema differences; retention is an observable-shell check. No new generation, selective-occurrence task, matched-schema comparison, held-out vocabulary study, or confirmatory test was run. Figures are unchanged. Verified 8 full main pages/18 total, embedded fonts, resolved references, no overflow, visible fields, and rendered-page review.
