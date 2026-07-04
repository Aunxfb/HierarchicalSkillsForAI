---
name: tokio
tags:
- rust
- async
- concurrent
aliases:
- tokio runtime
- rust async
description: Asynchronous runtime for the Rust programming language
depends_on:
- rust/basics
- rust/async
related:
- async-std
- smol
uses: 0
last_used: null
steps: []
followed_by: []
---
# Tokio

Tokio is an asynchronous runtime for the Rust programming language.

## Key Features

- **Fast**: Built on top of epoll, kqueue, and IOCP
- **Reliable**: Used in production by companies like AWS, Microsoft, and Discord
- **Scalable**: Handle thousands of concurrent connections

## Example

```rust
#[tokio::main]
async fn main() {
    let handle = tokio::spawn(async {
        println!("Hello from tokio!");
    });
    handle.await.unwrap();
}
```
