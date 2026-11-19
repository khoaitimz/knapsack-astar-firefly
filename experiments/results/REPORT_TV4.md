# Phần GUI và thực nghiệm – TV4 Tiến Tài

Tên đề tài: Ứng dụng thuật toán A* và thuật toán đom đóm (Firefly Algorithm) cho bài toán cái túi (Knapsack problem).

## Giao diện ứng dụng

Giao diện được tổ chức thành form cấu hình, bảng vật, bảng kết quả và ô chi tiết.
Người dùng sinh dữ liệu với số vật, tỷ lệ sức chứa và seed hoặc nạp tập JSON/CSV.
Seed giúp nhóm dùng lại cùng đầu vào khi trình bày. Hai nút chạy sử dụng cùng đối tượng
bài toán, nhờ đó tránh so sánh hai thuật toán trên hai tập vật khác nhau.

KnapsackMainWindow tiếp nhận thao tác và hiển thị; SolverWorker gọi solver trong QThread.
Tín hiệu result_ready mang nghiệm; tín hiệu finished của QThread chỉ dùng thu hồi luồng
và mở lại nút. Cách tách này giữ event loop giao diện hoạt động khi thuật toán đang tìm kiếm.
Khi lỗi, form hiện thông báo thay vì thêm hàng nghiệm giả. Khi chạy, thao tác đổi dữ liệu
bị khóa và yêu cầu đóng được hoãn để tránh hủy QThread còn hoạt động.

Bảng kết quả thể hiện giá trị, khối lượng, tính hợp lệ, thời gian và trạng thái dừng.
Một nghiệm khả thi khi hết giới hạn chưa đủ chứng minh tối ưu. Ô chi tiết liệt kê vật chọn
và metrics; file xuất chứa cả bài toán và nghiệm để đối chiếu. Các tham số FA gồm số cá thể,
vòng lặp, alpha, decay, beta0, gamma và seed; giới hạn thời gian áp dụng cho cả hai solver.

## Thiết kế thực nghiệm

Câu hỏi: với số vật và độ chặt sức chứa thay đổi, thời gian và chất lượng nghiệm của
A* và FA biến đổi như thế nào? Chỉ hai thuật toán của đề tài được so sánh.

Bộ sinh của TV1 cung cấp 27 instance: n thuộc {10,30,100}, tỷ lệ thuộc {0.25,0.5,0.75},
seed thuộc {42,43,44}. Mỗi instance được lưu nguyên trạng. FA lặp 10 seed để mô tả biến thiên;
A* chạy một lần vì tìm kiếm xác định với cùng đầu vào, nhưng thời gian vẫn phụ thuộc máy.
Trần thời gian mặc định là 2 giây/solver; giới hạn nút A* là 100000; FA có 20 cá thể và 100 vòng.
Không coi việc dừng sớm của FA là đã dùng hết ngân sách tương đương A*.

Mỗi vector trả về được đánh giá lại bằng core.evaluation; sai khác với tổng giá trị,
khối lượng, chỉ số chọn hoặc tính hợp lệ làm lần chạy mang trạng thái lỗi.
Trung bình, độ lệch chuẩn mẫu và giá trị tốt nhất chỉ dùng lần chạy hợp lệ. Khoảng cách
đến tối ưu chỉ tính khi A* trả optimal. Nếu A* chưa chứng minh tối ưu thì để trống gap,
không lấy nghiệm tạm làm đáp án chuẩn. Số lần hợp lệ luôn đi cùng thống kê để tránh che lỗi.

## Kết quả hiện có và giới hạn

Đã chạy bộ kiểm tra khả dụng 27 instance với 3 lần FA mỗi instance: 108 lần gọi đều
pending_implementation do hai solver còn khung. Vì vậy chưa có thời gian hay giá trị nghiệm
thực để so sánh. Các ô thống kê là null. Đây là bằng chứng tình trạng tích hợp, không phải
thất bại tối ưu hóa của A* hay FA. Không có kết luận định lượng nào về hiệu năng.

Sau khi ghép solver, chạy lệnh trong README, ghi cấu hình máy từ metadata và chèn bảng
summary thật vào mục này. Phân tích riêng theo cỡ và tỷ lệ sức chứa; nêu số lần timeout,
số lần hợp lệ, biến thiên FA và trường hợp A* chưa chứng minh tối ưu. Nếu vẽ biểu đồ,
trục thời gian dùng ms, trục chất lượng dùng giá trị hoặc gap có chuẩn xác nhận; ghi số mẫu.
Bộ uniform nhỏ không đại diện mọi dữ liệu thực; FA có thể nhạy tham số và seed.

## Ghép báo cáo và kiểm tra trước nộp

Chuyển nội dung vào mẫu chính thức, thống nhất ký hiệu với TV1–TV3; thêm hình GUI sau
khi chạy thật kèm giải thích thao tác và ý nghĩa trạng thái. Rà soát mọi khẳng định về
A*/FA với cài đặt cuối. Không chép ảnh thay phần phân tích. Ghép phần mở đầu, lý thuyết,
mô hình, cài đặt, thực nghiệm, kết luận, tài liệu tham khảo theo mẫu được cung cấp.

Turnitin: chưa kiểm tra. Chạy trên bản ghép cuối với cấu hình mặc định; chỉ điền tỷ lệ,
ngày kiểm tra và mã bài từ kết quả thật. Phải đạt dưới 30% rồi nối PDF kết quả vào cuối
báo cáo. Giữ lại bản báo cáo tương ứng với lần kiểm tra. Không cam kết trước tỷ lệ lặp.
