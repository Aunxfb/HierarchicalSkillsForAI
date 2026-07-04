import re
from pathlib import Path
from io import StringIO
import yaml
from .models import SkillMetadata


def parse_skill_md(filepath: Path) -> tuple[SkillMetadata, str] | None:
    content = filepath.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", content, re.DOTALL)
    if not m:
        return None

    yaml_text = m.group(1)
    body = m.group(2).strip()

    data = yaml.safe_load(yaml_text)
    if not isinstance(data, dict):
        return None

    name = data.get("name")
    if not name:
        return None

    metadata = SkillMetadata(
        name=str(name),
        tags=data.get("tags", []),
        aliases=data.get("aliases", []),
        description=data.get("description", ""),
        depends_on=data.get("depends_on", []),
        related=data.get("related", []),
        followed_by=data.get("followed_by", []),
        uses=data.get("uses", 0),
        last_used=data.get("last_used"),
        steps=data.get("steps", []),
    )
    return metadata, body


_REQUIRED_FIELDS = {
    "tags": [],
    "aliases": [],
    "description": "",
    "depends_on": [],
    "related": [],
    "followed_by": [],
    "uses": 0,
    "last_used": None,
    "steps": [],
}


def _read_frontmatter(content: str) -> tuple[str, dict, str] | None:
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n?)(.*)", content, re.DOTALL)
    if not m:
        return None
    prefix, body = m.group(1), m.group(4)
    data = yaml.safe_load(m.group(2))
    if not isinstance(data, dict):
        return None
    return prefix, data, body


def _write_frontmatter(filepath: Path, prefix: str, data: dict, body: str):
    buf = StringIO()
    yaml.dump(data, buf, default_flow_style=False, sort_keys=False, allow_unicode=True)
    new_content = f"{prefix}{buf.getvalue().rstrip()}\n---\n{body}"
    filepath.write_text(new_content, encoding="utf-8")


def ensure_skill_md_fields(filepath: Path):
    content = filepath.read_text(encoding="utf-8")
    parts = _read_frontmatter(content)
    if not parts:
        return
    prefix, data, body = parts

    name = data.get("name")
    if not name:
        return

    changed = False
    for field, default in _REQUIRED_FIELDS.items():
        if field not in data:
            data[field] = default
            changed = True

    if changed:
        _write_frontmatter(filepath, prefix, data, body)


def update_skill_md_usage(filepath: Path, uses: int, last_used: str):
    content = filepath.read_text(encoding="utf-8")
    parts = _read_frontmatter(content)
    if not parts:
        raise ValueError(f"Invalid SKILL.md format in {filepath}")

    prefix, data, body = parts
    data["uses"] = uses
    data["last_used"] = last_used
    _write_frontmatter(filepath, prefix, data, body)
