#!/usr/bin/env python3
"""Nộp phần của một thành viên: kiểm CSV, tạo 2 commit mang tên người chạy, rồi push.

python3 tools/nop_phan.py <Key> [duong_dan_csv] [--no-push]
Key: Tinh | Hung | Quan | Thanh | Thang | Duc
--chi-xem-anh: bỏ commit 2; mặc định commit 2 là tài liệu phần việc tạo từ số liệu trong repo (mặc định có; tắt bằng --chi-xem-anh)
CSV mặc định: ~/Downloads/review_extra_<Key>.csv
"""
import csv, shutil, subprocess, sys
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from pathlib import Path

TYPES = {"none", "missing_box", "bbox_drift", "class_swap", "category_swap", "instance_merge"}
root = Path(__file__).resolve().parent.parent
TASK = {"Hung": ["validator/README.md"], "Quan": ["tools/README.md"], "Thanh": ["submission/REPORT.md"],
        "Thang": ["tools/verify_v2.py"], "Duc": ["submission/r86007/security.md"]}



import csv as _csv, json as _json, re as _re, hashlib as _hl, datetime as _dt
from collections import Counter as _C


def _rd(p):
    return (root / p).read_text(encoding="utf-8")


def _csvrows(p):
    return list(_csv.DictReader(open(root / p, encoding="utf-8-sig", newline="")))


def make_doc(key):
    """Tài liệu về phần của người chạy, số liệu lấy từ file thật trong repo."""
    out = []
    if key == "Hung":
        v = _rd("validator/validate.py")
        out.append("## Validator: các loại lỗi luật nó bắt")
        types = sorted(set(_re.findall(r'add(?:_img)?\("([a-z_]+)"', v)))
        out += ["- " + t for t in types]
        out.append("\n## Các ngưỡng đầu file `validator/validate.py`")
        for l in v.splitlines():
            m = _re.match(r"^([A-Z_]+)\s*=\s*([0-9.]+)\s*#?\s*(.*)$", l)
            if m:
                out.append("- `%s = %s`: %s" % (m.group(1), m.group(2), m.group(3)))
        out.append("\nValidator chỉ đọc thư mục delivery truyền vào, chỉ dùng thư viện chuẩn của Python.")
    elif key == "Quan":
        out.append("## Công cụ trong `tools/`")
        for f in sorted((root / "tools").glob("*.py")):
            doc = _re.search(r'"""(.*?)"""', f.read_text(encoding="utf-8"), _re.S)
            first = doc.group(1).strip().splitlines()[0] if doc else ""
            out.append("- `tools/%s`: %s" % (f.name, first))
        out.append("\nHàng đợi ghép detection ↔ panoptic bằng pixel mask: xem hằng số INSIDE_OK, IOU_OK, MERGE_FRAC, SWAP_IOU ở `validator/validate.py`.")
    elif key == "Thanh":
        for label, d in (("seed luyện tập 86007", "submission/r86007"), ("đề ẩn", "submission/de_an")):
            rows = _csvrows(d + "/review_log.csv")
            e = _json.loads(_rd(d + "/errors.json"))["errors"]
            out.append("## Review %s" % label)
            out.append("- review_log.csv: %d dòng, %s" % (len(rows), dict(_C(r["verdict"] for r in rows))))
            out.append("- errors.json: %d lỗi, %s" % (len(e), dict(_C(x["type"] for x in e))))
    elif key == "Thang":
        v2 = next((root / "submission/r86007/handover").glob("*_v2"))
        files = [p for sub in ("images", "labels") for p in (v2 / sub).iterdir() if p.is_file()]
        man = {r["file"]: r["sha256"] for r in _csvrows(str(v2.relative_to(root)) + "/manifest.csv")}
        ok = sum(1 for p in files if man.get(p.relative_to(v2).as_posix()) == _hl.sha256(p.read_bytes()).hexdigest())
        out.append("## Lô v2 `%s`" % v2.name)
        out.append("- Số ảnh: %d, số file nhãn: %d" % (len(list((v2 / "images").iterdir())), len(list((v2 / "labels").iterdir()))))
        out.append("- manifest.csv khớp sha256: %d/%d file" % (ok, len(files)))
        out.append("- Ảnh chuyển rework: %d" % len(_csvrows(str(v2.relative_to(root)) + "/rework_queue.csv")))
        out += ["", "README.txt của v2:", ""] + ["    " + l for l in (v2 / "README.txt").read_text(encoding="utf-8").splitlines()]
        out.append("\nHash chứng minh file không bị đổi sau khi lập manifest; không chứng minh nhãn đúng.")
    elif key == "Duc":
        for label, d in (("seed luyện tập 86007", "submission/r86007"), ("đề ẩn", "submission/de_an")):
            t = _json.loads(_rd(d + "/trace.json"))
            out.append("## Truy vết %s" % label)
            out.append("- tier_a: %d ảnh, tier_b: %d ảnh, notify: %s" % (len(t["tier_a"]), len(t["tier_b"]), ", ".join(t["notify"])))
        heads = [l for l in _rd("submission/r86007/security.md").splitlines() if l.startswith("## ")]
        out.append("\n## security.md gồm các mục")
        out += ["- " + h[3:] for h in heads]
    return "\n".join(out)


