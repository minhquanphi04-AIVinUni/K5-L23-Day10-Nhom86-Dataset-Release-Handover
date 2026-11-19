# Bảo mật khi làm việc

> Gắn với lô lab250_0ed2f2035c24 (seed 86007) mà nhóm vừa bàn giao.

## 1. Ca USB: hết giờ, muốn chép lô về nhà làm tiếp
Không chép lô ra USB và không mang về nhà. Lô này có ảnh người thật (ví dụ 000000004395, 000000019402) cùng nhãn và thông tin người gán/kiểm (A01–A05, Q01–Q03), nên là dữ liệu của dự án, không phải của cá nhân. Gửi qua email cá nhân cũng sai vì dữ liệu rời khỏi hệ thống được kiểm soát và không thu hồi được. Nhờ người khác làm hộ ở máy của họ cũng sai vì người đó chưa được cấp quyền truy cập lô. Cách đúng: làm tiếp trên máy hoặc môi trường công ty trong giờ được phép, hoặc xin người phụ trách cấp quyền truy cập từ xa qua kênh chính thức (VPN, máy ảo của công ty), có ghi log.

## 2. Năm việc: được hay không
- **Mở job được giao trên máy công ty:** được. Đây là việc được phân công và chạy trong môi trường được quản lý.
- **Chụp màn hình gửi người quen:** không. Ảnh chụp chứa ảnh người thật và nhãn, gửi ra ngoài là làm lộ dữ liệu dự án.
- **Chép lô ra USB:** không. USB dễ thất lạc, không mã hoá và không có log truy cập.
- **Dán nhãn thật lên chatbot:** không với dữ liệu thật của dự án, vì dữ liệu có thể bị lưu hoặc dùng ngoài tầm kiểm soát. Riêng ảnh COCO của lab là công khai nên được phép, nhưng phải ghi vào `prompts.md`.
- **Đưa tài khoản CVAT cho đồng nghiệp:** không. Mỗi người dùng tài khoản của mình để log ghi đúng người gán/kiểm; nếu đồng nghiệp cần truy cập thì xin quản trị cấp tài khoản riêng.

## 3. Ca khuôn mặt: thấy mặt người rõ trong lô, guideline yêu cầu làm mờ
Ví dụ trong lô: ảnh 000000004395 chụp cận mặt một người nhìn rõ, và 000000019402 có hai người nhìn rõ mặt. Nếu guideline yêu cầu làm mờ mà thấy mặt rõ thì kết luận là **Hold** lô (không phát hành, không giao tiếp cho team AI) và **báo người phụ trách** (quản lý dự án hoặc người chịu trách nhiệm dữ liệu cá nhân). Không tự làm mờ vì sửa ảnh làm đổi nội dung lô đã giao, phá hash và lineage, và có thể làm mờ sai vùng hoặc sai quy cách mà người phụ trách mới là người quyết định. Không tự xoá ảnh vì mất bằng chứng và làm lô thiếu mà không ai biết. Người phụ trách sẽ quyết định làm mờ hoặc loại ảnh, rồi mới phát hành bản v2 mới kèm lineage.
