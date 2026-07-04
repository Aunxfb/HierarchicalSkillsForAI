---
name: pytest
tags:
- python
- testing
aliases:
- pytest framework
- python test
description: Python testing framework for writing and running tests
depends_on:
- python/basics
related:
- unittest
- nose2
uses: 0
last_used: null
steps: []
followed_by: []
---
# pytest

pytest is a mature full-featured Python testing tool.

## Installation

```bash
pip install pytest
```

## Basic Usage

```python
# test_sample.py
def test_addition():
    assert 1 + 1 == 2

def test_string():
    assert "hello".upper() == "HELLO"
```

Run with: `pytest`
