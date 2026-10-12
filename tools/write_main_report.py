"""Render a human-readable, source-linked report from saved numerical artifacts (stdlib)."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'analysis/results/main-20260929'
def load(n):return json.loads((OUT/n).read_text())
def pct(x):return f'{100*x:.2f}'
def interval(r):return f"{pct(r['point'])} [{pct(r['ci95'][0])}, {pct(r['ci95'][1])}]"
NAMES={'qwen38_27b':'Qwen3.8-27B','qwen35_9b':'Qwen3.5-9B','gemma4_31b':'Gemma-4-31B','gemma4_12b':'Gemma-4-12B','glm47_flash':'GLM-4.7-Flash','mistral_small3':'Mistral-Small-24B-Instruct-2501','gpt_oss_20b':'gpt-oss-20b','phi4':'Phi-4','seed_oss_36b':'Seed-OSS-36B','nemotron3_nano30b':'Nemotron-3-Nano-30B','falcon_h1_34b':'Falcon-H1-34B'}
def main():
 c=load('confirmatory.json');rows=load('model_metrics.json');sens=load('sensitivities.json');exp=load('exploratory.json');secondary=load('secondary_checks.json')
 descriptions={'H1':'语言清单：C−T− D0','H1i':'不可听标记：E_inaud_S','H2a':'语言清单 − 语言文字声明','H2b':'不可听标记 − 不可听叙述','H3':'语言清单 − 不理解标记','H4':'不可听标记 − 不理解标记','H5a':'状态探针答对后的语言越界'}
 lines=['# 主实验结果与交付记录 · 2026-09-29','',
 '机器统计、稳健性分析、图表和空白人工核对包已完成。**当前结果是规则计分结果，尚未经人工认证。** 所有日期按 2026-09-29；原 10 月分析安排已按用户要求提前。',
 '', '## 核心结论','',
 f"在固定的 11 个模型、33 个模型×语言单元中，语言不可理解条件的净越界为 **{interval(c['H1'])}%**，不可听标记条件为 **{interval(c['H1i'])}%**。这里的净越界是同一批回复的目标金丝雀命中率减去对换陪衬命中率，并不是未经校正的原始比例。两项现象在 **11/11 模型**中均超过 10 个百分点阈值并通过逐模型 Holm 校正。",
 '',f"两步视角过滤 M1g 的平均相对降幅为 **{interval(c['H5b']['reduction'])}%**；可用翻译器条件下的目标内容使用变化为 **{interval(c['H5b']['retention'])} 个百分点**。整体通过预设 50% 降幅与 −5pp 保留门，但有用内容仍有小幅下降，且不能泛化到每个模型、每个语种或每个角色。",'',
 'GLM-4.7-Flash 的两种越界点估计均恶化；Nemotron 的翻译器条件内容使用下降约 26pp；Qwen3.5-9B 下降约 13pp。中文子集、日语子集、去掉 Rogue，以及只有三个角色的两向自举，都未通过完整 H5b 门。',
 '', '## 数据与执行','',
 '- 15 个主运行模型：11 个确证集合模型与 4 个探索性规模模型；FS 4 个模型；替代系统提示 3 个模型 × 3 种。九个模型家族。',
 '- 主集 96 个骨架 × 3 语种；非 Cyberpunk 16 个骨架；正典／角色先验 52 个条目。独立试点 P01–P10 不进入主推断。',
 '- 原始记录 760,508 条；计划记录 760,512 条。4 条 Nemotron 第二步因第一步格式失败未生成，评分衍生文件显式补为 upstream_failure，并保留在分母。原始回复未改写。',
 '- 评分文件共 22 份、760,512 行；4,416 条截断和 5 条格式异常保留。所有生成文件曾按 SHA-256 与远端核对。评分文件完整性见 delivery-verification.json。',
 '- 主分析前本地锁定时间为 2026-09-29 19:48:21 UTC；生成早于锁定。**没有 OSF 预注册**。主结果首次查看不早于 20:00:30 UTC；次要补充实现与 GEE 修复明确标为事后。',
 '- 作业：27373721 评分；27373837 主统计；27373936 盲标／初始 GEE／图表；27374105 次要校准／事后 GEE 诊断。全部完成。',
 '', '## 统计口径','',
 '翻译探针须完整、非拒答且恢复两个金丝雀；每个模型×语种恢复率须 ≥85%。主集合 33/33 单元过门。外语条件只纳入该版本探针恢复成功的条目，英文不可听条件保留全部条目。单元等权；骨架同步重抽 2,000 次，保持跨语种、条件及 A/B 配对。截断、失败、拒答的目标和陪衬均记 0；多值对冲按原评分器逐类型处理。',
 '', '表中是点估计与双侧 95% 百分位区间；lower95 是未校正的单侧 95% 下界。主族八项采用近似 bootstrap 尾概率并做 Holm；这些 p 值不是精确随机化检验，最小分辨率为 1/2001。H5b 是交并检验，两分量取较大 p 后进入八项校正；未把两分量当成独立主假设。',
 '', '| 检验 | 统计量 | 估计与 95% CI（% 或 pp） | lower95 | Holm p | 锁定判据 |','|---|---|---:|---:|---:|---|']
 for k,desc in descriptions.items():
  r=c[k];lines.append(f"| {k} | {desc} | {interval(r)} | {pct(r['lower95'])} | {r['p_holm']:.4f} | 支持 |")
 for key,desc in [('reduction','平均相对降幅'),('retention','C−T+ 目标使用变化')]:
  r=c['H5b'][key];lines.append(f"| H5b / {key} | {desc} | {interval(r)} | {pct(r['lower95'])} | {c['H5b']['p_holm']:.4f}（联合） | 联合支持 |")
 lines+=['','H5a 使用 10 个模型、30 个有效模型×语言单元。GLM 在 288 个 C−T− D0 状态探针中均回答 Yes，而正确答案为 No；因此该模型在此条件分析中没有样本。不能据 H5a 声称所有模型都懂状态，或推断隐藏的认知机制。',
 '', '## 逐模型结果','', '下表均为百分数或百分点。M1g 对比只使用 content 与 plan 追问；前面的 H1/H1i 使用全部四类追问，分母不同。',
 '', '| 模型 | 语言清单 | 不可听标记 | 语言：基线 → M1g | 不可听：基线 → M1g | 有用内容变化 pp |','|---|---:|---:|---:|---:|---:|']
 for r in rows:
  val=lambda k:pct(r[k]['point'])
  lines.append(f"| {NAMES[r['model']]} | {val('language')} | {val('flag_inaudible')} | {val('base_language')} → {val('m1g_language')} | {val('base_inaudible')} → {val('m1g_inaudible')} | {val('retention')} |")
 lines+=['','完整区间在 [model_metrics.json](../analysis/results/main-20260929/model_metrics.json)。相对降幅按单元和边界计算后平均，不是两个汇总比例直接相除。',
 '', '![主边界结果](../analysis/results/main-20260929/figures/fig2_boundaries.png)',
 '', '![缓解结果](../analysis/results/main-20260929/figures/fig3_mitigation.png)',
 '', '## 稳健性与不能省略的例外','',
 '| 评分敏感性 | H1 % | H1i % | M1g 相对降幅 % | 保留变化 pp | 主族支持数 |','|---|---:|---:|---:|---:|---:|']
 for name,v in sens.items():lines.append(f"| {name} | {pct(v['H1']['point'])} | {pct(v['H1i']['point'])} | {pct(v['H5b']['reduction']['point'])} | {pct(v['H5b']['retention']['point'])} | {sum(x['supported'] for x in v.values())}/8 |")
 lines+=['', '- 3 个模型的全部 9 个替代提示组合均保持正向越界，最低点估计约 23.0%。此检查支持符号稳定，不等于提示措辞不影响幅度。',
 '- 留一角色时，前七项都通过；去掉 Rogue 后 H5b 未通过，保留变化 −4.89pp，Holm p=0.464。两向骨架×角色自举的 H5b 也未通过（p=0.130）；只有三个角色，此结果只作描述。',
 '- 按语种：H1 中文 65.56%、日语 64.43%、西语 70.10%；H5b 保留变化分别为 −5.12、−2.79、+2.04pp，完整联合门只在西语子集通过。子集未通过不等于已经证明无效。',
 '- 初始目标／陪衬二项 GEE 在 6/11 模型收敛，另外 5 个存在数值失败。全部诊断保留。事后另拟合仅目标金丝雀的二项 GEE，11/11 收敛，属于改变了建模目标的诊断，不替代原模型，更不替代骨架自举。',
 '- 嵌套结构限制：角色与骨架并非完整交叉；同一回复内 GEE 的聚类也不覆盖所有跨回复依赖。主推断始终采用同步骨架自举。',
 '', '## 探索性与校准结果','', '16 项探索对比作为一个 BH 家族（q=0.10）；下表仅摘录，完整结果包括正典、声明强度、模式与语种分解。',
 '', '| 对比 | 估计与 95% CI（pp） | BH q |','|---|---:|---:|']
 for k in ('deny_while_using','unattributed_share_D1_minus_U','offline_translator','FS_language_reduction','mode_DA_minus_OH','spoken_minus_real','non_cyberpunk_minus_main'):
  r=exp[k];lines.append(f"| {k} | {interval(r)} | {r['q_bh']:.4f} |")
 lines+=['', '- 非 Cyberpunk 臂净越界 50.09% [41.99, 58.28]；只纳入 31 个能力过门单元。不同情景集之间的差异不能解释为角色世界观的因果效应。',
 '- 原 proposal 的 deny-use 口径（content/plan、非拒答）约 5.00% [4.23, 5.77]，其下界未超过旧 5pp 阈值；不能用当前探索性“高于 0”结果倒推旧假设成立。',
 '- 未声明理解的使用占比（只排 A，不排转述）D1−U 为 0.32pp；排除转述后的版本为 7.65pp。结论依赖预先区分的语用类别，人工 marker 认证仍缺失。',
 '- 听懂对照 SU 为 75.70%，英文对照 84.52%；单元内 OC/SU 的平均为 88.99%。噪声命中约 0.31%，噪声校正越界 66.37%；错值校正约 66.59%。',
 '- 六组没有 B 版的格完成跨语种陪衬计算（73,152 个能力条件化回复），没有同型目标重叠；见 cross_language_foils.csv。它是次要描述，不扩张主族。',
 '- logit DI 的 11 个模型与合并行均有分量比例 <0.05；按 proposal 的稀疏率规则不报告不稳定的 logit 点估计，保留分量和绝对差之差。完整定义在 secondary_checks.json，并标记为主结果查看后完成的实现。',
 '- 规模曲线是无条件描述；小模型较少命中也可能源于无法恢复内容，不能等同于更好的视角控制。可选推理开关、托管模型、罗马字与采样温度臂没有运行，未新增 API 支出。',
 '', '## 人工包与交付文件','',
 '- [可分发核对包 ZIP](../deliverables/human-review-20260929.zip)：360 条双标、220 条漏检、3,211 条语言／回显队列，以及中文／日语／西语母语核对表与 96 题词形问卷。所有标签为空。',
 '- 主认证抽样中包含 200 条 C−T−、60 条应理解、40 条不可听／离线、30 条噪声、30 条缓解；C−T− 中含 50 条富集边界样本，阳性与 D1 否认样本最低配额均满足。确定性种子 2026092901。',
 '- 私有答案键、抽样概率在 audit-private；ZIP 不含答案键。标注顺序和 A/B 展示顺序随机；回复本身仍可能透露条件，无法保证彻底盲法。',
 '- 不能报告已通过 precision、recall、κ、AC1、母语自然度、词形可猜性或 Rogan–Gladen 校正。这些均依赖尚未发生的人工工作。生成后核查不追溯伪装成运行前筛选。',
 '- [完整数字目录](../analysis/results/main-20260929/)；四幅图均有 PNG、PDF、SVG；[英文稿](../paper/manuscript.md)；[主张核对与自审](../paper/claim-evidence-review.md)。',
 '', '## 复现与验收','',
 '本机只使用系统 Python 标准库；第三方分析在 Snellius 隔离环境运行。environment.txt 保存版本。analysis-lock.json 保留锁定时方法与材料哈希；analysis-execution.json 保存作业与补充分析记录。',
 '', '```bash', 'python3 -m unittest discover -s tests -v', 'python3 tools/verify_analysis_delivery.py', 'python3 tools/write_main_report.py', '```',
 '', '远端先运行 harness/score_main.sbatch，再运行 analyze_main.sbatch、postprocess_main.sbatch 与 secondary_main.sbatch。已有原始数据和评分文件均保存在本机 runs/ 与远端项目空间；无须为复现统计重新生成模型输出。',
 '', '数值验证包括三个合成测试（加速自举与原逐行实现逐次一致）、独立标准库逐行复算主点估计、22 份评分文件 SHA-256 核对，以及盲标配额／空标签／无元数据泄漏检查。结果均为对当前固定模型集合的结论。']
 (ROOT/'docs/main-results.md').write_text('\n'.join(lines)+'\n')
 table=['| Hypothesis | Estimate (95% CI) | Holm p |','|---|---:|---:|']
 for k in descriptions:table.append(f"| {k} | {interval(c[k])} | {c[k]['p_holm']:.4f} |")
 table.append(f"| H5b, relative reduction | {interval(c['H5b']['reduction'])} | {c['H5b']['p_holm']:.4f} (joint) |")
 table.append(f"| H5b, useful-content change | {interval(c['H5b']['retention'])} | Same joint test |")
 (ROOT/'paper/main-results-table.md').write_text('\n'.join(table)+'\n')
 print('Report and paper table written')
if __name__=='__main__':main()
