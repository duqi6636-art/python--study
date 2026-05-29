r"""
OOP 第五层：元类 + __init_subclass__（选学）
─────────────────────────────────────────
这一层是"框架开发者级别"的内容。
日常业务 99% 用不到，但能看懂这些会让你彻底理解 Python 的对象模型。

内容：
1. type ── 类的"类"
2. 元类是什么、何时用
3. __init_subclass__ ── 元类的现代替代品（更简单）
4. 实战：自动注册子类、强制约束子类
"""


# ══════════════════════════════════════════════════════
# 1. type 是什么
# ══════════════════════════════════════════════════════
# 在 Python 里"一切皆对象"，类本身也是对象。
# 那"类"这个对象的类型是什么？答案是 type。

class Foo:
    pass

print("── type 是类的类 ──")
print(type(42))            # <class 'int'>      整数的类型是 int
print(type("hello"))       # <class 'str'>      字符串的类型是 str
print(type(Foo))           # <class 'type'>     类 Foo 的类型是 type
print(type(int))           # <class 'type'>     int 自身的类型也是 type

# 也就是说：
#   42 是 int 的实例
#   int 是 type 的实例
#   type 是 type 的实例（自指）


# ══════════════════════════════════════════════════════
# 2. 用 type 动态创建类
# ══════════════════════════════════════════════════════
# 一般用 class 关键字定义类，等价的"动态版"是 type(name, bases, namespace)

# 普通定义
class Dog1:
    species = "Canis"
    def bark(self):
        return "Woof"


# 动态定义，完全等价
Dog2 = type(
    "Dog2",                                  # 类名
    (object,),                               # 父类元组
    {"species": "Canis", "bark": lambda self: "Woof"},   # 属性 / 方法
)

print("\n── 动态创建类 ──")
print(Dog1().bark())       # Woof
print(Dog2().bark())       # Woof
print(Dog2.__name__)       # 'Dog2'

# 这就是元类的本质：type 是默认的"类创建器"


# ══════════════════════════════════════════════════════
# 3. 自定义元类
# ══════════════════════════════════════════════════════
# 元类 = 控制"类怎么被创建"的钩子。
# 通过继承 type 实现。

class UpperAttrMeta(type):
    """让所有非下划线开头的属性名自动变大写"""
    def __new__(mcs, name, bases, namespace):
        new_namespace = {}
        for key, value in namespace.items():
            if not key.startswith("_"):
                new_namespace[key.upper()] = value
            else:
                new_namespace[key] = value
        return super().__new__(mcs, name, bases, new_namespace)


class Config(metaclass=UpperAttrMeta):
    debug = True
    port = 8080
    _secret = "abc"      # 下划线开头的不变


print("\n── 元类改写属性 ──")
print(Config.DEBUG)        # True   ← 被改成大写
print(Config.PORT)         # 8080
print(Config._secret)      # 'abc'  ← 没变
# print(Config.debug)      # AttributeError ← 已不存在小写版

# 元类的执行时机：
#   class Config(metaclass=...): 这一行执行时，元类的 __new__ 被调用
#   早于任何实例的创建


# ══════════════════════════════════════════════════════
# 4. 元类典型用途：自动注册子类
# ══════════════════════════════════════════════════════
# 一个常见框架需求：所有子类自动注册到一个全局表里

class HandlerMeta(type):
    """所有 Handler 子类自动注册到 REGISTRY"""
    REGISTRY: dict = {}

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        if name != "Handler":      # 跳过基类自己
            HandlerMeta.REGISTRY[name] = cls


class Handler(metaclass=HandlerMeta):
    def handle(self):
        raise NotImplementedError


class LoginHandler(Handler):
    def handle(self):
        return "处理登录"


class LogoutHandler(Handler):
    def handle(self):
        return "处理登出"


print("\n── 元类自动注册 ──")
print(HandlerMeta.REGISTRY)
# {'LoginHandler': <class>, 'LogoutHandler': <class>}

