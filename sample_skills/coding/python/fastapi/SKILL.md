---
name: fastapi

tags:
  - python
  - api
  - web

aliases:
  - fast api
  - fastapi framework

description: Python web framework for building APIs

depends_on:
  - python/basics
  - python/async

related:
  - flask
  - starlette

followed_by:
  - sqlalchemy
  - pytest

uses: 0
last_used: null

steps:
  - setup/project-scaffold
  - coding/python/fastapi/routing
  - coding/python/fastapi/middleware
---

# FastAPI

FastAPI is a modern, fast (high-performance) web framework for building APIs with Python.

## Key Features

- **Fast**: Very high performance, on par with **NodeJS** and **Go**
- **Fast to code**: Increase the speed to develop features by about 200% to 300%
- **Fewer bugs**: Reduce about 40% of human-induced errors
- **Intuitive**: Great editor support with auto-completion
- **Easy**: Designed to be easy to use and learn
- **Short**: Minimize code duplication
- **Robust**: Get production-ready code with automatic interactive documentation
- **Standards-based**: Based on (and fully compatible with) OpenAPI and JSON Schema

## Installation

```bash
pip install fastapi
pip install uvicorn  # for running the server
```

## Quick Start

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

Run with: `uvicorn main:app --reload`
