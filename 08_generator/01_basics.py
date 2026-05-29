r"""
生成器第一层：基础
─────────────────────────────────────────
内容：
1. 列表 vs 生成器：差别在哪
2. yield 关键字 ── 让函数变成生成器
3. 生成器对象的特性（懒、单次、有状态）
4. 生成器表达式 ── 像列表推导但返回生成器
5. next() / for / StopIteration
6. 用生成器处理"无限序列"和"大文件"
"""


# ══════════════════════════════════════════════════════
# 1. 列表 vs 生成器：先看现象
# ══════════════════════════════════════════════════════

# 列表：一次性把所有数据存进内存
nums_list = [x * x for x in range(10)]
print("── 列表 ──")
print(nums_list)             # 完整列表
print(type(nums_list))       # <class 'list'>


# 生成器：把方括号换成圆括号 ── 完全不同的东西
nums_gen = (x * x for x in range(10))
print("\n── 生成器表达式 ──")
print(nums_gen)              # <generator object ...> ← 还没产出任何值
print(type(nums_gen))        # <class 'generator'>

# 必须遍历才会产出值
for n in nums_gen:
    print(n, end=" ")        # 0 1 4 9 16 25 36 49 64 81
print()


# ══════════════════════════════════════════════════════
# 2. 用 yield 定义生成器函数
# ══════════════════════════════════════════════════════
# 函数体里只要有 yield，它就变成生成器函数

def squares(n):
    for i in range(n):
        yield i * i           # ← 关键字 yield，每次"产出"一个值
        # 注意：这里不是 return，函数不会结束！


print("\n── yield 定义生成器 ──")
g = squares(5)
print(g)                      # <generator object squares ...>
print(list(g))                # [0, 1, 4, 9, 16]


# ══════════════════════════════════════════════════════
# 3. 生成器的核心特性：懒（lazy）
# ══════════════════════════════════════════════════════
# yield 让函数"暂停"，调用方要时再继续

def trace_gen():
    print("  → 进入生成器")
    yield 1
    print("  → 第 1 次恢复")
    yield 2
    print("  → 第 2 次恢复")
    yield 3
    print("  → 函数即将结束")


print("\n── 暂停/恢复机制 ──")
g = trace_gen()
print("g 已创建（但还没执行任何代码）")

print(next(g))                # 触发执行，跑到第一个 yield 暂停
print(next(g))                # 从上次 yield 处继续
print(next(g))                # 再继续

try:
    next(g)                   # 函数已结束，抛 StopIteration
except StopIteration:
    print("  → StopIteration（生成器耗尽）")


# ══════════════════════════════════════════════════════
# 4. 生成器是"一次性"的
# ══════════════════════════════════════════════════════
# 不能像列表那样反复遍历

print("\n── 生成器只能消费一次 ──")
g = squares(3)
print(list(g))                # [0, 1, 4]
print(list(g))                # []  ← 已经空了

# 想反复用：要么转成 list，要么每次重新创建
print(list(squares(3)))       # 重新创建：可以
print(list(squares(3)))       # 再来一次：可以


# ══════════════════════════════════════════════════════
# 5. 生成器 vs 列表：内存对比
# ══════════════════════════════════════════════════════
import sys

# 100 万个数字
big_list = [x for x in range(1_000_000)]
big_gen = (x for x in range(1_000_000))

print("\n── 内存占用对比 ──")
print(f"列表大小:   {sys.getsizeof(big_list):>12,} 字节")
print(f"生成器大小: {sys.getsizeof(big_gen):>12,} 字节")
# 列表会占几 MB，生成器永远只占 200 字节左右
# 因为生成器只记着"算到哪了"，不存数据本身


# ══════════════════════════════════════════════════════
# 6. for 循环背后做了什么
# ══════════════════════════════════════════════════════
# for x in iterable: 等价于：

def manual_iter(iterable):
    it = iter(iterable)
    while True:
        try:
            x = next(it)
        except StopIteration:
            break
        # 处理 x
        print(f"  拿到: {x}")


