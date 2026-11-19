# Báo cáo nhóm 86

## 1. Số liệu luyện tập
- F1 (rule / cross_check / overall): seed 86007: 1.0 / 0.6 / 0.8; seed 7 (chưa review): rule 1.0, overall 0.8
- Lô sạch (`--no-faults`, 50 ảnh): 0 lỗi luật, 2 ứng viên. Hàng đợi seed 86007: 14 ảnh.
- Ngưỡng: ≥80% pixel segment trong box cùng lớp và IoU ≥ 0.6 thì khớp; `instance_merge` khi hai box cùng lớp mỗi box chứa riêng ≥25% pixel; `class_swap`/`category_swap` khi box khác lớp phủ segment IoU ≥ 0.5. Chọn bằng đo trên lô sạch (bản đầu `instance_merge` ra 277 ứng viên do box chồng tự nhiên, sau chỉnh còn 1).

## 2. Vì sao báo hết ứng viên làm F1 giảm?
Seed 86007 có 14 ứng viên, xem ảnh xác nhận 10 và loại 4 (lệch tự nhiên). Báo cả 14 thì thêm 4 báo thừa, precision còn khoảng 10/14 ≈ 71% mà recall không tăng, nên F1 giảm. Lô sạch 2 ứng viên/50 ảnh đều là lệch tự nhiên: báo hết thì toàn FP.

## 3. Quyết định và lineage
QC v1 = 21/250 = 8,4% > 2% nên **Hold** v1 (`lab250_0ed2f2035c24`); lineage có HOLD v1 và release v2 có parent. `impact`: `R-021: affected=True action=review_or_retrain`, vì R-021 đã train trên lô lỗi và đổi dataset không tự sửa model.

## 4. Hash chứng minh gì, không chứng minh gì?
Chứng minh file không bị đổi từ lúc lập manifest và gói v2 tái lập được. Không chứng minh nhãn đúng hay ảnh đúng nội dung (ảnh 000000005586 hash lệch nhưng mở ra còn nguyên, chỉ manifest sai). Không ghi đè v1 vì v1 đã giao và dùng để train R-021.

## 5. Truy vết
Tiêu chí: job guideline cũ theo `jobs.csv` (không theo trường của ảnh, vì có thể là `guideline_mismatch`, ví dụ 000000025139 ghi v1.2 nhưng job J10 là v1.3) và có box detection thuộc lớp đổi quy tắc. Seed 86007 (`cup`, scene_553 và scene_863): tier_a 4, tier_b 3, notify A04 và Q03.

## 6. Bug hoặc điểm chưa rõ
- README ghi Python 3.10+, macOS mặc định 3.9.6 làm `download_public.py` lỗi `hardlink_to`.
- `label_summary.csv` chỉ khớp (H9) khi liệt kê lớp có số lượng > 0; tài liệu chưa nói rõ.
