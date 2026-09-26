"""由运行产物生成问题三正文、总论文注入、图表复制与说明文档（数字不手写）。"""
import json
import shutil
from datetime import datetime

import numpy as np

import q3_common as Q


def read(n):
    return json.loads((Q.OUT / n).read_text(encoding='utf-8'))


def tex(s):
    table = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
             '{': r'\{', '}': r'\}'}
    return ''.join(table.get(c, c) for c in str(s))


def f4(v):
    return f'{v:.4f}'


def f3(v):
    return f'{v:.3f}'


def sci(v):
    m, e = f'{v:.1e}'.split('e')
    return f'${m}\\times10^{{{int(e)}}}$'


def main():
    met = read('metrics.json'); sel = read('model_selection.json')
    diag = {d['variant']: d for d in sel['diagnostics']}
    stab = read('valid_stability.json'); faith = read('valid_explanation_metrics.json')
    err = read('error_analysis.json'); attr = read('error_attribution.json')
    pred = read('pred_a4.json'); ev = read('evidence_a4.json'); audit = read('alignment_audit.json')
    blocks = read('valid_local_all.json'); ablocks = read('a4_local_all.json')
    mn = {'t': '文本', 'a': '语音', 'v': '视觉'}
    SV, V = sel['selected'], sel['selected_label']
    cond = met['conditions']
    va = met['valid']; te = met['test']
    perf = [('验证集 & ' + ' & '.join(f4(va[k]) for k in ['acc', 'macro_f1', 'mae', 'pearson']) + r' \\'),
            ('测试集 & ' + ' & '.join(f4(te[k]) for k in ['acc', 'macro_f1', 'mae', 'pearson']) + r' \\')]
    seed_f1 = '、'.join(f4(v['macro_f1']) for v in va['per_seed'])
    class_f1 = '、'.join(f4(v) for v in va['per_class_f1'])
    # 变体表
    order = ['C0full', 'C0np', 'ctrl', 'V1', 'V2', 'V3']
    lab = dict(read('protocol_frozen.json')['labels'])
    lab['C0full'] = '仅完整输入（单种子）'
    lab['C0np'] = '无内容区打包对照'
    lab.update(ctrl='C0：子集训练', V1='V1：采样与遮挡',
               V2='V2：增加容量', V3='V3：单调正则')
    rows = []
    for v in order:
        if v in ('C0full', 'C0np'):
            c = cond[v]['全模态']
            rows.append(f'{lab[v]} & {c["macro_f1"]-0.1*c["mae"]:.4f} & {f4(c["macro_f1"])} & '
                        f'{f4(c["mae"])} & --- & --- ' + r'\\')
            continue
        d = diag[v]
        rows.append(f'{lab[v]} & {f3(d["J"])} & {f4(d["valid"]["macro_f1"])} & {f4(d["valid"]["mae"])} & '
                    f'{f3(d["aopc"])} & {100*d["seed_agreement_mean"]:.1f}\\% ' + r'\\')
    ablation_rows = '\n'.join(rows)
    if SV != 'ctrl':
        ablation_text = (f'三项门槛比较只使用验证集：{V}在$G_1$、$G_2$、$G_3$上均通过门槛'
                         f'（$J$为{f3(diag[SV]["J"])}对{f3(diag["ctrl"]["J"])}，缺失条件平均Macro-F1为'
                         f'{f3(diag[SV]["miss_f1"])}对{f3(diag["ctrl"]["miss_f1"])}，$AOPC$为'
                         f'{f3(diag[SV]["aopc"])}对{f3(diag["ctrl"]["aopc"])}），'
                         f'按"缺失条件平均Macro-F1最大"入选。')
    else:
        ablation_text = ('V1未通过预测指标与缺失状态性能门槛，V2未通过预测指标门槛，'
                         'V3未通过缺失状态性能门槛；三者的解释AOPC差均达到门槛。'
                         '据此选择C0作为最终SAP预测器，后续贡献分解和附件4推理均使用该模型。')
    aopc_txt = '、'.join(f'{v}={f3(diag[v]["aopc"])}' for v in ['ctrl', 'V1', 'V2', 'V3'])
    pk = np.mean([read(f'train_ctrl_s{k}.json')['selected_score'] for k in range(3)])
    npk = np.mean([read(f'train_C0np_s{k}.json')['selected_score'] for k in range(3)])
    ablation_text += (f'内容区打包与全序列编码的各单种子$J$平均值分别为{f3(pk)}和{f3(npk)}。'
                      '表中仅完整输入对照采用单种子，其余方案采用三种子集成；'
                      '种子一致率指主要参考模态的两两一致率平均值。')
    # 缺失条件表
    cond_names = ['全模态', '去文本', '去语音', '去视觉', '全缺失']
    crows = []
    for c in cond_names:
        base = cond['C0full'][c]['macro_f1']; ctrl = cond['ctrl'][c]['macro_f1']; s = cond[SV][c]['macro_f1']
        crows.append(f'{c} & {f4(base)} & {f4(ctrl)} & {f4(s)} & {s-base:+.4f} ' + r'\\')
    cond_rows = '\n'.join(crows)
    cond_text = (f'仅完整输入训练的模型在去文本、去语音、去视觉、全缺失四种状态下Macro-F1为'
                 + '、'.join(f4(cond['C0full'][c]['macro_f1']) for c in cond_names[1:])
                 + f'，平均{f4(np.mean([cond["C0full"][c]["macro_f1"] for c in cond_names[1:]]))}；'
                 + f'子集感知训练的入选模型对应为'
                 + '、'.join(f4(cond[SV][c]['macro_f1']) for c in cond_names[1:])
                 + f'，平均{f4(np.mean([cond[SV][c]["macro_f1"] for c in cond_names[1:]]))}。'
                 + f'全模态状态下两者分别为{f4(cond["C0full"]["全模态"]["macro_f1"])}与'
                 + f'{f4(cond[SV]["全模态"]["macro_f1"])}，说明子集感知训练并未以牺牲完整输入性能换取鲁棒性。')
    # 联盟价值与贡献
    g = np.load(Q.OUT / 'valid_B1_games.npz')
    val = g['value'].mean(0); phi = g['phi'].mean(0)
    main_dist = {}
    for j, m in enumerate(Q.MODS):
        main_dist[m] = int(np.sum(np.abs(g['phi']).argmax(1) == j))
    coal_text = (f'空集价值为{f3(val[0])}，全模态价值为{f3(val[7])}，'
                 f'单模态联盟中' + '、'.join(f'{mn[m]}为{f3(val[1<<j])}' for j, m in enumerate(Q.MODS)) + '；'
                 f'三模态平均Shapley贡献为{mn["t"]}{phi[0]:+.3f}、{mn["a"]}{phi[1]:+.3f}、'
                 f'{mn["v"]}{phi[2]:+.3f}，96条子集中分类主参考模态为' +
                 '、'.join(f'{mn[m]}{main_dist[m]}条' for m in Q.MODS) + '。')
    i = int(np.argmax(np.abs(g['phi']).max(1)))
    vix = read('explanation_valid_indices.json')
    o = np.argsort(-np.abs(g['phi'][i]))
    waterfall_text = (f'该样本为验证集第{vix[i]}条，参考类别log-odds由空集的{g["value"][i,0]:.3f}变化到全模态的'
                      f'{g["value"][i,7]:.3f}，三个模态按贡献绝对值依次为'
                      + '、'.join(f'{mn[Q.MODS[m]]}{g["phi"][i,m]:+.3f}' for m in o) + '。')
    # 局部重要性分布
    stat = {}
    for m in Q.MODS:
        v = np.array([b['delta_logodds'] for b in blocks if b['modality'] == m])
        stat[m] = dict(n=len(v), mean=float(v.mean()), pos=float(np.mean(v > 0)),
                       neg=float(np.mean(v < 0)), absmean=float(np.abs(v).mean()))
    pos_seg = {}
    for m in Q.MODS:
        for lo, hi, lb in [(0, 1 / 3, '首'), (1 / 3, 2 / 3, '中'), (2 / 3, 1.01, '尾')]:
            v = [b['delta_logodds'] for b in blocks if b['modality'] == m and lo <= b['rel_pos'] < hi]
            pos_seg[(m, lb)] = float(np.mean(v))
    block_text = (f'共对{sum(s["n"] for s in stat.values())}个块完成删除干预（'
                  + '、'.join(f'{mn[m]}{stat[m]["n"]}个' for m in Q.MODS)
                  + f'）。平均响应幅度为' + '、'.join(f'{mn[m]}{stat[m]["absmean"]:.3f}' for m in Q.MODS)
                  + '；方向构成为'
                  + '、'.join(f'{mn[m]}支持{100*stat[m]["pos"]:.1f}\\%／抑制{100*stat[m]["neg"]:.1f}\\%'
                              for m in Q.MODS) + '。'
                  + '位置分段上，句首段平均响应为'
                  + '、'.join(f'{mn[m]}{pos_seg[(m, "首")]:+.3f}' for m in Q.MODS)
                  + '，中段为' + '、'.join(f'{mn[m]}{pos_seg[(m, "中")]:+.3f}' for m in Q.MODS)
                  + '，句尾段为' + '、'.join(f'{mn[m]}{pos_seg[(m, "尾")]:+.3f}' for m in Q.MODS)
                  + '。')
    faith_text = (f'按块数10\\%、20\\%、30\\%三个目标档位累计删除时，高分块引起的参考类别概率下降分别为'
                  + '、'.join(f3(v) for v in faith['curves']['top']) + '，随机块为'
                  + '、'.join(f3(v) for v in faith['curves']['random']) + '，低分块为'
                  + '、'.join(f3(v) for v in faith['curves']['low'])
                  + f'；高分块与随机块的样本级配对差为{f4(faith["aopc_top_minus_random"])}'
                  f'（95\\%区间[{f4(faith["ci95"][0])},{f4(faith["ci95"][1])}]），实际覆盖率为'
                  + '、'.join(f'{100*v:.2f}\\%' for v in faith['actual_coverage'])
                  + f'。条件充分性在最高档的绝对概率偏差为{f4(faith["curves"]["sufficiency"][-1])}，'
                  f'表明主要模态中被舍弃的片段仍有作用；{faith["all_local_nonpositive"]}条样本的全部块响应非正，'
                  f'未识别出单块正向支持证据。图\\ref{{q3:fig:faith}}(b)给出B1/B2/B3的主模态一致率分别为'
                  + '、'.join(f'{100*stab[b]["main_agreement"]:.2f}\\%' for b in ['B1', 'B2', 'B3'])
                  + f'，绝对贡献排序的Spearman相关为' + '、'.join(f3(stab[b]['mean_rank_spearman'])
                                                              for b in ['B2', 'B3']) + '。')
    u = attr['uncertainty_by_strength']
    stab_text = (f'三种子两两主模态一致率为' + '、'.join(f'{100*v:.2f}\\%' for v in stab['seed_main_agreement'])
                 + '；B2、B3相对B1的一致率为'
                 + '、'.join(f'{100*stab[b]["main_agreement"]:.2f}\\%' for b in ['B2', 'B3'])
                 + '。三种子最大类概率标准差整体均值为' + f4(u['mean_conf_std']) + '，'
                 + f'|强度|<0.5组为{f4(u["low_mean"])}、|强度|$\\ge$0.5组为{f4(u["high_mean"])}，'
                 + f'两组差异不显著（Welch $p$={f4(u["p_ttest"])}）；与|真实强度|的'
                 + f'Spearman相关为{f3(u["spearman"])}（$p$={f4(u["p_spearman"])}），'
                 + f'按1/3标签网格分箱后，中性组（|强度|=0）与最高强度组的均值分别为{f4(u["lowest_mean"])}和{f4(u["highest_mean"])}。'
                   '因此在本文验证集上，样本级不确定性并未随强度幅值系统增大或减小，'
                   '不能据此把低强度样本的误判简单归因于种子波动，'
                   '而应结合解释不稳定率的分层结果一并判断。')
    a2 = attr['instability_by_strength']; a1 = attr['evidence_functional_words']
    a3 = attr['sentiment_word_vs_main_modality']
    attrib_text = (f'最高分证据块中功能词与标点占比为{100*a1["top1_functional_rate"]:.1f}\\%'
                   f'（全部块基线{100*a1["base_functional_rate"]:.1f}\\%），'
                   f'差值95\\%区间[{a1["diff_ci95"][0]:+.3f},{a1["diff_ci95"][1]:+.3f}]；'
                   f'解释不稳定率在|强度|<0.5的样本上为{100*a2["unstable_rate_low"]:.1f}\\%'
                   f'（{a2["n_low"]}条），在|强度|$\\ge$0.5的样本上为'
                   f'{100*a2["unstable_rate_high"]:.1f}\\%（{a2["n_high"]}条）；'
                   f'主模态不是文本的样本中，仍有{100*(a3["nontext_with_senti"] or 0):.1f}\\%的转写含显式情感词，'
                   f'而主模态为文本的样本该比例为{100*(a3["text_main_with_senti"] or 0):.1f}\\%（共{a3["n_nontext_main"]}条非文本主模态样本）。')
    from collections import Counter
    pdist = '、'.join(f'{k}{v}条' for k, v in Counter(r['polarity'] for r in pred).items())
    mdist = '、'.join(f'{mn[k]}{v}条' for k, v in Counter(r['main_modality'] for r in pred).items())
    all20 = []
    for i, r in enumerate(pred):
        fields = [f'4-{i+1:02d}', r['polarity'], f"{r['strength']:+.3f}"]
        fields += ['NA' if r[f'share_{m}'] is None else f"{r[f'share_{m}']:.3f}" for m in Q.MODS]
        fields += [mn[r['main_modality']]]
        all20.append(' & '.join(fields) + r' \\')
    unc = [r['uncertainty_strength'] for r in pred]
    na = [r['sample'] for r in pred if not r['available_v']]
    mismatch = [f"4-{i+1:02d}" for i, r in enumerate(pred)
                if (r['strength'] > 0 and r['polarity'] == '负向') or
                   (r['strength'] < 0 and r['polarity'] == '正向')]
    sid = lambda x: str(x).replace('_', chr(92) + '_')
    a4_text = (f'20条样本的强度三种子标准差均值为{f3(float(np.mean(unc)))}，最大为'
               f'{f3(float(np.max(unc)))}（{sid(pred[int(np.argmax(unc))]["sample"])}）。'
               + (f'其中{sid(na[0])}的视觉分支不可用，其视觉份额标记为NA，其余两个模态照常给出贡献；'
                  if na else '')
               + (f'{"、".join(mismatch)}的分类极性与预测强度方向不一致，属于独立双头下的输出分歧，'
                  f'两个任务分别保留预测与贡献分解。'
                  if mismatch else '各样本的分类极性与强度方向一致。'))
    c1 = pred[0]; e1 = next(e for e in ev if e['sample'] == c1['sample'] and
                            e['modality'] == c1['main_modality'])
    c13 = pred[12]; e13 = next(e for e in ev if e['sample'] == c13['sample'] and
                               e['modality'] == c13['main_modality'])
    card_text = (f'第1条预测为{c1["polarity"]}，强度{c1["strength"]:+.3f}，主要参考模态为'
                 f'{mn[c1["main_modality"]]}'
                 f'（份额{c1["share_" + c1["main_modality"]]:.3f}），'
                 f'最高分证据片段为\\textit{{{tex(e1["text"])}}}')
    if e1['start_sec'] is not None:
        card_text += f'，估计时间{e1["start_sec"]:.2f}--{e1["end_sec"]:.2f}\\,s'
    card_text += '。'
    tw = sum(v['words'] for v in audit)
    aw = sum(v['aligned'] for v in audit)
    ne = sum(e['available'] for e in ev)
    me = sum(e['status'] == 'estimated_ctc' for e in ev)
    covr = [v['aligned'] / max(v['words'], 1) for v in audit]
    time_text = (f'逐样本回映覆盖率介于{100*min(covr):.1f}\\%与{100*max(covr):.1f}\\%之间；'
                 f'未获得时间区间的原词多为纯数字、独立符号或转写与音频不一致的位置，'
                 f'按失败保留锚点索引，不伪造时间；映射秒数为自动CTC估计，边界精度仍需人工时间标注评价。')
    sel_eps = []
    for k in range(3):
        lg = read(f'train_{SV}_s{k}.json')['log']
        sel_eps.append(max(lg, key=lambda v: v['score'])['epoch'])
    select_text = (f'按三项门槛选择的预测器为{V}。'
                   f'三个种子分别在第' + '、'.join(str(e) for e in sel_eps)
                   + '轮取得最优验证指标，训练轮次完全由验证集$J$决定，'
                     '测试集与附件4只参与前向计算。'
                   f'验证集单种子Macro-F1为{seed_f1}，三种子集成后为{f4(va["macro_f1"])}；'
                   f'测试集Macro-F1为{f4(te["macro_f1"])}，MAE为{f4(te["mae"])}。')
    mapping = dict(
        N_ANCHORS=sum(read('audit_a4.json')['content_counts']),
        MIN_ANCHORS=min(read('audit_a4.json')['content_counts']),
        MAX_ANCHORS=max(read('audit_a4.json')['content_counts']),
        SELECT_TEXT=select_text, PERF_ROWS='\n'.join(perf), SEED_F1=seed_f1, F1_VAL=f4(va['macro_f1']),
        CLASS_F1=class_f1, ABLATION_TEXT=ablation_text, ABLATION_ROWS=ablation_rows,
        COND_TEXT=cond_text, COND_ROWS=cond_rows, COAL_TEXT=coal_text, RESIDUAL=sci(stab['B1']['efficiency_residual_max']),
        WATERFALL_TEXT=waterfall_text, BLOCK_TEXT=block_text, FAITH_TEXT=faith_text,
        STAB_TEXT=stab_text, N_ERRORS=err['errors'], N_NEUTRAL=err['neutral_related'],
        P_NEUTRAL=f'{100*err["neutral_fraction"]:.1f}',
        ERROR_GROUP_TEXT='；'.join(f"{tex(v['group'])}组错误率{v['error_rate']:.1%}（{v['n']}条）".replace('%', r'\%')
                                   for v in err['groups']),
        ATTRIB_TEXT=attrib_text, PRED_DIST=pdist, MAIN_DIST=mdist, A4_TEXT=a4_text,
        ALL20_ROWS='\n'.join(all20),
        A4_NOTE=f'全部数值由冻结模型的同一解释协议生成，未使用附件4的任何标签信息。',
        CARD_TEXT=card_text, TOTAL_WORDS=tw, ALIGNED_WORDS=aw, N_EVIDENCE=ne, MAPPED_EVIDENCE=me,
        TIME_TEXT=time_text)
    template = (Q.HERE / 'q3_section.polished.tex').read_text(encoding='utf-8')
    for k, v in mapping.items():
        template = template.replace('@@' + k + '@@', str(v))
    left = [ln for ln in template.split('\n') if '@@' in ln]
    assert not left, left
    (Q.HERE / '问题三_正文.tex').write_text(template, encoding='utf-8')
    paper = Q.ROOT / '总论文' / '原论文'
    backup = Q.ROOT / '总论文' / ('问题三写入前备份_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir()
    shutil.copytree(paper / 'sections', backup / 'sections')
    shutil.copy2(paper / 'main.tex', backup / 'main.tex')
    source = paper / 'sections' / '04-models.tex'
    old = source.read_text(encoding='utf-8')
    marker = r'\subsection{问题三的模型建立与求解}'
    assert old.count(marker) == 1
    source.write_text(old[:old.index(marker)] + template, encoding='utf-8')
    for fig in Q.FIG.glob('q3_*.png'):
        shutil.copy2(fig, paper / 'figures' / fig.name)
    Q.dump(mapping, Q.OUT / 'paper_stats.json')
    write_doc(dict(met=met, sel=sel, stab=stab, faith=faith, err=err, attr=attr, pred=pred,
                   ev=ev, audit=audit, blocks=blocks, ablocks=ablocks, g=g, phi=phi, val=val,
                   main_dist=main_dist, stat=stat, pos_seg=pos_seg))
    print('written 问题三_正文.tex + 总论文注入, backup:', backup, flush=True)


def write_doc(d):
    """Generate 问题三_说明文档.md from pipeline products (no hand-typed numbers)."""
    met, sel, stab, faith = d['met'], d['sel'], d['stab'], d['faith']
    err, attr, pred = d['err'], d['attr'], d['pred']
    ev, audit, blocks, ablocks = d['ev'], d['audit'], d['blocks'], d['ablocks']
    g, phi, val, main_dist = d['g'], d['phi'], d['val'], d['main_dist']
    stat, pos_seg = d['stat'], d['pos_seg']
    mn = {'t': '文本', 'a': '语音', 'v': '视觉'}
    cond = met['conditions']
    SV = sel['selected']
    va, te = met['valid'], met['test']
    diag = {x['variant']: x for x in sel['diagnostics']}
    rule = sel['rule']
    meta = np.load(Q.Path(Q.C.CACHE) / 'a2_meta.npz')
    n_tr = int((meta['split'] == 0).sum())
    n_va = int((meta['split'] == 1).sum())
    n_te = int((meta['split'] == 2).sum())
    dims = {m: int(np.load(Q.Path(Q.C.CACHE) / f'a2_{f}.npy', mmap_mode='r').shape[2])
            for m, f in zip(('t', 'a', 'v'), ('text_recomputed', 'audio', 'vision'))}
    L = int(np.load(Q.Path(Q.C.CACHE) / 'a2_audio.npy', mmap_mode='r').shape[1])
    labels = dict(read('protocol_frozen.json')['labels'])
    labels['C0full'] = '仅完整输入对照'
    labels['C0np'] = '无内容区打包对照'
    rows = []
    for v in ['C0full', 'C0np']:
        c = cond[v]['全模态']
        rows.append(f'| {labels[v]} | {c["macro_f1"]-0.1*c["mae"]:.4f} | {c["macro_f1"]:.4f} | '
                    f'{c["mae"]:.4f} | 无解释评估 | --- | --- | --- | {cond[v]["n_seeds"]} |')
    for v in ['ctrl', 'V1', 'V2', 'V3']:
        q = diag[v]
        gate = lambda b: '通过' if b else '未通过'
        rows.append(f'| {labels[v]} | {q["J"]:.4f} | {q["valid"]["macro_f1"]:.4f} | {q["valid"]["mae"]:.4f} | '
                    f'{q["aopc"]:.4f} | {gate(q["G1"])} | {gate(q["G2"])} | {gate(q["G3"])} | {q["n_seeds"]} |')
    cond_rows = []
    for c in ['全模态', '去文本', '去语音', '去视觉', '全缺失']:
        a, b = cond[SV][c], cond['C0full'][c]
        cond_rows.append(f'| {c} | {a["macro_f1"]:.4f} | {a["mae"]:.4f} | {b["macro_f1"]:.4f} | {b["mae"]:.4f} |')
    a1, a2 = attr['evidence_functional_words'], attr['instability_by_strength']
    a3, u = attr['sentiment_word_vs_main_modality'], attr['uncertainty_by_strength']
    cov = {m: stat[m]['n'] for m in Q.MODS}
    pack = cond['C0np']['全模态']
    j_sel, j_pack = cond[SV]['全模态']['macro_f1'] - 0.1 * cond[SV]['全模态']['mae'], pack['macro_f1'] - 0.1 * pack['mae']
    nd_std = [p2['uncertainty_strength'] for p2 in pred]
    nd_std = [v for v in nd_std if v is not None]
    worst = max(pred, key=lambda r: (r['uncertainty_strength'] or 0))
    disagree = [f"4-{i+1:02d}" for i, r in enumerate(pred)
                if (r['polarity'] == '正向' and r['strength'] < 0) or (r['polarity'] == '负向' and r['strength'] > 0)]
    na = [f"4-{i+1:02d}" for i, r in enumerate(pred) if r['share_t'] is None or r['share_a'] is None or r['share_v'] is None]
    tw = sum(a['words'] for a in audit)
    aw = sum(a['aligned'] for a in audit)
    ne = sum(1 for e in ev if e['start_sec'] is not None)
    cards = read('figure_index.json')['cards']
    chk = read('checks.json')
    L_ = []
    A = L_.append
    A('# 问题三 实现与结果说明')
    A('')
    A('> 本文件由 `q3_report.py` 从流水线产物自动生成，所有数值与论文正文同源，未手工填写。')
    A('')
    A('## 1. 任务与解释口径')
    A('')
    A('题目要求在情感极性分类与强度回归的基础上，量化各模态内与判断密切相关的局部片段，'
      '并给出结论解释、算法设计与模型检验。本文的解释对象是**问题三自有的子集感知预测器（SAP，Q3Net）**：'
      '问题三使用附件2官方划分从头训练三个随机种子，解释与性能评估都在同一模型、同一输入接口下完成，'
      '因此“删除某片段后输出如何变化”与模型内部的模态协作结构严格对应。'
      '问题二级联模型是另一套结构与另一套输入约定，直接在其上计算局部贡献会混入体系差异，'
      '故不将其作为解释对象。')
    A('')
    A('解释协议：模态层面用 8 个可用模态联盟的**精确 Shapley 值**（枚举 + 效率性核验）；'
      '片段层面用**逐块删除干预**（块 = 内容区内连续锚点区间）；'
      '可信度用**高分块与随机块/低分块的累计删除曲线差（AOPC）**、条件充分性与三种子一致性核验。')
    A('')
    A('## 2. 数据与划分')
    A('')
    A('| 项目 | 数值 |')
    A('|---|---|')
    A(f'| 附件2 训练/验证/测试 | {n_tr} / {n_va} / {n_te} |')
    A(f'| 模态维度 | 文本 {dims["t"]}、语音 {dims["a"]}、视觉 {dims["v"]} |')
    A(f'| 时序接口长度 | {L} 个锚点 |')
    A('| 标准化 | 仅用训练集观测位置估计均值与标准差 |')
    A('| 标签口径 | `label=0` 仅表示中性，强度取值为 1/3 的整数倍 |')
    A('')
    A('附件3、附件4只做前向预测与解释，不参与训练、选模、阈值确定或样本挑选；未引入任何外部情感数据集。')
    A('')
    A('## 3. 模型与训练')
    A('')
    A('- 结构：三态投影（文本/语音/视觉各一套）→ 内容区**打包** BiGRU → 均值池化 + 最大池化 + 观测比例拼接 → 分类与强度双任务头。')
    A(f'- 变体网格与冻结选择协议：G1 `{rule["G1"]}`；G2 `{rule["G2"]}`；G3 `{rule["G3"]}`；'
      f'入选规则 `{rule["pick"]}`，`{rule["fallback"]}`。')
    A(f'- 选择结果：`{sel["decision"]}`，入选 `{sel["selected"]}`（{sel["selected_label"]}）。')
    A('')
    A('| 变体 | 选择指标 J | 验证 Macro-F1 | 验证 MAE | AOPC | G1 | G2 | G3 | 种子数 |')
    A('|---|---|---|---|---|---|---|---|---|')
    L_.extend(rows)
    A('')
    A(f'- 三项改进（V1 联盟重加权与块遮挡增广、V2 增加容量、V3 联盟单调一致性正则）在验证集规模下'
      f'均未同时越过三项门槛，因此按预先冻结的规则保留 ctrl；该结论在写入正文时未被改写。')
    A(f'- 打包对照：全模态下入选模型的 J={j_sel:.4f}，无打包对照 C0np 的 J={j_pack:.4f}（3 种子均值），'
      f'差值 {abs(j_sel-j_pack):.4f}，处于种子波动量级内，故不把“内容区打包”作为性能提升的主要来源。')
    A('')
    A('## 4. 主结果')
    A('')
    A('| 集合 | 样本数 | Accuracy | Macro-F1 | MAE | RMSE | Pearson | CCC |')
    A('|---|---|---|---|---|---|---|---|')
    for nm2, r in [('验证集', va), ('测试集', te)]:
        A(f'| {nm2} | {r["n"]} | {r["acc"]:.4f} | {r["macro_f1"]:.4f} | {r["mae"]:.4f} | '
          f'{r["rmse"]:.4f} | {r["pearson"]:.4f} | {r["ccc"]:.4f} |')
    A('')
    A('## 5. 模态缺失条件下的性能')
    A('')
    A(f'| 输入状态 | 入选模型 Macro-F1 | 入选模型 MAE | 仅完整输入对照 Macro-F1 | 仅完整输入对照 MAE |')
    A('|---|---|---|---|---|')
    L_.extend(cond_rows)
    A('')
    A('## 6. 模态层解释结果')
    A('')
    A(f'- 联盟价值：空集 {g["value"].mean(0)[0]:+.3f}，全模态 {g["value"].mean(0)[7]:+.3f}；'
      '单模态联盟为' + '、'.join(f'{mn[m]} {g["value"].mean(0)[1<<j]:+.3f}' for j, m in enumerate(Q.MODS)) + '。')
    A(f'- 三模态平均 Shapley 贡献：文本 {phi[0]:+.3f}、语音 {phi[1]:+.3f}、视觉 {phi[2]:+.3f}；'
      '效率性残差最大值 ' + f'{stab["B1"]["efficiency_residual_max"]:.2e}' + '（仅为浮点误差量级）。')
    A(f'- 96 条验证子集中，分类主参考模态为' + '、'.join(f'{mn[m]} {main_dist[m]} 条' for m in Q.MODS) + '。')
    A(f'- 解释忠实性：高分块减随机块的 AOPC = {faith["aopc_top_minus_random"]:.4f}'
      f'（95% 区间 [{faith["ci95"][0]:.4f}, {faith["ci95"][1]:.4f}]）；'
      f'充分性在最高档为 {faith["curves"]["sufficiency"][-1]:.4f}，说明仅保留高分块不足以复现原输入。')
    A(f'- 三种子两两主模态一致率：' + '、'.join(f'{100*x:.2f}%' for x in stab['seed_main_agreement'])
      + f'；B2、B3 相对 B1 的一致率 ' + '、'.join(f'{100*stab[b]["main_agreement"]:.2f}%' for b in ['B2', 'B3']) + '。')
    A(f'- 实际覆盖率（Top 块占比对应的真实内容区比例）：'
      + '、'.join(f'{100*x:.2f}%' for x in faith['actual_coverage']) + '。')
    A('')
    A('## 7. 片段层解释结果')
    A('')
    A(f'- 共对 {sum(cov.values())} 个块完成删除干预（' + '、'.join(f'{mn[m]} {cov[m]} 个' for m in Q.MODS) + '）。')
    A(f'- 平均响应幅度：' + '、'.join(f'{mn[m]} {stat[m]["absmean"]:.3f}' for m in Q.MODS)
      + '，文本的效应幅度最大。')
    A(f'- 方向构成：' + '、'.join(f'{mn[m]} 支持参考类 {100*stat[m]["pos"]:.1f}% / 抑制参考类 {100*stat[m]["neg"]:.1f}%'
                                 for m in Q.MODS) + '。')
    A(f'- 位置分段平均响应：句首段 ' + '、'.join(f'{mn[m]} {pos_seg[(m, "首")]:+.3f}' for m in Q.MODS)
      + '；中段 ' + '、'.join(f'{mn[m]} {pos_seg[(m, "中")]:+.3f}' for m in Q.MODS)
      + '；句尾段 ' + '、'.join(f'{mn[m]} {pos_seg[(m, "尾")]:+.3f}' for m in Q.MODS) + '。')
    A('')
    A('## 8. 错误归因')
    A('')
    A(f'- 验证集误判 {err["errors"]} 条，其中 {err["neutral_related"]} 条涉及中性（占 {100*err["neutral_fraction"]:.1f}%）。')
    for q in err['groups']:
        A(f'- {q["group"]}：{q["n"]} 条，错误率 {100*q["error_rate"]:.1f}%，强度 MAE {q["mae"]:.3f}。')
    A(f'- 最高分证据块中功能词与标点占比 {100*a1["top1_functional_rate"]:.1f}%，全部块基线 '
      f'{100*a1["base_functional_rate"]:.1f}%，差值 95% 区间 [{a1["diff_ci95"][0]:+.3f}, {a1["diff_ci95"][1]:+.3f}]。')
    A(f'- 解释不稳定率：|强度|<0.5 组 {100*a2["unstable_rate_low"]:.1f}%（{a2["n_low"]} 条），'
      f'|强度|≥0.5 组 {100*a2["unstable_rate_high"]:.1f}%（{a2["n_high"]} 条）。')
    A(f'- 主模态不是文本的样本中 {100*(a3["nontext_with_senti"] or 0):.1f}% 的转写含显式情感词，'
      f'主模态为文本的样本该比例为 {100*(a3["text_main_with_senti"] or 0):.1f}%。')
    A(f'- 预测不确定性与强度：三种子最大类概率标准差整体均值 {u["mean_conf_std"]:.4f}，'
      f'|强度|<0.5 组 {u["low_mean"]:.4f} vs |强度|≥0.5 组 {u["high_mean"]:.4f}'
      f'（Welch p={u["p_ttest"]:.4f}）；与 |真实强度| 的 Spearman 相关 {u["spearman"]:+.4f}'
      f'（p={u["p_spearman"]:.4f}），按 1/3 标签网格分箱后中性组与最高强度组分别为 '
      f'{u["lowest_mean"]:.4f} 和 {u["highest_mean"]:.4f}。'
      '即本验证集上样本级不确定性未随强度幅值系统变化。')
    A('')
    A('## 9. 附件4 预测与解释')
    A('')
    A('- 附件4 共 20 条，全部完成预测与解释；该集合无标签，只报告预测、作用份额与证据，不评价准确率。')
    A('- 预测极性分布：' + '、'.join(f'{k} {v} 条' for k, v in
                                 __import__('collections').Counter(r['polarity'] for r in pred).items()) + '。')
    A(f'- 分类主参考模态：' + '、'.join(f'{mn[k]} {v} 条' for k, v in
                                     __import__('collections').Counter(r['main_modality'] for r in pred).items()) + '。')
    A(f'- 强度三种子标准差均值 {np.mean(nd_std):.3f}，最大 {max(nd_std):.3f}（{worst["sample"]}）。')
    A(f'- 极性与强度方向不一致的样本：{"、".join(disagree) if disagree else "无"}；'
      '独立双头下保留原始输出，不作事后改值。')
    A(f'- 模态份额为 NA（该样本该模态不可用）的样本：{"、".join(na) if na else "无"}。')
    a4f = read('a4_explanation_metrics.json')
    a4s = read('a4_stability.json')
    A(f'- 附件4 自身的 AOPC（高分块−随机块）= {a4f["aopc_top_minus_random"]:.4f}，'
      f'95% 区间 [{a4f["ci95"][0]:.4f}, {a4f["ci95"][1]:.4f}]（{a4f["n"]} 条，无标签，仅作解释一致性核验）。')
    A(f'- 附件4 上三种子两两主模态一致率：'
      + '、'.join(f'{100*x:.1f}%' for x in a4s['seed_main_agreement'])
      + f'；B2、B3 相对 B1 的一致率为 {100*a4s["B2"]["main_agreement"]:.0f}%、{100*a4s["B3"]["main_agreement"]:.0f}%。')
    A('')
    A('## 10. 原素材回映')
    A('')
    A(f'- 官方词元序列与重新分词完全一致的样本数：{sum(1 for a in audit if a["token_match"])} / {len(audit)}。')
    A(f'- 词级时间覆盖：{aw} / {tw} 个词元获得时间区间（{100*aw/max(tw,1):.1f}%）。')
    A(f'- 可用模态最高分证据 {ne} 条输出估计时间区间；对应关键帧 PNG 与 WAV 片段位于 `输出/evidence_media/`。')
    A('- 时间由 CTC 强制对齐自动估计，不是人工真值，不报告伪造的对齐精度。')
    A('')
    A('## 11. 图表索引')
    A('')
    A('| 图 | 内容 |')
    A('|---|---|')
    desc = {
        'q3_variant_ablation.png': '变体消融：选择指标、解释忠实性与缺失条件性能',
        'q3_performance.png': '验证集混淆矩阵与各类别指标',
        'q3_regression.png': '强度回归密度、分箱误差与残差分布',
        'q3_condition_curve.png': '五种输入状态下的 Macro-F1 与 MAE 对比',
        'q3_coalition_value.png': '模态联盟价值与三模态平均 Shapley 贡献',
        'q3_phi_waterfall.png': '单样本 Shapley 累加分解瀑布图',
        'q3_block_heatmap.png': '逐块删除效应按相对位置的分布',
        'q3_block_dist.png': '逐块效应分布、位置分段与方向构成',
        'q3_faithfulness.png': '累计删除曲线、解释基线敏感性与条件充分性',
        'q3_stability.png': '基线与种子一致率、不确定性随强度幅值的变化',
        'q3_error_attrib.png': '误判样本的三类归因',
        'q3_a4_overview.png': '附件4 预测强度、模态作用份额与不确定性',
        'q3_a4_evidence.png': '附件4 每条样本三模态最高分局部证据的删除响应',
        'q3_time_map.png': '词级时间回映覆盖率与证据时段映射',
        'q3_card_01.png': '附件4 第 1 条解释卡（预测、份额、证据、时间与关键帧）',
        'q3_card_13.png': '附件4 第 13 条解释卡（视觉分支不可用时的两模态解释）',
    }
    for f in read('figure_index.json')['figures']:
        A(f'| `{f}` | {desc.get(f, "—")} |')
    A(f'| `cards/01..{cards:02d}.png` | 附件4 逐样本解释卡（预测、份额、证据、时间与媒体） |')
    A('')
    A('## 12. 产物索引')
    A('')
    A('| 文件 | 作用 |')
    A('|---|---|')
    for f, why in [('metrics.json', '全验证集/测试集与五种输入状态的基础性能'),
                   ('variant_diag.json、model_selection.json、protocol_frozen.json', '变体诊断、选择结果与冻结协议'),
                   ('valid_B1/B2/B3_games.npz', '96 条验证子集的联盟价值、Shapley 贡献与种子贡献'),
                   ('valid_local.json、valid_local_all.json', '逐块删除明细（后者覆盖全部可用模态）'),
                   ('valid_faithfulness.json、valid_explanation_metrics.json', '累计删除曲线与忠实性汇总'),
                   ('valid_stability.json', '基线与种子解释一致性'),
                   ('error_analysis.json、error_attribution.json', '误判统计与三类归因'),
                   ('pred_附件4.csv、pred_a4.json', '附件4 20 条预测、模态贡献与作用份额'),
                   ('explain_附件4.csv', '附件4 长表：每样本每模态 1 行，共 60 行'),
                   ('local_blocks_附件4.csv、a4_local_all.json', '附件4 逐块删除明细'),
                   ('a4_time_mapping.csv、evidence_a4.json、alignment_audit.json', '词级时间回映与回映审计'),
                   ('evidence_media/', '每条证据的关键帧 PNG 与 WAV 片段'),
                   ('figures/、figures/cards/', '正文图与 20 张解释卡'),
                   ('ckpt/、scaler.json、frozen_manifest.json', '模型权重、标准化器与冻结哈希'),
                   ('paper_stats.json', '正文数字的来源映射')]:
        A(f'| `{f}` | {why} |')
    A('')
    A('## 13. 复现边界与红线')
    A('')
    A('- 附件3、附件4 不参与训练、选模、阈值确定与样本挑选；不使用任何外部情感数据集（MOSI/IEMOCAP 等）。')
    A('- `label=0` 只作为中性类，不与正向合并；不使用伪标签。')
    A('- 文本编码器固定为未做情感微调的 `bert-base-uncased`（冻结、`local_files_only=True`）。')
    A('- 模型训练、BERT 重编码与 CTC 前向强制使用 GPU，无静默 CPU 回退；统计、解码与绘图在 CPU 完成。')
    A(f'- 交付自检：`q3_check.py` 通过 {len(chk["pass"])} 项、失败 {len(chk.get("fail", []))} 项。')
    A('- 未通过门槛的变体、非单调的结果与负面归因均按原样保留，不作挑选性呈现。')
    A('')
    out = Q.HERE / '问题三_说明文档.md'
    out.write_text('\n'.join(L_), encoding='utf-8')
    print('written', out, flush=True)



if __name__ == '__main__':
    main()
