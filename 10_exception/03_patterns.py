r"""
异常第三层：工程模式
─────────────────────────────────────────
内容：
1. 边界处理：哪一层接、哪一层抛
2. EAFP vs LBYL（Python 哲学）
3. 异常 → 业务异常的转换层
4. contextmanager 做"自动清理"
5. 抑制异常：contextlib.suppress
6. 顶层兜底：main 入口的 except 套路
7. 重试模式（含可恢复 vs 不可恢复区分）
"""

import contextlib
import logging
import time
import random


# ══════════════════════════════════════════════════════
# 1. 异常处理的"分层原则"
# ══════════════════════════════════════════════════════
#
# 一个常见的工程结构：
#
#   ┌──────────────────────────┐
#   │  顶层入口（main / 视图）   │  ← 这里兜底，记录日志、返回 500
#   ├──────────────────────────┤
#   │  业务层（Service）         │  ← 抛业务异常（AppError 子类）
#   ├──────────────────────────┤
#   │  数据访问层（DAO/HTTP/IO）  │  ← 把底层异常转换成业务异常
#   └──────────────────────────┘
#
# 三个原则：
#   1) 不要在低层 catch 之后只 print，要么处理、要么重抛
#   2) 跨层时把"基础设施异常"转成"业务异常"
#   3) 兜底放最外层（main / 入口），其他地方让异常自然冒泡


# ══════════════════════════════════════════════════════
# 2. EAFP vs LBYL ── Python 的哲学
# ══════════════════════════════════════════════════════
#
# LBYL: Look Before You Leap   先检查、再操作（C / Java 风格）
# EAFP: Easier to Ask Forgiveness than Permission  先做、出错再说（Python 风格）

data = {"name": "Alice"}

# LBYL 风格
def lbyl_get(d, key):
    if key in d:
        return d[key]
    return None


# EAFP 风格（Pythonic）
def eafp_get(d, key):
    try:
        return d[key]
    except KeyError:
        return None


print("── EAFP vs LBYL ──")
print(eafp_get(data, "name"))
print(eafp_get(data, "missing"))


# 为什么 Python 偏好 EAFP？
#   1) 简洁：try 块比 if/else 链短
#   2) 避免 TOCTOU 竞态条件（检查时存在，操作时已被删）
#   3) 异常路径只在出错时付代价（成功时几乎零成本）
#
# 例外：异常很常发生时（比如 50% 失败率），LBYL 反而更高效
#       异常应该是"异常情况"，不是常规控制流


# ══════════════════════════════════════════════════════
# 3. 转换层：把基础设施异常翻译成业务异常
# ══════════════════════════════════════════════════════
# 调用方不应该感知到"底层是 HTTP 还是数据库"

class UserNotFound(Exception):
    pass

class UserStorageError(Exception):
    pass


def fetch_user_from_http(user_id: int) -> dict:
    """假装一个 HTTP 调用，会抛 ConnectionError / TimeoutError 等"""
    if user_id == 1:
        return {"id": 1, "name": "Alice"}
    if user_id == 999:
        raise ConnectionError("HTTP 503")
    raise FileNotFoundError("user not in upstream")    # 模拟"找不到"


def get_user(user_id: int) -> dict:
    """业务层：把底层异常翻译成业务异常"""
    try:
        return fetch_user_from_http(user_id)
    except ConnectionError as e:
        raise UserStorageError(f"用户存储不可用") from e
    except FileNotFoundError as e:
        raise UserNotFound(f"用户 {user_id} 不存在") from e


print("\n── 异常翻译层 ──")
for uid in [1, 42, 999]:
    try:
        u = get_user(uid)
        print(f"  {uid}: {u}")
    except UserNotFound as e:
        print(f"  {uid}: 业务异常 - {e}")
    except UserStorageError as e:
        print(f"  {uid}: 基础设施异常 - {e}")


# 调用方代码非常清爽：
#   - 不用 import ConnectionError / FileNotFoundError
#   - 只 catch 自己关心的业务异常
#   - 想看"为什么"时，e.__cause__ 一直保留着原因


# ══════════════════════════════════════════════════════
# 4. contextmanager 做"自动清理"
# ══════════════════════════════════════════════════════
# 之前在装饰器章学过，这里再演示一次"异常安全"的资源管理

@contextlib.contextmanager
def db_connection(name: str):
    print(f"  打开连接 {name}")
    try:
        yield {"name": name}              # 把"连接"交给 with 块
    finally:
        print(f"  关闭连接 {name}")        # 永远会执行，即使异常


print("\n── contextmanager 异常安全 ──")
try:
    with db_connection("primary") as conn:
        print(f"  使用连接")
        raise RuntimeError("出错了")     # 即使这里炸了，连接也会关
