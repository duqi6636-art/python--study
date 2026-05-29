r"""
OOP 第四层：多继承 + MRO + Mixin
─────────────────────────────────────────
内容：
1. 多继承：class C(A, B)
2. MRO（方法解析顺序）：super() 怎么找方法
3. 菱形继承问题
4. Mixin 模式：横向能力的"组件化继承"
"""


# ══════════════════════════════════════════════════════
# 1. 基础多继承
# ══════════════════════════════════════════════════════

class Walker:
    def walk(self):
        return "走路"


class Swimmer:
    def swim(self):
        return "游泳"


class Duck(Walker, Swimmer):       # 同时继承两个父类
    def quack(self):
        return "嘎嘎"


print("── 多继承 ──")
d = Duck()
print(d.walk())     # 从 Walker 来
print(d.swim())     # 从 Swimmer 来
print(d.quack())    # 自己的方法


# ══════════════════════════════════════════════════════
# 2. MRO ── 方法解析顺序
# ══════════════════════════════════════════════════════
# 当多个父类有同名方法时，Python 按 MRO 顺序找

class A:
    def hello(self):
        return "A.hello"


class B:
    def hello(self):
        return "B.hello"


class C(A, B):       # A 在前，优先用 A 的方法
    pass


class D(B, A):       # B 在前，优先用 B 的方法
    pass


print("\n── MRO 决定优先级 ──")
print(C().hello())          # A.hello
print(D().hello())          # B.hello
print(C.__mro__)            # 看 C 的查找顺序

# MRO 输出：
# (<class 'C'>, <class 'A'>, <class 'B'>, <class 'object'>)
# 解读：找方法时按这个顺序，找到就停


# ══════════════════════════════════════════════════════
# 3. 菱形继承
# ══════════════════════════════════════════════════════
#
#       Base
#       /  \
#      X    Y
#       \  /
#       Diamond
#
# X 和 Y 都继承 Base，Diamond 同时继承 X 和 Y。
# Python 用 C3 算法保证 Base 只被走一次。

class Base:
    def __init__(self):
        print("  Base.__init__")

class X(Base):
    def __init__(self):
        super().__init__()
        print("  X.__init__")

class Y(Base):
    def __init__(self):
        super().__init__()
        print("  Y.__init__")

class Diamond(X, Y):
    def __init__(self):
        super().__init__()
        print("  Diamond.__init__")


print("\n── 菱形继承 ──")
Diamond()
# 输出顺序：
#   Base.__init__
#   Y.__init__
#   X.__init__
#   Diamond.__init__
#
# super() 不是简单地"调父类"，而是"按 MRO 找下一个"
# Diamond 的 MRO: Diamond → X → Y → Base → object
# 从 Diamond 调 super() 进入 X，X 调 super() 进入 Y（不是 Base！），
# Y 调 super() 才进入 Base。这就是 C3 算法保证 Base 只走一次的机制

print(Diamond.__mro__)


# ══════════════════════════════════════════════════════
# 4. super() 在多继承下的真实含义
# ══════════════════════════════════════════════════════
# super() 不等于"父类"，而是"MRO 中的下一个"
# 这个差别在多继承时非常关键

class P1:
    def greet(self):
        print("  P1.greet")
        # 这里如果有 super().greet() ，会进入 MRO 中 P1 的下一位

class P2:
    def greet(self):
        print("  P2.greet")

class Sub(P1, P2):
    def greet(self):
        print("  Sub.greet")
        super().greet()      # super() 进入 P1


print("\n── super 是 MRO 的下一位 ──")
Sub().greet()
# 输出：
#   Sub.greet
#   P1.greet


# ══════════════════════════════════════════════════════
# 5. Mixin 模式 ── 横向"插件式"继承
# ══════════════════════════════════════════════════════
# Mixin 是"专门用来被多继承的小类"，
# 提供一组特定能力，自己不能独立使用。

class JSONSerializableMixin:
    """给类加一个"转 JSON"的能力"""
    def to_json(self) -> str:
        import json
        return json.dumps(self.__dict__, ensure_ascii=False)


class TimestampMixin:
    """记录创建/修改时间"""
    def __init__(self):
        from datetime import datetime
        self.created_at = datetime.now().isoformat(timespec="seconds")


class LoggingMixin:
    """加一个简单的日志"""
    def log(self, msg: str):
        print(f"  [{type(self).__name__}] {msg}")


# 业务类组合多个 Mixin
class User(TimestampMixin, JSONSerializableMixin, LoggingMixin):
    def __init__(self, name: str, age: int):
        super().__init__()             # 触发 TimestampMixin.__init__
        self.name = name
        self.age = age


print("\n── Mixin ──")
u = User("Alice", 30)
u.log("用户创建")
print(u.to_json())


# Mixin 命名约定：
#   - 类名以 Mixin 结尾，让人一眼看出意图
#   - Mixin 不应被单独实例化
#   - 一个 Mixin 只做一件事
#
# 真实例子：
#   - Django 的 LoginRequiredMixin、CreateView
#   - SQLAlchemy 的 Mapped 系列


# ══════════════════════════════════════════════════════
# 6. Mixin vs 组合：什么时候用哪个
# ══════════════════════════════════════════════════════
#
# Mixin（多继承）：
#   - 提供"行为"，不引入大量状态
#   - 多个类需要复用同一组方法
#   - 调用方仍然把对象当成单一类型用
#
# 组合：
#   - 引入"实体"（如一个 logger 对象、一个 db 连接）
#   - 关注"持有什么"
#
# 经验法则：
#   - 不确定时优先组合
#   - Mixin 用在"轻量级行为复用"
#   - Mixin 别叠太多，3 个以内能管理


# ══════════════════════════════════════════════════════
# 7. 多继承的常见坑
# ══════════════════════════════════════════════════════

# 坑 1：__init__ 不一致
# 各父类 __init__ 签名不同时，super() 链会出问题
# 解决：约定所有 Mixin 用 *args, **kwargs，把不认识的参数继续往上传

class M1:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("  M1.__init__")

class M2:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("  M2.__init__")

class Combined(M1, M2):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        print(f"  Combined.__init__ name={name}")


print("\n── Mixin 链路安全的 __init__ ──")
Combined("alice")


# 坑 2：MRO 解析失败
# 如果继承顺序冲突，Python 直接报错
#
# class A: pass
# class B(A): pass
# class C(A, B): pass    # ❌ TypeError: MRO conflict
# 因为 C(A, B) 要求 A 在 B 前，但 B(A) 又要求 B 在 A 前


# ══════════════════════════════════════════════════════
# 8. 速查
# ══════════════════════════════════════════════════════
#
# 多继承的语法：
#   class Sub(Parent1, Parent2): ...
#
# MRO（方法解析顺序）：
#   class.__mro__  查看顺序
#   找方法时按这个顺序，找到就停
#
# super() 的真实含义：
#   不是"父类"，而是"MRO 中的下一个"
#
# Mixin 模式：
#   命名以 Mixin 结尾
#   每个 Mixin 只做一件事
#   一般放在多继承的"前面"（左边优先级高）
#
# 工程建议：
#   - 多继承让代码难追踪，能用组合就用组合
#   - 用 Mixin 时，所有 __init__ 用 *args, **kwargs 透传
#   - 复杂场景把每个父类的责任写在 docstring，不然 6 个月后没人看得懂
