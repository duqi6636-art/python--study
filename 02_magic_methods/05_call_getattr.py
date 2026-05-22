"""
第五层：高级行为
─────────────────────────────────────────
__call__         →  让对象像函数一样被调用：obj()
__getattr__      →  访问不存在的属性时触发（拦截）
__setattr__      →  设置任何属性时触发
__getattribute__ →  访问任何属性时触发（慎用）
__slots__        →  限制属性，节省内存
"""


# ══════════════════════════════════════════════════════
# 1. __call__ : 让对象可以像函数一样调用
# ══════════════════════════════════════════════════════

class Adder:
    """带状态的"函数"——闭包用类实现"""
    def __init__(self, base: int):
        self.base = base

    def __call__(self, x: int) -> int:
        # 让 obj(arg) 能调用
        return self.base + x


add5 = Adder(5)
print(add5(10))         # 15  ← 触发 __call__
print(add5(20))         # 25
print(callable(add5))   # True

# 实战意义：装饰器、工厂、有状态的回调
class Counter:
    def __init__(self):
        self.count = 0

    def __call__(self):
        self.count += 1
        return self.count


tick = Counter()
print(tick(), tick(), tick())   # 1 2 3


# ══════════════════════════════════════════════════════
# 2. __getattr__ : 访问"不存在"的属性时兜底
# ══════════════════════════════════════════════════════

class LazyConfig:
    """只在第一次访问属性时才去加载"""
    def __init__(self):
        self._data = None

    def __getattr__(self, name: str):
        # 只在正常属性查找失败后才被调用
        print(f"  [拦截] 访问了 {name}")
        if self._data is None:
            print("  [加载] 第一次访问，初始化数据")
            self._data = {"host": "localhost", "port": 8080, "debug": True}
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"无此配置: {name}")


cfg = LazyConfig()
print(cfg.host)         # 触发加载
print(cfg.port)         # 已加载，直接返回
# print(cfg.unknown)    # 抛 AttributeError

# 注意：__getattr__ 仅在 "找不到属性" 时调用
#       已经存在的属性（如 self._data）不会触发它


# ══════════════════════════════════════════════════════
# 3. __setattr__ : 拦截所有属性赋值
# ══════════════════════════════════════════════════════

class FrozenPoint:
    """坐标只读，赋值就报错"""
    def __init__(self, x: float, y: float):
        # 在 __init__ 里赋值也会触发 __setattr__！
        # 所以要用 object.__setattr__ 绕过
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)

    def __setattr__(self, name: str, value):
        raise AttributeError(f"FrozenPoint 是只读的，不能修改 {name}")

    def __repr__(self):
        return f"({self.x}, {self.y})"


p = FrozenPoint(1.0, 2.0)
print(p)                # (1.0, 2.0)
try:
    p.x = 100           # 触发 __setattr__，抛异常
except AttributeError as e:
    print(f"  错误: {e}")


# ══════════════════════════════════════════════════════
# 4. __getattribute__ : 拦截"所有"属性访问（极少用）
# ══════════════════════════════════════════════════════

class Tracer:
    def __init__(self):
        self.x = 10

    def __getattribute__(self, name: str):
        # 注意：每一次属性访问都会进来，包括 self.x、方法调用
        # 容易写出无限递归，必须用 object.__getattribute__ 取真实值
        print(f"  [trace] 访问 {name}")
        return object.__getattribute__(self, name)


t = Tracer()
_ = t.x                 # 触发 trace

# __getattribute__ vs __getattr__:
#   __getattribute__  ── 每次访问都触发（无差别拦截）
#   __getattr__       ── 仅在常规查找失败后兜底
# 实战中 99% 用 __getattr__，几乎不用 __getattribute__


# ══════════════════════════════════════════════════════
# 5. __slots__ : 限制属性 + 节省内存
# ══════════════════════════════════════════════════════

class Pixel:
    """普通类对象有 __dict__，可以随意加属性"""
    pass


class PixelSlim:
    """声明 __slots__ 后，禁止 __dict__，只允许列出的属性"""
    __slots__ = ("x", "y", "color")

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color


# 普通类：随便加属性
p1 = Pixel()
p1.foo = 123            # OK
print(p1.foo)

# slots 类：只能用声明的属性
p2 = PixelSlim(1, 2, "red")
print(p2.x, p2.color)
try:
    p2.foo = 123        # 报错
except AttributeError as e:
    print(f"  错误: {e}")

# 内存效益：批量创建上百万对象时，__slots__ 能省 30~50% 内存
# 副作用：失去 __dict__，无法用 getattr/setattr 动态扩展


# ══════════════════════════════════════════════════════
# 各魔法方法的"触发优先级"
# ══════════════════════════════════════════════════════
#
# 读属性 obj.x：
#   1. __getattribute__（每次必经）
#   2. 在 __dict__ / 类 / 父类中查找
#   3. 找不到 → __getattr__（兜底）
#
# 写属性 obj.x = v：
#   1. __setattr__（每次必经）
#
# 删属性 del obj.x：
#   1. __delattr__
#
# 调用 obj(...)：
#   1. __call__
#
# 实战推荐使用频率：
#   __call__         ★★★★★  装饰器、工厂、状态机
#   __getattr__      ★★★★    懒加载、属性代理、ORM
#   __slots__        ★★★     性能敏感场景
#   __setattr__      ★★      不可变对象、属性校验
#   __getattribute__ ★       几乎不用，容易踩坑
