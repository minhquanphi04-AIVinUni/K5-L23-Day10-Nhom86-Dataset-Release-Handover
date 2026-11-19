#!/usr/bin/env python3
"""Dựng lô v2 (detection) từ delivery v1 + errors.json. Chỉ thư viện chuẩn; KHÔNG sửa delivery/.

python tools/build_v2.py runs/r86007 [--fixed-hash-ok 000000005586,...]

--fixed-hash-ok: ảnh wrong_hash đã được MỞ XEM và còn nguyên (chỉ manifest sai) -> ở lại v2.
Ảnh wrong_hash không có trong danh sách này sẽ vào rework.
"""
import argparse, csv, hashlib, json, shutil
from collections import Counter
from pathlib import Path

DET_REWORK = {"missing_image", "invalid_class", "bbox_out_of_bounds", "duplicate_box", "class_swap", "bbox_drift", "missing_box"}
PAN_ONLY = {"invalid_category_id", "thing_overlap", "category_swap", "instance_merge"}

ap = argparse.ArgumentParser()
ap.add_argument("run")
ap.add_argument("--fixed-hash-ok", default="")
a = ap.parse_args()
run = Path(a.run); d = run / "delivery"
ok_hash = {x for x in a.fixed_hash_ok.split(",") if x}
rid = json.loads((d / "release.json").read_text(encoding="utf-8"))["release_id"]
man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))["items"]
meta = {m["image"]: dict(m) for m in json.loads((d / "metadata.json").read_text(encoding="utf-8"))["items"]}
jobs = {r["job_id"]: r for r in csv.DictReader((d / "jobs.csv").open(encoding="utf-8"))}
names = [l.split(" ", 1)[1].strip() for l in (d / "classes.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
errors = json.loads((run / "errors.json").read_text(encoding="utf-8"))["errors"]

types = {}
for e in errors:
    types.setdefault(e["target"], []).append(e["type"])
rework = {}
for img, ts in types.items():
    if img not in man:
        continue
    if any(t in DET_REWORK for t in ts) or ("wrong_hash" in ts and img not in ok_hash):
        rework[img] = ts[0]
keep = [n for n in sorted(man) if n not in rework]

# scene_leak: đưa cả cảnh về split chiếm đa số (hoà -> train)
for e in errors:
    if e["type"] == "scene_leak":
        ims = [m for m in meta.values() if m["scene_id"] == e["target"]]
        c = Counter(m["split"] for m in ims)
        best = max(c.values()); win = "train" if c.get("train", 0) == best else sorted(k for k, v in c.items() if v == best)[0]
        for m in ims:
            m["split"] = win

v2 = run / "handover" / f"{rid}_v2"
if v2.exists():
    shutil.rmtree(v2)
(v2 / "images").mkdir(parents=True); (v2 / "labels").mkdir()
for n in keep:
    shutil.copy2(d / man[n]["image"], v2 / "images" / f"{n}.jpg")
    shutil.copy2(d / man[n]["label"], v2 / "labels" / f"{n}.txt")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
with (v2 / "manifest.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["file", "sha256"])
    for sub in ("images", "labels"):
        for p in sorted((v2 / sub).iterdir()):
            w.writerow([f"{sub}/{p.name}", sha(p)])

cnt = Counter()
for n in keep:
    for l in (v2 / "labels" / f"{n}.txt").read_text(encoding="utf-8").splitlines():
        if l.strip():
            cnt[names[int(float(l.split()[0]))]] += 1
with (v2 / "label_summary.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["class", "count"])
    for k in sorted(cnt):
        w.writerow([k, cnt[k]])
    w.writerow(["TOTAL", sum(cnt.values())])

with (v2 / "truyvet.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["image", "scene_id", "split", "job_id", "annotator", "reviewer", "guideline"])
    for n in keep:
        m = meta[n]; j = jobs[m["job_id"]]
        w.writerow([n, m["scene_id"], m["split"], m["job_id"], j["annotator"], j["reviewer"], j["guideline"]])

with (v2 / "rework_queue.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["image", "type", "annotator", "reviewer", "action"])
    for n, t in sorted(rework.items()):
        j = jobs[meta[n]["job_id"]]
        w.writerow([n, t, j["annotator"], j["reviewer"], "gan lai nhan detection"])

# README.txt
err_targets = {e["target"] for e in errors}
by = Counter()
for t in err_targets:
    by[None] += 1
gl = {}
for jid, j in jobs.items():
    gl.setdefault(j["guideline"], []).append(jid)
gl_txt = ", ".join(f"{g} ({v[0]}-{v[-1]})" for g, v in sorted(gl.items()))
pan_only = sorted(t for t, ts in types.items() if t in man and t not in rework and all(x in PAN_ONLY for x in ts))
fix_hash = sorted(t for t in ok_hash if t in keep)
fix_gl = sorted(t for t, ts in types.items() if "guideline_mismatch" in ts)
fix_sc = sorted(t for t, ts in types.items() if "scene_leak" in ts)
rate = len(err_targets) / len(man)
who = sorted({(jobs[meta[n]["job_id"]]["annotator"], jobs[meta[n]["job_id"]]["reviewer"]) for n in rework})
txt = f"""Release: {rid}_v2
Parent: {rid}
Số ảnh: {len(keep)}
Số nhãn: {sum(cnt.values())}
Guideline: {gl_txt}
QC v1: {len(err_targets)}/{len(man)} = {rate*100:.1f}%
Kết luận v1: Hold — {rate*100:.1f}% ảnh/cảnh lỗi, vượt ngưỡng 2% (Day 7) nên không Release.
Kết luận v2: Release — tách {len(rework)} ảnh lỗi nhãn detection sang rework_queue, sửa hash/guideline/split, còn {len(keep)} ảnh không còn lỗi detection đã biết.
Ghi chú: wrong_hash {', '.join(fix_hash) or '-'}: đã mở ảnh kiểm, ảnh còn nguyên, chỉ manifest sai nên ghi hash mới. guideline_mismatch {', '.join(fix_gl) or '-'}: guideline lấy theo job trong jobs.csv. scene_leak {', '.join(fix_sc) or '-'}: đưa cả cảnh về một split. Ảnh rework ({len(rework)}) giao lại cho các cặp gán/kiểm {', '.join(a_+'/'+r_ for a_, r_ in who)}. Ảnh chỉ lỗi panoptic ở lại v2, báo team panoptic: {', '.join(pan_only) or '-'}.
"""
(v2 / "README.txt").write_text(txt, encoding="utf-8")
print(txt)
print("rework:", dict(sorted(rework.items())))
