r"""
typing 第三层：Protocol 深入 + TypedDict + NewType + Annotated
─────────────────────────────────────────
内容：
1. Protocol（结构化类型，深入版）
2. TypedDict ── 给字典加类型
3. NewType ── 给"语义不同但底层相同"的类型起新名字
4. Annotated ── 给类型加"附加元数据"（pydantic / FastAPI 大量用）
"""

from typing import Protocol, TypedDict, NewType, Annotated, runtime_checkable


# ══════════════════════════════════════════════════════
# 1. Protocol 深入：方法 + 属性 + 泛型
# ══════════════════════════════════════════════════════
# 你已经在 OOP 章节学过 Protocol 的基础概念
# 这一层看几个进阶用法

# 例子 1：要求对象有特定属性
class HasName(Protocol):
    name: str         # ← 协议可以约束属性，不只是方法


def greet(thing: HasName) -> str:
    return f"hello {thing.name}"


class Cat:
    name = "miaomiao"          # 不需要继承 HasName，只要"形状对"就行


class Robot:
    def __init__(self):
        self.name = "R2D2"


print("── Protocol 约束属性 ──")
print(greet(Cat()))
print(greet(Robot()))


# ══════════════════════════════════════════════════════
# 2. Protocol 多个方法 + 默认实现
# ══════════════════════════════════════════════════════
# Protocol 里的方法可以有默认实现（继承时可被复用）

class Sized(Protocol):
    def __len__(self) -> int: ...

    def is_empty(self) -> bool:
        return len(self) == 0      # 默认实现


def describe(s: Sized) -> str:
    return "空" if s.is_empty() else f"长度 {len(s)}"


# 注意：is_empty 的默认实现不会被"自动注入"到不继承 Sized 的类
# 调用方用普通 list 时，is_empty 必须存在才能调用
# 所以这种"协议默认实现"主要给"继承 Protocol 的类"用


# ══════════════════════════════════════════════════════
# 3. 泛型 Protocol
# ══════════════════════════════════════════════════════
from typing import TypeVar
T = TypeVar("T")


class Container(Protocol[T]):
    def add(self, item: T) -> None: ...
    def get_all(self) -> list[T]: ...


class IntList:
    def __init__(self):
        self._data: list[int] = []

    def add(self, item: int) -> None:
        self._data.append(item)

    def get_all(self) -> list[int]:
        return self._data


def add_many(c: Container[int], items: list[int]) -> None:
    for x in items:
        c.add(x)


print("\n── 泛型 Protocol ──")
inv = IntList()
add_many(inv, [1, 2, 3])
print(inv.get_all())


# ══════════════════════════════════════════════════════
# 4. TypedDict ── 给字典加类型
# ══════════════════════════════════════════════════════
# 场景：JSON 响应、API 返回 ── 数据是 dict，但每个 key 的类型固定

class UserDict(TypedDict):
    id: int
    name: str
    email: str


def render_user(u: UserDict) -> str:
    return f"#{u['id']} {u['name']} <{u['email']}>"


print("\n── TypedDict ──")
alice: UserDict = {"id": 1, "name": "Alice", "email": "a@x.com"}
print(render_user(alice))

# 类型检查器会做这些事：
#   - 确认 alice 必须有 id / name / email 三个 key
#   - alice["id"] 推导为 int
#   - alice["wrong_key"] 会报错（多写或拼错都被发现）


# 可选字段：用 NotRequired
from typing import NotRequired

class UserDictV2(TypedDict):
    id: int
    name: str
    email: NotRequired[str]    # 可有可无


# 全部可选：total=False
class PartialUser(TypedDict, total=False):
    id: int
    name: str
    email: str


# TypedDict 适合：
#   - 解析 JSON 后表达"这个 dict 的形状"
#   - 不想引入 dataclass 的开销，又想要类型提示
# 不适合：
#   - 需要方法 → 用 dataclass
#   - 需要不可变 → 用 NamedTuple


