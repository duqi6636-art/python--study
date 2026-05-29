r"""
装饰器第四层：标准库利器
─────────────────────────────────────────
Python 标准库自带一堆装饰器，工程里直接用，
比自己手写的更稳更快。本层覆盖最常用的：

1. @functools.lru_cache       带容量上限的缓存
2. @functools.cache           无上限缓存（Python 3.9+）
3. @functools.cached_property 惰性属性（只算一次）
4. @functools.singledispatch  按类型分派的"函数重载"
5. @functools.total_ordering  自动补齐比较运算符
6. @contextlib.contextmanager 把生成器变成上下文管理器
7. @staticmethod / @classmethod / @property  内置三件套
"""

import functools
import time
from contextlib import contextmanager


# ══════════════════════════════════════════════════════
# 1. @functools.lru_cache ── 上一层我们手写的"工业版"
# ══════════════════════════════════════════════════════
# 同样的输入只算一次，结果存起来。
# LRU = Least Recently Used，超出容量时丢弃最久未使用的

@functools.lru_cache(maxsize=128)   # 最多缓存 128 个不同输入
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


print("── lru_cache ──")
print(fib(50))                    # 瞬间出结果
print(fib.cache_info())           # 缓存命中统计
fib.cache_clear()                 # 手动清缓存

# 注意事项：
#   - 参数必须是"可哈希"的（int/str/tuple 行，list/dict 不行）
#   - maxsize=None 表示无上限（等同 @functools.cache）


# ══════════════════════════════════════════════════════
# 2. @functools.cache ── 无上限的 lru_cache（Python 3.9+）
# ══════════════════════════════════════════════════════
# 写起来比 lru_cache(maxsize=None) 更简洁

@functools.cache
def factorial(n: int) -> int:
    return 1 if n <= 1 else n * factorial(n - 1)

print("\n── cache ──")
print(factorial(20))
print(factorial.cache_info())


# ══════════════════════════════════════════════════════
# 3. @functools.cached_property ── 惰性属性（只算一次）
# ══════════════════════════════════════════════════════
# 第一次访问时计算，结果存到实例上；之后直接读，不再计算

class Dataset:
    def __init__(self, data: list[int]):
        self._data = data

    @functools.cached_property
    def stats(self) -> dict:
        print("  [计算] 跑一遍统计")
        return {
            "count": len(self._data),
            "sum": sum(self._data),
            "avg": sum(self._data) / len(self._data),
        }


print("\n── cached_property ──")
ds = Dataset([10, 20, 30, 40, 50])
print(ds.stats)    # 第一次：[计算] 出现
print(ds.stats)    # 第二次：直接返回，不再计算
print(ds.stats)    # 第三次：同上

# vs @property：
#   @property         每次访问都执行（适合廉价计算 / 实时数据）
#   @cached_property  只算一次（适合昂贵计算 / 不变数据）


# ══════════════════════════════════════════════════════
# 4. @functools.singledispatch ── 按类型分派的"函数重载"
# ══════════════════════════════════════════════════════
# 让一个函数根据"第一个参数的类型"调用不同实现

@functools.singledispatch
def render(value):
    """默认实现"""
    return f"未知类型: {value!r}"

@render.register(int)
def _(value):
    return f"整数 {value}（{value:b}）"

@render.register(str)
def _(value):
    return f"字符串 {value!r}（长度 {len(value)}）"

@render.register(list)
def _(value):
    return f"列表 [{', '.join(map(str, value))}]"


print("\n── singledispatch ──")
print(render(42))               # 走 int 分支
print(render("hello"))          # 走 str 分支
print(render([1, 2, 3]))        # 走 list 分支
print(render({"a": 1}))         # 没注册 dict，走默认


# ══════════════════════════════════════════════════════
# 5. @functools.total_ordering ── 自动补齐比较运算符
# ══════════════════════════════════════════════════════
# 只写 __eq__ 和 __lt__，自动生成 <= > >= !=

@functools.total_ordering
class Version:
    def __init__(self, major, minor):
        self.major = major
        self.minor = minor

    def __eq__(self, other):
        return (self.major, self.minor) == (other.major, other.minor)

    def __lt__(self, other):
        return (self.major, self.minor) < (other.major, other.minor)

    def __repr__(self):
        return f"v{self.major}.{self.minor}"


v1, v2 = Version(1, 0), Version(1, 5)
print("\n── total_ordering ──")
print(v1 < v2,  v1 <= v2,  v1 > v2,  v1 != v2)


# ══════════════════════════════════════════════════════
# 6. @contextlib.contextmanager ── 把生成器变上下文管理器
# ══════════════════════════════════════════════════════
# 不用写完整的类（__enter__ / __exit__），用 yield 就行

@contextmanager
def timer(name: str):
    start = time.perf_counter()
    print(f"  [{name}] 开始")
    try:
        yield                              # ← yield 之前 = __enter__
    finally:
        elapsed = time.perf_counter() - start
        print(f"  [{name}] 结束，{elapsed*1000:.1f}ms")
                                           # ← yield 之后 = __exit__


print("\n── contextmanager ──")
with timer("计算"):
    sum(range(10_000_000))

# 上一段是同步版。异步版用 @contextlib.asynccontextmanager，
# 用法一样，把 def 换成 async def，with 换成 async with


# ══════════════════════════════════════════════════════
# 7. 内置三件套：@staticmethod / @classmethod / @property
# ══════════════════════════════════════════════════════

class Pizza:
    DEFAULT_SIZE = 12

    def __init__(self, size: int, toppings: list[str]):
        self.size = size
        self.toppings = toppings

    # @property: 把方法变成属性访问（无需括号）
    @property
    def description(self) -> str:
        return f"{self.size}寸 ({', '.join(self.toppings)})"

    # @staticmethod: 不依赖实例和类，纯工具函数
    @staticmethod
    def calc_area(size: int) -> float:
        return 3.14 * (size / 2) ** 2

    # @classmethod: 第一个参数是类本身，常用作"替代构造函数"
    @classmethod
    def margherita(cls) -> "Pizza":
        return cls(cls.DEFAULT_SIZE, ["番茄", "马苏里拉", "罗勒"])


print("\n── property / staticmethod / classmethod ──")
p = Pizza.margherita()                  # 替代构造函数
print(p.description)                    # 用 property 像属性一样访问
print(Pizza.calc_area(12))              # 静态方法：类名直接调用


# ══════════════════════════════════════════════════════
# 8. 速查 + 何时用什么
# ══════════════════════════════════════════════════════
#
# @lru_cache(maxsize=N)    通用缓存，参数可哈希时用
# @cache                   无上限版（Python 3.9+），写法更短
# @cached_property         实例上"算一次的属性"，比 @property 省 CPU
# @singledispatch          根据参数类型分发（替代 if isinstance）
# @total_ordering          补齐比较运算符（dataclass(order=True) 是同类思路）
# @contextmanager          用 yield 写 with 块，比写类轻量
# @property                用方法实现"看起来像属性"的访问
# @staticmethod            纯工具函数，挂在类下方便归类
# @classmethod             第一个参数是 cls，常做替代构造函数
#
# 工程铁律：
#   能用标准库就别自己造。手写装饰器只适合"业务定制"，
#   通用能力（缓存、惰性、重载、比较）一律用 functools。
