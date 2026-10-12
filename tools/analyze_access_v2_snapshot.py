"""Read-only scientific inputs; post-hoc diagnostics for the nine-model snapshot.

Reuses the frozen scorer outputs and bootstrap implementation. Does not generate,
rescore, change a hypothesis, alter annotation packets, or update the manuscript.
All additional intervals are descriptive; no new hypothesis tests are reported.
"""
from pathlib import Path
import collections
import csv
import datetime
import hashlib
import html
import json
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from oc_v2.analyze import Bootstrap, model_skeleton_vector, paired_delta
from oc_v2.design import BOUNDARIES, public_shell

B = ROOT / "analysis/h200-v2-20261002"
OUT = B / "current-results-analysis"
NAMES = {"qwen38_27b": "Qwen 3.8 27B", "qwen35_9b": "Qwen 3.5 9B",
         "gemma4_31b": "Gemma 4 31B", "gemma4_12b": "Gemma 4 12B",
         "glm47_flash": "GLM 4.7 Flash", "gpt_oss_20b": "gpt-oss 20B",
         "phi4": "Phi-4", "nemotron3_nano30b": "Nemotron 3 Nano 30B",
         "falcon_h1_34b": "Falcon H1 34B"}
METHODS = ["full", "prose", "self_filter", "hard", "view"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def average(rr, field):
    assert rr
    return statistics.mean(r[field] for r in rr)


def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(p)


def csvsave(p, rows):
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    audit_path = B / "nine-model-verification.json"
    audit = read(audit_path)
    spec_path = ROOT / "docs/access-v2/spec-lock.json"
    lock_path = ROOT / "docs/access-v2/final-lock.json"
    spec, lock = read(spec_path), read(lock_path)
    frozen = read(B / "nine-model-results.json")
    old = read(B / "four-core-results.json")
    paper = read(B / "paper-descriptive-results.json")
    six = read(B / "method-six-descriptive-results.json")
    assert frozen["confirmatory"] == old["confirmatory"]
    assert sha(B / "nine-model-results.json") == audit["analysis_results_sha256"]
    for path, digest in {**lock["input_sha256"], **lock["code_sha256"]}.items():
        assert sha(ROOT / path) == digest, path
    models = [m for m in spec["main_models"] if m in audit["completed_main_models"]]
    core, methods = spec["confirmatory_models"], spec["method_models"]
    assert len(models) == 9 and len(methods) == 6 and len(core) == 4
    source_sha = {}
    rows, scorepaths = [], {}
    for name in audit["analysis_score_files"]:
        p = Path(name)
        digest = sha(p)
        assert digest == audit["models"][p.stem][p.parent.name]["scores_sha256"]
        assert digest == frozen["source_sha256"][str(p)]
        source_sha[str(p.relative_to(ROOT))] = digest
        rr = [json.loads(line) for line in p.read_text().splitlines()]
        assert len(rr) == audit["models"][p.stem][p.parent.name]["scored_endpoints"]
        assert all(r["model"] == p.stem and r["set"] == p.parent.name for r in rr)
        rows.extend(rr)
        scorepaths[p.stem, p.parent.name] = p
    assert len(rows) == len({(r["model"], r["set"], r["prompt_id"]) for r in rows})
    assert len(rows) == audit["total_scored_endpoints_including_pilot"] - 3000
    d = [r for r in rows if r["set"] == "discovery"]
    c = [r for r in rows if r["set"] == "confirmatory"]
    role = lambda r: r["Q"] in ("content", "plan") and r["delay"] == 0
    base = [r for r in d if role(r) and r["representation"] == "R2" and r["method"] == "full"]
    boot = Bootstrap()

    def interval(v):
        z = boot.vector(v)
        return {k: z[k] for k in ("estimate", "ci95", "n_skeletons")}

    def checkgrid(rr, mm, scenes, boundaries, access, reps, meth):
        expected = {(m, i, b, q, v, a, rep, me)
                    for m in mm for i in scenes for b in boundaries
                    for q in ("content", "plan") for v in ("A", "B")
                    for a in access for rep in reps for me in meth}
        observed = {(r["model"], r["item"], r["boundary"], r["Q"], r["version"],
                     r["accessible"], r["representation"], r["method"]) for r in rr}
        assert len(rr) == len(expected) and observed == expected

    allitems = {phase: {x["id"]: x for x in read(ROOT / f"items/access-v2/{phase}-items.json")["items"]}
                for phase in ("discovery", "confirmatory")}
    checkgrid(base, models, allitems["discovery"], BOUNDARIES, [False, True], ["R2"], ["full"])
    baseline, state, language, questions = [], [], [], []
    baseline_vectors = {}
    for m in models:
        for b in [*BOUNDARIES, "All"]:
            no = [r for r in base if r["model"] == m and not r["accessible"] and (b == "All" or r["boundary"] == b)]
            yes = [r for r in base if r["model"] == m and r["accessible"] and (b == "All" or r["boundary"] == b)]
            vd, va = model_skeleton_vector(no, [m], "D"), model_skeleton_vector(yes, [m], "hit_t")
            baseline_vectors[m, b] = vd
            baseline.append({"model": m, "boundary": b, "endpoints_per_access": len(no),
                             "inaccessible_D": average(no, "D"), "inaccessible_target": average(no, "hit_t"),
                             "inaccessible_foil": average(no, "hit_f"), "accessible_target": average(yes, "hit_t"),
                             "inaccessible_D_ci95": interval(vd)["ci95"], "accessible_target_ci95": interval(va)["ci95"],
                             "inaccessible_valid": average(no, "valid"), "accessible_valid": average(yes, "valid")})
            if b != "All":
                for q in ("content", "plan"):
                    rr = [r for r in no if r["Q"] == q]
                    questions.append({"model": m, "boundary": b, "question": q, "endpoints": len(rr), "D": average(rr, "D")})
        st = [r for r in d if r["model"] == m and r["Q"] == "state" and not r["accessible"]]
        assert len(st) == len({(r['item'], r['boundary'], r['version']) for r in st}) == 768
        lookup = {(r["item"], r["boundary"], r["version"]): r["state_correct"] for r in st}
        no = [r for r in base if r["model"] == m and not r["accessible"]]
        eligible = [r for r in no if lookup[r["item"], r["boundary"], r["version"]]]
        state.append({"model": m, "state_endpoints": len(st), "inaccessible_state_accuracy": average(st, "state_correct"),
                      "eligible_role_endpoints": len(eligible), "conditional_D": average(eligible, "D")})
        for lang in ("zh", "ja", "es"):
            tr = [r for r in d if r["model"] == m and r["Q"] == "translate" and r["lang"] == lang]
            rr = [r for r in no if r["boundary"] == "Understand" and r["lang"] == lang]
            assert len(tr) == 64 and len(rr) == 128
            language.append({"model": m, "language": lang, "translation_endpoints": len(tr),
                             "both_canary_translation": average(tr, "U2"), "capability_threshold": spec["capability_gate"],
                             "passes_diagnostic_threshold": average(tr, "U2") >= spec["capability_gate"],
                             "inaccessible_role_endpoints": len(rr), "inaccessible_D": average(rr, "D")})
    baseline_ref = read(ROOT / "paper/arr/discovery-baseline-data.json")["rows"]
    for ref in baseline_ref:
        rr = next(x for x in baseline if (x["model"], x["boundary"]) == (ref["model"], ref["boundary"]))
        assert abs(rr["inaccessible_D"] - ref["estimate"]) < 1e-12
    aggregate = []
    for b in BOUNDARIES:
        for access in (False, True):
            rr = [r for r in base if r["boundary"] == b and r["accessible"] == access]
            field = "hit_t" if access else "D"
            aggregate.append({"boundary": b, "accessible": access, "metric": field,
                              **interval(model_skeleton_vector(rr, models, field))})

    e3 = [r for r in d if role(r) and r["model"] in methods and r["item"] in lock["subsets"]["E3"]]
    method_cells, cost = [], []
    for m in methods:
        for b in BOUNDARIES:
            cells = {}
            for method in METHODS:
                mm, rep = ("full", "R3") if method == "prose" else (method, "R2")
                rr = [r for r in e3 if r["model"] == m and r["boundary"] == b and r["method"] == mm and r["representation"] == rep]
                checkgrid(rr, [m], lock["subsets"]["E3"], [b], [False, True], [rep], [mm])
                no, yes = [r for r in rr if not r["accessible"]], [r for r in rr if r["accessible"]]
                cell = {"model": m, "boundary": b, "method": method, "endpoints_per_access": len(no),
                        "inaccessible_D": average(no, "D"), "accessible_target": average(yes, "hit_t"),
                        "accessible_refusals": sum(r["score"]["R"] for r in yes), "accessible_invalid": sum(1-r["valid"] for r in yes)}
                method_cells.append(cell)
                cells[method] = cell
            for method in METHODS[1:]:
                cost.append({"model": m, "boundary": b, "method": method,
                             "forbidden_D_reduction": cells["full"]["inaccessible_D"]-cells[method]["inaccessible_D"],
                             "accessible_target_delta": cells[method]["accessible_target"]-cells["full"]["accessible_target"]})
    for ref in six["descriptive_estimates"]:
        field = "accessible_target" if ref["accessible"] else "inaccessible_D"
        est = statistics.mean(x[field] for x in method_cells if x["boundary"] == ref["boundary"] and x["method"] == ref["method"])
        assert abs(est-ref["estimate"]) < 1e-12

    e2 = [r for r in d if role(r) and r["item"] in lock["subsets"]["E2"] and not r["accessible"] and r["method"] == "full"]
    checkgrid(e2, models, lock["subsets"]["E2"], BOUNDARIES, [False], ["R1", "R2", "R3"], ["full"])
    representation = []
    cohorts = [(m, [m]) for m in models] + [("four_core", core), ("additional_five", [m for m in models if m not in core]), ("nine_models", models)]
    for label, mm in cohorts:
        for b in BOUNDARIES:
            rr = [r for r in e2 if r["model"] in mm and r["boundary"] == b]
            for rep in ("R1", "R3"):
                z = interval(paired_delta(rr, mm, "D", lambda r: r["representation"] == rep, lambda r: r["representation"] == "R2"))
                representation.append({"cohort": label, "models": mm, "boundary": b, "contrast": rep+"-minus-R2", **z})
                if label == "nine_models":
                    ref = next(x for x in frozen["exploratory_paired_contrasts"] if x["contrast"] == f"E2 {rep}-minus-R2 {b}")
                    assert z == {k: ref[k] for k in z}

    # A deterministic string diagnostic of the first self-filter step, not a new semantic label.
    filter_steps, examples = [], []
    for m in methods:
        p = scorepaths[m, "discovery"].parents[2] / f"responses/discovery/{m}/responses.jsonl"
        assert sha(p) == audit["models"][m]["discovery"]["responses_sha256"]
        source_sha[str(p.relative_to(ROOT))] = sha(p)
        wanted = {r["prompt_id"]: r for r in e3 if r["model"] == m and r["method"] == "self_filter" and r["accessible"]}
        raw = {r["prompt_id"]: r for r in map(json.loads, p.read_text().splitlines()) if r["prompt_id"] in wanted}
        assert len(raw) == len(wanted) == 768
        for b in BOUNDARIES:
            rr = [r for r in wanted.values() if r["boundary"] == b]
            shell_only = [r for r in rr if raw[r["prompt_id"]]["text"].strip() == public_shell(allitems["discovery"][r["item"]], b)]
            filter_steps.append({"model": m, "boundary": b, "accessible_role_endpoints": len(rr),
                                 "stage1_exact_public_shell_only": len(shell_only),
                                 "stage1_complete": sum(raw[r["prompt_id"]]["status"] == "complete" for r in rr),
                                 "stage2_target_hit": average(rr, "hit_t"),
                                 "note": "Exact-string match only; duplicated question-specific stage1 calls retained. Not human or semantic certification."})
            if m == "qwen38_27b" and b in ("Understand", "Receive") and shell_only:
                r = sorted(shell_only, key=lambda x: x["prompt_id"])[0]
                item = allitems["discovery"][r["item"]]
                examples.append({"selection": "First prompt_id among exact-shell-only accessible E3 examples; illustrative, not random",
                                 "model": m, "prompt_id": r["prompt_id"], "accessible": True,
                                 "gold_content": item["langs"][item["lang"]][r["version"]]["gold"][0],
                                 "stage1": raw[r["prompt_id"]]["text"], "stage2": r["text"],
                                 "stage1_source": str(p.relative_to(ROOT)), "stage2_source": str(scorepaths[m, "discovery"].relative_to(ROOT))})

    # Lexical-block sensitivity retains the observed mean and changes only the resampling unit.
    lexical = {}
    for phase, items in allitems.items():
        def pairid(item):
            lang = item["lang"]
            return lang + ":" + "|".join(item["langs"][lang][v][k] for v in ("A", "B") for k in ("OBJECT", "PLACE"))
        lexical[phase] = {i: pairid(item) for i, item in items.items()}
        counts = collections.Counter(lexical[phase].values())
        assert len(counts) == 12 and set(counts.values()) == {8}
    assert set(lexical["discovery"].values()) == set(lexical["confirmatory"].values())
    sensitivity = []

    def cluster(label, phase, values):
        groups = collections.defaultdict(list)
        for i, value in values.items():
            groups[lexical[phase][i]].append(value)
        clustered = interval({k: statistics.mean(v) for k, v in groups.items()})
        normal = interval(values)
        assert abs(clustered["estimate"]-normal["estimate"]) < 1e-12
        sensitivity.append({"metric": label, "phase": phase, "estimate": normal["estimate"],
                            "scene_ci95": normal["ci95"], "scene_count": len(values),
                            "lexical_block_ci95": clustered["ci95"], "lexical_blocks": len(groups),
                            "scope": "Post-hoc descriptive 12-block bootstrap; not a replacement confirmatory test"})

    for b in BOUNDARIES:
        no = [r for r in base if r["boundary"] == b and not r["accessible"]]
        cluster("nine_model_baseline_D_"+b, "discovery", model_skeleton_vector(no, models, "D"))
        no = [r for r in c if role(r) and r["boundary"] == b and not r["accessible"] and r["method"] == "full" and r["representation"] == "R2"]
        cluster("four_core_H1_D_"+b, "confirmatory", model_skeleton_vector(no, core, "D"))
    for access in (False, True):
        rr = [r for r in c if role(r) and r["method"] in ("full", "view") and r["accessible"] == access and r["representation"] == "R2"]
        left, right, field = ("view", "full", "hit_t") if access else ("full", "view", "D")
        cluster("four_core_accessible_view_minus_full" if access else "four_core_full_minus_view_D", "confirmatory",
                paired_delta(rr, core, field, lambda r: r["method"] == left, lambda r: r["method"] == right))
    rr = [r for r in c if r["Q"] == "awareness" and not r["accessible"] and r["boundary"] != "Hear" and r["method"] in ("view", "hard")]
    cluster("four_core_partial_retention_view_minus_hard", "confirmatory",
            paired_delta(rr, core, "awareness_correct", lambda r: r["method"] == "view", lambda r: r["method"] == "hard"))
    transfer = []
    for m in core:
        for b in [*BOUNDARIES, "All"]:
            no = [r for r in c if role(r) and r["method"] == "full" and not r["accessible"] and r["model"] == m and (b == "All" or r["boundary"] == b)]
            disc = statistics.mean(baseline_vectors[m, b].values())
            transfer.append({"model": m, "boundary": b, "discovery_D": disc, "confirmatory_D": average(no, "D"),
                             "confirmatory_minus_discovery": average(no, "D")-disc,
                             "caution": "Different names/personas/context together; not a causal character-name effect or unseen-vocabulary test"})

    report = {"created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Verified nine-model snapshot; additional analyses are post-hoc descriptive diagnostics",
              "completed_models": models, "pending_models": audit["pending_main_models"],
              "actual_records": audit["total_actual_records"], "planned_actual_records": 220088,
              "scored_endpoints_including_pilot": audit["total_scored_endpoints_including_pilot"],
              "analyzed_endpoints_excluding_pilot": len(rows), "human_labels": 0,
              "frozen_lock_sha256": sha(lock_path), "verification_sha256": sha(audit_path),
              "source_sha256": source_sha, "bootstrap_replicates": boot.B, "bootstrap_seed": boot.seed,
              "interpretation": ["D is target-minus-foil net use, not a universal error rate.",
                                 "Scene bootstrap is conditional on fixed model cohort, scorer and lexical inventory.",
                                 "Discovery and confirmation use the same 12 lexical pairs; 8 active strings per language.",
                                 "Language and lexical pair are not crossed; language differences are not causal language effects.",
                                 "Original frozen confirmatory results retained verbatim. Additional intervals have no new p-values."],
              "baseline_by_model": baseline, "baseline_by_boundary": aggregate, "baseline_question_diagnostics": questions,
              "independent_state_diagnostics": state, "language_diagnostics": language,
              "method_by_model": method_cells, "method_cost_by_model": cost, "method_six_aggregate": six["descriptive_estimates"],
              "representation_diagnostics": representation, "self_filter_stage1_exact_match": filter_steps,
              "illustrative_examples": examples, "lexical_block_sensitivity": sensitivity, "split_shift": transfer,
              "frozen_exploratory_contrasts": frozen["exploratory_paired_contrasts"],
              "frozen_confirmatory": frozen["confirmatory"], "four_core_descriptive": paper["descriptive_estimates"],
              "checks": {"frozen_input_and_code_sha_match": True, "all_source_sha_match": True,
                         "no_duplicate_scored_ids": True, "balanced_baseline_E2_E3_grids": True,
                         "all_36_published_baseline_cells_match": True, "all_40_six_method_cells_match": True,
                         "all_8_nine_model_E2_contrasts_match": True, "original_confirmation_unchanged": True}}
    OUT.mkdir(parents=True, exist_ok=True)
    save(OUT / "analysis.json", report)
    for name, rr in [("baseline", baseline), ("method-by-model", method_cells), ("method-costs", cost),
                     ("representations", representation), ("languages", language), ("state-probes", state),
                     ("lexical-sensitivity", sensitivity), ("self-filter-step1", filter_steps), ("split-shift", transfer), ("question-diagnostics", questions)]:
        csvsave(OUT / (name+".csv"), rr)
    render(report)
    save(OUT / "manifest.json", {"generator": str(Path(__file__).relative_to(ROOT)), "generator_sha256": sha(Path(__file__)),
                                "generated_files": {str(p.relative_to(ROOT)): sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "manifest.json"},
                                "checks": report["checks"]})
    print(json.dumps({"saved": str(OUT), "baseline_rows": len(baseline), "method_rows": len(method_cells),
                      "representation_rows": len(representation), "sensitivity": sensitivity,
                      "filter_step_diagnostics": [x for x in filter_steps if x["model"] == "qwen38_27b"]}, ensure_ascii=False, indent=2))


def render(r):
    esc = lambda x: html.escape(str(x))
    pct = lambda x: f"{100*x:.2f}"
    ci = lambda xs: f"[{pct(xs[0])}, {pct(xs[1])}]"
    def table(headers, rows):
        return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
    sections = []
    sections.append('<h2>1 · 核心判断</h2><p>现有证据支持：显式标出角色没有访问权，并不能稳定阻止模型使用眼前的内容。独立状态判断通常正确，角色回答仍会越界。输入投影能够降低这一影响；相比整条删除，它还保留可观察的事件发生信息。这个结论依赖正确的访问元数据和有限的自动评分定义。</p>')
    sections.append('<div class="note">全部数值采用百分数或百分点刻度。D = 目标使用率 − 干扰使用率；它不是通用错误率。新增分解与聚类区间均为事后描述性诊断，未添加确证检验，也未改写冻结分析。</div>')
    h = r['frozen_confirmatory']
    sections.append(table(['四核心独立确认 · 96 场景', '估计', '95% 场景 bootstrap 区间'],
                          [(b+' 不可访问 D', pct(v['estimate']), ci(v['ci95'])) for b,v in h['H1_components'].items()]+
                          [('独立状态判断正确时的 D',pct(h['H2']['estimate']),ci(h['H2']['ci95']))]+
                          [(name,pct(h['H3_components'][key]['estimate']),ci(h['H3_components'][key]['ci95'])) for name,key in
                           [('投影相对 full 的泄漏降低','forbidden_leak_reduction'),('投影的可访问信息使用变化','accessible_target_use_delta'),('投影相对删除的部分事件保留提升','partial_event_retention_improvement')]]))
    sections.append('<p>三个预先冻结的确证家族经 Holm 校正均为 p = 0.001499。检验对象是四核心的平均效应，不意味着每个模型、每个边界都独立通过。H2 的状态判断来自另一次调用，不能解释为同一段回答已经明确承认无权访问，更不能据此推断内部心理状态。</p>')
    baseline = {(x['model'],x['boundary']):x for x in r['baseline_by_model']}
    sections.append('<h2>2 · 九模型差异：低泄漏是否只是不会回答？</h2>')
    sections.append(table(['模型','听不到 D','听到但不懂 D','看不到内容 D','收不到内容 D','平均 D','可访问目标使用'],
                          [(NAMES[m],*[pct(baseline[m,b]['inaccessible_D']) for b in BOUNDARIES],pct(baseline[m,'All']['inaccessible_D']),pct(baseline[m,'All']['accessible_target'])) for m in r['completed_models']]))
    sections.append('<p>共同基线为 full/R2、96 场景、两问题和两个内容版本；每模型每边界每访问状态 384 个端点。所有不可访问基线的干扰命中均为 0，因此此表中 D 恰好等于目标命中率，但其他方法中两者未必相等。</p><p>Gemma 31B 平均 D 仅 2.86，可访问使用率为 87.63%；其中 Understand 的可访问使用率 98.44%、不可访问 D 0.52，支持其确实有较强的边界遵守能力。但 See 的可访问使用仅 66.93%，低泄漏仍须与可用性一起解释。Qwen 27B 的平均 D 为 15.10，可访问使用为 84.31%，也不能只凭泄漏把它排成整体最佳。不同系列和版本的差异不能归因于参数量本身。</p>')
    sections.append(table(['九模型 · 独立状态探测','不可访问状态判断正确率','正确探测对应的角色 D','条件角色端点'],
                          [(NAMES[x['model']],pct(x['inaccessible_state_accuracy']),pct(x['conditional_D']),x['eligible_role_endpoints']) for x in r['independent_state_diagnostics']]))
    sections.append('<p>九模型中的六个模型在不可访问状态探测上为 100%，但多个模型仍有很高的角色泄漏；Phi-4 为 76.56%，说明状态读取错误也可能构成它的部分问题。不能把所有模型的失败归结为单一机制。</p>')
    sections.append('<h2>3 · 方法比较：自我过滤的低泄漏有时来自过度删除</h2><p>下表为完整六模型 E3，48 个匹配场景，每模型每边界每状态 192 个端点。每格为「不可访问 D / 可访问目标使用」。</p>')
    agg = {(x['boundary'],x['method'],x['accessible']):x for x in r['method_six_aggregate']}
    sections.append(table(['方法',*BOUNDARIES],[(m,*[pct(agg[b,m,False]['estimate'])+' / '+pct(agg[b,m,True]['estimate']) for b in BOUNDARIES]) for m in METHODS]))
    sections.append('<p>view 将不可访问 D 降低 31.08–57.12 点。self_filter 在 Understand、Receive 的可访问使用分别损失 28.56、41.15 点；因此低泄漏本身不足以证明方法有效。view 相应损失为 3.73、3.30 点，代价较小，但区间为 [−5.73, −1.73]、[−5.30, −1.56]。四核心确认集的总体非劣结果不能直接外推为六模型所有边界都无损。</p>')
    mc = {(x['model'],x['boundary'],x['method']):x for x in r['method_by_model']}
    sections.append(table(['模型','Understand · full','view','self_filter','Receive · full','view','self_filter'],
                          [(NAMES[m],*[pct(mc[m,b,me]['accessible_target']) for b in ('Understand','Receive') for me in ('full','view','self_filter')]) for m in r['method_six_aggregate'][0]['models']]))
    sections.append('<p>view 的 Understand 代价在 Nemotron、Qwen 27B 上较明显；Receive 的平均下降主要受 Qwen 27B 影响。hard 与 view 的抑制能力接近；支持 view 的关键额外证据是保留观察到的事件，而不是比 hard 少泄漏。</p>')
    for x in r['illustrative_examples']:
        sections.append('<details open><summary>'+esc(NAMES[x['model']]+' · '+x['prompt_id'])+'</summary><p>此例本来允许访问；目标内容：'+esc(x['gold_content'])+'</p><blockquote>第一步：'+esc(x['stage1'])+'<br>第二步：'+esc(x['stage2'])+'</blockquote><p>按 prompt_id 排序选取的例证，不是随机样本或人工标签。</p></details>')
    steps = [x for x in r['self_filter_stage1_exact_match'] if x['model']=='qwen38_27b' and x['boundary'] in ('Understand','Receive')]
    sections.append(table(['Qwen 27B 第一阶段诊断','可访问角色端点','仅输出已知事件壳（完全字串匹配）','第二阶段目标命中'],[(x['boundary'],x['accessible_role_endpoints'],x['stage1_exact_public_shell_only'],pct(x['stage2_target_hit'])) for x in steps]))
    sections.append('<p>完全字串匹配是保守的机械诊断；未匹配的回复不等于保留了内容。两问题的第一步是分别生成的记录，计数不是独立场景数。所有这些例证来自已验证原始回复，没有重跑推理。</p>')
    sections.append('<h2>4 · 文字规则的效果依赖模型范围</h2><p>E2 固定 24 场景；下表为 R3（布尔值加文字规则）− R2（布尔值）的不可访问 D，负值代表改善。</p>')
    reps = {(x['cohort'],x['boundary'],x['contrast']):x for x in r['representation_diagnostics']}
    sections.append(table(['范围',*BOUNDARIES],[(label,*[pct(reps[key,b,'R3-minus-R2']['estimate'])+' '+ci(reps[key,b,'R3-minus-R2']['ci95']) for b in BOUNDARIES]) for key,label in [('four_core','原四核心'),('additional_five','新增五模型'),('nine_models','全部已完成九模型')]]))
    sections.append('<p>Understand 在原四核心为 +5.73 点，九模型为 −5.56 点；新增五模型的变化推动了方向翻转。这是模型范围敏感性，不能说九模型推翻了原四模型数据，也不能继续泛称“文字规则对理解边界没有帮助”。完整六模型 E3 又使用 48 场景，不能与此表无条件拼接。文字规则有帮助但不稳定，仍不等于结构化过滤。</p>')
    sections.append('<h2>5 · 语言、词配对复用与区间解释</h2><p>每种语言有 32 场景，但只有 4 组目标／干扰词配对、8 个不同的活跃句子。两套 96 场景使用相同的 12 组配对。确认集更换了角色、人物设定和场景，并非未见过词汇的测试；语言与词配对没有完全交叉，因此不适合声称日语、中文或西语本身导致差异。</p>')
    lang = {(x['model'],x['language']):x for x in r['language_diagnostics']}
    sections.append(table(['模型','中文翻译双词命中','日语翻译双词命中','西语翻译双词命中'],[(NAMES[m],*[pct(lang[m,l]['both_canary_translation']) for l in ('zh','ja','es')]) for m in r['completed_models']]))
    sections.append('<p>冻结能力诊断阈值为 85%。Qwen 27B、Qwen 9B、GLM、Nemotron 的日语单元低于阈值。主结果保留所有端点，未通过事后删掉低能力单元抬高效应。翻译命中是受词表评分影响的任务能力指标，不是人类流利度判断。</p>')
    sections.append(table(['事后敏感性 · 四核心确认','估计','原 96 场景区间','12 词配对块区间'],[(x['metric'].replace('four_core_',''),pct(x['estimate']),ci(x['scene_ci95']),ci(x['lexical_block_ci95'])) for x in r['lexical_block_sensitivity'] if x['phase']=='confirmatory']))
    sections.append('<p>额外聚类把同一词配对的 8 场景先合并，再重抽 12 个块，保留点估计。这不是新的确证 p 值；块数很少，也不能替代更广的词汇采样。两类区间均以已测模型和自动评分器为条件，不包含任意模型、任意语言或评分错误的不确定性。</p>')
    sections.append('<h2>6 · 延迟、选择与跨场景变化</h2><p>四核心的 Understand 在保留原上下文的 0、2、4 轮中性对话后，D 为 42.58、52.73、58.20；四轮相对即时增加 15.63 点，描述区间 [8.59, 22.66]。其他三个边界没有一致的单调增加证据。这支持内容影响在后续对话中持续，不是移除上下文后的隐式记忆机制。</p><p>四核心固定位置选择的 A−B 差在 full 中为 49.22–63.28 点，在 view 中为 0–0.78 点。内容影响扩展到文字选择，但实验没有执行现实动作。Gemma 31B 的平均 D 从发现集 2.86 增至确认集 11.07，表明低泄漏也随场景改变；不能将这种变化单独归因于角色名字。</p>')
    sections.append('<h2>7 · 论文应怎样收束</h2><ul><li>主线：访问元数据的可读性与角色回答的边界遵守分离；比较同时衡量泄漏抑制、允许内容使用和事件保留。</li><li>方法贡献：利用正确元数据进行内容投影并保留可观察事件壳。无需声称上下文过滤是全新思想。</li><li>九模型发现、六模型方法、四核心确认各自标明模型和场景范围；仍缺 Mistral、Seed，不能写十一模型全部完成。</li><li>避免“所有模型都不会遵守”“文字规则完全无效”“过滤完全无损”“100% 事件觉察意味着普遍可靠”等过强表述。</li><li>最需要补的是实际人类语义核对、语言母语/流利使用者审核及词形可猜性数据。当前真实人工标签仍为零；AI 代理标签仅覆盖四核心指定抽样范围。</li></ul>')
    sections.append('<h2>复现与审计</h2><p>本报告直接读取已验证分数和原始两阶段回复；重新核对冻结输入、代码与源文件 SHA，验证全部 36 个已刊基线单元、40 个六模型方法单元、8 个九模型 E2 对比，并确认原四核心确证结果原样保留。3000 个 pilot 端点未混入分析。15 条既有截断回复保留原零值规则；没有缺失或重复生成记录。</p><p>原始统计、来源 SHA、逐模型 CSV 和选择规则位于同目录 analysis.json、manifest.json 与 CSV 文件。生成程序：tools/analyze_access_v2_snapshot.py。原 ARR 稿、冻结科学代码、盲标包和 AI 标签均未改动。</p>')
    doc = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OverComprehension v2 · 已完成结果分析</title><style>body{margin:0;background:#f3f5f8;color:#182537;font:16px/1.75 system-ui,-apple-system,sans-serif}main{max-width:1160px;margin:36px auto;background:white;padding:42px 48px;border:1px solid #dce3eb;border-radius:14px}h1{font-size:30px;line-height:1.3;margin:0 0 14px}h2{font-size:22px;margin:40px 0 14px;border-top:1px solid #dce3eb;padding-top:24px}p{max-width:1000px}.meta{color:#52667d}.cards{display:flex;gap:18px;flex-wrap:wrap;margin:25px 0}.card{background:#eff5fb;padding:14px 22px;border-radius:9px;min-width:150px}.card b{display:block;font-size:27px;color:#15597e}.note{padding:15px 20px;background:#fff5df;border-left:4px solid #ad7422}.scroll{overflow-x:auto;margin:20px 0}table{border-collapse:collapse;min-width:680px;width:100%;font-size:14px;font-variant-numeric:tabular-nums}th{text-align:left;background:#eaf1f7;white-space:nowrap}th,td{padding:10px 12px;border-bottom:1px solid #dce3eb}tr:nth-child(even){background:#f7f9fc}td:first-child{font-weight:600}details{background:#f5f8fa;padding:14px 20px;margin:14px 0;overflow-wrap:anywhere}summary{cursor:pointer;font-weight:600}blockquote{border-left:3px solid #6d91ab;margin:12px 0;padding:5px 18px}li{margin:8px 0}footer{font-size:13px;color:#52667d;margin-top:35px}@media(max-width:700px){main{margin:0;padding:25px 18px;border:0;border-radius:0}h1{font-size:25px}.card{min-width:110px}}@media print{body{background:white}main{margin:0;border:0;padding:0}details{break-inside:avoid}}</style></head><body><main><h1>OverComprehension v2 · 现有结果分析</h1><p class="meta">九模型已验证快照 · 完整六模型方法比较 · 四核心独立确认<br>生成时间 '+esc(r['created_at_utc'])+' · 额外分析均标为描述性</p><div class="cards"><div class="card"><b>9 / 11</b>模型完成</div><div class="card"><b>207,416</b>已完成生成调用</div><div class="card"><b>94.24%</b>计划生成完成率</div><div class="card"><b>0</b>真实人工标签</div></div>'+''.join(sections)+'<footer>本报告分析已完成结果，不代表新一次 GPU 状态检查。后续推理仍仅允许空闲的物理 GPU 5。</footer></main></body></html>'
    (OUT / "report.html").write_text(doc)


if __name__ == "__main__":
    main()
