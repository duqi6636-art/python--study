r"""
typing 第一层：基础注解
─────────────────────────────────────────
你已经在 dataclass / Iterator / Protocol 里用过类型，
这一章把"基础语法"系统过一遍。

内容：
1. 函数参数 / 返回值注解
2. 容器类型：list[int] / dict[str, int] / tuple
3. Optional 和 None ──"可空"
4. Union 和 | 语法 ──"多选一"
5. Literal ── 限定取值
6. Final ── 不可重新赋值
7. type / TypeAlias ── 类型别名
8. 类型注解的"运行时不强制"特性
"""

from typing import Final, Literal


# ══════════════════════════════════════════════════════
# 1. 函数注解 ── 最常用
# ══════════════════════════════════════════════════════

def add(a: int, b: int) -> int:
    return a + b


def greet(name: str, age: int = 18) -> str:
    return f"{name} is {age}"


print("── 函数注解 ──")
print(add(1, 2))           # 3
print(greet("Alice"))      # Alice is 18

# 注解只是"提示"，运行时不会强制检查：
print(add("a", "b"))        # 'ab' ── 字符串拼接也能跑！
# 类型只在 IDE / mypy / pyright 这种工具里起作用
# Python 解释器本身不会抛 TypeError


# ══════════════════════════════════════════════════════
# 2. 变量注解
# ══════════════════════════════════════════════════════

count: int = 0
names: list[str] = []
config: dict[str, int] = {}


# ══════════════════════════════════════════════════════
# 3. 容器类型 ── 现代写法（Python 3.9+）
# ══════════════════════════════════════════════════════

# list / dict / tuple / set 直接当类型用
def get_users() -> list[str]:
    return ["alice", "bob"]


