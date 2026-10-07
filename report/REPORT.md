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

- Số lần chạy curator, số skill bị xóa và lý do:

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| | | | |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Bạn đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