# 调用方可以按名字拿对应的 Handler
HandlerMeta.REGISTRY["LoginHandler"]().handle()


# ══════════════════════════════════════════════════════
# 5. __init_subclass__ ── 元类的现代替代品
# ══════════════════════════════════════════════════════
# Python 3.6+ 提供 __init_subclass__，
# 90% 的元类需求可以用它代替，写法简单太多

class Plugin:
    REGISTRY: dict = {}

    def __init_subclass__(cls, **kwargs):
        """每次有子类时自动调用"""
        super().__init_subclass__(**kwargs)
        Plugin.REGISTRY[cls.__name__] = cls


class FormatterPlugin(Plugin):
    def format(self, x): return str(x)


class ValidatorPlugin(Plugin):
    def validate(self, x): return True


print("\n── __init_subclass__ ──")
print(Plugin.REGISTRY)
# {'FormatterPlugin': <class>, 'ValidatorPlugin': <class>}


# 比元类的好处：
#   - 不用继承 type，不用懂元类机制
#   - 在普通类里加一个方法就行
#   - 子类用法不变（不用写 metaclass=...）


# ══════════════════════════════════════════════════════
# 6. __init_subclass__ + 参数：强制约束子类
# ══════════════════════════════════════════════════════
# 子类继承时还能传参数给 __init_subclass__

class Connector:
    def __init_subclass__(cls, *, protocol: str, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.protocol = protocol
        print(f"  注册连接器 {cls.__name__} 协议 {protocol}")


class HTTPConnector(Connector, protocol="http"):
    pass


class WebSocketConnector(Connector, protocol="ws"):
    pass


# 没传 protocol 会报错：
# class BadConnector(Connector): pass
#   TypeError: missing keyword argument: 'protocol'

print("\n── 子类传参 ──")
print(HTTPConnector.protocol)      # 'http'
print(WebSocketConnector.protocol) # 'ws'


# ══════════════════════════════════════════════════════
# 7. 元类 vs 装饰类 vs __init_subclass__
# ══════════════════════════════════════════════════════
#
# 三种"加工类"的方式，能力递增（其实都能加工类，只是侵入性不同）：
#
# 装饰类：
#   @add_repr
#   class Foo: ...
#   - 最轻量、最直观
#   - 只能事后加工，不能控制实例化过程
#
# __init_subclass__：
#   class Plugin:
#       def __init_subclass__(cls, ...): ...
#   - 在父类里定义，子类自动触发
#   - 不需要继承 type
#   - 90% 元类需求都用它
#
# 元类（metaclass=type 子类）：
#   - 能力最强：控制类的创建、改写命名空间、控制实例化等
#   - 写起来最复杂、最容易出错
#   - 真正的元类需求：Django ORM Model、ABC、SQLAlchemy 的 declarative_base
#
# 选择优先级：
#   能用装饰类 > __init_subclass__ > 元类


# ══════════════════════════════════════════════════════
# 8. 速查
# ══════════════════════════════════════════════════════
#
# type ──"类的类"，所有类默认都是 type 的实例
#
# 元类的写法：
#   class MyMeta(type):
#       def __new__(mcs, name, bases, namespace): ...
#       def __init__(cls, name, bases, namespace): ...
#
#   class Foo(metaclass=MyMeta): ...
#
# __init_subclass__ ── 现代替代品：
#   class Base:
#       def __init_subclass__(cls, **kw): ...
#
# 工程建议：
#   - 业务代码几乎不需要元类
#   - 框架/库开发也优先考虑 __init_subclass__
#   - 真要写元类，先看看能不能用装饰类或 __init_subclass__ 实现
#
# 这一层重在"看懂"：
#   - 能看懂别人写的元类
#   - 知道 Django Model、SQLAlchemy 用了元类
#   - 自己写代码尽量避开
