r"""
装饰器第三层：类装饰器 + 装饰器叠加
─────────────────────────────────────────
本层回答三个问题：
1. 用"类"实现装饰器（不是用函数）
2. 装饰"类"本身（不是装饰函数）
3. @a @b @c def f() 的执行顺序到底是什么
"""

import functools


# ══════════════════════════════════════════════════════
# 1. 用"类"实现装饰器：__call__ 让对象可调用
# ══════════════════════════════════════════════════════
# 上一层我们见过的都是"函数装饰器"。
# 装饰器本质是"接收函数、返回可调用对象"——
# 类只要实现了 __call__，就是可调用对象，自然能当装饰器。

class CountCalls:
    """统计函数被调用了多少次"""
    def __init__(self, func):
        functools.update_wrapper(self, func)   # 等同于 @functools.wraps
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"  [{self.func.__name__}] 第 {self.count} 次调用")
        return self.func(*args, **kwargs)


@CountCalls
def greet(name):
    return f"Hello {name}"


print("── 类装饰器 ──")
greet("Alice")
greet("Bob")
greet("Charlie")
print(f"总调用: {greet.count}")    # ← 装饰器是"对象"，能直接读它的属性


# 函数装饰器 vs 类装饰器：
#   - 简单逻辑   → 函数装饰器（更轻量）
#   - 需要状态   → 类装饰器（属性管理状态比闭包更直观）
#   - 想暴露方法 → 类装饰器（如 cache_clear / reset 等管理方法）


# ══════════════════════════════════════════════════════
# 2. 带参数的类装饰器
# ══════════════════════════════════════════════════════

class Tag:
    """给被装饰的函数加一个"分类标签"，记录到全局注册表"""
    REGISTRY: dict[str, list] = {}

    def __init__(self, label: str):
        self.label = label

    def __call__(self, func):
        functools.update_wrapper(self, func)
        Tag.REGISTRY.setdefault(self.label, []).append(func.__name__)
        return func    # 这里直接返回原函数（只做"注册"，不包装）


@Tag("admin")
def manage_users(): ...

@Tag("admin")
def delete_data(): ...

@Tag("public")
def view_home(): ...


print("\n── 带参数的类装饰器（注册表模式）──")
print(Tag.REGISTRY)
# {'admin': ['manage_users', 'delete_data'], 'public': ['view_home']}


# ══════════════════════════════════════════════════════
# 3. 装饰"类"本身（不是装饰函数）
# ══════════════════════════════════════════════════════
# 装饰器不限于函数：拿到一个类，返回一个加工过的类。
# @dataclass、@functools.total_ordering 都是这种。

def add_repr(cls):
    """给任何类自动加一个 __repr__"""
    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{cls.__name__}({attrs})"
    cls.__repr__ = __repr__
    return cls


@add_repr
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


print("\n── 装饰类：自动加 __repr__ ──")
print(Point(3, 5))    # Point(x=3, y=5)


# 带参数的"装饰类"
def auto_str(prefix: str = ""):
    def decorator(cls):
        original_str = cls.__str__
        def __str__(self):
            return f"{prefix}{original_str(self)}"
        cls.__str__ = __str__
        return cls
    return decorator


@auto_str(prefix="🍕 ")
class Pizza:
    def __str__(self):
        return "玛格丽特"


print(str(Pizza()))    # 🍕 玛格丽特


# ══════════════════════════════════════════════════════
# 4. 装饰器叠加：@a @b @c 的执行顺序
# ══════════════════════════════════════════════════════
# 关键规则：从下往上"装饰"，从上往下"调用"。

def deco_a(func):
    print("  [装饰阶段] A 在装饰")
    @functools.wraps(func)
    def wrapper(*a, **kw):
        print("    A 进")
        result = func(*a, **kw)
        print("    A 出")
        return result
    return wrapper


def deco_b(func):
    print("  [装饰阶段] B 在装饰")
    @functools.wraps(func)
    def wrapper(*a, **kw):
        print("    B 进")
        result = func(*a, **kw)
        print("    B 出")
        return result
    return wrapper


def deco_c(func):
    print("  [装饰阶段] C 在装饰")
    @functools.wraps(func)
    def wrapper(*a, **kw):
        print("    C 进")
        result = func(*a, **kw)
        print("    C 出")
        return result
    return wrapper


