r"""
typing 第四层：高级 ── overload + cast + 类型收窄
─────────────────────────────────────────
内容：
1. @overload ── 同一个函数支持多种签名
2. cast ── 强制断言类型（绕过检查器）
3. 类型收窄（type narrowing）
   - isinstance / is None / 其他守卫
   - assert
4. TypeGuard ── 自定义类型守卫函数
5. typing.Never ── "永远不会到这"
"""

from typing import overload, cast, TypeGuard, Never, Any


# ══════════════════════════════════════════════════════
# 1. @overload ── 多签名重载
# ══════════════════════════════════════════════════════
# 场景：同一个函数，不同输入类型对应不同的返回类型

@overload
def parse(s: str) -> str: ...

@overload
def parse(s: int) -> int: ...

@overload
def parse(s: list[str]) -> list[str]: ...

def parse(s):                                # ← 真正的实现，不带类型注解
    """实际函数体"""
    if isinstance(s, str):
        return s.strip()
    if isinstance(s, int):
        return s * 2
    if isinstance(s, list):
        return [x.strip() for x in s]
    raise TypeError(s)


print("── @overload ──")
print(parse("  abc  "))           # IDE 知道返回 str
print(parse(10))                  # IDE 知道返回 int
print(parse(["  a  ", "  b  "]))  # IDE 知道返回 list[str]


# 关键规则：
#   - @overload 装饰的函数体永远写 ...
#   - 真正实现写在最后一个，没有 @overload
#   - @overload 只是"给类型检查器看"的签名，运行时不用
#
# 用途：
#   - 输入类型决定输出类型，无法用 TypeVar 表达时
#   - 比如：dict.get(key) 没默认值返 V|None，有默认值返 V


# ══════════════════════════════════════════════════════
# 2. 类型收窄：isinstance / is None
# ══════════════════════════════════════════════════════
# 类型检查器会跟踪你写的判断，自动收窄变量类型

def render(value: int | str | None) -> str:
    if value is None:
        return "(empty)"            # 此处 value: None
    if isinstance(value, int):
        return f"#{value}"          # 此处 value: int
    return value.upper()            # 此处 value: str（剩下的就是 str）


print("\n── 类型收窄 ──")
print(render(None))
print(render(42))
print(render("hello"))


# 关键：类型检查器会"读"你的 if 分支，自动推导剩下分支的类型
# 这就是为什么 IDE 在 if value is None: return 之后，
# 后面 value 的提示就只剩 int | str


# ══════════════════════════════════════════════════════
# 3. assert 也能收窄
# ══════════════════════════════════════════════════════

def get_first_char(s: str | None) -> str:
    assert s is not None              # ← assert 之后类型缩窄成 str
    return s[0]                       # IDE 不再警告 None


# 注意：assert 在 -O 优化模式下会被去掉
# 用于"应该永远成立"的不变式检查，不是错误处理


# ══════════════════════════════════════════════════════
# 4. cast ── 强制告诉类型检查器："你信我"
# ══════════════════════════════════════════════════════
# 当你比类型检查器更了解情况时，用 cast 强制断言

import json

def load_config() -> dict[str, str]:
    raw = json.loads('{"host": "localhost", "port": "8080"}')
    return cast(dict[str, str], raw)
    # json.loads 的返回类型是 Any，
    # 我们知道这次它是 dict[str, str]，用 cast 告诉检查器


print("\n── cast ──")
config = load_config()
print(config["host"].upper())     # 不警告，因为 cast 后类型已知

# cast 是"运行时无操作 + 编译期类型断言"
# 错用了 cast 不会报错，但会让类型系统失效，所以慎用


# ══════════════════════════════════════════════════════
# 5. TypeGuard ── 自定义"收窄函数"
# ══════════════════════════════════════════════════════
# isinstance 只能识别"内置 / 已注册"的类型
# 自己写的判断函数，类型检查器看不懂
# TypeGuard 让你的判断函数也能驱动类型收窄

