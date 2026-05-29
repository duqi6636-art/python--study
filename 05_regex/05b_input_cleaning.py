r"""
正则实战 B：清洗用户输入
─────────────────────────────────────────
场景：
  用户提交的文本千奇百怪，
  在存数据库 / 展示前需要一系列清洗操作

涵盖三类清洗：
  1. 脱敏    ── 隐藏敏感信息（手机、邮箱、身份证、卡号）
  2. 规范化  ── 去多余空白、统一标点、修剪
  3. 过滤    ── 移除危险字符、HTML 标签、不可见字符
"""

import re


# ══════════════════════════════════════════════════════
# 1. 脱敏（masking）
# ══════════════════════════════════════════════════════
# 思路：用 re.sub + 函数替换，针对每种敏感数据写一个 mask

PHONE_RE = re.compile(r"1[3-9]\d{9}")
EMAIL_RE = re.compile(r"([\w.+-]+)@([\w-]+(?:\.[\w-]+)+)")
ID_CARD_RE = re.compile(r"\b(\d{6})(\d{8})(\d{3}[\dXx])\b")
BANK_CARD_RE = re.compile(r"\b(\d{4})(\d{8,12})(\d{4})\b")


def mask_phone(m: re.Match) -> str:
    p = m.group()
    return f"{p[:3]}****{p[7:]}"


def mask_email(m: re.Match) -> str:
    user, domain = m.group(1), m.group(2)
    # 保留首字母 + 末字母，中间打码
    if len(user) <= 2:
        masked = "*" * len(user)
    else:
        masked = user[0] + "*" * (len(user) - 2) + user[-1]
    return f"{masked}@{domain}"


def mask_id_card(m: re.Match) -> str:
    # 18 位身份证：保留前 6 位（地区）+ 后 4 位
    head, _, tail = m.groups()
    return f"{head}********{tail}"


def mask_bank_card(m: re.Match) -> str:
    # 银行卡：保留前 4 + 后 4
    head, mid, tail = m.groups()
    return f"{head}{'*' * len(mid)}{tail}"


def sanitize(text: str) -> str:
    """一次性脱敏所有敏感信息"""
    text = PHONE_RE.sub(mask_phone, text)
    text = EMAIL_RE.sub(mask_email, text)
    text = ID_CARD_RE.sub(mask_id_card, text)
    text = BANK_CARD_RE.sub(mask_bank_card, text)
    return text


sample = """
  客户姓名：张三
  手机：13812345678
  邮箱：alice.work@example.com
  身份证：110101199001011234
  银行卡：6222021234567890123
  备注：紧急联系 18800001111
"""

print("── 脱敏前后对比 ──")
print(sample)
print("→ 脱敏后 →")
print(sanitize(sample))


# ══════════════════════════════════════════════════════
# 2. 规范化（normalize）
# ══════════════════════════════════════════════════════
# 用户输入往往：
#   - 头尾或中间有多余空格
#   - 全角/半角符号混用
#   - 多个换行
#   - 误用中英文标点

# 多个连续空白压成一个空格
def collapse_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


print("\n── 折叠空白 ──")
print(repr(collapse_whitespace("  hello    world  \n\n  python  ")))
# 'hello world python'


# 多个换行压成一个段落分隔
def collapse_blank_lines(s: str) -> str:
    return re.sub(r"\n\s*\n+", "\n\n", s.strip())


text = "段落一\n\n\n\n段落二\n   \n\n段落三"
print("\n── 折叠空行 ──")
print(repr(collapse_blank_lines(text)))


# 中英文标点统一（中文 → 英文）
PUNCT_MAP = {
    "，": ",",
    "。": ".",
    "！": "!",
    "？": "?",
    "：": ":",
    "；": ";",
    """: '"',
    """: '"',
    "'": "'",
    "'": "'",
    "（": "(",
    "）": ")",
}

# 用正则匹配所有中文标点，函数替换查表
ZH_PUNCT_RE = re.compile("|".join(map(re.escape, PUNCT_MAP.keys())))


def to_en_punct(s: str) -> str:
    return ZH_PUNCT_RE.sub(lambda m: PUNCT_MAP[m.group()], s)


print("\n── 标点统一 ──")
print(to_en_punct('你好，世界！这是一个"测试"。'))


# 手机号格式化：去掉所有分隔符，再按需重排
def normalize_phone(s: str) -> str:
    digits = re.sub(r"\D", "", s)         # 只保留数字
    if len(digits) == 11 and digits.startswith("1"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return digits


print("\n── 手机号规范 ──")
print(normalize_phone("138 1234 5678"))      # 138-1234-5678
print(normalize_phone("(138)-1234-5678"))    # 138-1234-5678
print(normalize_phone("+86 138 1234 5678"))  # 8613812345678（不是 11 位，原样返回数字）


# ══════════════════════════════════════════════════════
# 3. 过滤（filter）
# ══════════════════════════════════════════════════════

# 移除 HTML 标签（简单版，不要用来对抗恶意 XSS）
def strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


print("\n── 去 HTML 标签 ──")
print(strip_html("<p>Hello <b>world</b>!</p>"))
# Hello world!


# 移除所有控制字符（不可见的 ASCII 字符，常导致存库或显示出错）
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def strip_control(s: str) -> str:
    return CONTROL_RE.sub("", s)


print("\n── 去控制字符 ──")
dirty = "hello\x00\x01world\x07!"
print(repr(strip_control(dirty)))   # 'helloworld!'


# 过滤 emoji（如果业务要求纯文本）
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001F9FF"   # 各种表情符号
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "☀-⛿"
    "✀-➿]+",
    flags=re.UNICODE,
)


def strip_emoji(s: str) -> str:
    return EMOJI_RE.sub("", s)


print("\n── 去 emoji ──")
print(strip_emoji("好开心😊今天天气🌞真不错🎉"))


# ══════════════════════════════════════════════════════
# 4. 组合：完整的"清洗管道"
# ══════════════════════════════════════════════════════
# 实战中通常把多个清洗步骤串成一个 pipeline

def clean_user_comment(text: str) -> str:
    """评论清洗管道：用户提交评论 → 入库前处理"""
    text = strip_html(text)              # 1. 去 HTML
    text = strip_control(text)           # 2. 去控制字符
    text = to_en_punct(text)             # 3. 统一标点
    text = collapse_whitespace(text)     # 4. 折叠空白
    text = sanitize(text)                # 5. 脱敏
    return text


raw = """
  <script>alert(1)</script>
  你好！我的手机是 13812345678，
  邮箱 hello@example.com。
  欢迎    联系！  \x00
"""

print("\n── 完整管道 ──")
print(f"原始: {raw!r}")
print(f"清洗后: {clean_user_comment(raw)!r}")


# ══════════════════════════════════════════════════════
# 5. 工程建议
# ══════════════════════════════════════════════════════
#
# - 每个清洗步骤写成"独立函数"，输入输出都是 str
#   这样可以自由组合 / 单独测试 / 复用
#
# - 把正则编译成模块级常量
#   PHONE_RE = re.compile(...)
#   而不是在函数里反复 re.compile
#
# - 脱敏用"替换函数"而不是字符串模板
#   因为脱敏长度依赖原文长度，模板做不到
#
# - 标点 / emoji / 控制字符的范围
#   建议查表，写在常量里，避免每次现想 Unicode 区间
#
# - 安全场景慎用正则
#   对抗 XSS / SQL 注入要用专业库（bleach / 参数化查询）
#   正则只适合"善意清洗"，不适合做安全防线