def sh(*a, check=True):
    r = subprocess.run(a, cwd=root, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit("Lỗi lệnh %s:\n%s" % (" ".join(a), r.stderr.strip()))
    return r.stdout.strip()


args = [a for a in sys.argv[1:] if not a.startswith("--")]
push = "--no-push" not in sys.argv

if "--task" in sys.argv:
    key = args[0] if args else ""
    if key not in TASK:
        sys.exit("Dùng: python3 tools/nop_phan.py <Hung|Quan|Thanh|Thang|Duc> --task")
    name, email = sh("git", "config", "user.name", check=False), sh("git", "config", "user.email", check=False)
    if not name or not email:
        sys.exit('Chưa đặt tên/email git. Chạy:\n git config user.name "Ho Ten"\n git config user.email "email-github-cua-ban"')
    changed = [l.split(None, 1)[1].strip() for l in sh("git", "status", "--porcelain").splitlines() if l.strip()]
    mine = [c for c in changed if c in TASK[key]]
    if not mine:
        sys.exit("Chưa thấy thay đổi nào trong việc của bạn: %s. Làm xong việc được giao, lưu file rồi chạy lại." % ", ".join(TASK[key]))
    other = [c for c in changed if c not in TASK[key]]
    if other:
        print("Lưu ý: các file khác sẽ KHÔNG đưa vào commit:", ", ".join(other))
    print("Commit sẽ mang tên: %s <%s>" % (name, email))
    if input("Đúng chưa? (y/n) ").strip().lower() != "y":
        sys.exit("Dừng.")
    branch = sh("git", "rev-parse", "--abbrev-ref", "HEAD")
    for f in mine:
        sh("git", "add", f)
    sh("git", "commit", "-m", "task: %s (%s)" % (", ".join(mine), key))
    if "--no-push" not in sys.argv:
        out = subprocess.run(["git", "push", "-u", "origin", branch], cwd=root, capture_output=True, text=True)
        print(out.stdout + out.stderr)
    print("Xong commit 2.")
    sys.exit(0)

if not args or args[0] not in ('Tinh','Hung','Quan','Thanh','Thang','Duc'):
    sys.exit("Dùng: python3 tools/nop_phan.py <Tinh|Hung|Quan|Thanh|Thang|Duc> [file.csv]")
key = args[0]
_name = "review_extra_%s.csv" % key
_cands = [Path(args[1]).expanduser()] if len(args) > 1 else [root / "submission" / "r86007" / _name, Path.home() / "Downloads" / _name]
src = next((c for c in _cands if c.is_file()), _cands[-1])
if not src.is_file():
    sys.exit("Không thấy %s. Tải CSV từ trang xem ảnh về (thư mục Downloads hoặc submission/r86007/) rồi chạy lại." % _name)

# 1. kiểm CSV
rows = list(csv.DictReader(open(src, encoding="utf-8-sig", newline="")))
errs = []
if [c for c in (rows[0].keys() if rows else [])] != ["image", "type", "verdict", "note"]:
    errs.append("cột phải là image,type,verdict,note")
for r in rows:
    v, n = r.get("verdict", "").strip(), r.get("note", "").strip()
    if v not in ("ok", "confirmed", "rejected"):
        errs.append("%s: verdict '%s' không hợp lệ" % (r.get("image"), v))
    if v in ("confirmed", "rejected") and len(n) < 20:
        errs.append("%s: ghi chú dưới 20 ký tự" % r.get("image"))
    if r.get("type", "").strip() not in TYPES:
        errs.append("%s: type '%s' không hợp lệ" % (r.get("image"), r.get("type")))
if len(rows) != 5:
    errs.append("cần đúng 5 dòng, hiện có %d" % len(rows))
if errs:
    sys.exit("CSV chưa đạt:\n - " + "\n - ".join(errs))

# 2. danh tính git
name, email = sh("git", "config", "user.name", check=False), sh("git", "config", "user.email", check=False)
if not name or not email:
    sys.exit('Chưa đặt tên/email git. Chạy:\n git config user.name "Ho Ten"\n git config user.email "email-github-cua-ban"')
print("Commit sẽ mang tên: %s <%s>" % (name, email))
if input("Đúng chưa? (y/n) ").strip().lower() != "y":
    sys.exit("Dừng. Hãy đặt lại tên/email rồi chạy lại.")

# 3. commit 1: kết quả xem ảnh của chính người chạy
branch = "main"
sh("git", "checkout", "main")
sh("git", "pull", "--rebase", "--autostash", "origin", "main")
dst = root / "submission" / "r86007" / _name
dst.parent.mkdir(parents=True, exist_ok=True)
if src.resolve() != dst.resolve():
    shutil.copyfile(src, dst)
sh("git", "add", str(dst))
sh("git", "commit", "-m", "P2: xem 5 anh (%s)" % key)

# 4. commit 2: tài liệu về phần của mình, số liệu từ file thật trong repo
if "--chi-xem-anh" not in sys.argv:
    doc = root / "submission" / "ghi_chu" / ("%s.md" % key)
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("# Phần của %s\n\n_Số liệu lấy từ các file trong repo, ngày %s._\n\n%s\n"
                   % (name, _dt.date.today().isoformat(), make_doc(key)), encoding="utf-8")
    sh("git", "add", str(doc))
    sh("git", "commit", "-m", "tai lieu phan viec (%s)" % key)

# 5. push main (thử lại nếu người khác vừa push)
if push:
    ok = False
    for _ in range(3):
        out = subprocess.run(["git", "push", "origin", "main"], cwd=root, capture_output=True, text=True)
        if out.returncode == 0:
            ok = True
            break
        subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "main"], cwd=root, capture_output=True, text=True)
    print("Xong: đã commit và push main." if ok else "Push lỗi (kiểm tra bạn đã là Collaborator chưa). Nhắn nhóm trưởng, hoặc chạy lại: git push origin main\n" + out.stderr.strip())
else:
    print("Xong (chưa push). Chạy: git push origin main")
