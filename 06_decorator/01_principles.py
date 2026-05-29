r"""
装饰器第一层：理解原理
─────────────────────────────────────────
要看懂装饰器，必须先理解三件事：
1. Python 函数是"一等公民"
2. 函数可以嵌套，且能"记住"外层变量（闭包）
3. @decorator 只是一个语法糖

把这三件事拼起来，装饰器就清楚了。
"""


# ══════════════════════════════════════════════════════
# 1. 函数是"一等公民"（first-class object）
# ══════════════════════════════════════════════════════
# 函数和 int / str / list 一样，是普通对象，可以：
#   - 赋值给变量
#   - 当作参数传给别的函数
#   - 当作返回值
#   - 放进容器里

def greet(name: str) -> str:
    return f"Hello, {name}"


# (a) 赋值给变量 ── 函数本身是个对象
say_hi = greet
print(say_hi("Alice"))         # Hello, Alice
print(greet is say_hi)         # True   两个名字指向同一个函数对象

# (b) 当作参数传递
def call_twice(func, name):
    return func(name) + " | " + func(name)

print(call_twice(greet, "Bob"))   # Hello, Bob | Hello, Bob

# (c) 当作返回值
def make_greeter(prefix: str):
    def inner(name: str) -> str:
        return f"{prefix}, {name}"
    return inner       # 返回的是"函数对象"，不是调用结果

hello = make_greeter("Hello")
hi = make_greeter("Hi")
print(hello("Alice"))   # Hello, Alice
print(hi("Bob"))        # Hi, Bob


# ══════════════════════════════════════════════════════
# 2. 闭包（closure） ── 内层函数"记住"外层变量
# ══════════════════════════════════════════════════════
# 这是装饰器的核心机制

def counter():
    count = 0           # 外层变量

    def inner():
        nonlocal count  # 声明：我要修改外层的 count（不是新建本地变量）
        count += 1
        return count

    return inner


c1 = counter()      # 创建一个独立的"计数器函数"
c2 = counter()      # 再创建一个，count 互不影响

print(c1())   # 1
print(c1())   # 2
print(c1())   # 3
print(c2())   # 1   ← c2 有自己的 count

# 关键理解：
#   counter() 返回的是 inner 函数对象，
#   但这个 inner "随身带着" 外层的 count 变量。
#   这就是闭包：函数 + 它捕获到的外层变量。


# ══════════════════════════════════════════════════════
# 3. 最简单的装饰器：函数包函数
# ══════════════════════════════════════════════════════
# 装饰器 = 接收一个函数，返回一个"包装后"的新函数

def my_decorator(func):
    """这是一个最简单的装饰器：在调用前后打印日志"""
    def wrapper(*args, **kwargs):
        print(f"  [前置] 即将调用 {func.__name__}")
        result = func(*args, **kwargs)
        print(f"  [后置] 调用完成，返回 {result!r}")
        return result
    return wrapper


# (a) 不用语法糖：手动包装
def add(a, b):
    return a + b

add_with_log = my_decorator(add)
# 现在 add_with_log 就是被"包装"过的版本
print("\n── 手动包装 ──")
result = add_with_log(3, 5)
print(f"最终结果: {result}")


# ══════════════════════════════════════════════════════
# 4. @ 语法糖：和上面完全等价
# ══════════════════════════════════════════════════════

@my_decorator
def multiply(a, b):
    return a * b

# 上面的 @my_decorator 等价于：
#     def multiply(a, b): return a * b
#     multiply = my_decorator(multiply)

print("\n── 用 @ 语法糖 ──")
multiply(4, 6)


# ══════════════════════════════════════════════════════
# 5. 完整地把"语法糖展开"看一遍
# ══════════════════════════════════════════════════════

# 你写的代码：
#
#   @my_decorator
#   def multiply(a, b):
#       return a * b
#
# Python 实际执行的是：
#
#   def multiply(a, b):
#       return a * b
#   multiply = my_decorator(multiply)
#                   ↑           ↑
#                装饰器      原函数
#
# 即：用"装饰器(原函数)"返回的新函数，覆盖原函数的名字。


# ══════════════════════════════════════════════════════
# 6. 拆解执行过程
# ══════════════════════════════════════════════════════

def trace(func):
    print(f"  [装饰阶段] 正在装饰 {func.__name__}")     # 这一句在定义时就执行
    def wrapper(*args, **kwargs):
        print(f"  [调用阶段] {func.__name__}({args}, {kwargs})")
        return func(*args, **kwargs)
    return wrapper


print("\n── 装饰阶段 vs 调用阶段 ──")

@trace
def hello(name):       # ← 定义这一刻 trace 就被执行了一次
    return f"Hi {name}"

# 此时已经打印了 [装饰阶段] 那行
print("(模块已加载完成)")
print(hello("Alice"))     # 此时才打印 [调用阶段]
print(hello("Bob"))       # 每次调用都打印 [调用阶段]


# ══════════════════════════════════════════════════════
# 7. 装饰器到底"做了什么"
# ══════════════════════════════════════════════════════
# 三步：
#   ① 接收原函数 func
#   ② 定义一个新函数 wrapper(*args, **kwargs)，
#      在里面"前后加东西"，中间调用原函数
#   ③ 返回 wrapper
#
# 所有装饰器都是这个套路。区别只是 wrapper 里干什么。


# ══════════════════════════════════════════════════════
# 8. 一个实际的例子：计时装饰器
# ══════════════════════════════════════════════════════

import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  [{func.__name__}] 耗时 {elapsed*1000:.2f}ms")
        return result
    return wrapper


@timer
def slow_sum(n):
    return sum(range(n))


print("\n── 实战：计时装饰器 ──")
result = slow_sum(1_000_000)
print(f"结果: {result}")


# ══════════════════════════════════════════════════════
# 9. 关键速记
# ══════════════════════════════════════════════════════
#
# 函数是对象       ── 可以传、可以返、可以赋值
# 闭包            ── 内层函数能"记住"外层变量
# 装饰器          ── 拿一个函数，返回一个包装后的新函数
# @decorator      ── 等价于 func = decorator(func)
#
# 装饰器的标准模板：
#
#   def my_decorator(func):
#       def wrapper(*args, **kwargs):
#           # 前置代码
#           result = func(*args, **kwargs)
#           # 后置代码
#           return result
#       return wrapper
#
# 把这个模板背下来，装饰器就成功了一半。
