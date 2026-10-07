import os
import sys
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend

from .model import make_model
from .subagents import get_subagents

# ---- CÓ SẴN, KHÔNG SỬA: system prompt dùng chung cho mọi sinh viên (để đường cơ sở so sánh được) ----
PATHS_NOTE = (
    "PATHS: every path is relative to the sandbox root and never starts with '/'. "
    "The task files are in the folder workspace/ (for example workspace/app.log). "
    "Use exactly this relative form both in the file tools and in the shell (execute); "
    "the shell starts in the sandbox root. "
)
BASE_PROMPT = (
    "You are an engineering assistant working in a sandbox. "
    + PATHS_NOTE
    + "Use the shell to run Python and tests. "
    "When you are done, reply with a short summary that mentions only files you really created or changed."
)
SKILLS_NOTE = (
    " Skills are in the folder skills/ (one sub-folder per skill with a SKILL.md). "
    "As your FIRST action, read the SKILL.md of every skill whose description could apply to the task, "
    "then follow them. Never modify skills/."
)
SUBAGENTS_NOTE = (
    " You have specialised subagents (see the description of the task tool). "
    "For anything beyond a trivial step, delegate to a suitable subagent and put ALL the task rules and file paths "
    "in the delegation message, because a subagent sees only what you send. "
    "Check what a subagent returns before you rely on it."
)
# --------------------------------------------------------------------------------------------------


def make_backend(sandbox: Path):
    """Tạo backend (môi trường thực thi) cho tác tử."""
    python_dir = str(Path(sys.executable).parent)
    paths = [python_dir]

    if sys.platform == "win32":
        for git_path in [r"C:\Program Files\Git\usr\bin", r"C:\Program Files\Git\bin"]:
            if os.path.exists(git_path):
                paths.append(git_path)

    paths.extend(["/usr/local/bin", "/usr/bin", "/bin"])
    env_path = os.pathsep.join(paths)

    env = {
        "PATH": env_path,
        "HOME": str(sandbox),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    return LocalShellBackend(
        root_dir=sandbox,
        virtual_mode=True,
        inherit_env=False,
        env=env,
        timeout=120,
    )


def build_agent(sandbox: Path, mode: str = "single", use_skills: bool = False, model=None):
    """Tạo tác tử Deep Agents."""
    if mode not in ("single", "subagents"):
        raise ValueError(f"Invalid mode: {mode}. Must be 'single' or 'subagents'.")

    kwargs = {}
    prompt = BASE_PROMPT

    if mode == "subagents":
        subs = get_subagents()
        subagents_with_paths = []
        for sub in subs:
            s_dict = dict(sub)
            s_dict["system_prompt"] = f"{s_dict['system_prompt']} {PATHS_NOTE}"
            subagents_with_paths.append(s_dict)
        kwargs["subagents"] = subagents_with_paths
        prompt = prompt + SUBAGENTS_NOTE

    if use_skills:
        kwargs["skills"] = ["/skills/"]
        prompt = prompt + SKILLS_NOTE

    if model is None:
        model = make_model()

    return create_deep_agent(
        model=model,
        system_prompt=prompt,
        backend=make_backend(sandbox),
        **kwargs,
    )

