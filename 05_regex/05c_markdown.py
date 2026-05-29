r"""
正则实战 C：简单 Markdown → HTML 转换器
─────────────────────────────────────────
目标：
  实现一个迷你 Markdown 转换器，支持：
    # 标题、## 子标题       → <h1> / <h2>
    **粗体** / *斜体*       → <strong> / <em>
    `代码`                   → <code>
    [文本](链接)             → <a>
    - 列表项                 → <ul><li>
    ```代码块```             → <pre><code>
    段落自动包 <p>

技术点：
  - 多个 re.sub 串成"转换管道"
  - 顺序很重要：先处理"块级"再处理"行内"
  - 用占位符保护代码块，避免被后续规则误处理
  - 命名分组 + 函数替换组合
"""

import re


# ══════════════════════════════════════════════════════
# 1. 行内（inline）规则：粗体、斜体、行内代码、链接
# ══════════════════════════════════════════════════════
# 注意顺序：
#   - **粗体** 必须在 *斜体* 之前（否则 ** 会被斜体规则提前消耗）
#   - 行内代码 ` 优先级最高，里面的内容不应被任何规则改写

INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")
ITALIC_RE = re.compile(r"\*([^*\n]+)\*")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def render_inline(text: str) -> str:
    text = INLINE_CODE_RE.sub(r"<code>\1</code>", text)
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = ITALIC_RE.sub(r"<em>\1</em>", text)
    text = LINK_RE.sub(r"<a href='\2'>\1</a>", text)
    return text


# ══════════════════════════════════════════════════════
# 2. 块级（block）规则：标题、列表、代码块
# ══════════════════════════════════════════════════════

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def render_headings(md: str) -> str:
    def repl(m: re.Match) -> str:
        level = len(m.group(1))
        content = render_inline(m.group(2))
        return f"<h{level}>{content}</h{level}>"
    return HEADING_RE.sub(repl, md)


# 列表：连续的 - xxx 行合并成一个 <ul>
LIST_BLOCK_RE = re.compile(
    r"(?:^- .+\n?)+",       # 一行或多行以 "- " 开头
    re.MULTILINE,
)
LIST_ITEM_RE = re.compile(r"^- (.+)$", re.MULTILINE)


def render_lists(md: str) -> str:
    def repl(block_match: re.Match) -> str:
        block = block_match.group()
        items = LIST_ITEM_RE.findall(block)
        items_html = "".join(f"  <li>{render_inline(i)}</li>\n" for i in items)
        return f"<ul>\n{items_html}</ul>\n"
    return LIST_BLOCK_RE.sub(repl, md)


# 代码块：```...```
CODE_BLOCK_RE = re.compile(r"```(\w*)\n(.*?)\n```", re.DOTALL)


def render_code_blocks(md: str, store: dict) -> str:
    """先把代码块抽出来用占位符替换，最后再放回去"""
    def repl(m: re.Match) -> str:
        lang = m.group(1) or "plain"
        code = m.group(2)
        # html escape 关键字符
        code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        placeholder = f"@@CODE_BLOCK_{len(store)}@@"
        store[placeholder] = f"<pre><code class='lang-{lang}'>{code}</code></pre>"
        return placeholder
    return CODE_BLOCK_RE.sub(repl, md)


def restore_code_blocks(html: str, store: dict) -> str:
    for placeholder, real in store.items():
        html = html.replace(placeholder, real)
    return html


# ══════════════════════════════════════════════════════
# 3. 段落处理：剩下的非空行包成 <p>
# ══════════════════════════════════════════════════════

PARAGRAPH_RE = re.compile(r"^(?!\s*<|@@)(.+)$", re.MULTILINE)


def render_paragraphs(html: str) -> str:
    """不以 < 开头（不是已经处理过的块）且不是占位符的行包成 <p>"""
    def repl(m: re.Match) -> str:
        line = m.group(1).strip()
        if not line:
            return ""
        return f"<p>{render_inline(line)}</p>"
    return PARAGRAPH_RE.sub(repl, html)


# ══════════════════════════════════════════════════════
# 4. 完整转换器：把所有规则按正确顺序串起来
# ══════════════════════════════════════════════════════

def md_to_html(md: str) -> str:
    # Step 1: 抽出代码块（用占位符替换，避免后续规则破坏代码）
    code_store: dict = {}
    md = render_code_blocks(md, code_store)

    # Step 2: 块级元素（标题、列表）
    md = render_headings(md)
    md = render_lists(md)

    # Step 3: 段落 + 行内元素
    md = render_paragraphs(md)

    # Step 4: 把代码块放回去
    md = restore_code_blocks(md, code_store)

    return md.strip()


# ══════════════════════════════════════════════════════
# 5. 试一下完整例子
# ══════════════════════════════════════════════════════

sample = """\
# Python 学习笔记

## 异步编程

学习 **async/await** 让 Python 支持*异步*操作，关键函数是 `asyncio.run()`。

参考资料：
- 官方文档 [asyncio](https://docs.python.org/3/library/asyncio.html)
- 我的笔记 [async_demo](./01_async/01_sync_vs_async.py)
- 第三方库 **httpx**

## 代码示例

下面是一个最简单的协程：

```python
import asyncio

async def hello():
    print("hi")

asyncio.run(hello())
```

记得用 `asyncio.run()` 作为入口。
"""


if __name__ == "__main__":
    html = md_to_html(sample)
    print(html)
