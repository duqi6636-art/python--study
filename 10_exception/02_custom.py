r"""
异常第二层：自定义异常 + 异常链 + ExceptionGroup
─────────────────────────────────────────
内容：
1. 为什么要自定义异常
2. 自定义异常类的设计
3. 异常链：raise ... from（保留根因）
4. __cause__ 和 __context__ 的区别
5. 异常组（ExceptionGroup, Python 3.11+）
6. except* 语法
"""


# ══════════════════════════════════════════════════════
# 1. 为什么要自定义异常
# ══════════════════════════════════════════════════════
# 用内置异常的痛点：
#   - 调用方不知道这是"业务问题"还是"基础设施问题"
#   - 想精确捕获某种业务错误时，类型不够用
#   - 错误想带上额外字段（如错误码、上下文）

# 反例：什么都用 ValueError
def buy_bad(item: str, qty: int):
    if qty <= 0:
        raise ValueError(f"qty 必须 > 0: {qty}")
    if item not in ["apple", "banana"]:
        raise ValueError(f"商品不存在: {item}")
    return f"买了 {qty} 个 {item}"

# 调用方：except ValueError ← 抓到的是哪一种问题？分不清


# ══════════════════════════════════════════════════════
# 2. 设计自定义异常的标准做法
# ══════════════════════════════════════════════════════

class AppError(Exception):
    """所有业务异常的基类"""


class ValidationError(AppError):
    """数据校验失败"""


class NotFoundError(AppError):
    """资源不存在"""


class PermissionDeniedError(AppError):
    """权限不足"""


# 带额外字段的异常
class HTTPError(AppError):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"HTTP {status}: {message}")


print("── 自定义异常 ──")
try:
    raise HTTPError(404, "user not found")
except HTTPError as e:
    print(f"  status: {e.status}")
    print(f"  message: {e.message}")
    print(f"  str: {e}")


# 设计原则：
#   1) 整个项目有一个 AppError 根基类
#   2) 业务子类继承 AppError（ValidationError / NotFoundError ...）
#   3) 调用方按需选粒度捕获（ValidationError 还是 AppError）
#   4) 想带数据的异常 → 自定义 __init__


# ══════════════════════════════════════════════════════
# 3. 异常链 ── raise ... from
# ══════════════════════════════════════════════════════
# 场景：底层抛了 ValueError，业务层想包装成 ValidationError
# 但又不想丢失"原因"信息

def parse_age(s: str) -> int:
    try:
        return int(s)
    except ValueError as e:
        raise ValidationError(f"年龄字段无效: {s!r}") from e
        #                                        ^^^^^^
        # from e 让新异常的 __cause__ 指向原异常
        # 打印 traceback 时会显示完整的"因果链"


print("\n── 异常链 ──")
try:
    parse_age("abc")
except ValidationError as e:
    print(f"  外层异常: {e}")
    print(f"  根因: {e.__cause__}")
    print(f"  根因类型: {type(e.__cause__).__name__}")


# ══════════════════════════════════════════════════════
# 4. __cause__ vs __context__
# ══════════════════════════════════════════════════════
#
# __cause__   显式：raise X from Y    → X.__cause__ = Y
# __context__ 隐式：在 except 里又抛新异常时自动设置
#
# 区别：
#   - __cause__   ── 我故意把这两个异常关联起来（声明因果）
#   - __context__ ── Python 自动记下"前一个异常是什么"
#
# 打印时：
#   from Y      → "The above exception was the direct cause of the following exception:"
#   隐式 context → "During handling of the above exception, another exception occurred:"

# 演示隐式 context
class WrapError(Exception):
    pass

try:
    try:
        int("abc")             # ValueError
    except ValueError:
        raise WrapError("包装错误")     # 没用 from，但 Python 自动记 __context__
except WrapError as e:
    print(f"\n── __context__ vs __cause__ ──")
    print(f"  __context__: {e.__context__}")     # ValueError(...)
    print(f"  __cause__:   {e.__cause__}")        # None（没 from）


# 工程实践：永远用 from 显式表达因果
#   raise NewError(...) from e
# 不要让 Python 帮你"猜" __context__


# ══════════════════════════════════════════════════════
# 5. 抑制原异常：raise ... from None
# ══════════════════════════════════════════════════════
# 有时不想让用户看到底层细节（比如不暴露内部实现）

def public_api(s: str) -> int:
    try:
        return int(s)
    except ValueError:
        raise ValidationError("invalid input") from None
        #                                       ^^^^^^^
        # 显式说"我不想让原异常出现在 traceback 里"


print("\n── from None ──")
try:
    public_api("abc")
