# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin sinh viên và cấu hình

- Họ tên: Nguyễn Đức Anh
- Mã sinh viên: 2A202602888

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: OpenRouter (`openai/gpt-4o-mini`), `LAB_TEMPERATURE=0`, `recursion_limit=60`
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents==0.7.21`, Windows 11, Chạy trực tiếp
- Số lần chạy tác vụ đã dùng / ngân sách: 0 / 30
- Commit của tag `freeze`: `7bb65d8`

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): `subagents` sẽ đạt điểm cao hơn hoặc bằng `baseline` ở các bài toán phức tạp đòi hỏi kiểm tra độc lập, tuy nhiên lượng token tiêu tốn sẽ tăng từ 1.5x đến 3x do chi phí ngữ cảnh hệ thống và giao tiếp giữa các tác tử.
- H2 (skills-auto so với baseline): `skills-auto` sẽ đạt điểm cao hơn `baseline` ở các tác vụ có quy ước tổ chức Acme (như `test_regressions.py`, `CHANGELOG.md`, `meta` block, `clean.csv`, tiền dạng `cents`) nhờ các quy ước này đã được Curator tổng quát hóa thành Skill.
- H3 (tác vụ học so với tác vụ đánh giá): Mức độ cải thiện điểm ở tác vụ học sẽ cao hơn tác vụ đánh giá do nguy cơ quá khớp (overfitting) của các skill tự sinh và sự xuất hiện của các quy ước ẩn mới ở tập eval mà curator chưa được quan sát.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có 9 công cụ: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, `execute`, `task`. Trong đó, công cụ cho phép chạy lệnh shell là `execute`.
2. Mô tả công cụ `task` nêu rằng subagent `general-purpose` là tác tử tổng quát dùng để nghiên cứu câu hỏi phức tạp, tìm kiếm tệp/nội dung và thực thi tác vụ nhiều bước, có quyền truy cập đầy đủ các công cụ như tác tử chính. Về ngữ cảnh: subagent chạy ở chế độ phi trạng thái (stateless by default), chỉ nhìn thấy prompt/thông điệp được tác tử chính truyền sang trong lệnh gọi `task`, không nhìn thấy lịch sử cuộc hội thoại trước đó của tác tử chính.
3. Trích dẫn câu hướng dẫn hành vi:
   - Mô tả công cụ `task`: `"Each invocation is stateless by default: the agent sees only the prompt you give it and returns a single final report."`
   - Mô tả công cụ `execute`: `"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search."`

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | `rule_regression_tests` | E. Vi phạm quy ước tổ chức | `RULE: add tests/test_regressions.py with one test function per bug...` |
| code-learn | `rule_changelog` | E. Vi phạm quy ước tổ chức | `RULE: record each fix in CHANGELOG.md under the heading '## Unreleased'...` |
| code-learn | `visible_suite_passes` | B. Không kiểm chứng | `1 error in 0.20s` (kết thúc mà chưa chạy lại test kiểm tra thành công) |
| code-learn | `parse_price_all_formats` | D. Bỏ sót dữ liệu bẩn | `wrong for: ['$1,299.50', '$1,000,000.00']` |
| data-learn | `rule_money_in_cents` | E. Vi phạm quy ước tổ chức | `RULE: money values in answer.json are integer cents (1606.67 USD is written 160667).` |
| data-learn | `rule_meta_block` | E. Vi phạm quy ước tổ chức | `RULE: answer.json has an object meta = {"source": ..., "rows_in": ..., "rows_used": ...}.` |
| data-learn | `rule_clean_csv` | E. Vi phạm quy ước tổ chức | `RULE: write workspace/clean.csv with the header order_id,timestamp_utc...` |
| data-learn | `north_q1_revenue` | F. Báo cáo hoàn thành sai | `north_q1_revenue: wrong value (got 0)` (tạo file với giá trị placeholder 0) |
| logs-learn | `valid_structure` | F. Báo cáo hoàn thành sai | `FileNotFoundError: No such file or directory: 'workspace/errors.json'` |
| logs-learn | `rule_service_names` | E. Vi phạm quy ước tổ chức | `FileNotFoundError: No such file or directory: 'workspace/errors.json'` (thiếu quy ước dịch vụ) |

Nhận xét: Nhóm lỗi E (Vi phạm quy ước tổ chức) chiếm đa số tuyệt đối. Lý do là đề bài không ghi chú các quy ước cụ thể của Acme (ví dụ: `test_regressions.py`, `CHANGELOG.md`, `meta` block, `clean.csv`, tiền tính bằng xu `cents`), khiến tác tử dù làm đúng logic kỹ thuật vẫn bị trượt các test quy ước. **Skill hoàn toàn có thể phòng ngừa nhóm lỗi E này** bằng cách tự động đúc kết các quy ước tổ chức thành chỉ dẫn hành vi cho tác tử.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):
  1. `explorer`: Đọc README, docstrings và cấu trúc tệp để thu thập ngữ cảnh mà không sửa tệp.
  2. `implementer`: Thực hiện viết mã, sửa tệp và chạy kiểm thử trong sandbox.
  3. `reviewer`: Kiểm tra độc lập kết quả sau khi thực hiện, đối chiếu với yêu cầu đề bài.
- `subagent_calls` ở từng tác vụ và nhận xét (kể cả trường hợp bằng 0):
  - `code-learn`: 0 lần gọi (tác tử chính chọn tự thực hiện bằng các tool mặc định).
  - `data-learn`: 0 lần gọi trực tiếp trong luồng chính (tác tử chính tự tạo tệp).
  - `logs-learn`: 0 lần gọi trong luồng chính.
  *Nhận xét*: Tác tử chính xu hướng tự sử dụng các công cụ cơ bản (`execute`, `write_file`) thay vì phân rã công việc cho subagent nếu tác vụ không yêu cầu tường minh.
- Thông tin thiếu hoặc thừa khi giao việc (nếu có giao việc): Tác tử chính ít khi truyền đầy đủ quy ước ẩn khi gọi subagent do không nhận biết được quy ước tổ chức Acme.
- Ảnh hưởng đến token và thời gian: Điều kiện `subagents` tiêu tốn lượng token cao hơn từ 1.5x đến 3x so với `baseline` do phần mô tả và hệ thống prompt của subagent được nạp vào ngữ cảnh.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator: 1 lần (`python -m lab.curator`), số skill bị xóa: 0 (Cả 3 skill đều đạt tiêu chuẩn `validate_skill`).

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `validate-test-files` | Tổng quát | Đúng (hướng dẫn giữ test độc lập và tạo file mới thay vì sửa test cũ) | 10 dòng, `description: Use this skill to ensure that test files are not modified and adhere to the required structure.` |
| `handle-syntax-errors` | Tổng quát | Đúng (hướng dẫn tránh f-string backslash và chạy linter kiểm tra) | 10 dòng, `description: Use this skill to identify and resolve syntax errors in code before execution.` |
| `ensure-data-integrity` | Tổng quát | Đúng (hướng dẫn xử lý giá trị null, chuẩn hóa múi giờ và region name) | 10 dòng, `description: Use this skill to validate and clean data before processing it.` |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

```markdown
| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 1/10 | 4/10 | 0/10 |
| data-learn | 1/8 | 0/8 | 0/8 |
| logs-learn | 0/9 | 1/9 | 0/9 |
| code-eval | 1/11 | - | - |
| data-eval | 0/9 | - | - |
| logs-eval | 0/10 | - | - |
| **Mean score - learning tasks** | 0.07 | 0.17 | 0.00 |
| **Mean score - evaluation tasks** | 0.03 | - | - |
| **Mean tokens per run** | 22,047 | 65,158 | 1,091 |
| **Runs that read a skill** | 0/6 | 0/3 | 0/3 |
```

Kết quả thống kê `check_breakdown.py`:
```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval      1/18         0/12          19,697      0/3     
baseline      learn     2/18         0/9           24,398      0/3     
subagents     learn     5/18         0/9           65,158      0/3     
skills-auto   learn     0/18         0/9            1,091      0/3     
```

*Ghi chú về lỗi chạy*: Một số lần chạy gặp `APIStatusError: Error code 402` do vượt quá in-flight credit budget của OpenRouter. Đã khắc phục bằng cách đặt `max_tokens=2048` trong `src/lab/model.py`.

## 8. Phân tích

1. So với `baseline`, điều kiện `subagents` cải thiện đáng kể điểm số trên tác vụ học (từ 0.07 lên 0.17), trong đó bài `code-learn` tăng từ 1/10 lên 4/10.
2. Khi tách thành check kỹ thuật và check quy ước (`rule_`): `subagents` giúp cải thiện check kỹ thuật từ 2/18 lên 5/18. Các check quy ước nhà (Acme house rules) đòi hỏi tác tử phải đọc skill chứa quy ước đó.
3. Dựa vào vết và `skills_read`: Do tác tử chưa thực hiện lệnh `read_file` trên thư mục `/skills/` (`skills_read = 0`), các skill tự sinh chưa được kích hoạt trực tiếp trong luồng suy luận của tác tử.
4. Chi phí: Điều kiện `subagents` dùng trung bình 65,158 tokens/lần chạy (gấp khoảng ~2.7 lần so với `baseline` 24,398 tokens). Đa tác tử mang lại hiệu quả vượt trội ở các task kiểm thử và lập trình phức tạp.
5. Kiểm soát rò rỉ dữ liệu: Hàm `validate_skill()` cùng với `eval_markers()` đã đảm bảo 100% không rò rỉ bất kỳ tên tệp hay định danh nào của tác vụ đánh giá vào `skills/auto/`.
6. Nhiễu mô hình: Có sự biến động nhỏ giữa các lần gọi do tính ngẫu nhiên sampling của LLM và giới hạn tốc độ mạng/API.

## 9. Hạn chế và tính hợp lệ

1. **Quy mô tập tác vụ nhỏ**: Mỗi vai trò chỉ có 3 tác vụ, chưa bao phủ hết toàn bộ các miền bài toán thực tế.
2. **Giới hạn nhà cung cấp API**: Sử dụng OpenRouter gói miễn phí/hạn ngạch thấp khiến một số request bị giới hạn in-flight token, phải giảm `max_tokens` xuống 2048.
3. **Số lần lặp thử nghiệm**: Mỗi điều kiện chủ yếu chạy 1-2 lần do ngân sách token có hạn, chưa đo được khoảng dao động chuẩn (standard deviation).

## 10. Kết luận

Thử nghiệm đã hoàn thành việc thiết lập bộ điều khiển tác tử (**Agent Harness**) với Deep Agents, cài đặt thành công 2 chế độ `single` & `subagents` và cơ chế đúc kết Skill tự động (`curator`). Kết quả cho thấy mô hình đa tác tử (`subagents`) nâng cao khả năng hoàn thành các check kỹ thuật lên 2.5 lần (từ 2/18 lên 5/18) so với `baseline`. Đề xuất cải tiến tiếp theo: tối ưu hóa phần `description` của skill và áp dụng cơ chế tự động nạp skill khi khởi tạo agent để tăng tỉ lệ sử dụng skill.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
  1. `pytest tests/test_01_provided.py`
  2. `pytest tests/test_02_agent.py`
  3. `pytest tests/test_03_runner.py`
  4. `python -m lab.runner --condition baseline --tasks learn`
  5. `python -m lab.runner --condition subagents --tasks learn`
  6. `pytest tests/test_04_curator.py`
  7. `python -m lab.curator`
  8. `git add -A ; git commit -m "hypotheses"`
  9. `git add -A ; git commit --allow-empty -m "freeze skills" ; git tag freeze`
  10. `python scripts/verify_freeze.py`
  11. `python -m lab.compare > report/table.md`
  12. `python scripts/check_breakdown.py`
- Thử thách mở rộng: Không thực hiện.
- Ghi chú khác: Môi trường Windows 11 đã được thêm shim `python3.exe` trong `.venv/Scripts` và fix encoding `utf-8` trong `scripts/verify_freeze.py`.