print("\n── 装饰阶段（从下往上）──")

@deco_a
@deco_b
@deco_c
def hello():
    print("    hello() 实际逻辑")


# 装饰阶段的输出顺序：C → B → A
# 因为等价于：hello = deco_a(deco_b(deco_c(hello)))
#                              ↑↑↑
#                          最内层先执行


print("\n── 调用阶段（从上往下）──")
hello()
# 调用顺序（从外层到内层）：
#   A 进 → B 进 → C 进 → hello() → C 出 → B 出 → A 出


# ══════════════════════════════════════════════════════
# 5. 直观地理解装饰器叠加
# ══════════════════════════════════════════════════════
#
# 写法：
#   @deco_a
#   @deco_b
#   @deco_c
#   def hello(): ...
#
# 等价于：
#   hello = deco_a(deco_b(deco_c(hello)))
#
# 想象成"洋葱皮"：
#
#     deco_a 包在最外面
#       └─ deco_b
#            └─ deco_c
#                 └─ hello() 在最里面
#
# 调用 hello() 时：
#   - 先穿 A → 再穿 B → 再穿 C → 到达核心 → 出来时反过来：C → B → A
#
# 实战意义：
#   - 想最先触发的装饰器（如鉴权）写在最上面
#   - 想最贴近原函数的装饰器（如计时）写在最下面


# ══════════════════════════════════════════════════════
# 6. 实战：组合三个装饰器（鉴权 + 日志 + 计时）
# ══════════════════════════════════════════════════════

import time

current_user = {"role": "admin"}     # 模拟登录态


def require_role(role: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*a, **kw):
            if current_user.get("role") != role:
                raise PermissionError(f"需要 {role} 角色")
            return func(*a, **kw)
        return wrapper
    return decorator


def log_call(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        print(f"  [日志] 调用 {func.__name__}")
        return func(*a, **kw)
    return wrapper


def timeit(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        start = time.perf_counter()
        result = func(*a, **kw)
        ms = (time.perf_counter() - start) * 1000
        print(f"  [计时] {func.__name__} 用时 {ms:.2f}ms")
        return result
    return wrapper


@require_role("admin")    # ← 最外层：先鉴权，权限不够直接拒绝
@log_call                 # ← 中间：记录调用
@timeit                   # ← 最内层：贴近原函数，准确计时
def delete_user(uid: int):
    time.sleep(0.05)
    return f"已删除用户 {uid}"


print("\n── 三装饰器叠加 ──")
print(delete_user(42))


# 调用顺序：
#   require_role 检查 → log_call 记录 → timeit 计时 → 原函数 → timeit 出 → log_call 出 → require_role 出
#
# 顺序之所以这样安排：
#   - 鉴权失败时，根本不需要走日志和计时（短路）
#   - 计时贴近函数，结果不被装饰器开销污染
#   - 日志夹在中间，记录"被允许的调用"


# ══════════════════════════════════════════════════════
# 7. 类装饰器叠加 = 同样的规则
# ══════════════════════════════════════════════════════

def add_method(cls):
    cls.greet = lambda self: f"Hi from {cls.__name__}"
    return cls


def add_attr(cls):
    cls.version = "1.0"
    return cls


@add_method
@add_attr
class Tool:
    pass


print("\n── 装饰类叠加 ──")
print(Tool.version)         # 1.0
print(Tool().greet())       # Hi from Tool


# ══════════════════════════════════════════════════════
# 8. 工程总结
# ══════════════════════════════════════════════════════
#
# 类装饰器：
#   - 用 __call__ 让对象可调用
#   - 用实例属性管理状态（更直观，比闭包好读）
#   - 想暴露管理方法（reset / clear / inspect）时优先选
#
# 装饰类：
#   - 拿类、改类、还类
#   - @dataclass、@total_ordering 是经典例子
#   - 给一组类批量加属性 / 方法 / 注册到容器
#
# 叠加顺序：
#   - 装饰从下往上、调用从外到内
#   - 鉴权 → 日志 → 缓存 → 计时 → 原函数（典型顺序）
#   - 把"短路成本最低"的放最外层
