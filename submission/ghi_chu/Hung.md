# Phần của hunghocweb

_Số liệu lấy từ các file trong repo, ngày 2026-11-20._

## Validator: các loại lỗi luật nó bắt
- bbox_out_of_bounds
- duplicate_box
- guideline_mismatch
- invalid_category_id
- invalid_class
- missing_image
- scene_leak
- thing_overlap
- wrong_hash

## Các ngưỡng đầu file `validator/validate.py`
- `OOB_EPS_PX = 0.5`: box tràn mép quá nửa pixel mới tính
- `DUP_CENTER_PX = 3.0`: duplicate_box: lệch tâm tối đa
- `DUP_SIZE_PX = 2.0`: duplicate_box: lệch kích thước tối đa
- `AREA_TOL = 0.01`: thing_overlap: area khai > pixel thật quá 1%
- `CAND_IOU_MATCH = 0.1`: ghép box detection <-> segment (bbox_drift)
- `INSIDE_OK = 0.80`: >=80% pixel segment nằm trong box cùng lớp = khớp
- `IOU_OK = 0.60`: và IoU bbox >= 0.6
- `MERGE_FRAC = 0.25`: instance_merge: >=25% pixel trong mỗi box của >=2 box
- `SWAP_IOU = 0.5`: class_swap: box khác lớp phủ đúng vị trí
- `CAND_MISSING_MIN_AREA = 0.02`: segment thing >2% diện tích ảnh mà không có box

Validator chỉ đọc thư mục delivery truyền vào, chỉ dùng thư viện chuẩn của Python.
