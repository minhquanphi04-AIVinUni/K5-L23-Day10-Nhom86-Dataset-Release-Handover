#!/usr/bin/env python3
"""Validator nhóm 86. Chỉ đọc thư mục delivery truyền vào; chỉ thư viện chuẩn; không mạng.

python validator/validate.py <delivery> --out errors.json [--candidates candidates.json]

--out: lỗi luật (9 loại). --candidates: ứng viên lỗi gán nhãn để mở ảnh review.
"""
import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import pngutil  # noqa: E402  (đọc PNG, thư viện chuẩn)

# ---- ngưỡng (chỉnh sau khi đo trên lô sạch; ghi lý do vào REPORT.md) ----
OOB_EPS_PX = 0.5          # box tràn mép quá nửa pixel mới tính
DUP_CENTER_PX = 3.0       # duplicate_box: lệch tâm tối đa
DUP_SIZE_PX = 2.0         # duplicate_box: lệch kích thước tối đa
AREA_TOL = 0.01           # thing_overlap: area khai > pixel thật quá 1%
CAND_IOU_MATCH = 0.1      # ghép box detection <-> segment (bbox_drift)
INSIDE_OK = 0.80          # >=80% pixel segment nằm trong box cùng lớp = khớp
IOU_OK = 0.60             # và IoU bbox >= 0.6
MERGE_FRAC = 0.25         # instance_merge: >=25% pixel trong mỗi box của >=2 box
SWAP_IOU = 0.5            # class_swap: box khác lớp phủ đúng vị trí
CAND_MISSING_MIN_AREA = 0.02  # segment thing >2% diện tích ảnh mà không có box


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def read_labels(p: Path):
    rows = []
    if not p.is_file():
        return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        t = line.split()
        if len(t) == 5:
            try:
                rows.append((int(float(t[0])), *map(float, t[1:])))
            except ValueError:
                pass
    return rows


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    u = aw * ah + bw * bh - inter
    return inter / u if u > 0 else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("delivery")
    ap.add_argument("--out", required=True)
    ap.add_argument("--candidates")
    a = ap.parse_args()
    d = Path(a.delivery)

    manifest = load_json(d / "manifest.json")["items"]
    meta = load_json(d / "metadata.json")["items"]
    pan = load_json(d / "panoptic.json")
    classes = {}
    for line in (d / "classes.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            i, name = line.split(" ", 1)
            classes[int(i)] = name.strip()
    cats = {c["id"]: c for c in pan["categories"]}
    jobs = {}
    with (d / "jobs.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            jobs[r["job_id"]] = r["guideline"]

    size = {Path(i["file_name"]).stem: (i["width"], i["height"]) for i in pan["images"]}
    id2name = {i["id"]: Path(i["file_name"]).stem for i in pan["images"]}
    segs = {id2name[an["image_id"]]: an["segments_info"] for an in pan["annotations"]}

    errors = []  # (type, target)

    def add(t, target):
        errors.append((t, target))

    flagged = set()  # mỗi ảnh tối đa một lỗi

    def add_img(t, name):
        if name not in flagged:
            flagged.add(name)
            add(t, name)

    # --- file ---
    for name, it in manifest.items():
        img = d / it["image"]
        if not img.is_file():
            add_img("missing_image", name)
            continue
        if sha256(img) != it["image_sha256"]:
            add_img("wrong_hash", name)

    # --- metadata ---
    scene_splits = defaultdict(set)
    for m in meta:
        scene_splits[m["scene_id"]].add(m["split"])
        if jobs.get(m["job_id"]) != m["guideline_version"]:
            add_img("guideline_mismatch", m["image"])
    for sc, sp in scene_splits.items():
        if len(sp) > 1:
            add("scene_leak", sc)

    # --- detection ---
    boxes = {}  # name -> list[(cid, x, y, w, h) pixel top-left]
    for name, it in manifest.items():
        W, H = size.get(name, (None, None))
        rows = read_labels(d / it["label"])
        px = []
        bad_class = oob = False
        for cid, xc, yc, w, h in rows:
            if cid not in classes:
                bad_class = True
                continue
            if W:
                x0, y0 = (xc - w / 2) * W, (yc - h / 2) * H
                x1, y1 = (xc + w / 2) * W, (yc + h / 2) * H
                if x0 < -OOB_EPS_PX or y0 < -OOB_EPS_PX or x1 > W + OOB_EPS_PX or y1 > H + OOB_EPS_PX:
                    oob = True
                px.append((cid, x0, y0, w * W, h * H))
        if bad_class:
            add_img("invalid_class", name)
        if oob:
            add_img("bbox_out_of_bounds", name)
        boxes[name] = px
        dup = False
        for i in range(len(px)):
            for j in range(i + 1, len(px)):
                p, q = px[i], px[j]
                if (p[0] == q[0] and abs(p[3] - q[3]) <= DUP_SIZE_PX and abs(p[4] - q[4]) <= DUP_SIZE_PX
                        and abs((p[1] + p[3] / 2) - (q[1] + q[3] / 2)) <= DUP_CENTER_PX
                        and abs((p[2] + p[4] / 2) - (q[2] + q[4] / 2)) <= DUP_CENTER_PX):
                    dup = True
        if dup:
            add_img("duplicate_box", name)

    # --- panoptic ---
    pixel_cache = {}  # name -> {segment_id: pixel_count}
    for name, it in manifest.items():
        si = segs.get(name, [])
        if any(s["category_id"] not in cats for s in si):
            add_img("invalid_category_id", name)
        mp = d / it["mask"]
        if not mp.is_file():
            continue
        w, h, pix = pngutil.read_rgb(mp)
        runs = defaultdict(list)  # segment_id -> [(y, x0, x1)] (x1 không gồm)
        for y in range(h):
            base = y * w * 3
            x = 0
            while x < w:
                k = base + x * 3
                r, g, b = pix[k], pix[k + 1], pix[k + 2]
                x1 = x + 1
                while x1 < w and pix[base + x1 * 3] == r and pix[base + x1 * 3 + 1] == g and pix[base + x1 * 3 + 2] == b:
                    x1 += 1
                runs[r + g * 256 + b * 65536].append((y, x, x1))
                x = x1
        pixel_cache[name] = runs
        counts = {i: sum(x1 - x0 for _, x0, x1 in rs) for i, rs in runs.items()}
        for s in si:
            c = cats.get(s["category_id"])
            if c and c.get("isthing") and not s.get("iscrowd"):
                if s["area"] > counts.get(s["id"], 0) * (1 + AREA_TOL):
                    add_img("thing_overlap", name)
                    break

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"errors": [{"type": t, "target": g} for t, g in errors]},
                                      ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"rules: {len(errors)} loi -> {a.out}")

    if a.candidates:
        cands = make_candidates(manifest, size, boxes, segs, cats, classes, pixel_cache, skip=flagged)
        Path(a.candidates).parent.mkdir(parents=True, exist_ok=True)
        Path(a.candidates).write_text(json.dumps({"candidates": cands}, ensure_ascii=False, indent=1) + "\n",
                                      encoding="utf-8")
        print(f"candidates: {len(cands)} -> {a.candidates}")


