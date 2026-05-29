r"""
正则第一层：匹配基础
─────────────────────────────────────────
内容：
1. 四个核心函数：match / search / findall / finditer
2. 字符类：\d \w \s [a-z] [^abc] .
3. 量词：* + ? {n} {n,m}
4. 锚点：^ $ \b
"""

import re


# ══════════════════════════════════════════════════════
# 1. 四个核心函数 ── 一定要分清楚区别
# ══════════════════════════════════════════════════════

text = "Order 1001 paid, order 1002 pending, order 1003 paid"

# (1) re.match : 从字符串"开头"匹配，开头匹不上就 None
print(re.match(r"Order", text))     # <re.Match object>
print(re.match(r"paid", text))      # None  ← 不在开头

# (2) re.search : 在整个字符串里"搜索第一个"匹配
print(re.search(r"paid", text))     # 找到第一个 paid 的位置

# (3) re.findall : 返回"所有匹配"组成的列表（字符串列表）
print(re.findall(r"\d+", text))     # ['1001', '1002', '1003']

# (4) re.finditer : 返回"所有匹配"的迭代器（Match 对象）
for m in re.finditer(r"\d+", text):
    print(f"  位置 {m.start()}-{m.end()}, 值: {m.group()}")


# ══════════════════════════════════════════════════════
# 2. Match 对象的常用方法
# ══════════════════════════════════════════════════════

m = re.search(r"order (\d+) (paid|pending)", text, re.IGNORECASE)
if m:
    print(m.group())     # 整个匹配
    print(m.group(0))    # 同上
    print(m.group(1))    # 第一个分组：1001
    print(m.group(2))    # 第二个分组：paid
    print(m.groups())    # 所有分组：('1001', 'paid')
    print(m.span())      # (起始, 结束)


# ══════════════════════════════════════════════════════
# 3. 字符类（character class）
# ══════════════════════════════════════════════════════
#
# \d  → 任意数字           等价于 [0-9]
# \D  → 非数字
# \w  → 字母/数字/下划线    等价于 [a-zA-Z0-9_]
# \W  → 非 \w
# \s  → 空白字符（空格、tab、换行）
# \S  → 非空白
# .   → 任意字符（默认不含换行符）
# [abc]   → a、b 或 c 任一
# [^abc]  → 非 a、b、c
# [a-z]   → a 到 z 任一
# [a-zA-Z0-9]  → 组合
# ^abc        ← 在 [] 外面：锚点，表示"字符串开头"
# [^abc]      ← 在 [] 里面：取反，表示"非 abc"


print(re.findall(r"\d", "a1b2c3"))            # ['1', '2', '3']
print(re.findall(r"\w+", "hello, world!"))    # ['hello', 'world']
print(re.findall(r"[aeiou]", "Hello World"))  # ['e', 'o', 'o']
print(re.findall(r"[^aeiou\s]", "Hello"))     # ['H', 'l', 'l']  非元音非空白


re.findall(r"[^0-9]", "a1b2c3")          # ['a', 'b', 'c']    非数字
re.findall(r"[^a-zA-Z]", "Hello 123!")   # [' ', '1', '2', '3', '!']  非字母
re.findall(r"[^,]+", "apple,pear,banana")# ['apple', 'pear', 'banana']  非逗号



# ══════════════════════════════════════════════════════
# 4. 量词（quantifier）
# ══════════════════════════════════════════════════════
#
# *      → 0 次或多次
# +      → 1 次或多次
# ?      → 0 次或 1 次
# {n}    → 恰好 n 次
# {n,}   → 至少 n 次
# {n,m}  → n 到 m 次

print(re.findall(r"a*",   "aaab"))      # ['aaa', '', '']  ← 注意 * 会匹配空
print(re.findall(r"a+",   "aaab"))      # ['aaa']
print(re.findall(r"a?",   "abc"))       # ['a', '', '', '']
print(re.findall(r"\d{3}", "12 345 6789"))    # ['345', '678']
print(re.findall(r"\d{2,4}", "1 22 333 4444 55555"))
# ['22', '333', '4444', '5555']  ← 5555 是从 55555 中取的前 4 位（贪婪）


# ══════════════════════════════════════════════════════
# 5. 锚点（anchor）
# ══════════════════════════════════════════════════════
#
# ^   → 字符串开头
# $   → 字符串结尾
# \b  → 单词边界
# \B  → 非单词边界

# ^ 和 $
print(re.findall(r"^Order", "Order 1001"))    # ['Order']
print(re.findall(r"^Order", "An Order"))      # []  不在开头
print(re.findall(r"\d+$", "Order 1001"))      # ['1001']

# \b 单词边界 ── 区分"整词"和"子串"
# \bcat\b 就是"整词等于 cat"的意思，相当于其他语言里的"全字匹配"开关
print(re.findall(r"\bcat\b", "cat catalog scatter"))   # ['cat']
print(re.findall(r"cat",     "cat catalog scatter"))   # ['cat', 'cat', 'cat']


# ══════════════════════════════════════════════════════
# 6. 实战例子
# ══════════════════════════════════════════════════════

# (a) 提取手机号（中国大陆，11位，1开头）
# 长度 11 位 = 1 + 1 位（3~9） + 9 位数字
text = "联系电话: 13812345678 或 18800001111，固话 010-12345678"
phones = re.findall(r"1[3-9]\d{9}", text)
print(phones)    # ['13812345678', '18800001111']

# (b) 提取邮箱
# 正则引擎是贪婪的，但后面还有 \.\w+ 必须匹配。它会先尽量多吃，然后回溯让后面的部分能匹配上
text = "邮件 alice@example.com 和 bob.test@my-site.co.uk 请回复"
emails = re.findall(r"[\w.]+@[\w.-]+\.\w+", text)
print(emails)

# (c) 提取价格（支持小数）
text = "苹果 ¥3.5/斤，香蕉 ¥2/斤，葡萄 ¥15.99/斤"
prices = re.findall(r"\d+\.?\d*", text)
print(prices)    # ['3.5', '2', '15.99']

# (d) 验证用户名（字母开头，3-15 位字母数字下划线）
def is_valid_username(name: str) -> bool:
    return bool(re.match(r"^[a-zA-Z]\w{2,14}$", name))

print(is_valid_username("alice123"))   # True
print(is_valid_username("1abc"))       # False  数字开头
print(is_valid_username("ab"))         # False  太短
print(is_valid_username("a" * 20))     # False  太长


# ══════════════════════════════════════════════════════
# 7. 易错点速查
# ══════════════════════════════════════════════════════
#
# (a) 一定用 r"..." 原始字符串，否则反斜杠要写两次
#     re.findall("\\d+", text)   ❌ 难读
#     re.findall(r"\d+", text)   ✅ 推荐
#
# (b) 在字符类 [] 里，大部分元字符变成普通字符
#     [.+*]  → 匹配字面 .、+、*  （不需要转义）
#     但 -、^、] 在 [] 里仍有特殊意义，要小心位置或转义
#
# (c) match 只看开头，想全文搜索用 search
#     "abc" → match(r"b") = None
#     "abc" → search(r"b") = 找到
#
# (d) findall 返回 str 还是 tuple，取决于有没有分组
#     findall(r"\d+", text)        → ['1', '2']         无分组
#     findall(r"(\d)(\d)", text)   → [('1','2'),...]    有分组，返回 tuple
