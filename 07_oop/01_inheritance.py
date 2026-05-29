r"""
OOP 第一层：继承 + super + 抽象基类
─────────────────────────────────────────
内容：
1. 单继承：class B(A) 的语义
2. 方法重写（override）
3. super() 调用父类方法
4. 抽象基类（abc.ABC + @abstractmethod）
5. isinstance / issubclass 的运行时类型检查
"""

from abc import ABC, abstractmethod


# ══════════════════════════════════════════════════════
# 1. 单继承的基础
# ══════════════════════════════════════════════════════

class Animal:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def describe(self) -> str:
        return f"{self.name} is {self.age} years old"

    def speak(self) -> str:
        return "..."


class Dog(Animal):                  # Dog 继承自 Animal
    def speak(self) -> str:         # 重写父类方法
        return "Woof!"


class Cat(Animal):
    def speak(self) -> str:
        return "Meow~"


print("── 单继承 ──")
d = Dog("旺财", 3)
print(d.describe())     # 用的是父类的方法
print(d.speak())        # 用的是子类的方法

# 继承的"自动获得"：
#   Dog 没写 __init__、没写 describe，
#   但都从 Animal 继承过来了


# ══════════════════════════════════════════════════════
# 2. super() ── 调用父类方法
# ══════════════════════════════════════════════════════
# 子类想"在父类基础上扩展"时，用 super()

class GuideDog(Dog):
    def __init__(self, name: str, age: int, owner: str):
        super().__init__(name, age)        # 先让父类初始化 name 和 age
        self.owner = owner                  # 子类自己加 owner

    def describe(self) -> str:
        base = super().describe()           # 拿到父类的描述
        return f"{base}, 主人是 {self.owner}"


print("\n── super() 扩展父类 ──")
gd = GuideDog("Lucky", 5, "Alice")
print(gd.describe())     # Lucky is 5 years old, 主人是 Alice
print(gd.speak())        # Woof!  ← 从 Dog 继承


# ══════════════════════════════════════════════════════
# 3. 重写 vs 调用：两种处理父类逻辑的方式
# ══════════════════════════════════════════════════════

class Base:
    def process(self):
        print("  Base.process: 基础逻辑")


class Replace(Base):
    def process(self):              # 完全替换：不调用父类
        print("  Replace.process: 全新逻辑")


class Extend(Base):
    def process(self):              # 扩展：在父类基础上加东西
        super().process()
        print("  Extend.process: 额外补充")


print("\n── 重写 vs 扩展 ──")
Replace().process()
Extend().process()


# ══════════════════════════════════════════════════════
# 4. 抽象基类 ABC ── 定义"必须实现的方法"
# ══════════════════════════════════════════════════════
# 抽象基类是"半成品"：本身不能被实例化，
# 强制子类必须实现指定的方法。

class Shape(ABC):
    """所有形状的抽象基类"""

    @abstractmethod
    def area(self) -> float:
        """子类必须实现"""
        ...

    @abstractmethod
    def perimeter(self) -> float:
        ...

    def describe(self) -> str:           # 非抽象方法可以正常实现
        return f"area={self.area():.2f}, perimeter={self.perimeter():.2f}"


class Rectangle(Shape):
    def __init__(self, w: float, h: float):
        self.w = w
        self.h = h

    def area(self) -> float:
        return self.w * self.h

    def perimeter(self) -> float:
        return 2 * (self.w + self.h)


class Circle(Shape):
    def __init__(self, r: float):
        self.r = r

    def area(self) -> float:
        return 3.14159 * self.r ** 2

    def perimeter(self) -> float:
        return 2 * 3.14159 * self.r


print("\n── 抽象基类 ──")
shapes: list[Shape] = [Rectangle(3, 4), Circle(5)]
for s in shapes:
    print(s.describe())

# 抽象基类不能被实例化：
try:
    Shape()
except TypeError as e:
    print(f"  错误: {e}")
# TypeError: Can't instantiate abstract class Shape ...


# 漏实现抽象方法的子类也不能实例化：
class BadShape(Shape):
    def area(self) -> float:
        return 0
    # 漏了 perimeter

try:
    BadShape()
except TypeError as e:
    print(f"  错误: {e}")


# ══════════════════════════════════════════════════════
# 5. isinstance / issubclass ── 运行时类型检查
# ══════════════════════════════════════════════════════

print("\n── isinstance / issubclass ──")
d = Dog("旺财", 3)

# isinstance 检查"实例"
print(isinstance(d, Dog))       # True
print(isinstance(d, Animal))    # True   ← 子类实例 also is 父类实例
print(isinstance(d, Cat))       # False

# issubclass 检查"类"
print(issubclass(Dog, Animal))   # True
print(issubclass(Dog, Cat))      # False

# 多类型检查（传 tuple）
print(isinstance(d, (Dog, Cat)))   # True


# ══════════════════════════════════════════════════════
# 6. 多态（polymorphism） ── OOP 的核心价值
# ══════════════════════════════════════════════════════
# 同一份代码，对不同类型的对象表现出不同行为

def make_sound(animal: Animal):
    print(f"  {animal.name}: {animal.speak()}")


print("\n── 多态 ──")
animals: list[Animal] = [Dog("旺财", 3), Cat("咪咪", 2), GuideDog("Lucky", 5, "Alice")]
for a in animals:
    make_sound(a)

# make_sound 不关心传进来的具体是什么 Animal，
# 只关心它"有 speak() 方法"——这就是多态的精髓


# ══════════════════════════════════════════════════════
# 7. 实战：异常类的继承体系
# ══════════════════════════════════════════════════════
# Python 内置的异常本身就是一个继承体系

class AppError(Exception):
    """所有业务异常的基类"""

class ValidationError(AppError):
    """数据校验错误"""

class AuthError(AppError):
    """权限相关错误"""

class TokenExpired(AuthError):
    """token 过期，AuthError 的子类"""


# 这种设计的好处：调用方可以按"粒度"捕获
def handle():
    try:
        raise TokenExpired("token 过期")
    except AuthError as e:        # 抓所有权限错误（包括 TokenExpired）
        print(f"  权限错误: {e}")
    except AppError as e:         # 抓所有业务错误
        print(f"  业务错误: {e}")


print("\n── 异常继承体系 ──")
handle()


# ══════════════════════════════════════════════════════
# 8. 速查
# ══════════════════════════════════════════════════════
#
# 继承的语义：
#   class Child(Parent):  ── Child 自动拥有 Parent 的所有方法和属性
#
# 重写：
#   子类定义同名方法，调用时优先用子类的
#
# super()：
#   在子类里调用父类版本的方法，常用于"扩展而非替换"
#
# 抽象基类：
#   from abc import ABC, abstractmethod
#   继承 ABC，方法用 @abstractmethod 装饰
#   强制子类必须实现，否则不能实例化
#
# 工程铁律：
#   - 继承表达"是一个"（GuideDog is a Dog is an Animal）
#   - 不是 is-a 关系就用组合（下一章会讲）
#   - 父类不要超过 2~3 层，太深会变成调试噩梦
