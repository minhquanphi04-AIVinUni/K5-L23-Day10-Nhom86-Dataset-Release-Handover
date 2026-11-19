#!/usr/bin/env python3
"""Công cụ xem ảnh của nhóm (được dùng Pillow; validator thì không).

uv run --python 3.13 --with pillow tools/review_sheets.py <delivery> <candidates.json> <out_dir>

Mỗi ứng viên -> <out_dir>/<image>.png: trái = ảnh + box detection (đỏ, ghi tên lớp),
phải = ảnh + segment panoptic (thing tô màu, ghi tên lớp). Cộng index.html và review_log.todo.csv
(verdict/note để TRỐNG: người xem ảnh tự điền, không điền hộ).
"""
import csv
import html
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

d, cand_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
pan = json.loads((d / "panoptic.json").read_text(encoding="utf-8"))
cats = {c["id"]: c for c in pan["categories"]}
id2name = {i["id"]: Path(i["file_name"]).stem for i in pan["images"]}
segs = {id2name[a["image_id"]]: a["segments_info"] for a in pan["annotations"]}
classes = {}
for line in (d / "classes.txt").read_text(encoding="utf-8").splitlines():
    if line.strip():
        i, n = line.split(" ", 1)
        classes[int(i)] = n.strip()
man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))["items"]
cands = json.loads(cand_path.read_text(encoding="utf-8"))["candidates"]
PAL = [(230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 240, 240), (240, 50, 230)]


def panel(name):
    it = man[name]
    img = Image.open(d / it["image"]).convert("RGB")
    W, H = img.size
    k = max(1, round(640 / W))
    img = img.resize((W * k, H * k))
    left = img.copy()
    dr = ImageDraw.Draw(left)
    for line in (d / it["label"]).read_text(encoding="utf-8").splitlines():
        t = line.split()
        if len(t) != 5:
            continue
        c, xc, yc, w, h = int(float(t[0])), *map(float, t[1:])
        x0, y0, x1, y1 = (xc - w / 2) * W * k, (yc - h / 2) * H * k, (xc + w / 2) * W * k, (yc + h / 2) * H * k
        dr.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=2)
        dr.text((x0 + 2, y0 + 1), classes.get(c, f"?{c}"), fill=(255, 255, 0))
    mask = Image.open(d / it["mask"]).convert("RGB").resize((W * k, H * k), Image.NEAREST)
    right = img.copy()
    px, ov = mask.load(), right.load()
    sid = {}
    for n, s in enumerate(segs.get(name, [])):
        c = cats.get(s["category_id"])
        if c and c.get("isthing"):
            sid[s["id"]] = (PAL[n % len(PAL)], s)
    for y in range(H * k):
        for x in range(W * k):
            r, g, b = px[x, y]
            e = sid.get(r + g * 256 + b * 65536)
            if e:
                o = ov[x, y]
                ov[x, y] = tuple((o[i] + e[0][i]) // 2 for i in range(3))
    dr = ImageDraw.Draw(right)
    for col, s in sid.values():
        x, y, w, h = s["bbox"]
        dr.text((x * k + 2, y * k + 1), cats[s["category_id"]]["name"] + (" (crowd)" if s.get("iscrowd") else ""), fill=(255, 255, 255))
    sheet = Image.new("RGB", (left.width * 2 + 6, left.height), (30, 30, 30))
    sheet.paste(left, (0, 0))
    sheet.paste(right, (left.width + 6, 0))
    return sheet


rows, seen = [], set()
for c in cands:
    if c["image"] not in seen:
        seen.add(c["image"])
        panel(c["image"]).save(out / f"{c['image']}.png")
    rows.append(c)
with (out / "index.html").open("w", encoding="utf-8") as f:
    f.write("<meta charset=utf-8><body style='background:#222;color:#eee;font:14px sans-serif'><h2>Ung vien: trai = detection, phai = panoptic</h2>")
    for c in rows:
        f.write(f"<h3>{c['image']} &mdash; {html.escape(c['type'])} &mdash; {html.escape(c['note'])}</h3><img src='{c['image']}.png' style='max-width:100%'>")
with (out / "review_log.todo.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["image", "type", "verdict", "note"])
    for c in rows:
        w.writerow([c["image"], c["type"], "", ""])
print(f"{len(seen)} anh -> {out}/index.html")
