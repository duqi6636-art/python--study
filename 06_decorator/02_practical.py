r"""
装饰器第二层：实用装饰器
─────────────────────────────────────────
本层关注三件事：
1. 为什么要用 functools.wraps（保留原函数信息）
2. 带参数的装饰器（三层嵌套）
3. 几个超实用的装饰器：日志 / 计时 / 缓存 / 重试
"""

import functools
import time
import random


# ══════════════════════════════════════════════════════
# 1. 不用 functools.wraps 的"信息丢失"问题
# ══════════════════════════════════════════════════════

def bad_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@bad_decorator
def greet(name: str) -> str:
    """打招呼函数"""
    return f"Hello, {name}"


# 看看被装饰后 greet 的"身份信息"
print(greet.__name__)     # 'wrapper'   ← 名字变了！
print(greet.__doc__)      # None        ← docstring 丢了！

# 这会带来麻烦：
#   - 调试时打印的函数名是 wrapper，看不出原函数
#   - help(greet) 看不到原本的 docstring
#   - 一些框架（FastAPI、pytest）依赖函数名做路由 / 测试发现，会出错


# ══════════════════════════════════════════════════════
# 2. functools.wraps ── 一行解决
# ══════════════════════════════════════════════════════

def good_decorator(func):
    @functools.wraps(func)        # ← 关键：把 func 的信息复制给 wrapper
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@good_decorator
def hello(name: str) -> str:
    """打招呼函数（保留版）"""
    return f"Hi, {name}"


print(hello.__name__)     # 'hello'        ← 保住了
print(hello.__doc__)      # '打招呼函数（保留版）'
print(hello.__wrapped__)  # <function hello>  ← 还能拿到原函数

# 工程铁律：
#   写装饰器时，永远在 wrapper 上加 @functools.wraps(func)


# ══════════════════════════════════════════════════════
# 3. 带参数的装饰器 ── 三层嵌套
# ══════════════════════════════════════════════════════
# 普通装饰器：@decorator
# 带参数：    @decorator(param=value)
# 后者多套一层

# 比如想要 @repeat(times=3)，让函数被调用 3 次
def repeat(times: int):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            results = []
            for _ in range(times):
                results.append(func(*args, **kwargs))
            return results
        return wrapper
    return decorator


@repeat(times=3)
def roll_dice():
    return random.randint(1, 6)


print("\n── repeat(times=3) ──")
print(roll_dice())   # 比如 [4, 1, 6]


# 三层结构对照：
#
#   @repeat(times=3)             ← 调用 repeat(3) 拿到 decorator
#   def roll_dice(): ...         ← 再用 decorator 包装 roll_dice
#
# 等价于：
#   roll_dice = repeat(3)(roll_dice)
#                  ↑      ↑
#              第一层    第二层
#
# 三层从外到内：
#   ① repeat(times)        接收装饰器参数
#   ② decorator(func)      接收被装饰的函数
#   ③ wrapper(*args, **kw) 接收原函数的参数


# ══════════════════════════════════════════════════════
# 4. 实战 1：日志装饰器
# ══════════════════════════════════════════════════════

def log_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 把参数格式化成可读字符串
        all_args = list(map(repr, args)) + [f"{k}={v!r}" for k, v in kwargs.items()]
        sig = ", ".join(all_args)
        print(f"  → {func.__name__}({sig})")
        result = func(*args, **kwargs)
        print(f"  ← {func.__name__} = {result!r}")
        return result
    return wrapper


@log_call
def divide(a, b):
    return a / b


print("\n── 日志装饰器 ──")
divide(10, 3)
divide(8, b=2)


# ══════════════════════════════════════════════════════
# 5. 实战 2：计时装饰器（带参数版）
# ══════════════════════════════════════════════════════
# 让用户自己决定单位（毫秒/微秒）

def timeit(unit: str = "ms"):
    factor = {"s": 1, "ms": 1_000, "us": 1_000_000}[unit]

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * factor
            print(f"  [{func.__name__}] 耗时 {elapsed:.2f}{unit}")
            return result
        return wrapper
    return decorator


@timeit(unit="ms")
def slow_sum(n):
    return sum(range(n))


@timeit(unit="us")
def fast_add(a, b):
    return a + b


print("\n── 计时装饰器（带参数） ──")
slow_sum(1_000_000)
fast_add(1, 2)


# ══════════════════════════════════════════════════════
# 6. 实战 3：缓存装饰器（自己实现一遍 lru_cache）
# ══════════════════════════════════════════════════════
# 同样的输入只算一次，结果存起来

def memoize(func):
    cache = {}     # 闭包：每个被装饰函数有独立的 cache

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 用参数作为 key（kwargs 要排序后才稳定）
        key = (args, tuple(sorted(kwargs.items())))
        if key in cache:
            print(f"  [缓存命中] {func.__name__}{args}")
            return cache[key]
        result = func(*args, **kwargs)
        cache[key] = result
        return result

    wrapper.cache_clear = lambda: cache.clear()    # 加个清缓存的方法
    return wrapper


@memoize
def fib(n):
    """斐波那契：递归实现，没缓存会指数爆炸"""
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


print("\n── 缓存装饰器 ──")
print(fib(10))    # 第一次计算
print(fib(10))    # 直接命中缓存

# 不带缓存时 fib(35) 要跑几秒
# 带了缓存：每个 n 只算一次，瞬间返回
print(fib(35))


# ══════════════════════════════════════════════════════
# 7. 实战 4：重试装饰器（带参数）
# ══════════════════════════════════════════════════════

def retry(times: int = 3, delay: float = 0.1, exceptions: tuple = (Exception,)):
    """
    自动重试 times 次，每次失败后等 delay 秒
    只重试指定的异常类型，其他直接抛出
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    print(f"  [{func.__name__}] 第 {attempt} 次失败: {e}")
                    if attempt < times:
                        time.sleep(delay)
            raise last_err   # 全部重试失败，抛出最后一次的异常
        return wrapper
    return decorator


# 模拟一个不稳定的网络请求
attempt_count = 0

@retry(times=4, delay=0.05, exceptions=(ConnectionError,))
def flaky_request():
    global attempt_count
    attempt_count += 1
    if attempt_count < 3:
        raise ConnectionError(f"网络不稳定 (尝试 {attempt_count})")
    return "success"


print("\n── 重试装饰器 ──")
result = flaky_request()
print(f"最终结果: {result}")


# ══════════════════════════════════════════════════════
# 8. 标准模板速查
# ══════════════════════════════════════════════════════
#
# 不带参数的装饰器：
#
#   def my_decorator(func):
#       @functools.wraps(func)
#       def wrapper(*args, **kwargs):
#           # 前置
#           result = func(*args, **kwargs)
#           # 后置
#           return result
#       return wrapper
#
# 带参数的装饰器（三层）：
#
#   def my_decorator(param):
#       def decorator(func):
#           @functools.wraps(func)
#           def wrapper(*args, **kwargs):
#               # 用到 param、func
#               return func(*args, **kwargs)
#           return wrapper
#       return decorator
#
# 工程建议：
#   - 永远加 @functools.wraps(func)
#   - 用 *args, **kwargs 透明转发参数
#   - 装饰器内部访问外层变量靠"闭包"，写起来自然
#   - 复杂状态（缓存、计数器）用闭包变量持有
