r"""
typing 第二层：泛型 TypeVar / Generic / Self
─────────────────────────────────────────
内容：
1. TypeVar ── 类型参数化（让函数 / 类支持多种类型）
2. 自定义泛型类：class Box[T]
3. 有约束的 TypeVar（bound / 多类型）
4. Self ── 表达"返回自己这种类型"
5. ParamSpec ── 给装饰器签名加类型（进阶）
"""

from typing import TypeVar, Generic, Self, Callable
from collections.abc import Iterable


# ══════════════════════════════════════════════════════
# 1. TypeVar ── 类型参数化
# ══════════════════════════════════════════════════════
# 不用 TypeVar 时，"返回输入的第一个元素"这个函数没法准确写：

def first_bad(items: list) -> object:
    """返回 object，调用方拿到啥都不能用"""
    return items[0]


# 用 TypeVar：
T = TypeVar("T")

def first(items: list[T]) -> T:
    """传 list[int] 返回 int，传 list[str] 返回 str"""
    return items[0]


print("── TypeVar ──")
n = first([1, 2, 3])          # IDE 知道 n: int
s = first(["a", "b", "c"])    # IDE 知道 s: str
print(n, s)


# Python 3.12+ 简化语法（不用先声明 TypeVar）：
def first_v2[T](items: list[T]) -> T:
    return items[0]

# 等价于上面的写法，但不需要 from typing import TypeVar


# ══════════════════════════════════════════════════════
# 2. 多个类型参数
# ══════════════════════════════════════════════════════
K = TypeVar("K")
V = TypeVar("V")

def swap_kv(d: dict[K, V]) -> dict[V, K]:
    """{1:'a', 2:'b'} → {'a':1, 'b':2}"""
    return {v: k for k, v in d.items()}


print("\n── 多类型参数 ──")
print(swap_kv({1: "a", 2: "b"}))


# Python 3.12+：
def swap_kv_v2[K, V](d: dict[K, V]) -> dict[V, K]:
    return {v: k for k, v in d.items()}


# ══════════════════════════════════════════════════════
# 3. 自定义泛型类（容器、Box）
# ══════════════════════════════════════════════════════
# 让自己的类支持"持有任意类型 T"

class Box(Generic[T]):
    def __init__(self, value: T):
        self.value = value

    def get(self) -> T:
        return self.value

    def set(self, value: T) -> None:
        self.value = value


print("\n── 泛型类 ──")
int_box: Box[int] = Box(42)
str_box: Box[str] = Box("hello")
print(int_box.get())             # IDE 知道返回 int
print(str_box.get())             # IDE 知道返回 str


# Python 3.12+ 简化版：
class BoxV2[T]:
    def __init__(self, value: T):
        self.value = value

    def get(self) -> T:
        return self.value


# ══════════════════════════════════════════════════════
# 4. 有约束的 TypeVar：bound
# ══════════════════════════════════════════════════════
# bound 表示"T 必须是某个类的子类（或本身）"

# 例子：写一个排序函数，要求元素必须能比较
class Comparable:
    def __lt__(self, other) -> bool: ...


# 但 Python 内置类型并不继承 Comparable，所以这种写法少见
# 更常见用法：限制 T 必须是某个具体基类

class Animal:
    def speak(self) -> str: return "..."

class Dog(Animal):
    def speak(self) -> str: return "woof"

class Cat(Animal):
    def speak(self) -> str: return "meow"


A = TypeVar("A", bound=Animal)        # T 必须是 Animal 或它的子类

def play(animal: A) -> A:
    """传什么进去，返回的还是同一种"""
    print(f"  {animal.speak()}")
    return animal


print("\n── bound TypeVar ──")
d: Dog = play(Dog())                  # 返回 Dog
c: Cat = play(Cat())                  # 返回 Cat


# Python 3.12+：
def play_v2[A: Animal](animal: A) -> A:
    return animal


# ══════════════════════════════════════════════════════
# 5. 多类型约束：TypeVar(..., type1, type2)
# ══════════════════════════════════════════════════════
# 表示"T 必须是这几个类型中的某一个"（不是子类，是 exactly 这几个）

Number = TypeVar("Number", int, float)    # 只能是 int 或 float

