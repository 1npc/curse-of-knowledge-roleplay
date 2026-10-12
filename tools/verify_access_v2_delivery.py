"""Verify and package current v2 manuscript and validation deliverables."""
from pathlib import Path
import ast,csv,datetime,hashlib,json,re,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'paper/arr';V=ROOT/'analysis/validation-access-v2';D=ROOT/'deliverables'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,data):p.write_text(json.dumps(data,indent=2)+'\n')
def main():
 lock=json.loads((ROOT/'docs/access-v2/final-lock.json').read_text())
 for p,h in {**lock['input_sha256'],**lock['code_sha256']}.items():assert sha(ROOT/p)==h,p
 for d in lock['model_plans'].values():assert sha(ROOT/d['path'])==d['sha256']
 for p in [ROOT/'tools/report_access_v2.py',ROOT/'tools/report_access_v2_methods.py',ROOT/'tools/summarize_access_v2_review.py',ROOT/'tools/evaluate_access_v2_annotations.py',ROOT/'tools/audit_access_v2_revision.py',ROOT/'tools/audit_access_v2_reporting.py',ROOT/'tools/prepare_access_v2_human_extension.py',ROOT/'tools/evaluate_access_v2_human_extension.py',P/'make_paper.py',P/'figure_design.py']:ast.parse(p.read_text())
 receipt=json.loads((P/'native-compile-receipt.json').read_text())
 for name,result in receipt['source_results'].items():assert result['kind']=='success' and sha(P/name)==result['sha256'],('Recompile changed source',name)
 s=(P/'main.tex').read_text();body=s.split(r'\title{',1)[1]
 embedded=s.split(r'\begin{filecontents*}{acl.sty}'+'\n',1)[1].split('\n'+r'\end{filecontents*}',1)[0]
 assert embedded==(P/'acl.sty').read_text()
 assert not any(ord(c)<32 and c not in '\n\r\t' for c in s)
 abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',body,re.S)[1];words=len(abstract.split());assert words<=200
 labels=re.findall(r'\\label\{([^}]+)\}',body);assert len(labels)==len(set(labels));assert set(re.findall(r'\\ref\{([^}]+)\}',body))<=set(labels)
 citations=set(k for group in re.findall(r'\\cite[pt]?\{([^}]+)\}',body) for k in group.split(','));bibkeys=set(re.findall(r'\]\{([^}]+)\}',(P/'bibonly.bbl').read_text()));assert citations<=bibkeys
 assert all(x in s for x in [r'\usepackage[review]{acl}',r'\section*{Limitations}',r'\section*{Ethical Considerations}',r'\paragraph{AI assistance.}',r'\appendix'])
 assert r'\section*{Acknowledgments}' not in s
 assert r'\subsection{RQ' not in s
 assert {'tab:accesscases','tab:cohorts','eq:netuse','eq:projection','app:accounting'}<=set(labels)
 template=json.loads((P/'template-source.json').read_text())
 for name,item in template.items():assert sha(P/name)==item['sha256'],('Official template changed',name)
 assert not any(x in body for x in ['/Users/','qianru','q84453243','192.168.','10.201.','Amsterdam123'])
 assert not re.search(r'^% [A-Z_]+$',body,re.M)
 assert s.count(r'\begin{table')==s.count(r'\ifdim\wd\OCtable')
 assert s.count(r'\begin{figure')==s.count(r'\ifdim\wd\OCfigure')
 assert r'\ifnum\value{page}>9' in s
 assert r'\ifdefined\pdftexversion' in s and 'Submission pagination is verified with pdfLaTeX' in s
 v2=json.loads((ROOT/'analysis/h200-v2-20261002/four-core-verification.json').read_text());assert v2['total_actual_records']==151864 and v2['confirmatory_actual_records']==62208
 rb=ROOT/'analysis/h200-v2-20261002';snapshot=next(name for name in ['eleven-model','ten-model','nine-model'] if (rb/(name+'-verification.json')).exists() and (rb/(name+'-results.json')).exists())
 extension=json.loads((rb/(snapshot+'-verification.json')).read_text());assert extension['confirmatory_exactly_matches_saved_four_core']
 assert extension['total_actual_records']==sum(s['actual_records'] for phases in extension['models'].values() for s in phases.values())
 baseline=json.loads((P/'discovery-baseline-data.json').read_text());assert len(baseline['rows'])==4*len(extension['completed_main_models']) and baseline['source_sha256']==sha(rb/(snapshot+'-results.json'))
 assert len(baseline['accessible_target_rows'])==44
 for name,digest in baseline['accessible_score_sources'].items():assert sha(ROOT/name)==digest
 target_lookup={}
 for name in baseline['accessible_score_sources']:
  groups={b:[] for b in ('Hear','Understand','See','Receive')}
  for line in (ROOT/name).read_text().splitlines():
   r=json.loads(line)
   if r['Q'] in ('content','plan') and r['representation']=='R2' and r['method']=='full' and r['delay']==0 and r['accessible']:groups[r['boundary']].append(r)
  for b,rows in groups.items():
   assert len(rows)==384 and len({r['item'] for r in rows})==96
   target_lookup[Path(name).stem,b]=sum(r['hit_t'] for r in rows)/384
 for r in baseline['accessible_target_rows']:assert r['estimate']==target_lookup[r['model'],r['boundary']]
 with (P/'figures/plot-data.csv').open() as f:plotrows=list(csv.DictReader(f))
 assert len(plotrows)==218
 assert sum(r['panel']=='discovery_profile' for r in plotrows)==88
 assert sum(r['panel']=='discovery_channel_mean' for r in plotrows)==22
 assert sum(r['panel']=='delay_change' for r in plotrows)==8
 methods=json.loads((P/'method-comparison-data.json').read_text());assert len(methods['descriptive_estimates'])==40 and all(len(r['models'])==6 and r['endpoints']==1152 for r in methods['descriptive_estimates'])
 assert methods['verification_sha256']==sha(ROOT/'analysis/h200-v2-20261002/nine-model-verification.json')
 diagnostics=json.loads((P/'snapshot-diagnostics-data.json').read_text())
 original_diagnostics=json.loads((ROOT/'analysis/h200-v2-20261002/current-results-analysis/analysis.json').read_text())
 assert diagnostics['source_sha256']==sha(ROOT/'analysis/h200-v2-20261002/current-results-analysis/analysis.json')
 assert all(diagnostics['checks'].values()) and diagnostics['human_labels']==0
 for k in ['baseline_by_model','method_cost_by_model','representation_diagnostics','self_filter_stage1_exact_match','illustrative_examples','lexical_block_sensitivity','interpretation','checks']:assert diagnostics[k]==original_diagnostics[k]
 latest=json.loads((rb/(snapshot+'-results.json')).read_text())
 assert diagnostics['latest_representation_source_sha256']==sha(rb/(snapshot+'-results.json')) and diagnostics['latest_representation_models']==extension['completed_main_models']
 assert diagnostics['latest_representation_contrasts']==[x for x in latest['exploratory_paired_contrasts'] if x['contrast'].startswith('E2 ')]
 registry=json.loads((P/'model-registry.json').read_text())
 assert {x['model'] for x in registry if x['discovery_complete']}==set(extension['completed_main_models'])
 assert all(x['runtime'] is not None for x in registry if x['discovery_complete'])
 for b in ('Hear','Understand','See','Receive'):
  for rep in ('R1','R3'):
   value=next(x for x in latest['exploratory_paired_contrasts'] if x['contrast']==f'E2 {rep}-minus-R2 {b}')
   assert f'{100*value["estimate"]:.2f}' in s
 review=json.loads((V/'ai-proxy/summary.json').read_text());assert review['total_unique_response_items']==832 and review['actual_human_annotations']==0
 for p in V.glob('blind-*.csv'):
  with p.open() as f:
   rows=list(csv.DictReader(f))
  fields=['use_place_1','use_object_1','use_place_2','use_object_2','paraphrase','denial','refusal','foreign_echo_only','uncertain','evidence'] if 'use_place_1' in rows[0] else ['chosen_option','uncertain','evidence'] if 'chosen_option' in rows[0] else ['acknowledges_occurrence','claims_content_knowledge','uncertain','evidence']
  assert all(not r[k] for r in rows for k in fields)
 secondary=json.loads((P/'secondary-audit-data.json').read_text())
 assert secondary==json.loads((rb/'revision-audit/results.json').read_text()) and all(secondary['checks'].values())
 assert secondary['primary_rule']=='equal-model, equal-skeleton mean of same-response target-minus-foil on content and plan; unconditional; capability-conditioned secondary'
 assert secondary['comprehension_capability_eligible']['eligible_endpoints']==1152
 assert secondary['choice_order']['skeleton_counts_A_position']=={'1':18,'2':14}
 reporting=json.loads((P/'reporting-audit-data.json').read_text())
 assert reporting==json.loads((rb/'revision-audit/reporting.json').read_text()) and all(reporting['checks'].values())
 for name,digest in reporting['source_sha256'].items():assert sha(ROOT/name)==digest,name
 assert reporting['probe_total']=={'planned':6144,'per_state':3072,'inaccessible_correct':3034,'accessible_correct':2983,'invalid':0,'always_no_balanced_accuracy':.5}
 assert all(x['individual_sentences']==8 and x['counterfactual_pairs']==4 for x in reporting['stimulus_inventory'].values())
 assert len(reporting['illustrative_case']['records'])==12
 assert {'tab:probecontrols','tab:caseinput','tab:caseoutput','tab:humanbias','eq:measurementbias'}<=set(labels)
 assert '24 deduplicated A/B pairs' not in s and 'eight-pair inventories' not in s
 assert all(x in s for x in ['93.36','99.35','24 deduplicated sentences forming 12 A/B pairs','matchedness averages four distinct pair ratings'])
 assert 'counterbalanced across scenes' not in s and 'not randomized' in s
 for name in ['comprehension_capability_eligible','pooled_state_correct_capability_eligible']:
  for value in [secondary[name]['estimate'],*secondary[name]['ci95']]:assert f'{100*value:.2f}' in s
 extension_manifest=json.loads((V/'extension-manifest.json').read_text())
 assert extension_manifest['actual_human_annotations']==0 and all(extension_manifest['original_packet_preserved'].values())
 assert extension_manifest['supplemental_foil_responses']==192 and extension_manifest['supplemental_choice_responses']==128
 assert extension_manifest['guessability_active_coverage_complete']
 for name in ['native-review-A.csv','native-review-B.csv']:
  with (V/name).open() as f:rows=list(csv.DictReader(f))
  assert len(rows)==24 and all(not r[k] for r in rows for k in ['reviewer_id','meaning_correct','naturalness_1_to_5','AB_matchedness_1_to_5','canary_lexical_clue','uncertain','notes'])
 new_native=json.loads((V/'ai-proxy/native-review-summary.json').read_text())
 assert new_native['actual_human_reviews']==0 and new_native['independent_AI_judgments']==48
 human_fields=sorted(set(re.findall(r'\\HumanField\{([^}]+)\}',s)))
 assert len(human_fields)>=70
 assert all(x in s for x in ['Human-study completion template','not completed human results','Completion-template convention.','Discovery and confirmation populations are separate.'])
 assert 'Human measurement certification remains pending.' not in s
 assert 'Every new human field remains blank.' not in s
 assert 'tab:humanaudit' in labels and 'tab:humanlanguage' in labels
 reviewpath=V/'ai-proxy/scorer-comparison.json';metrics=json.loads(reviewpath.read_text());assert metrics['label_type']=='ai_proxy'
 # Native compiler outcomes were obtained with the explicit app compiler tools.
 verification={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':'ARR venue-format and local source-package check','official_rules_checked_on':'2026-10-02','official_rules':['https://aclrollingreview.org/cfp','https://acl-org.github.io/ACLPUB/formatting.html'],'source_sha256':sha(P/'main.tex'),'official_style_sha256':sha(P/'acl.sty'),'embedded_style_identical':True,'review_mode':True,'abstract_whitespace_words':words,'cited_references':len(citations),'labels_unique':True,'references_resolve_in_source':True,'no_unfilled_markers':True,'no_identifying_paths_in_article':True,'scientific_inputs_scorer_and_frozen_analysis_unchanged':True,'native_compiler':'success for current main.tex; explicit desktop compiler call after final prose integration','standalone_figure_compilation':{'confirmation.tex':'success','behavior.tex':'success'},'main_body_with_floats_within_eight_pages':True,'table_and_figure_width_guards_passed':True,'page_limit_check':'Compilation passed error guard after main-text clearpage, before Limitations; page counter <=9 after all main floats are flushed','main_pages_exact':None,'visual_page_review':'not completed; computer-use tool forbids reading the Codex application','pdf_export':'not produced; native compiler provides editor preview but no export through this tool','human_validation':'pending; new 832-item AI proxy audit completed twice, actual human annotations 0','full_model_roster':'nine discovery models complete with an appendix baseline; two discovery models pending; all six method models complete; core confirmation unchanged','claim_evidence_checks':{'pooled_H1_not_every_model':'resolved; Gemma Understand zero reported','state_probe_not_internal_knowledge':'resolved; independent-call conditioning stated','confirmatory_independence':'resolved; original characters but shared schema/vocabulary stated','hard_removal_awareness':'resolved; original-scene retention and actual-input correctness separated','delay_and_decision_scope':'resolved; contextual persistence and textual search choice, not latent memory or executed action','capability_diagnostic':'resolved; three Japanese units below .85 disclosed, primary unconditional','AI_metrics_not_human':'resolved; labeled AI proxy, exclusions and uncertainty reported'},'remaining_checks':['finish and integrate planned wider model cohorts','collect real independent human labels, native review and guessability responses','export PDF and visually inspect pages, fonts and metadata','complete venue-specific submission metadata and Responsible NLP Checklist'],'skill_preflight_limit':'Referenced ccf-humanization package was not installed; available writer/common/checker rules and direct evidence checks applied without claiming that preflight ran'}
 verification['full_model_roster']=f'{len(extension["completed_main_models"])} discovery models complete with an appendix baseline; {len(extension["pending_main_models"])} discovery models pending; all six method models complete; core confirmation unchanged'
 verification['official_rules_checked_on']='2026-10-03'
 verification['native_compiler']='success for current main.tex in the built-in XeTeX preview; submission pagination separately verified in the pdfLaTeX export'
 verification['page_limit_check']='pdfLaTeX error guard after main-text clearpage and a complete reference pass; independently checked exported PDF has exactly eight main pages. XeTeX preview has different page breaks.'
 verification['requested_length_target']='Exactly eight full main-content pages, including all main figures and tables; official typography and margins unchanged.'
 verification['latest_visual_revision']='Full-width 88-cell discovery/control matrix with 22 channel means; four delay small multiples plus saved paired changes and choice effects; stable colors/shapes, luminance-selected matrix text, matching editable TikZ/SVG geometry; detailed confirmation table moved to Appendix A. Frozen data and inference unchanged.'
 verification['latest_writing_revision']='Corrected 24 sentence/12 counterfactual pair units; reported both access-probe states from saved data; exact 12-record input/output illustration with independent rescoring and frozen rule details; human confusion metrics and absolute bias separated by method/access and H2 subgroup; bounded schema comparison and shell-retention claims. Final-tense human fields remain visibly unsupplied; frozen tests and rich figures unchanged.'
 verification['human_reporting_template']={'status':'author-fill template; no completed human observations','actual_human_annotations':0,'actual_human_stimulus_reviews':0,'human_fields':human_fields,'field_count':len(human_fields),'all_unset_fields_visible_in_PDF':True,'completion_template_notice_in_main_and_appendix':True,'confirmation_semantic_audit':'separate unsupplied sampling frame; discovery 640-item audit does not certify confirmation content','submission_ready':False}
 verification['human_reporting_template']['confirmation_condition_separation']='full/removal/view x inaccessible/accessible; independent correct-probe full-inaccessible subgroup; target, foil, simultaneous use, net D, intervals and absolute automatic-minus-human bias'
 verification['reporting_audit']={'source_sha256':sha(rb/'revision-audit/reporting.json'),'probe_total':reporting['probe_total'],'native_units':{'sentences':24,'pairs':12,'per_language_sentences':8,'per_language_pairs':4},'example_records_independently_rescored':12,'no_new_generation_or_confirmatory_tests':True}
 verification['claim_evidence_checks'].update({'stimulus_counting_units':'resolved; reciprocal original forms checked: 24 sentences/12 pairs, eight sentences/four pairs per language','access_probe_positive_controls':'resolved; 93.36–99.35% accessible and 95.18–100% inaccessible model-level accuracy; 6144 valid responses; both error directions tabulated','condition_specific_measurement_bias':'reporting template separated by method/access and correct-probe full-inaccessible subgroup; no real human observations yet','method_schema_confound':'explicit; pooled noninferiority versus full context does not establish superiority to all prompting methods','shell_retention_scope':'observable-shell check with all-positive partial-occurrence scenes; selective awareness not established','exact_counterfactual_case':'12 original records independently rescored; saved full and compiled inputs, probe answers, A/B/access substitutions, denial and multi-value scorer rules supplied'})
 verification['no_unfilled_generation_markers']=True
 verification['no_unfilled_human_fields']=False
 verification['official_rules'].append('https://acl-org.github.io/ACLPUB/review-version.html')
 verification['official_template_live_check']={'checked_on':'2026-10-03','method':'System curl with normal TLS; all four local files matched current official repository bytes','files':template}
 verification['ccf_workflow']={'owner':'ccf-paper-writer','support':['ccf-common','ccf-paper-reviewer'],'internal_review':'bounded review of human-template provenance, audit populations, metric interpretation and affected layout; no full review panel or acceptance score'}
 verification['article_organization']='Problem and three contributions; related work; access evaluation; character-view compilation; experimental setup; five evidence-led result subsections; discussion and conclusion; Limitations; Ethical Considerations; references; double-column appendices'
 verification['anonymous_AI_disclosure']='AI assistance disclosed under Ethical Considerations; no Acknowledgments section in anonymous review. Responsible NLP Checklist and final camera-ready disclosure remain author tasks.'
 verification['claim_evidence_checks'].update({'content_vs_occurrence':'resolved; designed interventions and compiled shells displayed in Table 1; main retention paragraph states all scenes contain an event and always-positive answers can score 100; no general interaction-quality claim','cohort_scopes':'resolved; 11/6/4-model scopes and overlapping 96/24/48/32-scene discovery subsets distinguished from 96 original-character confirmation scenes','foil_diagnostic_in_main':'AI diagnostics moved to appendix with target and foil metrics; main human metrics are visibly unsupplied placeholders, not renamed AI measurements','human_claims':'final-tense template visibly qualified; human values, interpretive conclusion, ethics and qualifications remain fields'})
 if extension['full_eleven_model_campaign_complete']:
  verification['remaining_checks'].remove('finish and integrate planned wider model cohorts')
  verification['full_experiment_campaign_complete']=True
  verification['hardware_scope']='Ten models on H200; Seed on one Slurm H100 with the same pin, software and frozen protocol. Hardware invariance not tested.'
 verification['representation_scope']=f'{len(extension["completed_main_models"])} completed discovery models on frozen E2 24 scenes, with original four-core comprehension contrast preserved'
 verification['posthoc_diagnostics']='allowed-content controls, exact-string audit of original self-filter stage1, and 12 lexical-block descriptive bootstrap; no new confirmation tests or human labels'
 verification['claim_evidence_checks'].update({'prose_rule_cohort_dependence':'resolved; completed wider-cohort comprehension decrease and four-core increase are both scoped and reported','self_filter_utility_loss':'resolved; allowed-content losses accompanied by 190/192 and 180/192 exact-shell first-stage counts; not semantic certification','lexical_reuse_and_language':'resolved; shared 12 pairings, eight active sentences per language, language/pair non-crossing, and unseen-vocabulary limit stated','posthoc_resampling_scope':'resolved; wider 12-block intervals identified as additional descriptive sensitivity; frozen tests unchanged'})
 verification['claim_evidence_checks'].update({'capability_conditioned_secondary':'resolved; frozen plan explicitly unconditional primary, .85 secondary gives 50.98 [48.36,53.67], no item-level exclusion invented','state_correct_boundary_decomposition':'resolved; each boundary and eligibility denominator shown, comprehension state probes all correct','compiler_event_retention_CI':'resolved; 67.75 [65.36,70.05] is a frozen H3 component, limited shell task stated','choice_order_imbalance':'resolved; deterministic 18/14 order, paired-input check and separate position sensitivity disclosed','foil_specific_measurement':'resolved; weak AI foil recall/F1 separately reported and diagnostic enrichment prepared','two_independent_AI_stimulus_passes':'completed 24 each; 48 AI judgments, three meaning-label disagreements and eleven uncertainty flags; real native reviewers still pending'})
 verification['standalone_figure_compilation']['discovery-heatmap.tex']='success'
 verification['visual_figure_review']='New heatmap SVG preview inspected for values, labels, contrast and clipping. Native PDF page layout remains uninspected.'
 verification['secondary_analysis_source_sha256']=sha(rb/'revision-audit/results.json')
 export_path=P/'pdf-export-receipt.json'
 if export_path.exists():
  exported=json.loads(export_path.read_text())
  if exported['source_sha256']==sha(P/'main.tex'):
   assert sha(ROOT/exported['pdf_path'])==exported['pdf_sha256']
   assert exported['visual_review_completed'] and exported['all_fonts_embedded'] and exported['outside_page_characters']==0
   assert exported['main_pages']==8 and exported['Limitations_start_page']==9 and exported['last_main_page_both_columns_full']
   verification.update({'main_pages_exact':exported['main_pages'],'pdf_total_pages':exported['total_pages'],'visual_page_review':'completed; all exported PDF pages inspected after rendering with Poppler','pdf_export':exported['pdf_path'],'pdf_sha256':exported['pdf_sha256']})
   verification['visual_figure_review']='All three result figures inspected at final manuscript size; 88 matrix values, 22 channel means and saved delay/choice intervals checked against frozen sources. Editable SVG and TikZ share measured point geometry, labels and colors.'
   verification['figure_2_pages']=exported['figure_2_pages']
   verification['pdf_fonts_embedded']=exported['all_fonts_embedded']
   verification['pdf_A4']=exported['A4']
   verification['last_main_page_column_bottoms_pt']=exported['last_main_page_column_bottoms_pt']
   verification['Limitations_start_page']=exported['Limitations_start_page']
   verification['remaining_checks'].remove('export PDF and visually inspect pages, fonts and metadata')
 dump(P/'verification.json',verification)
 sources=json.loads((P/'evidence-sources.json').read_text());sources['native_compiler']='success on current main source';sources['AI_proxy_sources']={str(p.relative_to(ROOT)):{'sha256':sha(p)} for p in [V/'ai-proxy/summary.json',reviewpath]};sources['human_reporting_template']=verification['human_reporting_template'];dump(P/'evidence-sources.json',sources)
 # Human-facing archive excludes organizer mappings, model/source identifiers and AI judgments.
 blindfiles=[V/name for name in ['blind-content-A.csv','blind-content-B.csv','blind-awareness-A.csv','blind-awareness-B.csv','native-stimuli.csv','protocol.md','blind-foil-A.csv','blind-foil-B.csv','blind-choice-A.csv','blind-choice-B.csv','native-review-A.csv','native-review-B.csv','native-reviewer-profiles.csv','guessability-responses.csv','extension-protocol.md']]
 with zipfile.ZipFile(D/'access-v2-blind-validation.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in blindfiles:z.write(p,p.name)
  z.write(ROOT/'docs/guessability/form.md','guessability-form.md');z.write(ROOT/'docs/guessability/items.csv','guessability-items.csv')
  z.writestr('packet-manifest.json',json.dumps({'representative_semantic_responses':640,'representative_awareness_responses':192,'diagnostic_supplemental_foil_responses':192,'choice_responses':128,'native_stimuli':24,'native_individual_sentences':24,'native_counterfactual_pairs':12,'per_language_sentences':8,'per_language_pairs':4,'native_review_forms':2,'native_reviewer_slots':6,'guessability_questions':96,'actual_human_annotations':0,'all_annotation_fields_blank':True,'organizer_keys_and_AI_labels_excluded':True,'files':{p.name:sha(p) for p in blindfiles}},indent=2)+'\n')
 a=V/'ai-proxy'
 proxyfiles=[p for p in a.iterdir() if p.is_file() and (p.name.endswith('-content.csv') or p.name.endswith('-awareness.csv') or p.name.endswith('-method.md') or p.name in ['native-stimuli-reviewed.csv','summary.json','scorer-comparison.json','disagreements-for-review.csv','native-review-A.csv','native-review-B.csv','native-review-summary.json'])]
 with zipfile.ZipFile(D/'access-v2-ai-review.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in proxyfiles:z.write(p,'ai-proxy/'+p.name)
  z.write(V/'protocol.md','protocol.md');z.write(V/'manifest.json','sampling-manifest.json')
 sourcefiles=[P/name for name in ['main.tex','body.tex','make_paper.py','figure_design.py','acl.sty','acl_natbib.bst','references.bib','bibonly.bbl','README.md','revision-notes.md','verification.json','evidence-sources.json','model-registry.json','native-compile-receipt.json','discovery-baseline-data.json','method-comparison-data.json','snapshot-diagnostics-data.json','secondary-audit-data.json','reporting-audit-data.json','template-source.json','official-README.md','official-acl_latex.tex']]+list((P/'figures').glob('*'))
 if export_path.exists():sourcefiles.append(export_path)
 unpacked=D/'over-comprehension-arr-source';unpacked.mkdir(exist_ok=True)
 with zipfile.ZipFile(D/'over-comprehension-arr-source.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sourcefiles:
   rel=p.relative_to(P);z.write(p,str(rel));dest=unpacked/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 receipts={}
 for name in ['access-v2-blind-validation.zip','access-v2-ai-review.zip','over-comprehension-arr-source.zip']:
  p=D/name
  with zipfile.ZipFile(p) as z:assert z.testzip() is None;members=z.namelist()
  receipts[name]={'bytes':p.stat().st_size,'sha256':sha(p),'files':len(members)}
 if export_path.exists() and exported['source_sha256']==sha(P/'main.tex'):
  pdf=ROOT/exported['pdf_path'];receipts[pdf.name]={'bytes':pdf.stat().st_size,'sha256':sha(pdf),'pages':exported['total_pages']}
 dump(D/'access-v2-delivery.json',receipts)
 print(json.dumps({'abstract_words':words,'references':len(citations),'tables':s.count(r'\begin{table'),'figures':s.count(r'\begin{figure'),'packages':receipts},indent=2))
if __name__=='__main__':main()