# ══════════════════════════════════════════════════════
# 5. NewType ── 同样底层、不同语义
# ══════════════════════════════════════════════════════
# 场景：UserId 和 OrderId 都是 int，但混用就出 bug
# 用 NewType 让类型检查器把它们当不同类型对待

UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)


def cancel_order(order_id: OrderId) -> None:
    print(f"  取消订单 {order_id}")


print("\n── NewType ──")
oid = OrderId(1001)
uid = UserId(42)

cancel_order(oid)        # ✅ 正确
# cancel_order(uid)       # ❌ 类型检查器：不能把 UserId 传给 OrderId
# cancel_order(1001)      # ❌ 类型检查器：不能把 raw int 传过来

# 运行时 NewType 是"零开销"：
#   UserId(42) 实际就是返回 42，没有真正包装
#   纯粹给类型检查器看的


# ══════════════════════════════════════════════════════
# 6. Annotated ── 给类型加"元数据"
# ══════════════════════════════════════════════════════
# 同一个类型，附加额外信息：值范围、单位、格式说明等
# pydantic / FastAPI 大量使用这个

# 比如：年龄是 int，但要求 0~150
Age = Annotated[int, "0 到 150 之间"]


def set_age(age: Age) -> None:
    print(f"  设置年龄 {age}")


# Annotated 的真实价值：和库配合
# 比如 pydantic：
#
#   from pydantic import Field
#   from typing import Annotated
#
#   class User(BaseModel):
#       age: Annotated[int, Field(ge=0, le=150)]
#       email: Annotated[str, Field(pattern=r"...")]
#
# Annotated 的第一个参数永远是真实类型，
# 后面的元数据由具体的库去解读

print("\n── Annotated ──")
set_age(25)


# 取出 Annotated 里的元数据
from typing import get_type_hints, get_args

def show_meta(func):
    hints = get_type_hints(func, include_extras=True)
    for name, hint in hints.items():
        if hasattr(hint, "__metadata__"):
            print(f"  {name}: {get_args(hint)}")


show_meta(set_age)
# (int, '0 到 150 之间')


# ══════════════════════════════════════════════════════
# 7. 实战：把 TypedDict / NewType 用在一起
# ══════════════════════════════════════════════════════

# 场景：处理 API 返回的用户列表

UserId2 = NewType("UserId2", int)


class UserResp(TypedDict):
    id: UserId2
    name: str
    age: int


def process_users(users: list[UserResp]) -> dict[UserId2, str]:
    """返回 id → name 的映射"""
    return {u["id"]: u["name"] for u in users}


print("\n── TypedDict + NewType 综合 ──")
data: list[UserResp] = [
    {"id": UserId2(1), "name": "alice", "age": 30},
    {"id": UserId2(2), "name": "bob", "age": 25},
]
print(process_users(data))


# ══════════════════════════════════════════════════════
# 8. 速查
# ══════════════════════════════════════════════════════
#
# Protocol：
#   class P(Protocol):
#       def method(self) -> ...
#       attr: str
#   ── 结构化类型：不需要继承，方法/属性"形状对"就算
#   ── 配 @runtime_checkable 后可用 isinstance
#
# TypedDict：
#   class User(TypedDict):
#       id: int
#       name: str
#   ── dict 的"类型化版本"
#   ── 适合 JSON / API 数据
#   ── NotRequired[T] 表示可选字段
#   ── total=False 表示全部可选
#
# NewType：
#   UserId = NewType("UserId", int)
#   ── 给同底层类型起"语义化新名字"
#   ── 防止 UserId 和 OrderId 串
#   ── 运行时零开销
#
# Annotated：
#   Annotated[int, "doc"]
#   ── 给类型加附加元数据
#   ── 给 pydantic / FastAPI 看
#
# 实战选型：
#   类有方法、需校验          → dataclass / pydantic
#   只有结构、来自外部 JSON   → TypedDict
#   底层类型相同、语义不同    → NewType
#   想给类型加约束元信息      → Annotated
#   "结构匹配就行"的鸭子接口  → Protocol
"""
"""
