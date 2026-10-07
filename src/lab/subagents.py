"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": "Use this subagent to read files, inspect project structures, read README/docstrings, and gather background context without modifying any files.",
            "system_prompt": "You are an exploration subagent. Your job is to carefully inspect files, read instructions/READMEs, analyze data structures or log formats, and return a accurate, detailed summary of your findings. Do NOT modify any files.",
        },
        {
            "name": "implementer",
            "description": "Use this subagent to perform code changes, create/update data processing scripts, fix bugs, and run tests or Python scripts in the sandbox.",
            "system_prompt": "You are an implementation subagent. Your job is to write code, modify files, run tests or scripts using the shell tool, and verify that the implementation works correctly according to specifications before reporting back.",
        },
        {
            "name": "reviewer",
            "description": "Use this subagent to perform independent code review, test verification, edge case checking, and schema validation after implementation.",
            "system_prompt": "You are a review subagent. Your job is to independently verify that solutions satisfy all task requirements and edge cases. Run tests or inspection commands, check for regression issues, and report any discrepancies without editing code directly.",
        },
    ]

