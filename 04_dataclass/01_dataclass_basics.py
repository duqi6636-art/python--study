"""
dataclass 基础
─────────────────────────────────────────
为什么需要 dataclass？
  写"只是用来装数据的类"时，__init__ / __repr__ / __eq__ 这些
  样板代码每次都要重复写一遍。dataclass 让 Python 自动生成它们。
"""

from dataclasses import dataclass, field, asdict, astuple, replace
from typing import ClassVar


# ══════════════════════════════════════════════════════
# 1. 对比：普通类 vs dataclass
# ══════════════════════════════════════════════════════

# 普通类的写法
class PointOld:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"PointOld(x={self.x}, y={self.y})"

    def __eq__(self, other):
        if not isinstance(other, PointOld):
            return NotImplemented
        return self.x == other.x and self.y == other.y


# dataclass 写法：一行装饰器搞定
@dataclass
class Point:
    x: float
    y: float


p1 = Point(1.0, 2.0)
p2 = Point(1.0, 2.0)
print(p1)              # Point(x=1.0, y=2.0)   ← 自动生成 __repr__
print(p1 == p2)        # True                  ← 自动生成 __eq__
print(p1.x, p1.y)      # 1.0 2.0


# ══════════════════════════════════════════════════════
# 2. 字段默认值
# ══════════════════════════════════════════════════════

@dataclass
class User:
    name: str                       # 必填
    age: int = 18                   # 有默认值
    role: str = "user"              # 有默认值


u1 = User("Alice")
u2 = User("Bob", 30, "admin")
print(u1, u2)

# 规则：有默认值的字段必须放在没默认值的字段后面
# @dataclass
# class Bad:
#     a: int = 1
#     b: int       # ❌ 报错


# ══════════════════════════════════════════════════════
# 3. 可变默认值的坑：必须用 field(default_factory=...)
# ══════════════════════════════════════════════════════

# ❌ 错误：所有实例会共享同一个 list！
# @dataclass
# class TeamBad:
#     members: list = []   # 报错：mutable default

# ✅ 正确：用 default_factory，每次创建实例时调用一次

# default_factory=list 创建实例时调用 list()
# 每个实例拿到的都是自己独立的空 list，互不影响
# 几个常用配置
# members: list = field(default_factory=list)        # 工厂函数生成默认值
# secret:  str  = field(default="x", repr=False)     # 不出现在 __repr__ 中
# area:    float = field(init=False)                  # 不出现在 __init__ 参数中
# tags:    set  = field(default_factory=set)         # 同理
# config:  dict = field(default_factory=dict)        # 同理


@dataclass
class Team:
    name: str
    members: list = field(default_factory=list)
    config: dict = field(default_factory=dict)


t1 = Team("A")
t2 = Team("B")
t1.members.append("Alice")
print(t1.members)      # ['Alice']
print(t2.members)      # []      ← 各自独立


# ══════════════════════════════════════════════════════
# 4. 常用参数：frozen / order / slots
# ══════════════════════════════════════════════════════

# frozen=True : 不可变（赋值会报错）
@dataclass(frozen=True)
class Coord:
    lat: float
    lng: float


c = Coord(31.2, 121.5)
try:
    c.lat = 99    # ❌ FrozenInstanceError
except Exception as e:
    print(f"  错误: {type(e).__name__}")

# frozen=True 还会自动生成 __hash__，对象能放进 set/dict 的 key
print({Coord(1, 2), Coord(1, 2), Coord(3, 4)})   # 去重后 2 个


# order=True : 自动生成 __lt__ / __le__ / __gt__ / __ge__
@dataclass(order=True)
class Score:
    value: int
    name: str


scores = [Score(80, "A"), Score(60, "B"), Score(90, "C")]
print(sorted(scores))   # 按 value 升序，再按 name


# slots=True (Python 3.10+) : 用 __slots__ 优化内存
@dataclass(slots=True)
class Pixel:
    x: int
    y: int
    color: str


px = Pixel(1, 2, "red")
try:
    px.foo = 123    # ❌ slots 类不能加新属性
except AttributeError as e:
    print(f"  错误: {e}")


# ══════════════════════════════════════════════════════
# 5. 计算字段 / 排除字段：field() 进阶
# ══════════════════════════════════════════════════════

@dataclass
class Rectangle:
    width: float
    height: float
    # repr=False : 不出现在 __repr__ 中
    # compare=False : 不参与 __eq__ 比较
    secret: str = field(default="hidden", repr=False, compare=False)


r = Rectangle(10, 20)
print(r)    # Rectangle(width=10, height=20)   ← secret 被隐藏


# __post_init__ : 在 __init__ 之后自动调用，做派生计算
@dataclass
class Circle:
    radius: float
    area: float = field(init=False)   # init=False : 不出现在构造函数

    def __post_init__(self):
        self.area = 3.14159 * self.radius ** 2


c = Circle(radius=5.0)
print(c)    # Circle(radius=5.0, area=78.53975)


# ══════════════════════════════════════════════════════
# 6. ClassVar : 标记"类级别"变量，dataclass 会忽略它
# ══════════════════════════════════════════════════════

@dataclass
class Counter:
    name: str
    instances: ClassVar[int] = 0   # 不是实例字段，所有实例共享

    def __post_init__(self):
        Counter.instances += 1


Counter("A"); Counter("B"); Counter("C")
print(Counter.instances)    # 3


# ══════════════════════════════════════════════════════
# 7. 实用工具：asdict / astuple / replace
# ══════════════════════════════════════════════════════

@dataclass
class Book:
    title: str
    author: str
    pages: int


b = Book("流浪地球", "刘慈欣", 320)

# 转字典 / 元组（嵌套 dataclass 会递归处理）
print(asdict(b))    # {'title': '流浪地球', 'author': '刘慈欣', 'pages': 320}
print(astuple(b))   # ('流浪地球', '刘慈欣', 320)

# replace : 基于现有对象创建一个修改了部分字段的新对象
b2 = replace(b, pages=350)
print(b2)           # Book(title='流浪地球', author='刘慈欣', pages=350)
print(b)            # 原对象未变


# ══════════════════════════════════════════════════════
# 8. 嵌套 dataclass
# ══════════════════════════════════════════════════════

@dataclass
class Address:
    city: str
    zipcode: str


@dataclass
class Person:
    name: str
    address: Address


p = Person("Alice", Address("Shanghai", "200000"))
print(p)
print(asdict(p))    # 嵌套字段也会递归转成 dict


# ══════════════════════════════════════════════════════
# dataclass vs 其他选择
# ══════════════════════════════════════════════════════
#
# 普通类         ── 有复杂逻辑的对象
# dataclass     ── 数据载体，需要少量方法（推荐默认选择）
# NamedTuple    ── 只读、轻量、可解包
# TypedDict     ── 字典 + 类型提示，不是真正的对象
# pydantic      ── 需要严格运行时类型校验时（如 API 入参）
#
# 实战建议：
#   - 业务对象、配置项、API 响应模型 → dataclass
#   - 不可变值对象（坐标、向量、ID）→ @dataclass(frozen=True)
#   - 性能敏感、批量创建 → @dataclass(slots=True)
#   - 需要数据校验 → 直接上 pydantic