except RuntimeError as e:
    print(f"  外层捕获: {e}")


# ══════════════════════════════════════════════════════
# 5. contextlib.suppress ── 优雅吞异常
# ══════════════════════════════════════════════════════
# 偶尔确实需要"如果失败了就当没发生"

# 反例（笨拙）：
#   try:
#       os.remove("temp.txt")
#   except FileNotFoundError:
#       pass

# 正确写法：
import os, tempfile

with tempfile.NamedTemporaryFile(delete=False) as f:
    path = f.name

print("\n── suppress 吞异常 ──")
with contextlib.suppress(FileNotFoundError):
    os.remove(path)        # 第一次成功
    os.remove(path)        # 第二次会 FileNotFoundError，但被吞了
print("  无论文件在不在，都安全走过")


# 关键：suppress 只接受具体异常类型，不要 suppress(Exception) 这样
# 不然就和 except: pass 一样糟


# ══════════════════════════════════════════════════════
# 6. 顶层兜底（main 入口）
# ══════════════════════════════════════════════════════
# 整个程序的最外层应该有个"统一异常处理"，避免崩溃 / 暴露细节

logger = logging.getLogger(__name__)


def business_logic():
    raise UserStorageError("DB 挂了")


def main():
    try:
        business_logic()
    except UserNotFound as e:
        logger.warning(f"用户不存在: {e}")
        return 404                                   # 返回业务码
    except UserStorageError as e:
        logger.error(f"存储错误: {e}", exc_info=True)
        return 500
    except Exception as e:                           # 兜底：未预期的异常
        logger.exception("未预期错误")               # exception() 自动带 traceback
        return 500
    return 0


# 顶层捕 Exception 是合理的，但要做两件事：
#   1) 记录完整 traceback（logger.exception()）
#   2) 给调用方返回有意义的状态码 / 错误响应


print("\n── 顶层兜底 ──")
status = main()
print(f"  退出状态: {status}")


# ══════════════════════════════════════════════════════
# 7. 实战：可重试 vs 不可重试
# ══════════════════════════════════════════════════════
# 重试要看异常类型 ── 业务错误重试无意义，基础设施错误才该重试

class RetryableError(Exception):
    """可重试错误（如网络抖动、超时）"""

class FatalError(Exception):
    """不可重试错误（业务参数错、权限不足）"""


def call_with_retry(func, max_retries: int = 3, base_delay: float = 0.05):
    last = None
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except RetryableError as e:
            last = e
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))    # 指数退避
                print(f"  第 {attempt} 次失败（可重试），{delay:.2f}s 后重试")
                time.sleep(delay)
        except FatalError:
            raise                                            # 不重试，直接抛
    raise last                                               # 重试用完


# 模拟一个"前两次失败、第三次成功"的接口
attempt_count = 0

def flaky_call():
    global attempt_count
    attempt_count += 1
    if attempt_count < 3:
        raise RetryableError(f"暂时不可用（{attempt_count}）")
    return "ok"


print("\n── 可重试 vs 不可重试 ──")
result = call_with_retry(flaky_call)
print(f"  最终结果: {result}")


# 关键：通过"异常类型"决定是否重试
# 业务代码只要正确分类异常，重试器就能自动判断


# ══════════════════════════════════════════════════════
# 8. logger.exception 的妙用
# ══════════════════════════════════════════════════════
# 很多人不知道，except 里直接 logger.exception() 会自动带完整 traceback
# 比 logger.error(str(e)) 强多了

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

print("\n── logger.exception ──")
try:
    int("xyz")
except ValueError:
    # logger.exception("解析失败")    # 自动加 traceback
    print("  实际工程中：logger.exception('解析失败') 会输出完整堆栈")


# ══════════════════════════════════════════════════════
# 9. 速查
# ══════════════════════════════════════════════════════
#
# 分层原则：
#   底层 → 业务层时翻译异常（raise BusinessErr from e）
#   业务层抛"业务异常"
#   顶层兜底（main / 视图）
#
# Python 哲学：
#   EAFP > LBYL（异常少见时）
#   try / except 通常比 if 检查更 Pythonic
#
# 工具：
#   contextlib.contextmanager   自动清理
#   contextlib.suppress(T)      明确吞特定异常
#   logger.exception(msg)       自动带 traceback
#
# 重试：
#   按异常类型分"可重试 / 不可重试"
#   退避策略：base * 2**(n-1) 指数退避
#   最多重试 N 次，最后还失败就向上抛
#
# 工程铁律：
#   - 不要 except: pass
#   - 不要 except Exception 后吞掉
#   - 跨层异常用 raise NewError from e
#   - 顶层兜底 + logger.exception() 是最低标准
#   - 业务异常体系比错误码字段更优雅
"""
"""
