r"""
OOP 第二层：组合优于继承 + Protocol
─────────────────────────────────────────
内容：
1. 继承的局限：is-a 不成立时的痛苦
2. 组合：has-a 关系，对象包对象
3. 鸭子类型：Python 的"看着像就行"哲学
4. typing.Protocol：把鸭子类型变成可静态检查的接口
"""

from typing import Protocol, runtime_checkable


# ══════════════════════════════════════════════════════
# 1. 继承用错的典型例子
# ══════════════════════════════════════════════════════
# 假设我们有一个 Engine（引擎）和 Car（汽车）
# 错误的继承思路：Car 继承 Engine 来"复用启动逻辑"

class EngineBad:
    def start(self):
        print("  引擎启动")


class CarBad(EngineBad):    # ❌ 错：Car is-a Engine？显然不是
    def drive(self):
        self.start()        # 用了引擎的能力


# 这种继承在能跑，但语义错了：
#   "汽车是一种引擎" ← 不成立
#   "汽车有一个引擎" ← 才对


# ══════════════════════════════════════════════════════
# 2. 组合：has-a 关系
# ══════════════════════════════════════════════════════

class Engine:
    def __init__(self, hp: int):
        self.hp = hp

    def start(self):
        print(f"  引擎启动（{self.hp}马力）")


class Wheel:
    def __init__(self, size: int):
        self.size = size


class Car:
    """汽车 = 一个引擎 + 四个轮子（组合）"""
    def __init__(self, hp: int, wheel_size: int):
        self.engine = Engine(hp)                      # 拥有一个引擎
        self.wheels = [Wheel(wheel_size) for _ in range(4)]   # 拥有四个轮子

    def drive(self):
        self.engine.start()
        print(f"  车开动（{len(self.wheels)} 轮，规格 {self.wheels[0].size}）")


print("── 组合 ──")
car = Car(hp=200, wheel_size=18)
car.drive()

# 组合的好处：
#   - 语义对：Car has-a Engine（汽车有一个引擎）
#   - 可替换：换引擎不影响 Car 的设计
#   - 解耦：Engine 改动不会污染 Car


# ══════════════════════════════════════════════════════
# 3. 继承 vs 组合的判断方法
# ══════════════════════════════════════════════════════
#
# 问自己一个问题："X 是一种 Y 吗？"
#
#   GuideDog is-a Dog        ✅ 用继承
#   Dog is-a Animal          ✅ 用继承
#   Car is-a Engine          ❌ 用组合
#   User is-a Email          ❌ 用组合
#   Order is-a OrderItem     ❌ 用组合
#
# 经验法则：
#   - 不确定时用组合
#   - 继承层级控制在 2~3 层内
#   - 跨语义边界（如业务对象继承基础设施）一律用组合


# ══════════════════════════════════════════════════════
# 4. 鸭子类型 ── Python 的哲学
# ══════════════════════════════════════════════════════
# "如果它走起来像鸭子，叫起来像鸭子，那它就是鸭子"
#
# Python 不强制类型，只看"对象有没有需要的方法"

class Duck:
    def quack(self):
        return "嘎嘎"


class Person:
    def quack(self):                # 完全无关的类，但有 quack 方法
        return "我也能学嘎嘎"


def make_quack(thing):
    """不管你是什么，能 quack 就行"""
    return thing.quack()


print("\n── 鸭子类型 ──")
print(make_quack(Duck()))      # 嘎嘎
print(make_quack(Person()))    # 我也能学嘎嘎
# Person 不继承 Duck，也不实现什么接口，
# 但只要有 quack 方法就能用


# ══════════════════════════════════════════════════════
# 5. 鸭子类型的痛点：没有静态检查
# ══════════════════════════════════════════════════════
#
# 上面的 make_quack 没法在编辑器里写类型注解：
#   def make_quack(thing: ???):
#
# 你想表达"thing 必须有 quack 方法"，但没有现成的类型可写。
#
# 解决方案：typing.Protocol


