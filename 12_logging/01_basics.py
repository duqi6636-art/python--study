r"""
logging 第一层：基础
─────────────────────────────────────────
内容：
1. 为什么不该用 print
2. 五个日志级别
3. getLogger ── 拿到 logger 的标准姿势
4. basicConfig ── 一行配置
5. 异常日志：logger.exception()
6. 几个新手陷阱
"""

import logging


# ══════════════════════════════════════════════════════
# 1. 为什么不该用 print
# ══════════════════════════════════════════════════════
#
# print 的问题：
#   - 没有"级别"概念：调试信息和错误混在一起
#   - 没有时间戳、文件、行号
#   - 关不掉：一旦发布，调试 print 还在到处刷屏
#   - 不能输出到文件 / 远程
#   - 多线程下输出会乱
#
# logging 的价值：
#   - 5 个级别（DEBUG / INFO / WARNING / ERROR / CRITICAL）
#   - 自带时间、模块、行号、级别
#   - 一处配置全局生效
#   - 能输出到任意地方（文件 / 控制台 / 网络）
#   - 线程安全


# ══════════════════════════════════════════════════════
# 2. 五个日志级别
# ══════════════════════════════════════════════════════
#
# DEBUG     10   细节调试信息（生产环境关掉）
# INFO      20   关键流程节点（生产环境通常开着）
# WARNING   30   非预期但能继续（默认级别）← 标杆
# ERROR     40   出问题了，但程序还能跑
# CRITICAL  50   严重错误，程序可能要终止
#
# 默认级别是 WARNING：低于 WARNING 的不打印

# 不配置直接调用：
print("── 默认级别（WARNING）──")
logging.debug("看不到我")
logging.info("看不到我")
logging.warning("WARNING：能看到")
logging.error("ERROR：能看到")
logging.critical("CRITICAL：能看到")


# ══════════════════════════════════════════════════════
# 3. basicConfig ── 最简单的一次性配置
# ══════════════════════════════════════════════════════

# 重置之前的 root logger 配置（force=True 是 Python 3.8+）
logging.basicConfig(
    level=logging.DEBUG,                     # 接收 DEBUG 及以上
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    force=True,
)

print("\n── basicConfig 后 ──")
logging.debug("现在 DEBUG 也看得到了")
logging.info("流程开始")
logging.warning("有点不对劲")
logging.error("真的出错了")


# format 里的占位符（最常用）：
#   %(asctime)s    时间
#   %(levelname)s  级别名（DEBUG / INFO / ...）
#   %(name)s       logger 名字
#   %(message)s    消息本身
#   %(filename)s   文件名
#   %(lineno)d     行号
#   %(funcName)s   函数名
#   %(process)d    进程号
#   %(threadName)s 线程名


# ══════════════════════════════════════════════════════
# 4. getLogger ── 工程里的标准姿势
# ══════════════════════════════════════════════════════
# 永远不要直接用 logging.info() / logging.error()
# 而是先拿一个属于自己模块的 logger

logger = logging.getLogger(__name__)
# __name__ 是模块名（比如 "myapp.service.user"）
# 这样不同模块的日志能区分来源

print("\n── 模块级 logger ──")
logger.info("模块级日志，name 字段会显示模块名")
logger.warning("便于过滤和定位")


# 为什么用 __name__？
#   - 自动获得"分层名字"，符合包结构
#   - 后续可以按模块单独配置日志级别
#   - 比硬编码字符串更稳（重命名模块时不会忘改）


# ══════════════════════════════════════════════════════
# 5. 异常日志：logger.exception()
# ══════════════════════════════════════════════════════
# 在 except 块里用 exception()，自动带完整 traceback

print("\n── exception() ──")
try:
    int("xyz")
except ValueError:
    logger.exception("解析整数失败")     # ← 自动附加 traceback
    # 等同于 logger.error("...", exc_info=True)


# 三种打异常日志的写法：
#
#   logger.error(str(e))                   ❌ 丢失 traceback，没法定位
#   logger.error("出错: %s", e)            ❌ 同上
#   logger.exception("出错")              ✅ 自动带完整堆栈
#   logger.error("出错", exc_info=True)    ✅ 等价写法


# ══════════════════════════════════════════════════════
# 6. 用 % 占位符（推荐写法）
# ══════════════════════════════════════════════════════
# logger 支持"延迟格式化"：参数不会立即拼接成字符串
# 只有真的要输出时才格式化 → 性能 + 安全

user = "alice"
count = 42

# 推荐：
logger.info("用户 %s 操作了 %d 次", user, count)

# 不推荐（虽然能跑）：
logger.info(f"用户 {user} 操作了 {count} 次")
# 问题：不管日志级别多低都会先做 f-string 拼接
#       如果 user 是个昂贵的对象（比如要查数据库的对象），就白算了


# ══════════════════════════════════════════════════════
# 7. 新手陷阱：basicConfig 只生效一次
# ══════════════════════════════════════════════════════
#
# 第一次调用 basicConfig 后再调用，默认会被忽略
# 想覆盖必须 force=True（Python 3.8+）
#
# 这就是为什么本文件开头的 force=True 很重要

# 反例：
#   import some_lib    ← 这个库内部偷偷调了 basicConfig
#   logging.basicConfig(level=DEBUG)   ← 没生效，因为已经配过了
#
# 工程铁律：
#   - 自己代码里只在程序入口调一次 basicConfig
#   - 库代码永远不要调 basicConfig（这是应用的责任）


# ══════════════════════════════════════════════════════
# 8. 反例 vs 正例
# ══════════════════════════════════════════════════════
#
# ❌ 反例：
#   def login(user):
#       print(f"DEBUG: {user} 来了")     # 永远在打
#       try:
#           do_auth(user)
#       except Exception as e:
#           print(f"出错了: {e}")        # 没有 traceback
#
# ✅ 正例：
#   logger = logging.getLogger(__name__)
#
#   def login(user):
#       logger.debug("用户 %s 进入登录流程", user)
#       try:
#           do_auth(user)
#       except Exception:
#           logger.exception("登录失败 user=%s", user)


# ══════════════════════════════════════════════════════
# 9. 速查
# ══════════════════════════════════════════════════════
#
# 5 个级别（从轻到重）：
#   DEBUG / INFO / WARNING / ERROR / CRITICAL
#
# 标准入口写法（每个模块开头）：
#   logger = logging.getLogger(__name__)
#
# 应用入口配置：
#   logging.basicConfig(
#       level=logging.INFO,
#       format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
#   )
#
# 异常日志：
#   logger.exception("xxx")        # 带 traceback（最常用）
#
# 占位符 vs f-string：
#   logger.info("user=%s", user)   推荐（延迟格式化）
#   logger.info(f"user={user}")    能跑但浪费性能
#
# 工程铁律：
#   - 永远不写 print，永远用 logger
#   - 每个模块用 getLogger(__name__)
#   - basicConfig 只在程序入口写一次
#   - 库代码绝不配置 logging
#   - 异常用 logger.exception()
"""
"""
