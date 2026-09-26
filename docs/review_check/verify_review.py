"""Read saved outputs and reproduce selected review diagnostics without inference."""
from pathlib import Path
import ast
import json
import itertools
import zipfile

import numpy as np
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
Q2 = ROOT / "问题二实现"
Q3 = ROOT / "问题三实现"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def agreement(a, b):
    cm = np.zeros((3, 3), dtype=int)
    np.add.at(cm, (a, b), 1)
    observed = np.trace(cm) / cm.sum()
    expected = np.dot(cm.sum(0), cm.sum(1)) / cm.sum() ** 2
    return {"agreement": float(observed), "kappa": float((observed - expected) / (1 - expected)),
            "confusion": cm.tolist()}


def selected_code(path, names):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    return compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec")


result = {}
b1 = np.load(Q3 / "输出/valid_B1_games.npz")
main = np.abs(b1["phi"]).argmax(1)
result["valid_main_distribution"] = np.bincount(main, minlength=3).tolist()
result["baseline_agreement"] = {}
for baseline in ("B2", "B3"):
    other = np.load(Q3 / f"输出/valid_{baseline}_games.npz")
    result["baseline_agreement"][baseline] = agreement(main, np.abs(other["phi"]).argmax(1))
seedmain = np.abs(b1["seedphi"]).argmax(2)
result["seed_agreement"] = {
    f"{a}-{b}": agreement(seedmain[a], seedmain[b])
    for a, b in itertools.combinations(range(3), 2)
}
a1 = np.load(Q3 / "输出/a4_B1_games.npz")
a2 = np.load(Q3 / "输出/a4_B2_games.npz")
result["a4_b1_b2"] = agreement(np.abs(a1["phi"]).argmax(1), np.abs(a2["phi"]).argmax(1))
result["a4_class_reg_main_difference"] = int(np.sum(
    np.abs(a1["phi"]).argmax(1) != np.abs(a1["phir"]).argmax(1)))

ns = {"np": np}
exec(selected_code(Q2 / "q2_recon.py", {"auc_score"}), ns)
result["auc_tie_counterexample"] = ns["auc_score"]([1, 1], [0, 1])

valid = np.load(Q3 / "输出/valid_predictions.npz")
magnitude = np.abs(valid["truth"]).astype(float)
edges = [0, 1/3, 2/3, 1, 5/3, 3]
result["magnitude_bins_raw"] = [int((magnitude == 0).sum())] + [
    int(((magnitude > lo) & (magnitude <= hi)).sum()) for lo, hi in zip(edges[:-1], edges[1:])]
snapped = magnitude.copy()
for boundary in edges[1:-1]:
    snapped[np.isclose(snapped, boundary, rtol=0, atol=1e-6)] = boundary
result["magnitude_bins_tolerance"] = [int((snapped == 0).sum())] + [
    int(((snapped > lo) & (snapped <= hi)).sum()) for lo, hi in zip(edges[:-1], edges[1:])]
evaluation = read_json(Q2 / "输出/valid_eval.json")
result["length_bins_total"] = sum(row["n"] for row in evaluation["bins_content_len"])
result["valid_count"] = evaluation["n_valid"]
rows = read_json(Q2 / "输出/boot_diff.json")["split"]["test"]["tsrf_vs_bases"]
ordered = sorted(rows, key=lambda r: r["p"])
result["holm_smallest"] = {"base": ordered[0]["base"], "p": ordered[0]["p"],
                            "adjusted_p": min(1, len(rows) * ordered[0]["p"])}
result["kd_sweep"] = [{"tag": r["tag"], "J": r["sel"]}
                      for r in read_json(Q2 / "输出/kd_sweep3.json")["rows"]]

result["archives"] = {}
for path in (ROOT / "总论文/原论文").glob("*.zip"):
    with zipfile.ZipFile(path) as archive:
        tex = [n for n in archive.namelist() if n.endswith("sections/04-models.tex")]
        text = archive.read(tex[0]).decode("utf-8-sig") if tex else ""
        result["archives"][path.name] = {"bytes": path.stat().st_size,
            "contains_06170": "0.6170" in text, "contains_01068": "0.1068" in text,
            "contains_function_words": "功能词" in text,
            "python_files": sum(n.endswith(".py") for n in archive.namelist()),
            "weight_files": sum(n.endswith(".pt") for n in archive.namelist())}

pdf = pdfium.PdfDocument(str(ROOT / "总论文/原论文/main.pdf"))
result["pdf_pages"] = len(pdf)
for page in (1, 2, 5, 16, 17, 39):
    pdf[page].render(scale=1.5).to_pil().save(OUT / f"page_{page}.png")

(OUT / "evidence.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