def is_str_list(items: list[Any]) -> TypeGuard[list[str]]:
    """返回 True 表示 items 是 list[str]"""
    return all(isinstance(x, str) for x in items)


def process(items: list[Any]) -> str:
    if is_str_list(items):
        # 类型检查器知道：这里 items 已收窄为 list[str]
        return ", ".join(items)
    return str(items)


print("\n── TypeGuard ──")
print(process(["a", "b", "c"]))
print(process([1, 2, 3]))


# 没 TypeGuard 时，编辑器在 if 块里看到的还是 list[Any]，
# 用 join 时会警告"参数应该是 Iterable[str]"
# 加上 TypeGuard 后，类型检查器收窄，警告消失


# ══════════════════════════════════════════════════════
# 6. typing.Never ── "永远到不了"
# ══════════════════════════════════════════════════════
# Never 表示"永远不会有值的类型"
# 用途 1：穷尽匹配（exhaustive check）保证所有情况都处理了

from typing import Literal

def color_name(c: Literal["red", "green", "blue"]) -> str:
    if c == "red":
        return "红色"
    if c == "green":
        return "绿色"
    if c == "blue":
        return "蓝色"
    # 走到这里说明 c 既不是 red/green/blue
    # 但 Literal 已经限制只能是这三个，所以 c 类型应该是 Never
    _exhaustive_check(c)
    raise ValueError(f"未知颜色 {c}")


def _exhaustive_check(x: Never) -> Never:
    """收到任何东西都报错；类型检查时如果调用方传了非 Never，会被发现"""
    raise AssertionError(f"未处理的分支: {x}")


# 用途：
#   如果你给 c 加了一种新色（"yellow"），但忘了在 if 里处理，
#   _exhaustive_check(c) 这一行类型检查器会报错：
#   "Argument of type Literal["yellow"] is not assignable to Never"
#   ← 强制提醒你补上分支

print("\n── Never 穷尽检查 ──")
print(color_name("red"))
print(color_name("blue"))


# ══════════════════════════════════════════════════════
# 7. 实战：用 overload 改进 dict 风格 API
# ══════════════════════════════════════════════════════

T = type("T", (), {})       # 假装一个 TypeVar 用占位

from typing import TypeVar
T = TypeVar("T")
D = TypeVar("D")


class Cache:
    def __init__(self):
        self._data: dict[str, Any] = {}

    @overload
    def get(self, key: str) -> Any | None: ...

    @overload
    def get(self, key: str, default: D) -> Any | D: ...

    def get(self, key, default=None):
        return self._data.get(key, default)


print("\n── overload + 默认值 ──")
c = Cache()
c._data = {"x": 1}
print(c.get("x"))                    # 1
print(c.get("missing"))              # None
print(c.get("missing", "default"))   # 'default'
# IDE 能根据有没有传 default 推导不同的返回类型


# ══════════════════════════════════════════════════════
# 8. 速查
# ══════════════════════════════════════════════════════
#
# @overload：
#   多个 @overload 描述不同签名（函数体写 ...）
#   最后一个是真实现（不带 @overload）
#   仅类型检查器使用，运行时不影响
#
# 类型收窄：
#   if x is None / is not None
#   if isinstance(x, T)
#   assert x is not None
#   ── 检查器会跟踪分支，自动缩小类型
#
# cast(T, value)：
#   "我比你更了解类型，请按 T 处理"
#   运行时零开销
#   慎用，错了会让类型系统失效
#
# TypeGuard[T]：
#   def is_xx(x) -> TypeGuard[T]: ...
#   让自定义判断函数也能驱动类型收窄
#
# Never：
#   穷尽匹配的"哨兵类型"
#   配合 if/elif 链确保所有分支都处理
#   忘了加分支 → 类型检查器报错提醒
#
# 工程铁律：
#   - 优先用 isinstance / is None 让 IDE 自动推导
#   - 只在"检查器不够聪明"时才用 cast
#   - 写库的公共 API 多用 @overload
#   - Literal + Never 组合是"穷尽匹配"的黄金搭档
"""
"""
