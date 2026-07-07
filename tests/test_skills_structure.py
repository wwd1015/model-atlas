"""Contract tests for the skills/ tree.

Enforces the Agent Skills conventions adopted from the community standard
(agentskills.io / anthropics/skills) plus Atlas's own two-shape rule:

- every skill folder has a SKILL.md with parseable YAML frontmatter;
- `name` matches the folder and the spec's naming constraints;
- `description` exists, fits the spec's 1024-char cap, and is bracket-free;
- `type` declares the shape, and the folder contains that shape's files;
- SKILL.md stays within the 500-line progressive-disclosure budget;
- `.claude/skills/` carries exactly one discovery symlink per skill.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / "skills"
DISCOVERY_DIR = REPO / ".claude" / "skills"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

TYPE_REQUIRED_FILES = {
    "deterministic": ["helper.py"],
    "llm-runbook": ["prepare_worklist.py", "runbook_template.md"],
}

SKILL_DIRS = sorted(
    d for d in SKILLS_DIR.iterdir()
    if d.is_dir() and not d.name.startswith("_")
)
SKILL_IDS = [d.name for d in SKILL_DIRS]


def frontmatter(skill_dir: Path) -> dict:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{skill_dir.name}: SKILL.md must open with frontmatter"
    block = text.split("\n---", 2)[0].removeprefix("---\n")
    data = yaml.safe_load(block)
    assert isinstance(data, dict), f"{skill_dir.name}: frontmatter is not a YAML mapping"
    return data


def test_skills_exist():
    assert SKILL_DIRS, "no skill folders found under skills/"


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_has_skill_md(skill_dir):
    assert (skill_dir / "SKILL.md").is_file()


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_name_field(skill_dir):
    name = frontmatter(skill_dir).get("name")
    assert name == skill_dir.name, "frontmatter name must equal the folder name"
    assert len(name) <= 64
    assert NAME_RE.fullmatch(name), "name must be kebab-case: lowercase, digits, single hyphens"


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_description_field(skill_dir):
    desc = frontmatter(skill_dir).get("description")
    assert isinstance(desc, str) and desc.strip(), "description is required — it is the trigger"
    assert len(desc) <= 1024, "spec caps description at 1024 chars"
    assert "<" not in desc and ">" not in desc, "angle brackets can inject into system prompts"
    # what-it-does AND when-to-use: the trigger half is the part teams forget.
    assert "use when" in desc.lower() or "use " in desc.lower(), (
        "description should say when to use the skill, not only what it does"
    )


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_type_and_shape(skill_dir):
    skill_type = frontmatter(skill_dir).get("type")
    assert skill_type in TYPE_REQUIRED_FILES, (
        f"type must be one of {sorted(TYPE_REQUIRED_FILES)}"
    )
    for required in TYPE_REQUIRED_FILES[skill_type]:
        assert (skill_dir / required).is_file(), (
            f"{skill_type} skills must ship {required}"
        )


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_body_size_budget(skill_dir):
    lines = (skill_dir / "SKILL.md").read_text(encoding="utf-8").count("\n") + 1
    assert lines <= 500, "keep SKILL.md under 500 lines; move detail to supporting files"


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_discovery_symlink(skill_dir):
    link = DISCOVERY_DIR / skill_dir.name
    assert link.is_symlink(), f"missing .claude/skills/{skill_dir.name} symlink"
    assert link.resolve() == skill_dir.resolve(), f"{link} points at the wrong target"


def test_no_stale_discovery_symlinks():
    stale = [
        p.name for p in DISCOVERY_DIR.iterdir()
        if p.name not in SKILL_IDS
    ]
    assert not stale, f".claude/skills/ entries without a skills/ folder: {stale}"


def test_templates_ship_required_files():
    template_root = SKILLS_DIR / "_template"
    expected = {
        "type-a-deterministic": ["SKILL.md", "helper.py"],
        "type-b-runbook": ["SKILL.md", "prepare_worklist.py", "runbook_template.md"],
    }
    for folder, files in expected.items():
        for f in files:
            assert (template_root / folder / f).is_file(), f"_template/{folder}/{f} missing"
