"""
枚举类 Enum
─────────────────────────────────────────
为什么需要枚举？
  把"一组有限的、命名的常量"打包成一个类型，
  避免散落在代码里的魔法数字 / 魔法字符串。
"""

from enum import Enum, IntEnum, Flag, auto, unique


# ══════════════════════════════════════════════════════
# 1. 基础用法：Enum
# ══════════════════════════════════════════════════════

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


# 三种访问方式
print(Color.RED)           # Color.RED        ← 成员对象
print(Color.RED.name)      # 'RED'            ← 名字
print(Color.RED.value)     # 1                ← 值

# 通过 value 反查
print(Color(1))            # Color.RED
# 通过 name 反查
print(Color["RED"])        # Color.RED


# ══════════════════════════════════════════════════════
# 2. 枚举的核心特性：单例 + 不可比较 int
# ══════════════════════════════════════════════════════

print(Color.RED == Color.RED)      # True
print(Color.RED is Color.RED)      # True   ← 单例，is 也成立
print(Color.RED == 1)              # False  ← 不会和 int 直接相等
# print(Color.RED < Color.GREEN)   # 报错：Enum 默认不能比较大小


# ══════════════════════════════════════════════════════
# 3. auto() : 不关心具体值，让 Python 自动赋值
# ══════════════════════════════════════════════════════

class Status(Enum):
    PENDING = auto()        # 1
    RUNNING = auto()        # 2
    DONE = auto()           # 3
    FAILED = auto()         # 4


print([s.value for s in Status])   # [1, 2, 3, 4]


# ══════════════════════════════════════════════════════
# 4. IntEnum : 既是枚举又是 int（可以参与数值比较）
# ══════════════════════════════════════════════════════

class Priority(IntEnum):
    LOW = 1
    NORMAL = 5
    HIGH = 10


print(Priority.HIGH > Priority.LOW)    # True   ← 可以比较
print(Priority.NORMAL + 1)             # 6      ← 当作整数运算
print(Priority.HIGH == 10)             # True   ← 和 int 直接相等

# 适合：本来就是整数语义的场景（优先级、HTTP 状态码、等级）


# ══════════════════════════════════════════════════════
# 5. 字符串枚举（Python 3.11+ 有 StrEnum）
# ══════════════════════════════════════════════════════

class Env(str, Enum):
    """老写法：继承 str 即可"""
    DEV = "dev"
    PROD = "prod"
    TEST = "test"


print(Env.DEV == "dev")        # True
print(f"running in {Env.DEV}")  # 'running in Env.DEV'

# Python 3.11+ 推荐：from enum import StrEnum 直接用


# ══════════════════════════════════════════════════════
# 6. 在 if / match 中使用
# ══════════════════════════════════════════════════════

def handle(status: Status):
    if status is Status.PENDING:
        return "等待中"
    elif status is Status.RUNNING:
        return "运行中"
    elif status is Status.DONE:
        return "完成"
    else:
        return "失败"


print(handle(Status.RUNNING))


# match 写法（Python 3.10+）
def handle_v2(status: Status) -> str:
    match status:
        case Status.PENDING:  return "等待中"
        case Status.RUNNING:  return "运行中"
        case Status.DONE:     return "完成"
        case Status.FAILED:   return "失败"


print(handle_v2(Status.DONE))


# ══════════════════════════════════════════════════════
# 7. 遍历 + 检查"是不是某个枚举的成员"
# ══════════════════════════════════════════════════════

for s in Status:
    print(f"  {s.name} = {s.value}")

print(Status.RUNNING in Status)        # True


# ══════════════════════════════════════════════════════
# 8. @unique : 防止重复值
# ══════════════════════════════════════════════════════

@unique
class Direction(Enum):
    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3
    # UP = 0   # 加上这行会报错：ValueError: duplicate values

# 不加 @unique 时，重复值的成员会变成"别名"指向第一个


# ══════════════════════════════════════════════════════
# 9. Flag : 位运算枚举（权限、特性开关）
# ══════════════════════════════════════════════════════

class Permission(Flag):
    READ = auto()           # 1
    WRITE = auto()          # 2
    EXECUTE = auto()        # 4
    ALL = READ | WRITE | EXECUTE


# 用 | 组合，用 & 检查
p = Permission.READ | Permission.WRITE
print(p)                        # Permission.WRITE|READ
print(Permission.READ in p)     # True
print(Permission.EXECUTE in p)  # False
print(Permission.ALL)           # Permission.EXECUTE|WRITE|READ


# ══════════════════════════════════════════════════════
# 10. 给枚举加方法（枚举本质是类）
# ══════════════════════════════════════════════════════

class HttpStatus(IntEnum):
    OK = 200
    NOT_FOUND = 404
    SERVER_ERROR = 500

    def is_error(self) -> bool:
        return self.value >= 400

    @classmethod
    def from_code(cls, code: int) -> "HttpStatus":
        return cls(code)


print(HttpStatus.OK.is_error())           # False
print(HttpStatus.NOT_FOUND.is_error())    # True
print(HttpStatus.from_code(500))          # HttpStatus.SERVER_ERROR
