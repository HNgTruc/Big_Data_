# Yêu cầu đồ án — Nhập môn dữ liệu lớn

> Nguồn: file `Yêu cầu đồ án.docx` (thư mục "Dữ liệu lớn - SV" trên Google Drive của người dùng),
> bản sửa đổi gần nhất ngày 2026-09-25. Đây là bản tóm tắt; số mục theo file gốc.

## 1. Mục tiêu
Vận dụng kiến thức Big Data để thiết kế và triển khai **một phần** quy trình xử lý dữ liệu lớn: hiểu vai trò từng thành phần,
xác định đúng đầu vào/đầu ra, chọn công nghệ phù hợp và chứng minh quy trình hoạt động trên dữ liệu có đặc trưng dữ liệu lớn.
Đánh giá theo khả năng **giải thích, thiết kế, triển khai và kiểm chứng**; chỉ chạy được notebook hoặc sao chép pipeline mà không giải thích được thì không đạt.

## 2. Pipeline tổng quát
Sources → Ingestion → Storage → Processing → Analytics → Presentation → Decision/Action.

## 3. Tổ chức nhóm
Tối đa 05 thành viên. Mỗi nhóm chọn 01 quy trình con ở mục 4 (hoặc đề xuất khác được giảng viên chấp thuận).
Khuyến khích đầu ra nhóm trước là đầu vào nhóm sau, nhưng mỗi nhóm phải có sản phẩm độc lập đánh giá được.

## 4. Quy trình con đã chọn: Storage → Processing
- Bài toán gợi ý: làm sạch, chuẩn hóa, kết hợp và tổng hợp dữ liệu lớn.
- Công nghệ gợi ý: Apache Spark, PySpark, Spark SQL.
- Sản phẩm tối thiểu: job xử lý phân tán; dữ liệu trước/sau xử lý; thống kê chất lượng và thời gian xử lý.

## 5. Yêu cầu bắt buộc cho mỗi nhóm
- 5.1 Quy trình được chọn: giai đoạn phụ trách, ranh giới bắt đầu/kết thúc, quan hệ với giai đoạn trước/sau.
- 5.2 Bài toán cụ thể và tính chất dữ liệu lớn: vì sao cần Big Data; chỉ ra **ít nhất 02** đặc trưng (Volume, Velocity, Variety, Veracity) hoặc nhu cầu xử lý phân tán/mở rộng.
- 5.3 Input: nguồn, cách thu thập, định dạng, schema, số lượng bản ghi/khối lượng, tốc độ phát sinh (nếu có), trường chính, ví dụ bản ghi.
- 5.4 Output: kết quả đầu ra chính xác, định dạng và ví dụ.
- 5.5 Công nghệ: liệt kê từng công nghệ, vai trò, lý do chọn, vị trí trong kiến trúc.
- 5.6 Sơ đồ luồng xử lý: thành phần, luồng dữ liệu, giao thức/định dạng chính, nơi xử lý/lưu trữ.
- 5.7 Kết quả demo/thực nghiệm: log, ảnh chụp, dashboard, dữ liệu trước/sau, throughput/latency/thời gian xử lý, kết quả truy vấn.
- 5.8 Khả năng tái lập: mã nguồn/cấu hình, hướng dẫn chạy, yêu cầu môi trường, dữ liệu mẫu hoặc script sinh dữ liệu.

## 6. Báo cáo
Khuyến nghị khoảng 30 trang A4, không tính bìa, mục lục, tài liệu tham khảo, phụ lục.

Cấu trúc: trang bìa và thông tin nhóm (tên đề tài, học phần, lớp, thành viên, phân công thực tế); tóm tắt khoảng 150–250 từ;
1 Giới thiệu; 2 Cơ sở và công nghệ liên quan; 3 Dữ liệu và yêu cầu; 4 Thiết kế hệ thống; 5 Cài đặt và triển khai;
6 Thực nghiệm và đánh giá; 7 Kết quả demo; 8 Thảo luận; 9 Kết luận; tài liệu tham khảo; phụ lục
(hướng dẫn chạy, cấu hình, schema, API, đường dẫn mã nguồn, bảng phân công/đóng góp).

### Thang điểm (10 điểm)
| Tiêu chí | Điểm |
|---|---|
| Mức độ hoàn thành hệ thống theo phạm vi đã chọn | 2.5 |
| Thiết kế và triển khai kỹ thuật | 2.0 |
| Thực nghiệm và bằng chứng hoạt động | 2.0 |
| Thể hiện đặc trưng Big Data và khả năng mở rộng | 1.5 |
| Phân tích kết quả và thảo luận | 1.0 |
| Chất lượng báo cáo và khả năng tái lập | 1.0 |

## 7. Minh chứng cần nộp
Báo cáo PDF theo mục 6; mã nguồn và cấu hình (repository hoặc file nén, có README cài đặt và chạy); dữ liệu (đường dẫn nguồn, dữ liệu mẫu hoặc script sinh,
không bắt buộc nộp toàn bộ dữ liệu lớn); minh chứng demo (ảnh chụp, log, dashboard, kết quả API hoặc video ngắn); bảng phân công và đóng góp.

## 8. Công cụ AI và trung thực học thuật
Được dùng AI hỗ trợ nhưng nhóm chịu trách nhiệm hoàn toàn và phải hiểu hệ thống. Không nộp mã, sơ đồ hoặc báo cáo AI sinh ra mà không giải thích được.
Quyết định kỹ thuật quan trọng phải có lập luận của nhóm. Dùng AI đáng kể thì ghi ngắn gọn trong phụ lục: công cụ, mục đích, phần đã kiểm tra/chỉnh sửa.
