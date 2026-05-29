r"""
OOP 第三层：封装 + property 进阶
─────────────────────────────────────────
内容：
1. 命名约定：_x（保护）、__x（名字改写）
2. @property + setter + deleter（完整版属性）
3. 实战：用 property 实现校验、派生属性
4. 描述符简介（__get__ / __set__）
"""


# ══════════════════════════════════════════════════════
# 1. 命名约定 ── Python 的"伪私有"
# ══════════════════════════════════════════════════════
# Python 没有 private/protected/public 关键字，
# 用命名约定表达可见性：
#
#   x       → 公开属性
#   _x      → "保护"，约定上不要外部直接用
#   __x     → "私有"，触发 name mangling

class Account:
    def __init__(self, balance: float):
        self.balance = balance        # 公开
        self._note = "internal"       # "保护"
        self.__pin = "1234"            # 真正"私有"


a = Account(100)
print("── 命名约定 ──")
print(a.balance)        # 100      公开访问 OK
print(a._note)          # 'internal'  能访问，但你"不应该"用
# print(a.__pin)        # AttributeError ← 直接访问报错

# 但 __pin 不是真私有，只是被改写了名字：
print(a._Account__pin)  # '1234'   ← 通过这个名字仍能访问
#
# Python 把 __pin 改成了 _Account__pin（自动加前缀 _类名__）
# 这叫 "name mangling"，目的是避免子类意外覆盖父类的同名属性


# ══════════════════════════════════════════════════════
# 2. name mangling 真正的用途
# ══════════════════════════════════════════════════════
# 不是为了"私有"，而是为了"避免父子类属性冲突"

class Parent:
    def __init__(self):
        self.__id = "parent-id"        # → _Parent__id

    def get_id(self):
        return self.__id               # 父类内部访问的还是 _Parent__id


class Child(Parent):
    def __init__(self):
        super().__init__()
        self.__id = "child-id"         # → _Child__id（不会覆盖父类的）


c = Child()
print("\n── name mangling ──")
print(c.get_id())                  # 'parent-id'  ← 父类的方法访问父类的 __id
print(c._Parent__id)               # 'parent-id'
print(c._Child__id)                # 'child-id'
# 这种"自动加前缀"避免了子类无意中覆盖父类的属性


# ══════════════════════════════════════════════════════
# 3. @property ── 把方法伪装成属性
# ══════════════════════════════════════════════════════
# 之前学过基础用法。这次看完整版：getter / setter / deleter

class Temperature:
    def __init__(self, celsius: float = 0):
        self._celsius = celsius              # 真正存储用 _celsius

    @property
    def celsius(self) -> float:
        """getter：t.celsius 时调用"""
        return self._celsius

    @celsius.setter
    def celsius(self, value: float):
        """setter：t.celsius = 30 时调用"""
        if value < -273.15:
            raise ValueError(f"温度不能低于绝对零度: {value}")
        self._celsius = value

    @celsius.deleter
    def celsius(self):
        """deleter：del t.celsius 时调用"""
        print("  [警告] 重置温度为 0")
        self._celsius = 0

    @property
    def fahrenheit(self) -> float:
        """派生属性：从 celsius 计算"""
        return self._celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value: float):
        """允许通过华氏度反向赋值"""
        self.celsius = (value - 32) * 5 / 9   # 通过 setter 设置，享受校验


print("\n── property setter/deleter ──")
t = Temperature(20)
print(t.celsius)         # 20         ← getter
t.celsius = 30           # ← setter
print(t.celsius)         # 30
print(t.fahrenheit)      # 86.0       ← 派生属性
t.fahrenheit = 100       # ← 反向赋值
print(t.celsius)         # 37.78
del t.celsius            # ← deleter
print(t.celsius)         # 0

try:
    t.celsius = -300     # 校验
except ValueError as e:
    print(f"  错误: {e}")


# ══════════════════════════════════════════════════════
# 4. property 的几个典型用途
# ══════════════════════════════════════════════════════

# (a) 属性校验
class User:
    def __init__(self, age: int):
        self.age = age              # 走 setter，自动校验

    @property
    def age(self):
        return self._age

    @age.setter
    def age(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"非法年龄: {value!r}")
        self._age = value


print("\n── property 校验 ──")
u = User(25)
print(u.age)
try:
    u.age = -5
except ValueError as e:
    print(f"  错误: {e}")


# (b) 派生属性（计算字段）
class Rectangle:
    def __init__(self, w, h):
        self.w = w
        self.h = h

    @property
    def area(self):
        return self.w * self.h


r = Rectangle(3, 4)
print(r.area)         # 12，像普通属性一样访问，但是动态计算的


# (c) 兼容性：原本是属性后来要改成方法
# 在不破坏旧代码的前提下加入逻辑
class Counter:
    def __init__(self):
        self._count = 0

    @property
    def count(self):
        # 第一版直接是 self.count = 0
        # 后来发现需要"读取时记日志"，改成 property，调用方代码不用改
        print("  [审计] 读取了 count")
        return self._count

    @count.setter
    def count(self, v):
        self._count = v


print("\n── property 改造旧代码 ──")
c = Counter()
c.count = 10
_ = c.count          # 触发 [审计]


# ══════════════════════════════════════════════════════
# 5. 描述符（descriptor）── property 的"通用版"
# ══════════════════════════════════════════════════════
# property 是给"单个属性"加 getter/setter/deleter
# 描述符是把这套逻辑"做成可复用的类"，多处使用

class PositiveNumber:
    """复用的"必须是正数"的字段"""
    def __set_name__(self, owner, name):
        # Python 自动把字段名告诉描述符
        self.private_name = f"_{name}"

    def __get__(self, instance, owner):
        return getattr(instance, self.private_name)

    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError(f"必须是正数，得到 {value}")
        setattr(instance, self.private_name, value)


class Product:
    price = PositiveNumber()         # 类级别声明，所有实例共享"校验逻辑"
    quantity = PositiveNumber()

    def __init__(self, price, quantity):
        self.price = price           # 触发 PositiveNumber.__set__
        self.quantity = quantity


print("\n── 描述符 ──")
p = Product(price=10, quantity=5)
print(p.price, p.quantity)           # 10 5

try:
    p.price = -1
except ValueError as e:
    print(f"  错误: {e}")

# 描述符的优势：
#   - 一次定义，多处复用（property 每个属性都得写一遍）
#   - 是 Python 的底层机制，@property 本身就是用描述符实现的
# 实战中：
#   - 1~2 个属性 → 用 property 即可
#   - 同一个校验/转换逻辑用在多处 → 写描述符


# ══════════════════════════════════════════════════════
# 6. 速查
# ══════════════════════════════════════════════════════
#
# 命名约定：
#   x       公开属性（外部可用）
#   _x      "保护"（约定不外用，无强制）
#   __x     name mangling（避免父子类冲突，不是真正的私有）
#
# property 完整版：
#   @property                  getter
#   @<name>.setter             setter
#   @<name>.deleter            deleter
#
# 何时用 property：
#   - 需要校验赋值
#   - 派生/计算属性
#   - 改造旧代码不破坏调用方
#
# 何时用描述符：
#   - 同一个 getter/setter 逻辑要在多个属性 / 多个类上复用
#
# 工程建议：
#   - 简单数据类用 dataclass，别动不动就上 property
#   - 校验逻辑超过一两条 → 直接上 pydantic
#   - 描述符是"造轮子"工具，业务代码很少需要
