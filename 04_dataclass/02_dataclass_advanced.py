"""
dataclass 进阶
─────────────────────────────────────────
- kw_only : 强制关键字参数
- 继承 dataclass 时的"默认值顺序"问题
- InitVar : 只在初始化用、不存为字段
- 自定义 __post_init__ 做校验
- match_args : 配合 match 模式匹配
"""

from dataclasses import dataclass, field, InitVar, KW_ONLY


# ══════════════════════════════════════════════════════
# 1. 继承 dataclass 的"默认值陷阱"
# ══════════════════════════════════════════════════════

@dataclass
class Animal:
    name: str
    species: str = "unknown"   # 父类有默认值


# ❌ 这样写会报错
# @dataclass
# class Dog(Animal):
#     breed: str            # 子类无默认值
# 因为合并后顺序变成 (name, species="unknown", breed)
# 等同于"无默认值的参数排在有默认值之后" → SyntaxError

# ✅ 解决方案 1：子类字段也给默认值
@dataclass
class Dog(Animal):
    breed: str = "unknown"


print(Dog("旺财", breed="柴犬"))


# ══════════════════════════════════════════════════════
# 2. kw_only=True : 强制使用关键字参数（更彻底的解法）
# ══════════════════════════════════════════════════════

@dataclass(kw_only=True)
class AnimalKW:
    name: str
    species: str = "unknown"


@dataclass(kw_only=True)
class DogKW(AnimalKW):
    breed: str            # 没有默认值也没问题！


# 必须用关键字参数
d = DogKW(name="旺财", breed="柴犬")
print(d)
# DogKW("旺财", "柴犬")   # ❌ 不允许位置参数


# ══════════════════════════════════════════════════════
# 3. KW_ONLY : 只让"某些字段"成为关键字参数（部分强制）
# ══════════════════════════════════════════════════════

@dataclass
class Request:
    method: str             # 位置参数
    url: str                # 位置参数
    _: KW_ONLY              # ← 分隔符，下面的字段必须用关键字
    timeout: int = 30
    retries: int = 3
    headers: dict = field(default_factory=dict)


# url 之前可以位置参数，timeout/retries/headers 必须关键字
r = Request("GET", "/api/users", timeout=60, retries=5)
print(r)
# Request("GET", "/api/users", 60)   # ❌ 不允许


# ══════════════════════════════════════════════════════
# 4. InitVar : 只在初始化用，不存成字段
# ══════════════════════════════════════════════════════

@dataclass
class Account:
    username: str
    password_hash: str = field(init=False)   # 不在 __init__ 参数中
    raw_password: InitVar[str] = ""          # 仅传给 __post_init__

    def __post_init__(self, raw_password: str):
        # raw_password 不会成为实例属性，只作为参数传入
        self.password_hash = f"hashed({raw_password})"


a = Account(username="alice", raw_password="secret123")
print(a)                    # password_hash 在 repr 中
print(hasattr(a, "raw_password"))   # False  ← 不是属性


# ══════════════════════════════════════════════════════
# 5. __post_init__ 做校验
# ══════════════════════════════════════════════════════

@dataclass
class Range:
    low: int
    high: int

    def __post_init__(self):
        if self.low > self.high:
            raise ValueError(f"low ({self.low}) 不能大于 high ({self.high})")


print(Range(0, 10))
try:
    Range(10, 0)
except ValueError as e:
    print(f"  捕获: {e}")


# ══════════════════════════════════════════════════════
# 6. 配合 match 模式匹配（Python 3.10+）
# ══════════════════════════════════════════════════════

@dataclass
class Circle:
    radius: float

@dataclass
class Square:
    side: float

@dataclass
class Rectangle:
    width: float
    height: float


def area(shape) -> float:
    match shape:
        case Circle(radius=r):
            return 3.14159 * r * r
        case Square(side=s):
            return s * s
        case Rectangle(width=w, height=h):
            return w * h
        case _:
            raise TypeError("未知形状")


print(area(Circle(5)))
print(area(Square(4)))
print(area(Rectangle(3, 6)))


# ══════════════════════════════════════════════════════
# 7. 位置匹配 : 利用 __match_args__ 自动生成
# ══════════════════════════════════════════════════════
# dataclass 默认会生成 __match_args__ = ('字段1', '字段2', ...)
# 所以可以用位置匹配，更简洁

def area_v2(shape) -> float:
    match shape:
        case Circle(r):                    # 位置匹配：第一个字段是 radius
            return 3.14159 * r * r
        case Square(s):
            return s * s
        case Rectangle(w, h):
            return w * h


print(area_v2(Circle(5)))


# ══════════════════════════════════════════════════════
# 8. 综合例子：把所有特性用上
# ══════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True, kw_only=True)
class HttpRequest:
    """
    frozen   : 不可变（请求构造后不应再改）
    slots    : 节省内存
    kw_only  : 强制关键字参数，避免 Request("GET","POST",...) 这种眼瞎
    """
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    body: str = ""
    timeout: int = 30

    def __post_init__(self):
        if self.method not in ("GET", "POST", "PUT", "DELETE"):
            raise ValueError(f"非法 method: {self.method}")
        if self.timeout <= 0:
            raise ValueError("timeout 必须大于 0")


req = HttpRequest(
    method="POST",
    url="/api/login",
    body='{"user":"alice"}',
    timeout=10,
)
print(req)

# 验证：frozen 生效
try:
    req.timeout = 5
except Exception as e:
    print(f"  {type(e).__name__}: 不可变")

# 验证：kw_only 生效
try:
    HttpRequest("GET", "/api")   # 没用关键字
except TypeError as e:
    print(f"  TypeError: {e}")

# 验证：__post_init__ 校验生效
try:
    HttpRequest(method="WTF", url="/api")
except ValueError as e:
    print(f"  ValueError: {e}")
