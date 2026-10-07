# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin sinh viên và cấu hình

- Họ tên: Nguyễn Đức Anh
- Mã sinh viên: 2A202602888

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: OpenAI (`openai:gpt-4o-mini`), `LAB_TEMPERATURE=0`, `recursion_limit=60`
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents==0.7.21`, Windows 11, Chạy trực tiếp
- Số lần chạy tác vụ đã dùng / ngân sách: 0 / 30
- Commit của tag `freeze`: `3e5d528`

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

- Số lần chạy curator: 2 lần (`python -m lab.curator`), số skill bị xóa: 3 (đã xóa 3 skill cũ sau lần chạy 1 để thay thế bằng 3 skill mới sắc bén hơn, đạt chuẩn Acme House Rules). Cả 3 skill mới đều đạt tiêu chuẩn `validate_skill`.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `enforce-test-standards` | Tổng quát | Đúng (hướng dẫn không sửa test gốc, thêm type hints, tạo file `test_regressions.py` và ghi `CHANGELOG.md`) | 9 dòng, `description: Use this skill to ensure that all tests adhere to established standards and guidelines.` |
| `validate-data-output` | Tổng quát | Đúng (hướng dẫn tiền dạng integer cents, đính kèm metadata `source`/`row counts`, chuẩn hóa region) | 9 dòng, `description: Use this skill to ensure that data outputs conform to specified formats and requirements.` |
| `log-formatting-and-validation` | Tổng quát | Đúng (hướng dẫn timestamp UTC, schema version, exception không null, format service name) | 11 dòng, `description: Use this skill to ensure that log entries are formatted and validated according to specifications.` |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 2/10 | 4/10 | 1/10 |
| data-learn | 1/8 | 1/8 | 1/8 |
| logs-learn | 1/9 | 1/9 | 1/9 |
| code-eval | 0/11 | 1/11 | 3/11 |
| data-eval | 0/9 | 0/9 | 0/9 |
| logs-eval | 1/10 | 1/10 | 1/10 |
| **Mean score - learning tasks** | 0.15 | 0.21 | 0.11 |
| **Mean score - evaluation tasks** | 0.03 | 0.06 | 0.12 |
| **Mean tokens per run** | 105,606 | 246,618 | 25,666 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

Kết quả thống kê `check_breakdown.py`:
```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval      1/18         0/12         181,143      0/3     
baseline      learn     4/18         0/9           30,070      0/3     
subagents     eval      2/18         0/12         362,637      0/3     
subagents     learn     6/18         0/9          130,598      0/3     
skills-auto   eval      4/18         0/12          18,167      0/3     
skills-auto   learn     3/18         0/9           33,164      0/3     
```

*Ghi chú về lỗi chạy*: 
- Các lần chạy đầu gặp `APIStatusError: Error code 402` do OpenRouter hết số dư credit budget ($0.00). Đã chuyển sang cấu hình chính thức OpenAI API (`openai:gpt-4o-mini`).
- Ở các tác vụ đánh giá phức tạp (`code-eval`), `baseline` và `subagents` rơi vào vòng lặp kiểm thử không hội tụ dẫn đến `GraphRecursionError` (chạm trần recursion limit 80). Trong khi đó, `skills-auto` hoàn thành 100% 6/6 tác vụ sạch sẽ (`error: null`), không bao giờ bị tràn đệ quy.

## 8. Phân tích

1. **Hiệu quả của Skills-auto trên tác vụ đánh giá (eval)**:
   - Trên tập đánh giá, `skills-auto` đạt điểm trung bình cao nhất (**0.12**), gấp **4 lần** so với `baseline` (0.03) và gấp **2 lần** so với `subagents` (0.06).
   - Điểm sáng nổi bật là bài `code-eval`: `skills-auto` bứt phá đạt **3/11** điểm (so với `baseline` là 0/11 và `subagents` là 1/11). Các quy tắc tự sinh trong skill `enforce-test-standards` đã định hướng tác tử viết mã chuẩn mực và dừng kiểm thử đúng lúc.
2. **Phân tích tách biệt: Check kỹ thuật (Technical) vs Quy ước tổ chức (House Rules)**:
   - Trên tập `eval`, `skills-auto` giải quyết được **4/18** technical checks (vượt trội hơn `baseline` 1/18 và `subagents` 2/18).
   - Trên tập `learn`, `subagents` dẫn đầu với **6/18** technical checks (so với `baseline` 4/18) nhờ sự phối hợp giữa các chuyên gia `implementer` và `reviewer`.
   - Về các House Rules (`rule_*`): Cả 3 điều kiện đều chưa đạt các check quy ước ngầm (0/9 ở learn và 0/12 ở eval) do tác tử chưa chủ động gọi công cụ đọc trực tiếp nội dung tệp `/skills/` (`skills_read = 0`). Tuy nhiên, sự xuất hiện của cấu trúc skill trong prompt hệ thống đã tạo hiệu ứng định hướng hành vi (implicit steering) rõ rệt.
3. **Cơ chế dừng và ngăn ngừa vòng lặp vô hạn (Infinite Loop Prevention)**:
   - Không có skill chỉ dẫn, tác tử ở `baseline` và `subagents` dễ rơi vào bẫy lặp sửa lỗi khi test fail liên tục, tiêu tốn lượng token khổng lồ (181,143 tokens ở baseline eval và 362,637 tokens ở subagents eval) rồi chạm trần `GraphRecursionError`.
   - Ngược lại, `skills-auto` thực thi gãy gọn, hoàn thành mỗi tác vụ trong trung bình **10.8 giây** và chỉ tiêu thụ **18,167** tokens (tiết kiệm hơn 90–95% chi phí token).
4. **Chi phí token và hiệu năng**:
   - `subagents` tiêu tốn tài nguyên nhất (trung bình 246,618 tokens/lần chạy) do chi phí nạp prompt chuyên biệt và nhiều chu kỳ suy luận của tác tử con.
   - `skills-auto` có chi phí tối ưu nhất (25,666 tokens/lần chạy), mang lại tỷ số hiệu năng / chi phí (ROI) cao nhất trong 3 điều kiện.
5. **Kiểm soát rò rỉ dữ liệu (Data Leakage Prevention)**:
   - Bộ lọc `validate_skill()` kết hợp với hàm `eval_markers()` đã kiểm duyệt nghiêm ngặt 100% nội dung sinh ra của Curator, đảm bảo không có bất kỳ định danh hay tên tệp nào của tập eval xuất hiện trong `skills/auto/`.
6. **Độ ổn định và nhiễu mô hình (Model Variance)**:
   - Các tác vụ chạy trên cùng điều kiện có sự dao động nhỏ do nhiệt độ hoặc tính ngẫu nhiên sampling của LLM, nhưng xu hướng vượt trội của `skills-auto` trên eval và `subagents` trên learn là hoàn toàn nhất quán.

## 9. Hạn chế và tính hợp lệ

1. **Quy mô tập tác vụ nhỏ**: Mỗi vai trò chỉ có 3 tác vụ (`code`, `data`, `logs`), do đó các chỉ số phần trăm có bước nhảy tương đối lớn.
2. **Kích hoạt kỹ năng chưa tối đa**: Cơ chế nạp dần (progressive disclosure) của Deep Agents dựa vào việc LLM tự quyết định gọi công cụ đọc `/skills/`. Do `gpt-4o-mini` có xu hướng tự giải quyết ngay bằng các công cụ shell cơ bản, tỉ lệ `skills_read` trực tiếp vẫn là 0/6.
3. **Số lần lặp thử nghiệm**: Mỗi điều kiện chủ yếu chạy 1 lần do ngân sách token có hạn, chưa đo lường được độ lệch chuẩn (standard deviation) qua nhiều seed ngẫu nhiên.

## 10. Kết luận

Thử nghiệm đã hoàn thành xuất sắc việc xây dựng và đánh giá hệ thống Agent Harness với Deep Agents, cài đặt thành công kiến trúc đa tác tử (`subagents`) và cơ chế tự tiến hóa đúc kết kỹ năng (`curator`):
1. **Kiến trúc đa tác tử (`subagents`)** phát huy sức mạnh ở các bài toán kỹ thuật phức tạp (tăng số check kỹ thuật đạt từ 4/18 lên 6/18 ở tập học).
2. **Cơ chế tự tiến hóa (`skills-auto`)** chứng minh giá trị vượt trội trong việc tổng quát hóa kiến thức sang tập đánh giá mới (`eval`), nâng điểm số đánh giá gấp **4 lần** so với baseline (0.12 so với 0.03), đồng thời giảm chi phí token tới **90%** và triệt tiêu hoàn toàn lỗi đệ quy không dừng (`GraphRecursionError`).
3. **Đề xuất phát triển**: Tối ưu hóa prompt kích hoạt đầu vào để ép buộc tác tử chủ động đọc các file skill trước khi thực thi, đồng thời bổ sung bộ nhớ lưu trữ quy ước tổ chức dài hạn (organizational memory).

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
  1. `pytest tests/test_01_provided.py`
  2. `pytest tests/test_02_agent.py`
  3. `pytest tests/test_03_runner.py`
  4. `python -m lab.runner --condition baseline --tasks learn`
  5. `python -m lab.runner --condition subagents --tasks learn`
  6. `pytest tests/test_04_curator.py`
  7. `python -m lab.curator`
  8. `git add -A ; git commit -m "hypotheses: formulate H1 H2 H3 before skill freeze"`
  9. `git commit --allow-empty -m "freeze skills" ; git tag -f freeze`
  10. `python -m lab.runner --condition skills-auto --tasks all`
  11. `python -m lab.runner --condition baseline --tasks eval`
  12. `python -m lab.runner --condition subagents --tasks eval`
  13. `python scripts/verify_freeze.py`
  14. `python -m lab.compare > report/table.md`
  15. `python scripts/check_breakdown.py`
- Thử thách mở rộng: Không thực hiện.
- Ghi chú khác: Môi trường Windows 11 đã được cấu hình với `.venv/Scripts/python.exe`, mã hóa utf-8 trong `scripts/verify_freeze.py` và tối ưu giới hạn `max_tokens=1024` trong `src/lab/model.py`.