def inside_frac(runs, box):
    """Tỉ lệ pixel của segment nằm trong box (pixel: x,y,w,h)."""
    bx, by, bw, bh = box
    tot = ins = 0
    for y, x0, x1 in runs:
        n = x1 - x0
        tot += n
        if by <= y < by + bh:
            ins += max(0, min(x1, bx + bw) - max(x0, bx))
    return ins / tot if tot else 0.0


def pair_stats(name, boxes, segs, cats, pixels):
    """Với mỗi segment thing (không crowd): các box phủ nó, kèm tỉ lệ pixel nằm trong box."""
    out = []
    det = boxes.get(name, [])
    for s in segs.get(name, []):
        c = cats.get(s["category_id"])
        runs = pixels.get(name, {}).get(s["id"])
        if not c or not c.get("isthing") or s.get("iscrowd") or not runs:
            continue
        ov = []
        for i, b in enumerate(det):
            f = inside_frac(runs, b[1:])
            if f > 0:
                ov.append((i, f, iou(tuple(s["bbox"]), b[1:])))
        out.append((s, c, ov))
    return out


def make_candidates(manifest, size, boxes, segs, cats, classes, pixels, skip=()):
    """Ứng viên lỗi gán nhãn: ghép det <-> panoptic bằng pixel mask, so lớp qua TÊN."""
    out = []
    for name in manifest:
        if name not in size:
            continue
        W, H = size[name]
        if name in skip:
            continue
        det = boxes.get(name, [])
        stats = pair_stats(name, boxes, segs, cats, pixels)
        taken = {}  # box i -> segment id đã khớp tốt (>=INSIDE_OK, IoU>=IOU_OK, cùng lớp)
        for s, c, ov in stats:
            for i, f, v in ov:
                if classes.get(det[i][0]) == c["name"] and f >= INSIDE_OK and v >= IOU_OK:
                    taken[i] = s["id"]
        for s, c, ov in stats:
            ov = [t for t in ov if taken.get(t[0], s["id"]) == s["id"]]
            same = [(i, f, v) for i, f, v in ov if classes.get(det[i][0]) == c["name"]]
            other = [(i, f, v) for i, f, v in ov if classes.get(det[i][0]) != c["name"]]
            good = [t for t in same if t[1] >= INSIDE_OK and t[2] >= IOU_OK]
            if good:
                continue
            # instance_merge: hai box cùng lớp, MỖI box chứa riêng (box kia không chứa) >= MERGE_FRAC pixel
            runs = pixels[name][s["id"]]
            big = [t for t in same if t[1] >= MERGE_FRAC]
            merged = False
            for a_ in range(len(big)):
                for b_ in range(a_ + 1, len(big)):
                    A, B = det[big[a_][0]][1:], det[big[b_][0]][1:]
                    x0, y0 = max(A[0], B[0]), max(A[1], B[1])
                    x1, y1 = min(A[0] + A[2], B[0] + B[2]), min(A[1] + A[3], B[1] + B[3])
                    inter = inside_frac(runs, (x0, y0, max(0, x1 - x0), max(0, y1 - y0))) if x1 > x0 and y1 > y0 else 0.0
                    if big[a_][1] - inter >= MERGE_FRAC and big[b_][1] - inter >= MERGE_FRAC:
                        merged = True
            if merged:
                out.append({"image": name, "type": "instance_merge", "note": f"{c['name']} chia 2 box cung lop"})
                continue
            if same:
                bi, f, v = max(same, key=lambda t: t[2])
                if v >= CAND_IOU_MATCH:
                    out.append({"image": name, "type": "bbox_drift", "note": f"{c['name']} inside={f:.2f} iou={v:.2f}"})
                continue
            if other:
                bi, f, v = max(other, key=lambda t: t[2])
                if v >= SWAP_IOU:
                    out.append({"image": name, "type": "class_swap|category_swap",
                                "note": f"det={classes.get(det[bi][0])} pan={c['name']} iou={v:.2f}"})
                    continue
            if s["area"] / (W * H) >= CAND_MISSING_MIN_AREA and not ov:
                out.append({"image": name, "type": "missing_box", "note": f"seg {c['name']} area={s['area']}"})
    return out


if __name__ == "__main__":
    main()
