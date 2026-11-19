# TỔNG QUAN THUẬT TOÁN & BẢNG SO SÁNH – KNAPSACK AI PROJECT

**Chủ sở hữu:** TV3

---

## 1. So sánh phương pháp giải

| Tiêu chí | A* Search (TV2) | Firefly Algorithm (TV3) |
| :--- | :--- | :--- |
| **Bản chất** | Tìm kiếm nhánh cận chính xác (Exact Tree Search) | Metaheuristic tiến hóa bầy đàn (Swarm Intelligence) |
| **Đảm bảo tối ưu** | Có (nếu duyệt hết cây trạng thái mà không chạm ngưỡng timeout/nodes) | Không đảm bảo tối ưu toàn cục, tiệm cận nghiệm tốt |
| **Độ phức tạp thời gian** | Số mũ $O(2^n)$ trong trường hợp xấu nhất | Đa thức $O(I \cdot P^2 \cdot n)$ với $I$ vòng lặp, $P$ đom đóm, $n$ vật phẩm |
| **Không gian trạng thái** | Cây quyết định nhị phân có thứ tự mật độ giảm dần | Không gian liên tục $\mathbb{R}^n$ ánh xạ qua Sigmoid $\sigma(y) \ge 0.5$ |
| **Xử lý vi phạm sức chứa** | Cắt nhánh trực tiếp khi vượt capacity hoặc bị tỉa cận | Hàm `repair_solution(..., strategy="density_asc")` loại vật phẩm mật độ thấp |
| **Độ phụ thuộc ngẫu nhiên** | Hoàn toàn tất định (Deterministic) | Ngẫu nhiên có kiểm soát bởi `seed` |

---

## 2. Thông số điều khiển (Hyperparameters)

### 2.1. A* Search
- `time_limit_sec`: Mặc định 5.0s.
- `max_expanded_nodes`: Mặc định 100,000 nút.

### 2.2. Firefly Algorithm (`FireflyConfig`)
- `population_size`: Kích thước đàn đom đóm (mặc định 20).
- `max_iterations`: Số vòng lặp tối đa (mặc định 100).
- `alpha`: Hệ số nhiễu ngẫu nhiên ban đầu (mặc định 0.5).
- `alpha_decay`: Hệ số giảm dần của nhiễu sau mỗi vòng lặp (mặc định 0.98).
- `beta0`: Độ hấp dẫn cực đại tại khoảng cách $r = 0$ (mặc định 1.0).
- `gamma`: Hệ số hấp thụ ánh sáng của môi trường (mặc định 1.0).
- `coord_min`, `coord_max`: Biên tọa độ liên tục (mặc định $[-6.0, 6.0]$).
- `seed`: Hạt giống ngẫu nhiên phục vụ tái lập (mặc định 42).
- `time_limit_sec`: Ngưỡng ngắt thời gian (mặc định 5.0s).