except ValidationError as e:
    print(f"  外层异常: {e}")
    print(f"  __cause__: {e.__cause__}")    # None
    print(f"  __suppress_context__: {e.__suppress_context__}")  # True


# ══════════════════════════════════════════════════════
# 6. ExceptionGroup ── Python 3.11+
# ══════════════════════════════════════════════════════
# 一次性抛多个异常（典型场景：并发任务、批量校验）
# Python 3.11+ 内置了这个能力

def validate_user(data: dict) -> None:
    errors = []
    if "name" not in data:
        errors.append(ValidationError("缺少 name"))
    if not isinstance(data.get("age"), int):
        errors.append(ValidationError("age 必须是 int"))
    if data.get("email") and "@" not in data["email"]:
        errors.append(ValidationError("email 格式错误"))
    if errors:
        raise ExceptionGroup("用户数据校验失败", errors)


print("\n── ExceptionGroup ──")
try:
    validate_user({"age": "old", "email": "broken"})
except* ValidationError as eg:
    # except* 是新语法（Python 3.11+），专门匹配 ExceptionGroup 中的子异常
    for e in eg.exceptions:
        print(f"  - {e}")


# ══════════════════════════════════════════════════════
# 7. except* 的精髓：按类型分组处理
# ══════════════════════════════════════════════════════

class NetworkError(AppError):
    pass


def parallel_tasks():
    """假装并发跑了几个任务，混合两种异常"""
    raise ExceptionGroup(
        "并发任务失败",
        [
            ValidationError("用户 1 数据错"),
            NetworkError("用户 2 请求超时"),
            ValidationError("用户 3 数据错"),
            NetworkError("用户 4 连接失败"),
        ],
    )


print("\n── except* 分组 ──")
try:
    parallel_tasks()
except* ValidationError as eg:
    print("  数据错误:")
    for e in eg.exceptions:
        print(f"    - {e}")
except* NetworkError as eg:
    print("  网络错误:")
    for e in eg.exceptions:
        print(f"    - {e}")


# 关键区别：
#   except    ← 匹配第一个异常就停
#   except*   ← 把异常组里所有匹配的子异常一起处理
#
# 如果异常组里有匹配某 except* 也有匹配另一 except* 的，
# 两个分支都会被执行（每个只拿到自己匹配的那部分）


# ══════════════════════════════════════════════════════
# 8. 实战：HTTP 客户端的异常体系
# ══════════════════════════════════════════════════════

class APIError(AppError):
    """API 调用失败的根类"""

class APITimeoutError(APIError):
    """请求超时"""

class APIClientError(APIError):
    """4xx 错误"""
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"客户端错误 {status}: {body[:50]}")

class APIServerError(APIError):
    """5xx 错误"""
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"服务端错误 {status}: {body[:50]}")


def call_api(status: int, body: str = ""):
    """模拟一个 HTTP 客户端"""
    if status == 0:
        raise APITimeoutError("connection timed out")
    if 400 <= status < 500:
        raise APIClientError(status, body)
    if 500 <= status < 600:
        raise APIServerError(status, body)
    return "ok"


print("\n── HTTP 异常体系 ──")
for status in [200, 0, 404, 503]:
    try:
        result = call_api(status, "page not found")
    except APITimeoutError:
        print(f"  {status}: 超时，可重试")
    except APIClientError as e:
        print(f"  {status}: 业务错误（不该重试）{e.status}")
    except APIServerError as e:
        print(f"  {status}: 服务端错误（可重试）{e.status}")
    except APIError as e:
        print(f"  {status}: 其他 API 错误 {e}")
    else:
        print(f"  {status}: {result}")


# ══════════════════════════════════════════════════════
# 9. 速查
# ══════════════════════════════════════════════════════
#
# 自定义异常：
#   class AppError(Exception): ...
#   class ValidationError(AppError): ...
#   class NotFoundError(AppError): ...
#
# 带数据的异常：
#   class HTTPError(AppError):
#       def __init__(self, status, message):
#           self.status = status
#           super().__init__(f"HTTP {status}: {message}")
#
# 异常链：
#   raise NewError(...) from old_e    保留根因
#   raise NewError(...) from None     抹掉根因
#
# __cause__ vs __context__：
#   from 显式 → __cause__
#   except 中又抛 → __context__（自动）
#
# ExceptionGroup（3.11+）：
#   raise ExceptionGroup("msg", [exc1, exc2, ...])
#   except* T as eg: ...    分组捕获
#
# 工程铁律：
#   - 项目级 AppError 根基类，所有自定义异常继承它
#   - 包装底层异常时永远用 from
#   - 公开 API 不暴露细节时用 from None
#   - 并发 / 批量场景考虑 ExceptionGroup
"""
"""