# ══════════════════════════════════════════════════════
# 6. Protocol ── 结构化类型（structural typing）
# ══════════════════════════════════════════════════════
# Protocol 表达"任何有这些方法的对象都算"
# 不需要继承 Protocol，只需要"形状对"

class Quackable(Protocol):
    """任何能 quack 的东西"""
    def quack(self) -> str: ...


def make_quack_typed(thing: Quackable) -> str:
    return thing.quack()


print("\n── Protocol ──")
print(make_quack_typed(Duck()))      # ✅ Duck 有 quack 方法
print(make_quack_typed(Person()))    # ✅ Person 也有 quack 方法

# 关键差别 vs 抽象基类：
#   ABC：必须显式继承（class Duck(QuackableABC)）
#   Protocol：不用继承，只要"形状对"就行
#
# Python 类型检查器（mypy / pyright）能识别 Protocol，
# 在编辑时就能报错，而不是运行时


# ══════════════════════════════════════════════════════
# 7. @runtime_checkable ── 让 Protocol 支持 isinstance
# ══════════════════════════════════════════════════════

@runtime_checkable
class Comparable(Protocol):
    def __lt__(self, other) -> bool: ...
    def __eq__(self, other) -> bool: ...


print("\n── runtime_checkable ──")
print(isinstance(5, Comparable))         # True ← int 有 __lt__/__eq__
print(isinstance("abc", Comparable))     # True ← str 也有
print(isinstance([1, 2], Comparable))    # True


# ══════════════════════════════════════════════════════
# 8. 实战：用 Protocol 解耦业务代码
# ══════════════════════════════════════════════════════
# 场景：发通知。可以发邮件、短信、推送
# 不希望业务代码依赖具体的发送方式

class Notifier(Protocol):
    """任何"能发通知的东西"都行"""
    def send(self, to: str, msg: str) -> None: ...


class EmailNotifier:
    def send(self, to: str, msg: str) -> None:
        print(f"  📧 邮件 -> {to}: {msg}")


class SMSNotifier:
    def send(self, to: str, msg: str) -> None:
        print(f"  📱 短信 -> {to}: {msg}")


class PushNotifier:
    def send(self, to: str, msg: str) -> None:
        print(f"  🔔 推送 -> {to}: {msg}")


# 业务代码只依赖 Protocol，不依赖具体实现
def notify_user(notifier: Notifier, user_id: str, message: str):
    notifier.send(user_id, message)


print("\n── Protocol 解耦业务 ──")
for n in [EmailNotifier(), SMSNotifier(), PushNotifier()]:
    notify_user(n, "user-42", "你的订单已发货")

# 这三个 Notifier 类没有任何继承关系，
# 但都能传给 notify_user，这就是 Protocol 的威力


# ══════════════════════════════════════════════════════
# 9. Protocol vs ABC 选择指南
# ══════════════════════════════════════════════════════
#
# 用 Protocol（推荐默认）：
#   - 想"事后兼容"已有的类（不能改它们的继承关系）
#   - 接口很轻量（一两个方法）
#   - 想用鸭子类型 + 类型检查
#
# 用 ABC：
#   - 想强制子类继承（让继承关系在 isinstance 中显式可见）
#   - 父类有大量"通用实现"想分享给子类
#   - 跟传统 OOP 框架（如 Django）配合
#
# 现代 Python 工程倾向于用 Protocol


# ══════════════════════════════════════════════════════
# 10. 关键速记
# ══════════════════════════════════════════════════════
#
# is-a → 继承        car is-a vehicle ✅
# has-a → 组合       car has-a engine ✅
#
# 鸭子类型 = "看方法不看血统"，Python 的核心哲学
#
# Protocol = 把鸭子类型变成可标注的"接口"
#   不需要继承，只看结构（结构化类型）
#   类型检查器能识别，运行时也可以用 isinstance（需 @runtime_checkable）
#
# 工程建议：
#   - 90% 场景用组合 + Protocol
#   - 继承只用在"明显的 is-a"上
#   - 不要为了"复用代码"而继承（那是组合的工作）
