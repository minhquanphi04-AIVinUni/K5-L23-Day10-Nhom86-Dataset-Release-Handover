Release: lab250_0ed2f2035c24_v2
Parent: lab250_0ed2f2035c24
Số ảnh: 235
Số nhãn: 1639
Guideline: v1.2 (J01-J03), v1.3 (J04-J10)
QC v1: 21/250 = 8.4%
Kết luận v1: Hold — 8.4% ảnh/cảnh lỗi, vượt ngưỡng 2% (Day 7) nên không Release.
Kết luận v2: Release — tách 15 ảnh lỗi nhãn detection sang rework_queue, sửa hash/guideline/split, còn 235 ảnh không còn lỗi detection đã biết.
Ghi chú: wrong_hash 000000005586: đã mở ảnh kiểm, ảnh còn nguyên, chỉ manifest sai nên ghi hash mới. guideline_mismatch 000000025139: guideline lấy theo job trong jobs.csv. scene_leak scene_326: đưa cả cảnh về một split. Ảnh rework (15) giao lại cho các cặp gán/kiểm A01/Q03, A03/Q01, A03/Q02, A04/Q02, A04/Q03, A05/Q03. Ảnh chỉ lỗi panoptic ở lại v2, báo team panoptic: 000000001268, 000000015440, 000000021604.
