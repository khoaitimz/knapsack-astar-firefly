# Slide TV4 – GUI / Thực nghiệm

Ghép sau phần FA của TV3; dùng tên đề tài đúng README ở slide tiêu đề chung.

## Slide 1 — Từ bài toán đến form ứng dụng (45 giây)
- Sinh hoặc nạp dữ liệu; hiển thị vật và sức chứa.
- Chọn tham số A*/FA; giữ nguyên đầu vào khi đổi thuật toán.
- Luồng nền giữ giao diện phản hồi, bảng thể hiện trạng thái dừng.
Lời dẫn: form tách thao tác người dùng khỏi phần tìm kiếm. Giải thích optimal khác feasible.

## Slide 2 — Quy trình demo (60 giây)
- Chạy python main.py; chọn 10 vật, tỷ lệ 0.5, seed 42, giới hạn 2 giây.
- Sinh dữ liệu, chạy A*, đọc giá trị/khối lượng/trạng thái và vật chọn.
- Chạy FA trên cùng dữ liệu, đối chiếu hai hàng; xuất JSON.
- Đổi seed FA và chạy lại để minh họa tính ngẫu nhiên sau khi solver hoàn chỉnh.
Lưu ý hiện tại: cả hai solver còn khung; demo lúc này chỉ chứng minh form và xử lý lỗi.
Chỉ chuyển sang demo nghiệm sau khi ghép TV2/TV3 và kiểm thử lại. Dự phòng nạp JSON đã lưu.

## Slide 3 — Thực nghiệm có thể chạy lại (45 giây)
- 27 instance = 3 cỡ × 3 tỷ lệ × 3 seed dữ liệu.
- A* một lần, FA 10 seed/instance; cùng trần 2 giây.
- Giá trị trung bình/tốt nhất/độ lệch chuẩn, thời gian và gap có chuẩn tối ưu.
Lời dẫn: gap không được tính với nghiệm A* chưa chứng minh tối ưu. Không so sánh thuật toán ngoài đề tài.

## Slide 4 — Kết quả và giới hạn (45 giây)
- Hiện có 108/108 lần gọi pending; chưa có số liệu hiệu năng.
- Sau ghép: thay slide này bằng bảng summary thật và giải thích theo cỡ/sức chứa.
- Chỉ kết luận trong phạm vi dữ liệu, cấu hình và máy đo đã công bố.
Lời dẫn: không lấy dữ liệu mock trong test làm kết quả thuật toán.

## Câu hỏi dự kiến

**Tại sao chạy FA nhiều lần?** Seed khác nhau giúp đo biến thiên nghiệm; báo cáo cả độ lệch chuẩn.

**A* timeout có làm chuẩn tối ưu được không?** Không. Chỉ dùng status optimal làm chuẩn gap.

**Vì sao QThread?** Đưa vòng tính toán ra khỏi event loop để cửa sổ vẫn tiếp nhận sự kiện;
không có nghĩa Python tự động chạy CPU nhanh hơn.

**FA có chắc tìm tối ưu?** Không có bảo đảm từ cơ chế ngẫu nhiên; đạt giá trị bằng A* optimal
trên một instance chỉ xác nhận lần chạy đó đạt chuẩn.

**Đã đạt Turnitin chưa?** Chưa; cần bản ghép cuối và kết quả chính thức cấu hình mặc định,
tỷ lệ dưới 30%, nối file vào cuối báo cáo.
