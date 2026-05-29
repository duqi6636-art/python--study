r"""
正则第三层：替换、分割、编译
─────────────────────────────────────────
内容：
1. re.sub  ── 替换（含用函数动态替换、反向引用回填）
2. re.subn ── 替换并返回替换次数
3. re.split ── 用正则切分字符串
4. re.compile ── 预编译，性能 + 复用
5. 标志位：IGNORECASE / MULTILINE / DOTALL / VERBOSE
"""

import re


# ══════════════════════════════════════════════════════
# 1. re.sub ── 基础替换
# ══════════════════════════════════════════════════════

# 把所有数字替换成 #
text = "订单 1001 金额 99.5"
print(re.sub(r"\d+", "#", text))    # '订单 # 金额 #.#'

# count 参数：限制最多替换几次
print(re.sub(r"\d+", "#", text, count=1))   # '订单 # 金额 99.5'


# ══════════════════════════════════════════════════════
# 2. re.sub 的"反向引用回填" ── 重排或加工原文
# ══════════════════════════════════════════════════════

# 把 "姓 名" 改成 "名 姓"
text = "Wang Alice, Li Bob"
print(re.sub(r"(\w+) (\w+)", r"\2 \1", text))
# 'Alice Wang, Bob Li'

# 用命名分组：\g<name> 比 \1 更可读
text = "2026-05-25"
print(re.sub(r"(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})",
             r"\g<d>/\g<m>/\g<y>", text))
# '25/05/2026'


# ══════════════════════════════════════════════════════
# 3. re.sub 的"函数替换" ── 最强武器
# ══════════════════════════════════════════════════════
# 当替换逻辑不是简单字符串拼接时，传一个函数进去
# 函数接收 Match 对象，返回字符串

# 把所有数字 +10
def add_10(m: re.Match) -> str:
    n = int(m.group())
    return str(n + 10)

print(re.sub(r"\d+", add_10, "苹果 5 元，香蕉 3 元"))
# '苹果 15 元，香蕉 13 元'


# 大写所有 \b 后第一个字母（句首字母大写）
def to_upper(m: re.Match) -> str:
    return m.group().upper()

print(re.sub(r"\b\w", to_upper, "hello world"))
# 'Hello World'


# 脱敏：把手机号中间 4 位变成 ****
def mask_phone(m: re.Match) -> str:
    p = m.group()
    return p[:3] + "****" + p[7:]

text = "联系 13812345678 或 18800001111"
print(re.sub(r"1[3-9]\d{9}", mask_phone, text))
# '联系 138****5678 或 188****1111'


# ══════════════════════════════════════════════════════
# 4. re.subn ── 替换 + 返回替换次数
# ══════════════════════════════════════════════════════

result, count = re.subn(r"\d+", "#", "a1b2c3")
print(result, count)    # 'a#b#c#' 3


# ══════════════════════════════════════════════════════
# 5. re.split ── 用正则切分（比 str.split 强大）
# ══════════════════════════════════════════════════════

# 多种分隔符（任何空白、逗号、分号）
text = "apple, banana;  cherry  pear, orange"
print(re.split(r"[,;]\s*|\s+", text))
# ['apple', 'banana', 'cherry', 'pear', 'orange']

# 分割但保留分隔符（用捕获分组）
text = "1+2-3*4"
print(re.split(r"([+\-*/])", text))
# ['1', '+', '2', '-', '3', '*', '4']

# maxsplit 参数：最多切几次
print(re.split(r"\s+", "a b c d e", maxsplit=2))
# ['a', 'b', 'c d e']


# ══════════════════════════════════════════════════════
# 6. re.compile ── 预编译
# ══════════════════════════════════════════════════════
# 同一个正则反复使用时，编译一次比每次现解析快得多

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

texts = [
    "联系 alice@example.com",
    "邮件 bob.test@my-site.co.uk",
    "客服 service@company.cn",
]
for t in texts:
    m = EMAIL.search(t)     # 直接用编译好的对象，方法名一样
    if m:
        print(m.group())

