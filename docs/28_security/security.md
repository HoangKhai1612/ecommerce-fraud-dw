PHASE 28 — Security

1. Mục tiêu
Phase 28 tăng cường bảo mật cho hệ thống Data Warehouse và phát hiện gian lận thương mại điện tử. Phạm vi bao gồm phân quyền cơ sở dữ liệu, kiểm soát câu lệnh SQL, bảo vệ thông tin xác thực, kiểm soát truy cập API và rà soát cấu hình mạng.

2. Phân quyền cơ sở dữ liệu
Tài khoản AI Assistant sử dụng nguyên tắc đặc quyền tối thiểu. Tài khoản ai_assistant_ro chỉ được cấp quyền đọc dữ liệu thuộc schema marts theo phạm vi nghiệp vụ cần thiết.
Tài khoản ETL, tài khoản Airflow và tài khoản quản trị được tách biệt theo trách nhiệm. Các quyền được xác minh bằng truy vấn catalog của PostgreSQL và thử nghiệm truy cập thực tế.
Không cấp quyền SUPERUSER cho tài khoản ứng dụng.

3. Ngăn chặn SQL injection
SQL do AI Assistant sinh ra phải được kiểm tra trước khi thực thi. Chính sách kiểm soát bao gồm giới hạn loại câu lệnh, schema được phép truy cập, số lượng statement và số hàng trả về.
Validator không thay thế quyền bảo mật của PostgreSQL. Các truy vấn được thực thi bằng tài khoản chỉ đọc, có giới hạn thời gian và giới hạn tài nguyên phù hợp.
Các truy vấn có tham số sử dụng parameterized queries thay vì nối chuỗi đầu vào trực tiếp.

4. Quản lý thông tin xác thực
Thông tin xác thực không được lưu trong mã nguồn hoặc commit lên Git. File .env.example chỉ chứa giá trị minh họa. Các bí mật thực tế được cung cấp qua cấu hình môi trường hoặc cơ chế secrets phù hợp với môi trường triển khai.
Khi phát hiện bí mật đã bị commit, cần thu hồi hoặc thay thế bí mật đó; chỉ xóa file khỏi commit hiện tại là chưa đủ.

5. Bảo mật API và network
Các endpoint cần được bảo vệ bằng xác thực và giới hạn lưu lượng phù hợp. Các dịch vụ nội bộ không được công khai cổng mạng nếu không có nhu cầu thực tế.
Rate limiting, xác thực, TLS, kiểm soát quyền và giới hạn tài nguyên là các lớp bảo vệ riêng biệt.

6. Kiểm thử và evidence
Evidence được lưu trong evidence/phase_28/. Mỗi kết quả kiểm tra phải phản ánh đầu ra thực tế của lần chạy tương ứng.
Các trạng thái PASS, FAIL và SKIPPED phải được phân biệt. Kiểm tra chưa thực hiện không được đánh dấu PASS.

7. Giới hạn
Phase 28 không tự động chứng minh hệ thống hoàn toàn an toàn. Phạm vi xác minh phụ thuộc vào các bài kiểm thử đã chạy, cấu hình thực tế và quyền truy cập của môi trường kiểm thử.

8. Chuyển tiếp
Phase tiếp theo: PHASE 29 — Final Documentation.