def count_words(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for w in text.split():
        counts[w] = counts.get(w, 0) + 1
    return counts


print("\n── 容器类型 ──")
print(get_users())
print(count_words("hello world hello"))


# tuple 的两种用法：
#   tuple[int, str]      ── 固定长度、各位置类型不同
#   tuple[int, ...]      ── 任意长度、所有元素都是 int

def coordinates() -> tuple[float, float]:
    return (12.5, 34.7)


def all_ages() -> tuple[int, ...]:
    return (18, 25, 30, 45)


# 老语法（Python 3.8 及以前）：from typing import List, Dict
# 现代代码不需要再用 typing.List / Dict，直接用内置就行


# ══════════════════════════════════════════════════════
# 4. Optional ──"可能是 None"
# ══════════════════════════════════════════════════════
# Optional[T] 等价于 T | None

def find_user(name: str) -> str | None:
    """可能找不到，返回 None"""
    db = {"alice": "Alice 30", "bob": "Bob 25"}
    return db.get(name)


print("\n── Optional ──")
result = find_user("alice")
print(result)
# 类型检查器会要求：用 result 之前必须先判空
if result is not None:
    print(result.upper())   # 现在 IDE 知道 result 是 str


# 老写法：from typing import Optional
#   def f() -> Optional[str]:    # 等价于 str | None
# 现代代码用 |  更直观


# ══════════════════════════════════════════════════════
# 5. Union ── 多种类型之一
# ══════════════════════════════════════════════════════
# T | U 是 Python 3.10+ 的"联合类型"语法

def parse_id(value: int | str) -> str:
    """接受 int 或 str"""
    return str(value)


print("\n── Union（| 语法）──")
print(parse_id(42))
print(parse_id("user-42"))


# 多种类型连续 |：
def to_str(x: int | float | bool | str) -> str:
    return str(x)


# Python 3.9 及以前：from typing import Union
#   def parse_id(value: Union[int, str]) -> str: ...


# ══════════════════════════════════════════════════════
# 6. Literal ── 限定具体取值
# ══════════════════════════════════════════════════════

def fetch(method: Literal["GET", "POST", "PUT", "DELETE"], url: str) -> None:
    print(f"  {method} {url}")


print("\n── Literal ──")
fetch("GET", "/api/users")
# fetch("BLAH", ...)   ← 类型检查器会报错

# 比起 enum，Literal 更轻量；
# 适合那种"参数只能是几个特定字符串"的场景


# Literal 也能放数字 / 布尔
def set_log_level(level: Literal[0, 1, 2, 3]) -> None: ...


# ══════════════════════════════════════════════════════
# 7. Final ── 不可重新赋值（常量）
# ══════════════════════════════════════════════════════

MAX_RETRIES: Final = 3
API_BASE: Final[str] = "https://api.example.com"

# Final 表达"这是一个常量，不该再被赋值"
# 类型检查器会拦截：MAX_RETRIES = 5  ← 报错
# 运行时仍然能改，只是工具会警告

# 在类里也能用：
class Config:
    VERSION: Final = "1.0.0"     # 类常量，不允许子类覆盖


# ══════════════════════════════════════════════════════
# 8. 类型别名
# ══════════════════════════════════════════════════════
# 复杂类型起个名字，提高可读性

# 老写法：
UserId = int
UserMap = dict[UserId, str]

# Python 3.12+ 推荐写法（type 关键字）：
# type UserId = int
# type UserMap = dict[UserId, str]

def get_username(user_id: UserId, users: UserMap) -> str | None:
    return users.get(user_id)


print("\n── 类型别名 ──")
users: UserMap = {1: "alice", 2: "bob"}
print(get_username(1, users))


# ══════════════════════════════════════════════════════
# 9. Any / object ── 两种"任何类型"
# ══════════════════════════════════════════════════════
from typing import Any


def parse_json(s: str) -> Any:
    """JSON 可能是任何东西，用 Any 关闭类型检查"""
    import json
    return json.loads(s)


def to_string(x: object) -> str:
    """object 是所有类的祖先，但你拿到后不能用 .upper() 之类的方法"""
    return str(x)


# Any vs object：
#   Any     "类型检查器请闭嘴"，对它做任何操作都不报错
#   object  真实的 Python 类型基类，所有对象都是 object，
#           但只能用 object 自己的方法（str、repr 等）
#
# Any 是"逃生舱"，能不用就不用


# ══════════════════════════════════════════════════════
# 10. 注解只是"提示"，不强制
# ══════════════════════════════════════════════════════
# 这是 Python 类型注解最关键的特性：

def repeat_text(s: int) -> int:
    """注解说要 int，但传 str 也能"跑"（只是行为不一样）"""
    return s * 3


print("\n── 注解不强制 ──")
print(repeat_text(3))        # 9     按 int 算
print(repeat_text("ab"))     # 'ababab'   字符串也接受，因为 str * 3 合法
# Python 不会因为类型不匹配抛错；
# 类型检查的工作交给 IDE / mypy / pyright 这些静态分析器

# 如果想"运行时校验类型"，要用 pydantic / typeguard 这类库


# ══════════════════════════════════════════════════════
# 11. 让 IDE / mypy 真的检查你的代码
# ══════════════════════════════════════════════════════
#
# 命令行：
#   pip install mypy
#   mypy your_file.py
#
# IDE：
#   VS Code: Pylance（默认开）
#   PyCharm: 内置类型检查
#
# 配置：
#   pyproject.toml 里加 [tool.mypy] 段，
#   推荐启用：strict = true
#
# 工程铁律：
#   - 写新代码就加注解，不补旧代码
#   - 边界（公共 API、库的入口）必须注解
#   - 内部小函数能省则省
#   - Any 是最后的逃生舱
#   - 注解错了比没注解还糟（误导调用方）


# ══════════════════════════════════════════════════════
# 12. 速查
# ══════════════════════════════════════════════════════
#
# 基础：
#   x: int                       变量
#   def f(a: int) -> str: ...    函数
#
# 容器（Python 3.9+）：
#   list[int]
#   dict[str, int]
#   tuple[int, str]              定长
#   tuple[int, ...]              变长
#   set[str]
#
# 可空 / 多选：
#   x: str | None                可为 None
#   x: int | str                 多选一
#
# 字面量：
#   Literal["GET", "POST"]
#   Literal[1, 2, 3]
#
# 常量：
#   X: Final = 3
#   X: Final[int] = 3
#
# 类型别名：
#   UserId = int                 老写法
#   type UserId = int            Python 3.12+
#
# 万能：
#   Any                          关闭检查（慎用）
#   object                       所有类型的祖先（能力有限）
"""
"""
