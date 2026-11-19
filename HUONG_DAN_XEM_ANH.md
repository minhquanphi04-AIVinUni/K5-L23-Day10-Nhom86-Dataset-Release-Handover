# Xem ảnh (mỗi người 5 ảnh)

1. **Lấy repo mới nhất:** chưa có thì `git clone https://github.com/minhquanphi04-AIVinUni/K5-L23-Day10-Nhom86-Dataset-Release-Handover.git`, đã có thì `git pull`.
2. **Xem ảnh:** vào thư mục `xem_anh/` trong repo, nháy đúp mở file HTML của mình bằng trình duyệt: Quân `xem_anh_Quan.html`, Thành `xem_anh_Thanh.html`, Thắng `xem_anh_Thang.html`, Đức `xem_anh_Duc.html`, Hùng `xem_anh_Hung.html`. Chọn *Không thấy lỗi* / *Có lỗi* / *Lệch tự nhiên*; nếu có lỗi hoặc lệch tự nhiên thì chọn loại lỗi và ghi chú bằng lời của mình (ít nhất 20 ký tự). Bấm **Tải CSV**.
3. **Chạy lệnh của mình** trong thư mục repo (chọn dòng theo máy):

| Người | Windows (PowerShell) | Mac / Linux |
|---|---|---|
| Quân | `py tools/nop_phan.py Quan` | `python3 tools/nop_phan.py Quan` |
| Thành | `py tools/nop_phan.py Thanh` | `python3 tools/nop_phan.py Thanh` |
| Thắng | `py tools/nop_phan.py Thang` | `python3 tools/nop_phan.py Thang` |
| Đức | `py tools/nop_phan.py Duc` | `python3 tools/nop_phan.py Duc` |
| Hùng | `py tools/nop_phan.py Hung` | `python3 tools/nop_phan.py Hung` |

Gõ `y` khi được hỏi. Nếu Windows lỗi font tiếng Việt, thêm `-X utf8` sau `py`.
