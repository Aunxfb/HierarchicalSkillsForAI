from pathlib import Path
import tempfile
import yaml
from src.frontmatter import parse_skill_md


def test_parse_basic_skill():
    content = """\
---
name: fastapi
tags:
  - python
  - api
description: A web framework
steps:
  - setup
  - routing
---
# FastAPI
Content here
"""
    f = Path(tempfile.mktemp(suffix=".md"))
    f.write_text(content)
    result = parse_skill_md(f)
    assert result is not None
    meta, body = result
    assert meta.name == "fastapi"
    assert meta.tags == ["python", "api"]
    assert meta.description == "A web framework"
    assert meta.steps == ["setup", "routing"]
    assert "Content here" in body
    f.unlink()


def test_parse_minimal():
    content = """\
---
name: test
---
"""
    f = Path(tempfile.mktemp(suffix=".md"))
    f.write_text(content)
    result = parse_skill_md(f)
    assert result is not None
    meta, body = result
    assert meta.name == "test"
    assert meta.tags == []
    f.unlink()


def test_parse_no_frontmatter():
    f = Path(tempfile.mktemp(suffix=".md"))
    f.write_text("Just some markdown\nNo frontmatter")
    result = parse_skill_md(f)
    assert result is None
    f.unlink()


def test_parse_missing_name():
    content = """\
---
tags: [python]
---
Content
"""
    f = Path(tempfile.mktemp(suffix=".md"))
    f.write_text(content)
    result = parse_skill_md(f)
    assert result is None
    f.unlink()


def test_parse_aliases_and_relations():
    content = """\
---
name: kerberoasting
aliases:
  - kerberoast
  - kerberos roasting
depends_on:
  - ad/domain-enum
related:
  - asreproasting
followed_by:
  - golden-ticket
---
"""
    f = Path(tempfile.mktemp(suffix=".md"))
    f.write_text(content)
    result = parse_skill_md(f)
    assert result is not None
    meta, _ = result
    assert meta.aliases == ["kerberoast", "kerberos roasting"]
    assert meta.depends_on == ["ad/domain-enum"]
    assert meta.related == ["asreproasting"]
    assert meta.followed_by == ["golden-ticket"]
    f.unlink()
