"""Assemble the current ARR draft from verified v2 evidence (stdlib only).
Formatting and descriptive plots do not change the frozen scientific analysis.
The pre-v2 manuscript is retained in archive/pre-access-v2-source.zip.
"""
from pathlib import Path
import csv,hashlib,json,re
from figure_design import discovery_profiles, behavior_panels, confirmation_boundaries
P=Path(__file__).resolve().parent;ROOT=P.parents[1];R=ROOT/'analysis/h200-v2-20261002'
MODELS={'qwen38_27b':'Qwen3.8-27B','qwen35_9b':'Qwen3.5-9B','gemma4_31b':'Gemma-4-31B','gemma4_12b':'Gemma-4-12B','glm47_flash':'GLM-4.7-Flash','mistral_small3':'Mistral-Small-24B','gpt_oss_20b':'gpt-oss-20b','phi4':'Phi-4','seed_oss_36b':'Seed-OSS-36B','nemotron3_nano30b':'Nemotron-3-Nano-30B','falcon_h1_34b':'Falcon-H1-34B'}
BOUNDS=('Hear','Understand','See','Receive');COLORS=['OCblue','OCorange','OCgreen','OCpurple']
def pc(x):return f'{100*x:.2f}'
def ci(r):return '['+', '.join(pc(v) for v in r['ci95'])+']'
def esc(x):return str(x).replace('_',r'\_').replace('&',r'\&').replace('%',r'\%')
def literal(x):
 replacements={'\\':r'\textbackslash{}','{':r'\{','}':r'\}','_':r'\_','%':r'\%','&':r'\&','#':r'\#','$':r'\$','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
 return ''.join(replacements.get(c,c) for c in str(x))
def tab(rows,cols,caption,label,wide=False):
 env='table*' if wide else 'table'
 return '\n'.join([r'\begin{'+env+'}[t]',r'\centering\small',r'\begin{lrbox}{\OCtable}\begin{tabular}{@{}'+cols+'@{}}',r'\toprule',*rows,r'\bottomrule',r'\end{tabular}\end{lrbox}',r'\ifdim\wd\OCtable>\linewidth\PackageError{access-paper}{Table '+label+r' exceeds its column}{Revise the table layout.}\fi',r'\usebox{\OCtable}',r'\caption{'+caption+'}',r'\label{'+label+'}',r'\end{'+env+'}'])
def figure(plot,caption,label,wide=False):
 env='figure*' if wide else 'figure'
 return '\n'.join([r'\begin{'+env+'}[t]',r'\centering\begin{lrbox}{\OCfigure}',plot,r'\end{lrbox}',r'\ifdim\wd\OCfigure>\linewidth\PackageError{access-paper}{Figure '+label+r' exceeds its column}{Revise the figure layout.}\fi',r'\usebox{\OCfigure}',r'\caption{'+caption+'}',r'\label{'+label+'}',r'\end{'+env+'}'])
def reporting_tables(body,reporting):
 rows=[r'Model & Channel & No correct (/192) & Yes correct (/192) & False Yes & False No\\',r'\midrule']
 for r in reporting['probe_controls']:
  n=r['inaccessible'];y=r['accessible']
  rows.append(MODELS[r['model']]+' & '+r['boundary']+' & '+f'{n["correct"]} ({pc(n["accuracy"])}\\%)'+' & '+f'{y["correct"]} ({pc(y["accuracy"])}\\%)'+' & '+str(n['yes'])+' & '+str(y['no'])+r'\\')
 body=body.replace('% PROBE_CONTROL_TABLE',tab(rows,'llrrrr','Independent confirmation access probes in both states. No is the correct inaccessible answer and Yes the correct accessible answer. Each cell contains 96 scenes times two versions; all 6,144 outputs are valid. False Yes and False No count the two error directions. Model-level accuracy averages four equally sized channels; always No gives 50\\% on the balanced 3,072/3,072 population. These saved-data summaries add no hypothesis test.','tab:probecontrols',True))
 case=reporting['illustrative_case']['records']
 def record(version,accessible,method,Q='content'):
  return next(r for r in case if r['version']==version and r['accessible']==accessible and r['method']==method and r['Q']==Q)
 role=record('A',False,'full');probe=record('A',False,'probe','state');view=record('A',False,'view')
 rolelines=role['messages'][0]['content'].split('\n');probelines=probe['messages'][0]['content'].split('\n')
 assert rolelines[1:]==probelines[1:]
 rows=[r'Input component & Exact saved text or specified substitution\\',r'\midrule']
 for label,text in [('Role system prefix',rolelines[0]),('Shared character',rolelines[1]),('Full scene (A, no access)',rolelines[2]),('Role user message',role['messages'][1]['content']),('Independent probe prefix',probelines[0]),('Independent probe user',probe['messages'][1]['content'])]:
  rows.append(label+r' & {\footnotesize\ttfamily '+literal(text)+r'}\\')
 rows.append(r'Counterfactual B & Replace \texttt{The glove is in the church.} with \texttt{The broom is in the stairwell.}\\')
 rows.append(r'Accessible control & Replace \texttt{audible\_to\_Mira Sen}: \texttt{false} with \texttt{true}.\\')
 rows.append(r'Inaccessible view scene & {\footnotesize\ttfamily '+literal(view['messages'][0]['content'].split('\n')[2])+r'}\\')
 input_table=tab(rows,'lX','Exact messages for the selected hearing case, with A/B and access-state substitutions. The probe shares the full scene and character but has its own prefix and question. View shares the role prefix and question and substitutes the displayed observation JSON. Accessible view contains the permitted event in its observation list.','tab:caseinput',True)
 input_table=input_table.replace(r'\begin{tabular}{@{}lX@{}}',r'\begin{tabularx}{\textwidth}{@{}lX@{}}').replace(r'\end{tabular}',r'\end{tabularx}')
 body=body.replace('% CASE_INPUT_TABLE',input_table)
 rows=[r'Version & Access & Probe & Full-context spoken reply & Character-view spoken reply\\',r'\midrule']
 for accessible in (False,True):
  for version in ('A','B'):
   f=record(version,accessible,'full');v=record(version,accessible,'view');p=record(version,accessible,'probe','state')
   rows.append(version+' & '+('Yes' if accessible else 'No')+' & '+literal(p['text'])+' & '+literal(f['text'])+' & '+literal(v['text'])+r'\\')
 output_table=tab(rows,'llcXX','All saved content replies and independent probe answers for C001, Qwen3.5-9B, R2, delay zero. Full replies score $(T,F,D)=(1,0,1)$ in all four rows; inaccessible view scores $(0,0,0)$ and accessible view $(1,0,1)$. This selected illustration is not a prevalence sample.','tab:caseoutput',True)
 output_table=output_table.replace(r'\begin{tabular}{@{}llcXX@{}}',r'\begin{tabularx}{\textwidth}{@{}llcXX@{}}').replace(r'\end{tabular}',r'\end{tabularx}')
 return body.replace('% CASE_OUTPUT_TABLE',output_table)
def main():
 results=json.loads((R/'four-core-results.json').read_text());conf=results['confirmatory'];desc=json.loads((R/'paper-descriptive-results.json').read_text());rr=desc['descriptive_estimates'];body=(P/'body.tex').read_text()
 def find(panel,**kw):
  v=[r for r in rr if r['panel']==panel and all(r.get(k)==val for k,val in kw.items())];assert len(v)==1,(panel,kw,len(v));return v[0]
 access_rows=[r'Channel & Inaccessible condition & Compiled observation\\',r'\midrule',
  r'\textsc{Hear} & English speech cannot be heard & No observation\\',
  r'\textsc{Understand} & Speech is heard in an unknown language & Actor says something in that language\\',
  r'\textsc{See} & Item and destination are hidden & Actor appears to put something away\\',
  r'\textsc{Receive} & Message content is private to someone else & Actor visibly sends a message\\']
 access_table='\n'.join([r'\begin{table*}[t]',r'\centering\small',r'\begin{lrbox}{\OCtable}\begin{tabularx}{\textwidth}{@{}lXX@{}}',r'\toprule',*access_rows,r'\bottomrule',r'\end{tabularx}\end{lrbox}',r'\ifdim\wd\OCtable>\linewidth\PackageError{access-paper}{Table tab:accesscases exceeds its column}{Revise the table layout.}\fi',r'\usebox{\OCtable}',r'\caption{Access interventions and partial observations. Each event contains an item--location fact; the inaccessible compiled observation omits both values. Accessible controls retain the full event. These are illustrations of the designed schema, not model responses.}',r'\label{tab:accesscases}',r'\end{table*}'])
 body=body.replace('% ACCESS_CASES_TABLE',access_table)
 cohort_rows=[r'Analysis & Models & Scenes\\',r'\midrule',
  r'Discovery baseline & 11 & 96\\',r'State representations & 11 & 24\\',
  r'Method comparison & 6 & 48\\',r'Delay and search choice & 4 & 32\\',
  r'Original-character confirmation & 4 & 96\\']
 body=body.replace('% COHORT_TABLE',tab(cohort_rows,'lrr','Model and scene scopes. Discovery subsets overlap and are not additive; confirmation uses new original-character scenes with the shared instrument. Calibration is excluded from these rows.','tab:cohorts'))
 # One final-size geometry drives editable TikZ and SVG exports.
 boundary,boundary_svg=confirmation_boundaries(rr)
 body=body.replace('% BOUNDARY_FIGURE',figure(boundary,'Original-character confirmation: four models and 96 matched scene skeletons. Connected estimates compare accessible and inaccessible net canary use; whiskers give unadjusted 95\\% paired-bootstrap intervals. Values are equal-model, equal-skeleton automatic scores.','fig:boundaries'))
 rows=[r'Family / component & Estimate (pp) & 95\% CI & Null & Holm $p$\\',r'\midrule']
 for i,b in enumerate(BOUNDS):
  d=conf['H1_components'][b];rows.append(f'H1: {b} & {pc(d["estimate"])} & {ci(d)} & 0 & '+('0.0015' if i==0 else '---')+r'\\')
 d=conf['H2'];rows.append(f'H2: State-correct net use & {pc(d["estimate"])} & {ci(d)} & 0 & 0.0015'+r'\\');rows.append(r'\midrule')
 for i,(key,label) in enumerate([('forbidden_leak_reduction','H3: Full minus view leakage'),('accessible_target_use_delta','View minus full accessible use'),('partial_event_retention_improvement','View minus hard event retention')]):
  d=conf['H3_components'][key];rows.append(f'{label} & {pc(d["estimate"])} & {ci(d)} & '+('$-5$' if i==1 else '0')+' & '+('0.0015' if i==0 else '---')+r'\\')
 body=body.replace('% CONFIRMATORY_TABLE',tab(rows,'lrrcr','Frozen confirmation results. H1 is the conjunction of four positive boundary effects; H3 combines leakage reduction, accessible-use noninferiority, and event-retention improvement. Each family receives one Holm-adjusted value. H2 includes 6,068 eligible role-playing endpoints. Intervals are two-sided and unadjusted; testing is one-sided.','tab:confirm',True))
 rows=[r'Method & Leakage & Access. use & Event retention\\',r'\midrule']
 for method,label in [('full','Full context'),('hard','Hard removal'),('view','Character view')]:
  values=[find('confirmatory_method',method=method,accessible=False),find('confirmatory_method',method=method,accessible=True),find('confirmatory_partial_awareness',method=method,metric='awareness_correct')]
  rows.append(label+' & '+' & '.join(pc(x['estimate']) for x in values)+r'\\')
 body=body.replace('% METHOD_TABLE',tab(rows,'lrrr','Confirmation cohort. Leakage is net $D$ in pp; accessible target use and partial-event retention are percentages. Retention excludes Hear. Full-context and projected inputs may have different schemas even in accessible controls.','tab:methods'))
 behavior,behavior_svg=behavior_panels(rr,results['exploratory_paired_contrasts'])
 body=body.replace('% BEHAVIOR_FIGURE',figure(behavior,'Four core models and 32 matched discovery scenes. (a) Net use after neutral exchanges; labels give four-turn estimates. (b) Paired two- and four-turn changes from zero under full context (open and filled circles). (c) Change in choosing location A when inaccessible content switches from B to A; orange/green numbers give full/view estimates. Shading and whiskers show unadjusted 95\\% paired-bootstrap intervals. Invalid choices remain in the denominator.','fig:behavior',True))
 spec=json.loads((ROOT/'docs/access-v2/spec-lock.json').read_text());ref=json.loads((ROOT/'harness/weights_reference.json').read_text())['models']
 snapshot=next(name for name in ['eleven-model','ten-model','nine-model'] if (R/(name+'-verification.json')).exists() and (R/(name+'-results.json')).exists())
 extension_path=R/(snapshot+'-results.json');audit_path=R/(snapshot+'-verification.json')
 extension=json.loads(extension_path.read_text());audit=json.loads(audit_path.read_text())
 assert extension['confirmatory']==conf and audit['confirmatory_exactly_matches_saved_four_core']
 assert hashlib.sha256(extension_path.read_bytes()).hexdigest()==audit['analysis_results_sha256']
 diagnostics_path=R/'current-results-analysis/analysis.json';diagnostics=json.loads(diagnostics_path.read_text())
 assert diagnostics['actual_records']<=audit['total_actual_records'] and all(diagnostics['checks'].values())
 assert set(diagnostics['completed_models'])<=set(audit['completed_main_models'])
 assert diagnostics['verification_sha256']==hashlib.sha256((R/'nine-model-verification.json').read_bytes()).hexdigest()
 assert diagnostics['frozen_confirmatory']==conf
 diagnostic_keys=['baseline_by_model','method_cost_by_model','representation_diagnostics','self_filter_stage1_exact_match','illustrative_examples','lexical_block_sensitivity','interpretation','checks']
 diagnostic_export={'source_sha256':hashlib.sha256(diagnostics_path.read_bytes()).hexdigest(),'scope':diagnostics['scope'],'human_labels':0,**{k:diagnostics[k] for k in diagnostic_keys},'latest_representation_source_sha256':hashlib.sha256(extension_path.read_bytes()).hexdigest(),'latest_representation_models':audit['completed_main_models'],'latest_representation_contrasts':[r for r in extension['exploratory_paired_contrasts'] if r['contrast'].startswith('E2 ')]}
 (P/'snapshot-diagnostics-data.json').write_text(json.dumps(diagnostic_export,indent=2)+'\n')
 completed=set(audit['completed_main_models'])
 cohort_word={9:'nine',10:'ten',11:'eleven'}[len(completed)]
 method_report=json.loads((R/'method-six-descriptive-results.json').read_text())
 assert set(audit['completed_method_models'])==set(spec['method_models'])
 def find_method(**kw):
  selected=[r for r in method_report['descriptive_estimates'] if all(r.get(k)==v for k,v in kw.items())]
  assert len(selected)==1 and selected[0]['endpoints']==1152
  return selected[0]
 (P/'method-comparison-data.json').write_text(json.dumps(method_report,indent=2)+'\n')
 rows=[r'Checkpoint repository & Revision prefix & Snapshot role\\',r'\midrule']
 for m in spec['main_models']:
  role='Core complete' if m in spec['confirmatory_models'] else 'Discovery complete' if m in completed else 'Extension pending'
  rows.append(r'\texttt{'+esc(ref[m]['repo'])+'} & '+r'\texttt{'+ref[m]['revision'][:12]+'} & '+role+r'\\')
 roster_caption='Pinned model roster. All eleven discovery models are complete; four form the prespecified confirmation cohort. Full revisions and exact run metadata are retained in the accompanying registry.' if not audit['pending_main_models'] else 'Pinned model roster. Pending means no result from that checkpoint is included in this draft snapshot. Full revisions and exact completed-run metadata are retained in the accompanying registry.'
 body=body.replace('% MODEL_ROSTER',tab(rows,'lll',roster_caption,'tab:roster',True))
 rows=[r'Model & Hear & Understand & See & Receive\\',r'\midrule'];baseline=[]
 for m in spec['main_models']:
  if m not in completed:continue
  values=[]
  for b in BOUNDS:
   cells=[c for c in extension['cells'] if c['model']==m and c['set']=='discovery' and c['boundary']==b and c['representation']=='R2' and c['method']=='full' and c['delay']==0 and not c['accessible'] and c['Q'] in ('content','plan')]
   assert len(cells)==2 and {c['Q'] for c in cells}=={'content','plan'}
   assert all(c['metric']=='D' and c['planned']==192 and c['n_skeletons']==96 for c in cells)
   value=sum(c['estimate'] for c in cells)/2;values.append(pc(value))
   baseline.append({'model':m,'boundary':b,'estimate':value,'planned_endpoints':384,'n_skeletons':96})
  rows.append(MODELS[m]+' & '+' & '.join(values)+r'\\')
 body=body.replace('% DISCOVERY_BASELINE_TABLE',tab(rows,'lrrrr',f'Descriptive full-context R2 baseline for the {cohort_word} completed discovery models. Each cell averages content and planning responses over the same 96 scenes and two counterfactual versions, with 384 planned endpoints. Values are net canary-use points on inaccessible scenes; these are point estimates, not additional confirmation tests.','tab:discoverybaseline',True))
 (P/'discovery-baseline-data.json').write_text(json.dumps({'source_sha256':hashlib.sha256(extension_path.read_bytes()).hexdigest(),'rows':baseline},indent=2)+'\n')
 # Accessible target use is distinct from net D. Read exact frozen hit_t.
 accessible=[];accessible_sources={}
 for name in audit['analysis_score_files']:
  path=Path(name)
  if path.parent.name!='discovery':continue
  digest=hashlib.sha256(path.read_bytes()).hexdigest()
  assert digest==audit['models'][path.stem]['discovery']['scores_sha256']
  assert digest==extension['source_sha256'][str(path)]
  accessible_sources[str(path.relative_to(ROOT))]=digest
  selected=[]
  for line in path.read_text().splitlines():
   r=json.loads(line)
   if r['Q'] in ('content','plan') and r['representation']=='R2' and r['method']=='full' and r['delay']==0 and r['accessible']:selected.append(r)
  assert len(selected)==1536 and all(r['model']==path.stem for r in selected)
  for b in BOUNDS:
   rows=[r for r in selected if r['boundary']==b]
   assert len(rows)==384 and len({r['item'] for r in rows})==96
   assert len({r['prompt_id'] for r in rows})==384
   value=sum(r['hit_t'] for r in rows)/384
   saved=[r for r in diagnostics['baseline_by_model'] if r['model']==path.stem and r['boundary']==b]
   if saved:assert value==saved[0]['accessible_target']
   accessible.append({'model':path.stem,'boundary':b,'estimate':value,'planned_endpoints':384,'n_skeletons':96})
 assert len(accessible)==44
 (P/'discovery-baseline-data.json').write_text(json.dumps({'source_sha256':hashlib.sha256(extension_path.read_bytes()).hexdigest(),'rows':baseline,'accessible_target_rows':accessible,'accessible_score_sources':accessible_sources},indent=2)+'\n')
 labels={**MODELS,'nemotron3_nano30b':'Nemotron-30B','mistral_small3':'Mistral-24B'}
 heatmap_plot,heatmap_svg=discovery_profiles(baseline,accessible,spec['main_models'],labels,spec['confirmatory_models'])
 body=body.replace('% DISCOVERY_HEATMAP',figure(heatmap_plot,'Eleven-model discovery, full-context R2: 96 matched scenes, 384 endpoints per cell. (a) Inaccessible net use in pp; (b) accessible target use in percent; (c) equal-channel means (circles: net use; squares: target use). Both matrices use linear 0--100 scales. Name dots mark the four-model core. These automatic-score profiles are descriptive and do not define an overall utility ranking.','fig:discoveryheatmap',True))
 rows=[r'Model & Hear & Understand & See & Receive & State correct & Conditional $D$\\',r'\midrule']
 for r in desc['confirmatory_model_detail']:rows.append(MODELS[r['model']]+' & '+' & '.join(pc(r[k]) for k in ['Hear','Understand','See','Receive','inaccessible_state_accuracy','conditional_D'])+r'\\')
 body=body.replace('% MODEL_DETAIL',tab(rows,'lrrrrrr','Confirmation model detail. Boundary columns and conditional $D$ are net canary-use points; state correctness is a percentage. Every model has eligible role endpoints. The pooled four-boundary claim does not assert a positive effect in every cell.','tab:modeldetail',True))
 rows=[r'Model & Chinese & Japanese & Spanish\\',r'\midrule']
 for m in spec['confirmatory_models']:
  vals=[next(r for r in desc['confirmatory_translation'] if r['model']==m and r['language']==l) for l in ['zh','ja','es']]
  rows.append(MODELS[m]+' & '+' & '.join(pc(v['both_canary_translation_use']) for v in vals)+r'\\')
 body=body.replace('% TRANSLATION_TABLE',tab(rows,'lrrr','Both-canary translation use on 64 original-character prompts per model--language unit (\\%). The diagnostic threshold is 85\\%; the primary analysis is unconditional.','tab:translate',True))
 secondary_path=R/'revision-audit/results.json';secondary=json.loads(secondary_path.read_text())
 assert all(secondary['checks'].values()) and secondary['primary_rule']==spec['primary_estimand']
 assert secondary['compiler_vs_delete_retention']['estimate']==conf['H3_components']['partial_event_retention_improvement']['estimate']
 (P/'secondary-audit-data.json').write_text(json.dumps(secondary,indent=2)+'\n')
 reporting_path=R/'revision-audit/reporting.json';reporting=json.loads(reporting_path.read_text())
 assert all(reporting['checks'].values())
 for name,digest in reporting['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
 (P/'reporting-audit-data.json').write_text(json.dumps(reporting,ensure_ascii=False,indent=2)+'\n')
 body=reporting_tables(body,reporting)
 rows=[r'Boundary & State-correct $D$ [95\% CI] & $N$ & Capability-eligible $D$ [95\% CI] & $N$\\',r'\midrule']
 for b in BOUNDS:
  x=secondary['state_correct_by_boundary'][b];a=x['state_correct_unconditional'];g=x['state_correct_capability_eligible']
  rows.append(b+' & '+pc(a['estimate'])+' '+ci(a)+' & '+str(a['eligible_endpoints'])+' & '+pc(g['estimate'])+' '+ci(g)+' & '+str(g['eligible_endpoints'])+r'\\')
 body=body.replace('% CAPABILITY_STATE_TABLE',tab(rows,'llrlr','State-correct boundary decomposition in the four-model confirmation. Values are pp. The .85 gate applies only to comprehension; all of its state probes are correct. Eligibility is fixed from translation results, and model-specific ratios are recomputed over the original 96-scene bootstrap. These are secondary descriptive intervals, without additional confirmation tests.','tab:stateboundary',True))
 rows=[r'Boundary & Membership minus flag & Prose+flag minus flag\\',r'\midrule']
 contrasts=extension['exploratory_paired_contrasts']
 for b in BOUNDS:
  vals=[next(c for c in contrasts if c['contrast']==f'E2 {rep}-minus-R2 {b}') for rep in ['R1','R3']]
  rows.append(b+' & '+' & '.join(pc(v['estimate'])+' '+ci(v) for v in vals)+r'\\')
 body=body.replace('% REPRESENTATION_TABLE',tab(rows,'lll',f'Representation effects on inaccessible net use (pp), with 95\\% descriptive intervals. {cohort_word.capitalize()} completed discovery models, 24 matched scenes. The same comprehension prose contrast is +5.73 [0.00, 11.98] in the four-core subset.','tab:representation',True))
 rows=[r'Boundary & Method & Inaccessible $D$ & Accessible target use\\',r'\midrule']
 for b in BOUNDS:
  for method,label in [('full','Full'),('prose','Prose+flag'),('self_filter','Self-filter'),('hard','Hard removal'),('view','Character view')]:
   vals=[find_method(boundary=b,method=method,accessible=a) for a in [False,True]]
   rows.append(b+' & '+label+' & '+' & '.join(pc(v['estimate'])+' '+ci(v) for v in vals)+r'\\')
 body=body.replace('% DISCOVERY_METHOD_TABLE',tab(rows,'llll','Five methods in the complete prespecified six-model discovery cohort on 48 matched scenes (1,152 endpoints per cell). Leakage is net pp; accessible use is a percentage. These are descriptive cells with unadjusted 95\\% paired-bootstrap intervals.','tab:discoverymethods',True))
 rows=[r'Boundary & Method & Delay 0 & Delay 2 & Delay 4\\',r'\midrule']
 for b in BOUNDS:
  for method in ['full','view']:
   vals=[find('persistence',boundary=b,method=method,delay=d) for d in [0,2,4]]
   rows.append(b+' & '+method+' & '+' & '.join(pc(v['estimate'])+' '+ci(v) for v in vals)+r'\\')
 body=body.replace('% DELAY_TABLE',tab(rows,'lllll','Delayed net use (pp), 32-scene subset, with 95\\% intervals. The original event remains in context throughout the scripted exchanges.','tab:delay',True))
 rows=[r'Boundary & Method & Fixed-A choice contrast & 95\% CI & Valid choices (\%)\\',r'\midrule']
 for b in BOUNDS:
  for method in ['full','view']:
   d=find('decision',boundary=b,method=method);rows.append(b+' & '+method+' & '+pc(d['estimate'])+' & '+ci(d)+' & '+pc(d['valid_choice_fraction'])+r'\\')
 body=body.replace('% DECISION_TABLE',tab(rows,'llrrr','Fixed-A decision contrast (pp) and response validity. The choice of location A is tracked across versions, independently of its option number.','tab:decision',True))
 rows=[r'Boundary & Method & A first (18 scenes) & A second (14 scenes) & Equal-position effect\\',r'\midrule']
 for x in secondary['choice_order']['effects']:
  vals=[x['A_location_position'][str(k)] for k in (1,2)]
  equal={'estimate':x['equal_position_estimate'],'ci95':x['equal_position_ci95']}
  rows.append(x['boundary']+' & '+x['method']+' & '+' & '.join(pc(v['estimate'])+' '+ci(v) for v in [*vals,equal])+r'\\')
 body=body.replace('% CHOICE_ORDER_TABLE',tab(rows,'lllll','Additional descriptive option-position sensitivity (pp, 95\\% intervals). A/B order and the question are identical within every pair. The equal-position estimate weights the two order strata equally and resamples scenes independently within each stratum; original paired effects and tests remain unchanged.','tab:choiceorder',True))
 human_rows=[r'Endpoint & TP & FP & FN & P (\%) & R (\%) & F1 (\%) & $\kappa$\\',r'\midrule']
 human_endpoints=[('Discovery target','DT'),('Discovery foil','DF')]
 conditions=[('Full, inaccessible','FI'),('Full, accessible','FA'),('Removal, inaccessible','HI'),('Removal, accessible','HA'),('View, inaccessible','VI'),('View, accessible','VA'),('Full, correct probe','FS')]
 short_conditions=[('Full I','FI'),('Full A','FA'),('Removal I','HI'),('Removal A','HA'),('View I','VI'),('View A','VA'),('Full I, correct probe','FS')]
 for label,key in short_conditions:human_endpoints.extend([(label+' target',key+'T'),(label+' foil',key+'F')])
 human_endpoints.append(('Confirm. occurrence','O'))
 for label,key in human_endpoints:
  human_rows.append(label+' & '+' & '.join(r'\HumanField{'+key+'-'+metric+'}' for metric in ['tp','fp','fn','p','r','f','k'])+r'\\')
 body=body.replace('% HUMAN_AUDIT_TABLE',tab(human_rows,'lrrrrrrr','Human-study completion fields, not observed results. Counts compare the scorer with adjudicated labels; P/R/F1 are population-weighted within each audit. Agreement is before adjudication. Discovery and confirmation populations are separate. I/A denote inaccessible/accessible. Correct-probe full context is the inaccessible H2 subgroup, overlapping Full I. Unresolved counts and intervals are reported in the text.','tab:humanaudit',True))
 bias_rows=[r'Confirmation condition & $n$ & $P(T)$ & $P(F)$ & $P(T\land F)$ & Human $D$ [95\% CI] & Auto$-$human\\',r'\midrule']
 for label,key in conditions:
  rate_fields=' & '.join(r'\HumanField{'+key+'-'+metric+'}' for metric in ['N','T','F','B'])
  d_fields=r'\HumanField{'+key+r'-D} [\HumanField{'+key+r'-L}, \HumanField{'+key+r'-U}]'
  bias_rows.append(label+' & '+rate_fields+' & '+d_fields+r' & \HumanField{'+key+r'-BIAS}\\')
 body=body.replace('% HUMAN_BIAS_TABLE',tab(bias_rows,'lrrrrrr','Human measurement-sensitivity completion fields. Use rates are percentages; $D$, intervals, and automatic-minus-human bias are pp. Each row uses its own inclusion weights and model/boundary aggregation. Correct-probe full context matches H2. Semantic disclosure under view is checked with union use as well as net $D$. Fields are unsupplied observations.','tab:humanbias',True))
 language_rows=[r'Language & Meaning (/8) & Naturalness & A/B match & Clues (/8) & $\kappa$\\',r'\midrule']
 for label,key in [('Chinese','ZH'),('Japanese','JA'),('Spanish','ES')]:
  language_rows.append(label+' & '+' & '.join(r'\HumanField{'+key+'-'+metric+'}' for metric in ['ok','n','m','c','k'])+r'\\')
 body=body.replace('% HUMAN_LANGUAGE_TABLE',tab(language_rows,'lrrrrr','Completion fields for two fluent/native reviewers per language. Meaning and clues use eight individual sentences per language; naturalness averages eight sentence ratings, and A/B matchedness averages four distinct pair ratings. $\\kappa$ is sentence-meaning agreement. The inventory contains 24 sentences and 12 pairs; bracketed outcomes are unsupplied.','tab:humanlanguage',True))
 native_summary_path=ROOT/'analysis/validation-access-v2/ai-proxy/native-review-summary.json'
 if native_summary_path.exists():
  native=json.loads(native_summary_path.read_text())
  native_text=(f'Two independent AI proxy reviews each covered all 24 stimuli, disagreeing on meaning labels for {native["meaning_disagreement_rows"]} and flagging {native["uncertain_in_either_rows"]} as uncertain in either review. Their labels and notes remain separate from human stimulus judgments and empirical guessability responses.')
 else:native_text='Two independent AI proxy reviews of all 24 paired stimuli are in preparation. They remain distinct from the blank human forms and provide no native-speaker certification or empirical guessability rates.'
 body=body.replace('% NATIVE_PROXY_STATUS',native_text)
 # Preserve old reference keys, adding the verified MENTOR entry.
 bib=(P/'bibonly.bbl').read_text()
 mentor=r'''\bibitem[{Zhu et~al.(2026)Zhu, Gao, and Shi}]{zhu2026mentor}
Zhuoning Zhu, Xingyu Gao, and Hailong Shi. 2026.
\newblock \href{https://doi.org/10.18653/v1/2026.findings-acl.1046}{MENTOR: Mitigating identity drift in dynamic role-playing via dual-chain structured memory}.
\newblock In \emph{Findings of the Association for Computational Linguistics: ACL 2026}, pages 20865--20882, San Diego, California, United States. Association for Computational Linguistics.
'''
 if 'zhu2026mentor' not in bib:bib=bib.replace(r'\end{thebibliography}',mentor+'\n'+r'\end{thebibliography}');(P/'bibonly.bbl').write_text(bib)
 used=set(k for group in re.findall(r'\\cite[pt]?\{([^}]+)\}',body) for k in group.split(','))
 chunks=re.split(r'(?=\\bibitem)',bib);entries=[]
 for chunk in chunks[1:]:
  key=re.search(r'\]\{([^}]+)\}',chunk).group(1)
  if key in used:entries.append(chunk.split(r'\end{thebibliography}')[0])
 assert len(entries)==len(used)
 body=body.replace('% INLINE_BIBLIOGRAPHY',r'\begin{thebibliography}{'+str(len(entries))+'}\n'+r'\providecommand{\natexlab}[1]{#1}'+'\n'+''.join(entries)+r'\end{thebibliography}')
 assert not re.search(r'^% [A-Z_]+$',body,re.M),'Unfilled insertion marker'
 preamble=r'''\documentclass[11pt]{article}
\usepackage[review]{acl}
\usepackage{times,latexsym}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{microtype,booktabs,amsmath,amssymb,tabularx}
\usepackage{tikz}
\newsavebox{\OCtable}
\newsavebox{\OCfigure}
\definecolor{OCblue}{HTML}{0072B2}
\definecolor{OCorange}{HTML}{D55E00}
\definecolor{OCgreen}{HTML}{009E73}
\definecolor{OCpurple}{HTML}{CC79A7}
\hypersetup{pdfauthor={Anonymous},pdftitle={Role-Playing Language Models Use Information Their Characters Cannot Access}}
'''
 style=(P/'acl.sty').read_text();(P/'main.tex').write_text('% Standalone anonymous ARR working draft. Official style embedded unchanged.\n'+r'\begin{filecontents*}{acl.sty}'+'\n'+style+'\n'+r'\end{filecontents*}'+'\n'+preamble+body)
 figures=P/'figures';figures.mkdir(exist_ok=True)
 standalone=r'''\documentclass[11pt]{article}
\usepackage[margin=1.5cm]{geometry}
\usepackage{times,tikz}
\definecolor{OCblue}{HTML}{0072B2}
\definecolor{OCorange}{HTML}{D55E00}
\definecolor{OCgreen}{HTML}{009E73}
\definecolor{OCpurple}{HTML}{CC79A7}
\pagestyle{empty}
\begin{document}
'''
 (figures/'confirmation.tex').write_text(standalone+'\\centering\n'+boundary+'\n'+r'\end{document}')
 (figures/'confirmation.svg').write_text(boundary_svg+'\n')
 (figures/'behavior.svg').write_text(behavior_svg+'\n')
 (figures/'behavior.tex').write_text(standalone+'\\centering\n'+behavior+'\n'+r'\end{document}')
 (figures/'discovery-heatmap.tex').write_text(standalone+'\\centering\n'+heatmap_plot+'\n'+r'\end{document}')
 (figures/'discovery-heatmap.svg').write_text(heatmap_svg+'\n')
 with (figures/'plot-data.csv').open('w',newline='') as f:
  fields=['panel','model','boundary','method','accessible','delay','metric','estimate','ci95_low','ci95_high','endpoints','n_skeletons'];w=csv.DictWriter(f,fields);w.writeheader()
  for r in rr:w.writerow({**{k:r.get(k,'') for k in fields if not k.startswith('ci95')},'ci95_low':r['ci95'][0],'ci95_high':r['ci95'][1]})
  for values,access,metric in [(baseline,False,'D'),(accessible,True,'hit_t')]:
   for r in values:w.writerow({'panel':'discovery_profile','model':r['model'],'boundary':r['boundary'],'method':'full','accessible':access,'delay':0,'metric':metric,'estimate':r['estimate'],'endpoints':384,'n_skeletons':96})
  for m in spec['main_models']:
   for values,metric in [(baseline,'D'),(accessible,'hit_t')]:
    w.writerow({'panel':'discovery_channel_mean','model':m,'method':'full','metric':metric,'estimate':sum(r['estimate'] for r in values if r['model']==m)/4,'endpoints':1536,'n_skeletons':96})
  for r in results['exploratory_paired_contrasts']:
   if r['contrast'].startswith('E5 ') and ' full ' in r['contrast']:
    w.writerow({'panel':'delay_change','boundary':r['contrast'].split()[-1],'method':'full','delay':int(r['contrast'].split()[1][5]),'metric':'D_delta','estimate':r['estimate'],'ci95_low':r['ci95'][0],'ci95_high':r['ci95'][1],'n_skeletons':r['n_skeletons']})
 registry=[]
 for m in spec['main_models']:
  path=R/('gemma4_31b' if m=='gemma4_31b' else 'core-rest')/'responses/confirmatory'/m/'run.json'
  if m not in spec['confirmatory_models']:path=R/({'falcon_h1_34b':'falcon','mistral_small3':'mistral','seed_oss_36b':'seed'}.get(m,'extensions-four'))/'responses/discovery'/m/'run.json'
  registry.append({'model':m,'repo':ref[m]['repo'],'revision':ref[m]['revision'],'completed_core_snapshot':m in spec['confirmatory_models'],'discovery_complete':m in completed,'runtime':{k:v for k,v in json.loads(path.read_text()).items() if k not in ['weights_path','prompts_file']} if path.exists() else None})
 (P/'model-registry.json').write_text(json.dumps(registry,indent=2)+'\n')
 sources={'primary_results':str((R/'four-core-results.json').relative_to(ROOT)),'descriptive_results':str((R/'paper-descriptive-results.json').relative_to(ROOT)),'verification':str((R/'four-core-verification.json').relative_to(ROOT)),'discovery_results':str(extension_path.relative_to(ROOT)),'discovery_verification':str(audit_path.relative_to(ROOT)),'six_model_method_description':str((R/'method-six-descriptive-results.json').relative_to(ROOT)),'posthoc_snapshot_diagnostics':str(diagnostics_path.relative_to(ROOT))}
 sources['secondary_capability_and_choice_audit']=str(secondary_path.relative_to(ROOT))
 sources['saved_probe_controls_case_and_stimulus_units']=str(reporting_path.relative_to(ROOT))
 sources['human_extension_manifest']='analysis/validation-access-v2/extension-manifest.json'
 if native_summary_path.exists():sources['new_independent_AI_stimulus_reviews']=str(native_summary_path.relative_to(ROOT))
 (P/'evidence-sources.json').write_text(json.dumps({'snapshot':f'four-model core plus {cohort_word}-model descriptive discovery baseline and complete six-model method comparison','sources':{k:{'path':v,'sha256':hashlib.sha256((ROOT/v).read_bytes()).hexdigest()} for k,v in sources.items()},'human_validation':'pending; AI proxy only','full_roster':f'{len(audit["pending_main_models"])} discovery models pending; all 6 method models complete','native_compiler':'not yet checked for current source'},indent=2)+'\n')
 print('Wrote main.tex;',len(used),'references; editable TikZ/SVG composite figures and 218-row plot table')
if __name__=='__main__':main()
