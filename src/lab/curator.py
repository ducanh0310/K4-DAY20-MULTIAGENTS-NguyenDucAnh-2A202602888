"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import re
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy


# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ)."""
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md)."""
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file."""
    if out_dir is None:
        out_dir = ROOT / "skills" / "auto"
    out_dir = Path(out_dir)
    results_path = Path(results_dir) / source_condition

    runs = []
    if results_path.exists():
        for run_file in sorted(results_path.glob("*/run.json")):
            try:
                r = json.loads(run_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            # CRITICAL: ONLY process learning tasks (role == "learn")
            if r.get("role") != "learn":
                continue

            trace_file = run_file.parent / "trace.md"
            trace = (trace_file.read_text(encoding="utf-8")[-6000:]) if trace_file.exists() else ""

            failed = [c for c in r.get("checks", []) if not c.get("passed", True)]
            if failed:
                runs.append({
                    "task": r.get("task", run_file.parent.name),
                    "failed": failed,
                    "trace": trace,
                })

    if not runs:
        print("Warning: no failed checks found in learning runs for condition:", source_condition)
        return []

    prompt_parts = [
        f"You are a skill curator writing SKILL files for an engineering AI agent.",
        f"Below are the failed checks (check names and evaluator feedback/detail) and execution traces of past learning runs.",
        f"Analyze these failures and extract GENERAL procedural skills (rules/conventions/checklists) to prevent similar errors in future tasks.",
        f"Rules for writing skills:",
        f"- Skill must be general: do NOT mention specific task IDs, task-specific file names, answers, or exact numbers.",
        f"- Each skill must have YAML frontmatter with `name` (kebab-case, lowercase alphanumeric with hyphens) and `description` (one sentence stating WHEN TO USE).",
        f"- The body must be concise (at most 40 lines) with actionable guidelines or checklists.",
        f"- Output format MUST be strictly as follows for each skill (at most {max_skills} skills):",
        f"=== SKILL: <name> ===",
        f"---",
        f"name: <name>",
        f"description: <when to use>",
        f"---",
        f"<body lines>",
        f"=== END ===",
        f"\nPAST FAILED RUNS:",
    ]

    for run in runs:
        prompt_parts.append(f"\nTask: {run['task']}")
        prompt_parts.append("Failed checks:")
        for c in run["failed"]:
            prompt_parts.append(f"- {c['name']}: {c.get('detail', '')}")
        if run["trace"]:
            prompt_parts.append(f"Trace (last part):\n{run['trace'][-2000:]}")

    prompt = "\n".join(prompt_parts)

    if model is None:
        model = make_model()

    reply = model.invoke(prompt)
    reply_text = str(reply.content) if hasattr(reply, "content") else str(reply)

    written = []
    blocks = parse_skill_blocks(reply_text)
    for name, text in blocks:
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            print(f"Skipping skill block '{name}' due to validation problems: {problems}")
            continue

        skill_folder = out_dir / name
        skill_folder.mkdir(parents=True, exist_ok=True)
        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(text, encoding="utf-8")
        written.append(skill_file)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
