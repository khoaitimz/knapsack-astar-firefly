# Dataset mẫu cho bài toán 0/1 Knapsack

Mỗi bộ dữ liệu có hai bản `.json` và `.csv` chứa cùng vật phẩm, thứ tự và sức chứa.
Các chỉ số trong bảng tính từ **0** theo thứ tự vật phẩm trong file.

| Dataset | Số vật phẩm | Sức chứa | Giá trị tối ưu | Một tập chỉ số tối ưu | Mục đích |
| --- | ---: | ---: | ---: | --- | --- |
| `sample_01` | 4 | 20.0 | 39.0 | `[0, 3]` | Ví dụ cơ bản trong interface contract. |
| `sample_02` | 3 | 50.0 | 220.0 | `[1, 2]` | Tham lam theo mật độ chỉ đạt 160.0; nghiệm tối ưu chọn hai vật phẩm sau. |
| `sample_03` | 5 | 7.5 | 22.0 | `[1, 2]` | Trọng lượng thập phân, vật phẩm giá trị 0 và vật phẩm vượt sức chứa. |
| `sample_04` | 5 | 15.0 | 24.0 | `[0, 1, 2, 3, 4]` | Tất cả vật phẩm vừa đủ sức chứa; có nhiều nghiệm tối ưu do vật phẩm giá trị 0. |
| `sample_05` | 3 | 2.0 | 0.0 | `[]` | Mọi vật phẩm đều quá nặng; tập rỗng vẫn là nghiệm khả thi và tối ưu. |
| `sample_06` | 12 | 35.0 | 72.0 | `[0, 2, 4, 6, 8, 11]` | Bộ lớn hơn để thử nghiệm lựa chọn tổ hợp và các vật phẩm cùng mật độ. |

Giá trị tối ưu được kiểm chứng bằng vét cạn trong `tests/test_core.py`.
Một dataset có thể có nhiều tập vật phẩm tối ưu khác nhau.

Nạp dữ liệu từ thư mục gốc dự án:

```python
from core.dataset import load_dataset_csv, load_dataset_json

problem_json = load_dataset_json("assets/datasets/sample_02.json")
problem_csv = load_dataset_csv("assets/datasets/sample_02.csv")
assert problem_json == problem_csv
```

JSON sử dụng các trường `name`, `capacity`, `items`; mỗi vật phẩm có `id`, `value`, `weight`.
CSV bắt đầu bằng dòng `# capacity: <sức chứa>` và tiêu đề `id,value,weight`.