# 编译对象支持所有 re 模块函数：search / match / findall / sub ...
print(EMAIL.findall("a@x.com or b@y.org"))


# ══════════════════════════════════════════════════════
# 7. 标志位 (flags)
# ══════════════════════════════════════════════════════

# (a) re.IGNORECASE / re.I ── 忽略大小写
print(re.findall(r"python", "Python PYTHON pYTHON", re.IGNORECASE))
# ['Python', 'PYTHON', 'pYTHON']

# (b) re.MULTILINE / re.M ── ^ 和 $ 匹配每行的开头/结尾
text = "line1\nline2\nline3"
print(re.findall(r"^line\d", text))             # ['line1']  默认只匹配整体开头
print(re.findall(r"^line\d", text, re.M))       # ['line1', 'line2', 'line3']

# (c) re.DOTALL / re.S ── 让 . 也能匹配换行符
text = "abc\ndef"
print(re.findall(r"a.+f", text))                # []          默认 . 不含 \n
print(re.findall(r"a.+f", text, re.DOTALL))     # ['abc\ndef']

# (d) 多个标志组合：用 |
flags = re.IGNORECASE | re.MULTILINE
print(re.findall(r"^hello", "Hello\nHELLO\nworld", flags))
# ['Hello', 'HELLO']


# ══════════════════════════════════════════════════════
# 8. re.VERBOSE / re.X ── 可读的复杂正则（重要）
# ══════════════════════════════════════════════════════
# 允许在正则里加空白和注释，让长正则不再是"火星文"

PHONE = re.compile(r"""
    1               # 必须 1 开头
    [3-9]           # 第 2 位 3-9
    \d{9}           # 后 9 位数字
""", re.VERBOSE)

print(PHONE.findall("电话 13812345678 或 18800001111"))


# 复杂版：邮箱
EMAIL_X = re.compile(r"""
    [\w.+-]+        # 用户名：字母/数字/下划线/. + -
    @
    [\w-]+          # 域名主体（不含点）
    (?:\.[\w-]+)+   # 一个或多个 .xxx 后缀
""", re.VERBOSE)

print(EMAIL_X.findall("a@x.com 或 alice+work@my-site.co.uk"))


# 注意：VERBOSE 模式下，空格被忽略
# 想匹配字面空格要写 \  或放在字符类里 [ ]
SPACE_PATTERN = re.compile(r"""
    \w+             # 单词
    \              # 一个空格（用反斜杠转义）
    \w+             # 单词
""", re.VERBOSE)
print(SPACE_PATTERN.search("hello world").group())


# ══════════════════════════════════════════════════════
# 9. 综合实战：一个 Markdown 链接转换器
# ══════════════════════════════════════════════════════
# 把 "[text](url)" 转成 HTML "<a href='url'>text</a>"

MD_LINK = re.compile(r"""
    \[              # 字面 [
    (?P<text>[^\]]+) # 链接文本：除 ] 之外
    \]              # 字面 ]
    \(              # 字面 (
    (?P<url>[^)]+)  # URL：除 ) 之外
    \)              # 字面 )
""", re.VERBOSE)


def md_to_html(m: re.Match) -> str:
    return f"<a href='{m['url']}'>{m['text']}</a>"


md = "查看 [文档](https://docs.example.com) 和 [源码](https://github.com/x/y)"
print(MD_LINK.sub(md_to_html, md))


# ══════════════════════════════════════════════════════
# 10. 工程建议
# ══════════════════════════════════════════════════════
#
# 何时用 re.compile：
#   - 同一个正则用 ≥ 2 次
#   - 在循环里使用
#   - 写在模块顶部当常量
#
# 何时用 re.VERBOSE：
#   - 正则超过一行能写下的复杂度
#   - 团队协作的项目（其他人要能读懂）
#
# 替换函数 vs 字符串模板：
#   - 简单回填字段 → 用 r"\g<name>" 字符串模板
#   - 需要计算、判断、查表 → 用函数
#
# 命名约定：
#   - 编译后的正则用全大写常量：EMAIL_RE / PHONE_RE
#   - 表达"这是个正则常量"，避免混淆
