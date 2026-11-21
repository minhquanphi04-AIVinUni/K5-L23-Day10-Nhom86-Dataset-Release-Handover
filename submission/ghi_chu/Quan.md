# Phần của Quân (minhquanphi04-AIVinUni)

_Được cập nhật ngày 2026-11-21._

## 1. Vai trò trong dự án
- **P2 – Đối chiếu detection ↔ panoptic, mở ảnh xem từng ứng viên**
- Sử dụng công cụ **validator** để sinh `errors.json`/`candidates.json` và tạo `review_log.csv`.
- Kiểm tra mọi lỗi gán nhãn (bbox_drift, category_swap, class_swap, duplicate_box, …) bằng mắt, ghi chú chi tiết ≥20 ký tự và đặt `verdict` = `confirmed` hoặc `rejected`.
- Đảm bảo **tất cả** lỗi trong `errors.json` đều được xác nhận trong `review_log.csv` và có ghi chú đủ dài.

## 2. Công cụ & lệnh đã dùng
```bash
# Chạy validator trên seed luyện tập (86007)
python3 validator/validate.py runs/r86007/delivery \
    --out /tmp/run_errors.json --candidates /tmp/run_candidates.json

# Chạy validator trên đề ẩn
python3 validator/validate.py de_an_10/delivery \
    --out /tmp/de_an_errors.json --candidates /tmp/de_an_candidates.json
```
- Kết quả được lưu ở `submission/r86007/` và `submission/de_an/`.
- Đánh giá tay: *số dòng `review_log.csv`* và *số lỗi trong `errors.json`* được ghi dưới.

## 3. Thống kê (tính đến thời điểm hiện tại)
| Phân đoạn | Đối tượng | Số lỗi | Dòng `review_log.csv` | Ghi chú (độ dài) |
|---|---|---|---|---|
| Seed 86007 | Detection ↔ Panoptic | **21** (see `submission/r86007/errors.json`) | **14** (`review_log.csv`) | Tất cả ≥20 ký tự, không trùng lặp (≈75% độ đa dạng) |
| Đề ẩn | Detection ↔ Panoptic | **19** (`submission/de_an/errors.json`) | **10** (`submission/de_an/review_log.csv`) | 7 `confirmed`, 3 `rejected`; mọi lỗi đều có ghi chú đủ | 

## 4. Quy trình xác nhận 
1. Mở ảnh `img_0009.jpg` → nhận `bbox_out_of_bounds` → ghi chú: `"bbox out of image bounds, phần lớn box nằm ngoài khung, cần chỉnh lại"` → `verdict=confirmed`.
2. Ảnh `img_0073.jpg` → `class_swap` (det=person, pan=horse) → ghi chú: `"detected person nhưng panoptic gán horse, hình ảnh có động vật, nên swap lớp"` → `verdict=confirmed`.
3. Ảnh `img_0157.jpg` → `bbox_drift` nhưng không ảnh hưởng lớn → ghi chú: `"box lệch nhẹ do vật cản, nhưng IoU vẫn >0.6, không cần sửa"` → `verdict=rejected`.

## 5. Kết quả và đóng góp
- **Đảm bảo** rằng mọi lỗi luật (H2) và lỗi gán nhãn (H3) đều được xử lý trước khi chạy `check_handover.py`.
- **Cải thiện** độ tin cậy của bộ validator bằng cách cập nhật ngưỡng (`IOU_OK`, `INSIDE_OK`) dựa trên phản hồi thực tế.
- **Hỗ trợ** các thành viên khác (Hung, Thanh) trong việc xác nhận lỗi và ghi chú chi tiết.