print("\n── for 的本质 ──")
manual_iter([10, 20, 30])
manual_iter(squares(3))      # 生成器也走一样的协议


# ══════════════════════════════════════════════════════
# 7. 用生成器实现"无限序列"
# ══════════════════════════════════════════════════════
# 列表做不到（内存装不下），生成器轻松做到

def naturals():
    """0, 1, 2, 3, 4, ..."""
    n = 0
    while True:                # ← 真的写无限循环
        yield n
        n += 1


def primes():
    """质数序列：用生成器+生成器"""
    candidate = 2
    while True:
        if all(candidate % p != 0 for p in range(2, int(candidate ** 0.5) + 1)):
            yield candidate
        candidate += 1


print("\n── 无限序列 ──")
# 拿前 10 个自然数
import itertools
print(list(itertools.islice(naturals(), 10)))
# [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# 拿前 10 个质数
print(list(itertools.islice(primes(), 10)))
# [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

# islice 可以"切"无限生成器，自然就停下来了


# ══════════════════════════════════════════════════════
# 8. 实战：流式读取大文件（不全部读入内存）
# ══════════════════════════════════════════════════════
# 文件对象本身就是生成器（按行）
#
# 经典写法：
#
#   with open("huge.log") as f:
#       for line in f:                   # 一次只读一行
#           if "ERROR" in line:
#               print(line)
#
# 100GB 的日志文件也能处理，因为每次只在内存里放一行。

# 演示：构造一个"假"文件流，再过滤
def fake_log_lines():
    yield "INFO  user login\n"
    yield "ERROR db connection failed\n"
    yield "INFO  request received\n"
    yield "ERROR timeout\n"
    yield "INFO  done\n"


def only_errors(lines):
    """对生成器二次加工，仍是生成器"""
    for line in lines:
        if "ERROR" in line:
            yield line


print("\n── 生成器管道 ──")
errors = only_errors(fake_log_lines())
for e in errors:
    print(f"  {e.strip()}")

# 这种 "生成器 → 生成器 → 生成器" 的链式处理叫"管道（pipeline）"
# 每个环节都是惰性的，整条链不会一次性把全部数据加载进内存


# ══════════════════════════════════════════════════════
# 9. 生成器表达式 vs 列表推导式
# ══════════════════════════════════════════════════════

data = [1, 2, 3, 4, 5]

list_comp = [x * 2 for x in data]        # 立即计算，返回 list
gen_expr = (x * 2 for x in data)         # 惰性，返回 generator

print("\n── 表达式形式对比 ──")
print(list_comp)                          # [2, 4, 6, 8, 10]
print(gen_expr)                           # <generator>
print(sum(x * 2 for x in data))           # 直接传给 sum 时不用括号
# 这是 Python 的特殊语法：函数只有一个参数时，圆括号可以省

# 何时用列表推导：
#   - 需要反复遍历
#   - 需要索引、切片、len()
#   - 数据量小
#
# 何时用生成器表达式：
#   - 只遍历一次
#   - 数据量大或无限
#   - 后续要传给 sum / max / min / any / all 这些"消费者"


# ══════════════════════════════════════════════════════
# 10. 速查
# ══════════════════════════════════════════════════════
#
# 生成器函数：
#   def f():
#       yield x        ← 暂停并产出 x
#       yield y        ← 调用 next 时从这里继续
#
# 生成器表达式：
#   (expr for x in iterable if cond)
#
# 关键特性：
#   - 惰性（只在被请求时才计算）
#   - 单次（不能重复遍历，需重新创建）
#   - 有状态（记得自己执行到哪）
#   - 节省内存（不存数据，只存"位置"）
#
# 工程建议：
#   - 数据流大或无限 → 生成器
#   - 需要随机访问 / 多次遍历 → 列表
#   - 配合 sum / max / any / all 时优先用生成器表达式
#   - 文件、网络、数据库结果集 → 天然生成器场景
"""
"""
