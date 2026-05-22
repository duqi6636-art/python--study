"""
第二层：运算符重载
─────────────────────────────────────────
让你的对象支持 +、-、==、<、len()、in 等运算符
本质：每个运算符背后都对应一个魔法方法
"""


# ══════════════════════════════════════════════════════
# 1. 算术运算：__add__ / __sub__ / __mul__
# ══════════════════════════════════════════════════════

class Vector:
    """二维向量"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"

    def __add__(self, other: "Vector") -> "Vector":
        # a + b  →  a.__add__(b)
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector") -> "Vector":
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector":
        # 向量 * 数字
        return Vector(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vector":
        # 数字 * 向量（左操作数不认识右边时，Python 反过来调用 __rmul__）
        return self.__mul__(scalar)


a = Vector(1, 2)
b = Vector(3, 4)
print(a + b)        # Vector(4, 6)
print(b - a)        # Vector(2, 2)
print(a * 3)        # Vector(3, 6)   ← __mul__
print(3 * a)        # Vector(3, 6)   ← __rmul__


# ══════════════════════════════════════════════════════
# 2. 比较运算：__eq__ / __lt__ / __le__ ...
# ══════════════════════════════════════════════════════

class Money:
    def __init__(self, amount: float, currency: str = "CNY"):
        self.amount = amount
        self.currency = currency

    def __repr__(self):
        return f"{self.amount}{self.currency}"

    def __eq__(self, other) -> bool:
        # a == b
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: "Money") -> bool:
        # a < b
        if self.currency != other.currency:
            raise ValueError("不同币种不能比较")
        return self.amount < other.amount

    def __hash__(self):
        # 定义了 __eq__ 必须也定义 __hash__，否则不能放进 set/dict 的 key
        return hash((self.amount, self.currency))


m1 = Money(100)
m2 = Money(100)
m3 = Money(200)
print(m1 == m2)       # True
print(m1 == m3)       # False
print(m1 < m3)        # True

# 只要定义了 __lt__ 和 __eq__，sorted() 就能用
prices = [Money(50), Money(200), Money(100)]
print(sorted(prices)) # [50CNY, 100CNY, 200CNY]

# __hash__ 让它能进 set
print({m1, m2, m3})   # {100CNY, 200CNY}（m1==m2，被去重）


# ══════════════════════════════════════════════════════
# 3. 全部比较运算符 + functools.total_ordering 偷懒
# ══════════════════════════════════════════════════════

from functools import total_ordering


@total_ordering
class Version:
    """只要定义 __eq__ 和 __lt__，自动补全 <= > >= !="""
    def __init__(self, major: int, minor: int):
        self.major = major
        self.minor = minor

    def __repr__(self):
        return f"v{self.major}.{self.minor}"

    def __eq__(self, other):
        return (self.major, self.minor) == (other.major, other.minor)

    def __lt__(self, other):
        return (self.major, self.minor) < (other.major, other.minor)


v1 = Version(1, 0)
v2 = Version(1, 5)
print(v1 < v2)        # True   ← 自己定义的
print(v1 <= v2)       # True   ← total_ordering 自动补
print(v1 != v2)       # True   ← 自动补
print(v2 >= v1)       # True   ← 自动补


# ══════════════════════════════════════════════════════
# 4. 单目运算 & 内置函数
# ══════════════════════════════════════════════════════

class Temperature:
    def __init__(self, celsius: float):
        self.celsius = celsius

    def __repr__(self):
        return f"{self.celsius}°C"

    def __neg__(self):
        # -obj
        return Temperature(-self.celsius)

    def __abs__(self):
        # abs(obj)
        return Temperature(abs(self.celsius))

    def __bool__(self):
        # bool(obj)，决定 if obj: 的真假
        # 0 度认为是"假"
        return self.celsius != 0


t = Temperature(-15)
print(-t)             # 15°C    ← __neg__
print(abs(t))         # 15°C    ← __abs__
print(bool(t))        # True    ← __bool__
print(bool(Temperature(0)))  # False


# ══════════════════════════════════════════════════════
# 运算符 → 魔法方法 对照表
# ══════════════════════════════════════════════════════
#
# 算术：
#   a + b    →  __add__   /  __radd__
#   a - b    →  __sub__   /  __rsub__
#   a * b    →  __mul__   /  __rmul__
#   a / b    →  __truediv__
#   a // b   →  __floordiv__
#   a % b    →  __mod__
#   a ** b   →  __pow__
#   -a       →  __neg__
#   abs(a)   →  __abs__
#
# 比较：
#   a == b   →  __eq__
#   a != b   →  __ne__         （定义了 __eq__ 自动有）
#   a <  b   →  __lt__
#   a <= b   →  __le__
#   a >  b   →  __gt__
#   a >= b   →  __ge__
#
# 内置函数：
#   len(a)   →  __len__
#   bool(a)  →  __bool__
#   hash(a)  →  __hash__
#
# 增量赋值（可选）：
#   a += b   →  __iadd__      （没定义就退化成 a = a + b）
#   a -= b   →  __isub__