def double(x: Number) -> Number:
    return x * 2


print("\n── 约束 TypeVar ──")
print(double(3))         # 6 (int)
print(double(3.14))      # 6.28 (float)
# double("abc")          # 类型检查器会报错


# bound vs 约束：
#   bound=Animal              → 任何 Animal 子类
#   ("int", "float")          → 仅这两种之一


# ══════════════════════════════════════════════════════
# 6. Self ── "返回自己这种类型"
# ══════════════════════════════════════════════════════
# 链式调用、构造器模式经常需要这个

class QueryBuilder:
    def __init__(self):
        self._filters: list[str] = []

    def where(self, cond: str) -> Self:    # Self 表示"返回自己这种类型"
        self._filters.append(cond)
        return self

    def build(self) -> str:
        return " AND ".join(self._filters)


# 没 Self 时的痛点：
#   - 子类继承后，调 .where() 返回的类型还是父类，IDE 提示丢失
#   - 链式调用之后只能调父类的方法
#
# 用 Self 后，子类继承时类型自动变成子类自己

class AdvancedQuery(QueryBuilder):
    def order_by(self, field: str) -> Self:
        self._filters.append(f"ORDER BY {field}")
        return self


print("\n── Self ──")
q = (AdvancedQuery()
     .where("age > 18")
     .where("country = 'CN'")
     .order_by("name")               # ← 父类返回 AdvancedQuery，能继续调子类方法
     .build())
print(q)


# ══════════════════════════════════════════════════════
# 7. classmethod 里的 Self（替代构造函数）
# ══════════════════════════════════════════════════════

class User:
    def __init__(self, name: str):
        self.name = name

    @classmethod
    def from_dict(cls, d: dict) -> Self:    # ← Self 让子类用时类型自动正确
        return cls(d["name"])


class Admin(User):
    pass


print("\n── classmethod 里的 Self ──")
admin = Admin.from_dict({"name": "alice"})
print(type(admin).__name__)    # 'Admin'  ← 类型推导正确
# 没 Self 时返回类型会是 User，而不是 Admin


# ══════════════════════════════════════════════════════
# 8. ParamSpec ── 装饰器的"参数签名透传"
# ══════════════════════════════════════════════════════
# 写装饰器时想"保留被装饰函数的参数签名"，用 ParamSpec

from typing import ParamSpec
import functools

P = ParamSpec("P")
R = TypeVar("R")


def log_call(func: Callable[P, R]) -> Callable[P, R]:
    """带类型的 log 装饰器：保留原签名"""
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"  调用 {func.__name__}({args}, {kwargs})")
        return func(*args, **kwargs)
    return wrapper


@log_call
def add(a: int, b: int) -> int:
    return a + b


print("\n── ParamSpec ──")
print(add(2, 3))
# IDE 仍然知道 add(a: int, b: int) -> int
# 没 ParamSpec 时，装饰后 IDE 看到的签名变成 *args, **kwargs


# Python 3.12+：
# def log_call_v2[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...


# ══════════════════════════════════════════════════════
# 9. 速查
# ══════════════════════════════════════════════════════
#
# TypeVar 用法：
#   T = TypeVar("T")                                普通
#   T = TypeVar("T", bound=Base)                    必须是 Base 子类
#   T = TypeVar("T", int, str)                      只能是 int 或 str
#
# 泛型类：
#   class Box(Generic[T]): ...                      老写法
#   class Box[T]: ...                               Python 3.12+
#
# 函数泛型：
#   def f(x: T) -> T: ...                           需要先 T = TypeVar("T")
#   def f[T](x: T) -> T: ...                        Python 3.12+，免预声明
#
# Self：
#   def method(self) -> Self: ...                   表示"自己这个类"
#   配合链式调用、@classmethod 替代构造函数
#
# ParamSpec：
#   P = ParamSpec("P")                              用于装饰器透传签名
#   def deco(func: Callable[P, R]) -> Callable[P, R]: ...
#
# 工程铁律：
#   - 容器 / 工具函数想支持多类型 → TypeVar
#   - 子类继承的链式调用 / 工厂方法 → Self
#   - 写装饰器要保留签名 → ParamSpec
#   - Python 3.12+ 工程：优先用新语法（class Box[T]）
"""
"""
