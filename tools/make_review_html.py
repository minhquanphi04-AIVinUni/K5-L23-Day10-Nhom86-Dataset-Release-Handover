#!/usr/bin/env python3
"""Tạo file HTML tự chứa (ảnh nhúng sẵn) cho mỗi thành viên xem 5 ảnh và xuất CSV.

uv run --python 3.13 --with pillow tools/make_review_html.py runs/r86007
"""
import base64, io, json, random, sys
from pathlib import Path
from PIL import Image

run = Path(sys.argv[1])
man = sorted(json.load(open(run / "delivery/manifest.json"))["items"])
done = {c["image"] for c in json.load(open(run / "candidates.json"))["candidates"]}
done |= {e["target"] for e in json.load(open(run / "rules.json"))["errors"]}
pool = [n for n in man if n not in done]
random.Random(86).shuffle(pool)
people = [("Tinh", "Lê Văn Trung Tình", 0), ("Hung", "Nguyễn Văn Hùng", 100), ("Quan", "Phí Minh Quân", 20),
          ("Thanh", "Đinh Tuấn Thành", 40), ("Thang", "Đinh Quang Thắng", 60), ("Duc", "Thạch Trung Đức", 80)]
PAGE = open(Path(__file__).with_name("review_page.html"), encoding="utf-8").read()
out = run / "review_html"; out.mkdir(exist_ok=True)
for key, full, start in people:
    imgs = sorted(pool[start:start + 5])
    items = []
    for n in imgs:
        p = run / "extra_review" / key / "sheets" / f"{n}.png"
        buf = io.BytesIO(); Image.open(p).convert("RGB").save(buf, "JPEG", quality=82)
        items.append({"image": n, "src": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()})
    html = PAGE.replace("__NAME__", full).replace("__KEY__", key).replace("__ITEMS__", json.dumps(items))
    (out / f"xem_anh_{key}.html").write_text(html, encoding="utf-8")
    print(key, len(items), "anh")
