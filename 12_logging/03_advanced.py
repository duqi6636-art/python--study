r"""
logging 第三层：进阶
─────────────────────────────────────────
内容：
1. logger 的"层级关系"（点号命名 + propagate）
2. dictConfig ── 配置文件式日志（推荐）
3. 异常追踪：exc_info / stack_info
4. 第三方库的日志静音 / 调音
5. 多模块协作的最佳实践
6. 结构化日志（JSON 格式）
"""

import logging
import logging.config
import json


# ══════════════════════════════════════════════════════
# 1. logger 的层级关系
# ══════════════════════════════════════════════════════
# logger 的名字用点号分层，自动形成"祖先链"
#
#   root
#     └─ "myapp"
#           └─ "myapp.api"
#                 └─ "myapp.api.user"
#
# 调用 logger.info() 时：
#   先经过自己的 Handler
#   再"冒泡"给父级 logger（如果 propagate=True）
#   一路冒到 root

# 演示
logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s", force=True)

parent = logging.getLogger("myapp")
child = logging.getLogger("myapp.api")
grandchild = logging.getLogger("myapp.api.user")

print("── 层级关系 ──")
grandchild.info("从最深的子 logger 发出")
# 输出 1 次：经过 grandchild，但 grandchild / child / parent 都没自己的 Handler，
# 一路冒泡到 root，root 有 basicConfig 安装的 Handler，输出


# 加上自己的 Handler 看一下"冒泡"现象
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("    >>> %(name)s: %(message)s"))
child.addHandler(ch)         # 给 child 单独配 Handler

print("\n── 冒泡现象 ──")
grandchild.info("从孙子发出")
# 这条会被打印 2 次：
#   1) child 的 Handler 处理（因为 grandchild 冒泡到 child）
#   2) root 的 Handler 处理（因为 grandchild → child → root 继续冒泡）


# 阻止冒泡：propagate = False
child.propagate = False
print("\n── 关掉冒泡 ──")
grandchild.info("再来一次")
# 这次只输出 1 次：在 child 处停了


# 工程意义：
#   - 应用顶层 logger（如 "myapp"）配 Handler
#   - 子 logger（"myapp.api"）默认让日志冒泡上来
#   - 单个子模块想特殊处理（如关掉某个噪音模块）时再单独配


# ══════════════════════════════════════════════════════
# 2. dictConfig ── 推荐的工程配置方式
# ══════════════════════════════════════════════════════
# 用一个字典声明全部配置（formatters + handlers + loggers）
# 比 addHandler / setLevel 一堆调用清晰得多

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    # 格式器
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d] %(message)s",
        },
    },

    # 输出器
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
        },
        # 文件 handler 演示用，注释掉以免在 demo 时产生文件
        # "file": {
        #     "class": "logging.handlers.RotatingFileHandler",
        #     "filename": "app.log",
        #     "maxBytes": 10_000_000,
        #     "backupCount": 5,
        #     "level": "DEBUG",
        #     "formatter": "detailed",
        # },
    },

    # logger 们
    "loggers": {
        "myapp2": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "myapp2.noisy": {                    # 子 logger 想单独调高级别
            "level": "WARNING",
        },
    },

    # root 兜底
    "root": {
        "level": "WARNING",
        "handlers": ["console"],
    },
}

logging.config.dictConfig(LOG_CONFIG)

print("\n── dictConfig ──")
logging.getLogger("myapp2").info("应用日志")
logging.getLogger("myapp2.noisy").info("看不到（noisy 级别 WARNING）")
logging.getLogger("myapp2.noisy").warning("看得到")


# 实战中这个字典通常放在配置文件里：
#   - settings.py / config.py
#   - YAML / JSON 文件
# 应用启动时 logging.config.dictConfig(load_config())


# ══════════════════════════════════════════════════════
# 3. 异常追踪：exc_info 和 stack_info
# ══════════════════════════════════════════════════════

logger = logging.getLogger("myapp2")

print("\n── exc_info ──")
try:
    int("xyz")
except ValueError:
    logger.error("解析失败", exc_info=True)
    # 等同于 logger.exception("解析失败")


print("\n── stack_info（无异常时也想看堆栈）──")
def caller():
    logger.warning("这条日志我想看到调用者", stack_info=True)


def outer():
    caller()


outer()
# stack_info=True 即使没异常也会附上调用栈
# 调试"谁调的我"非常好用


# ══════════════════════════════════════════════════════
# 4. 第三方库的日志静音
# ══════════════════════════════════════════════════════
# 常见痛点：requests / urllib3 / boto3 这些库 DEBUG 一开就刷屏
# 解决：单独把它们的 logger 调到 WARNING+

# 比如：
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# 在 dictConfig 里也可以：
#   "loggers": {
#       "urllib3": {"level": "WARNING"},
#       "botocore": {"level": "WARNING"},
#   }


# ══════════════════════════════════════════════════════
# 5. 给日志添加"上下文"：extra 参数
# ══════════════════════════════════════════════════════
# 想在每条日志里都带上 request_id / user_id 等上下文

ctx_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] [req=%(request_id)s] %(message)s"
)
ctx_handler = logging.StreamHandler()
ctx_handler.setFormatter(ctx_formatter)

ctx_logger = logging.getLogger("ctx_demo")
ctx_logger.addHandler(ctx_handler)
ctx_logger.setLevel(logging.INFO)
ctx_logger.propagate = False

print("\n── extra 上下文 ──")
ctx_logger.info("用户登录", extra={"request_id": "req-001"})
ctx_logger.info("订单创建", extra={"request_id": "req-002"})


# 注意：用 extra 的字段必须出现在 format 里
# 没传 extra 时 logger 会报错，所以一般配合"Adapter"或 Filter 给所有日志补上


class RequestIdFilter(logging.Filter):
    """没传 request_id 时给个默认值"""
    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


ctx_handler.addFilter(RequestIdFilter())
print("\n── 加了 Filter 之后没传 extra 也不报错 ──")
ctx_logger.info("没传 request_id 也能跑")


# ══════════════════════════════════════════════════════
# 6. 结构化日志（JSON 格式）
# ══════════════════════════════════════════════════════
# 文本日志难解析，云原生场景倾向 JSON 行（一行一个 JSON）
# 自己写个 Formatter 即可

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # 保留 extra 字段
        for key, val in record.__dict__.items():
            if key not in ("args", "asctime", "created", "exc_info", "exc_text",
                           "filename", "funcName", "levelname", "levelno", "lineno",
                           "module", "msecs", "msg", "name", "pathname", "process",
                           "processName", "relativeCreated", "stack_info", "thread",
                           "threadName", "taskName", "message"):
                payload[key] = val
        return json.dumps(payload, ensure_ascii=False)


json_logger = logging.getLogger("json_demo")
json_handler = logging.StreamHandler()
json_handler.setFormatter(JsonFormatter())
json_logger.addHandler(json_handler)
json_logger.setLevel(logging.INFO)
json_logger.propagate = False

print("\n── 结构化 JSON 日志 ──")
json_logger.info("用户登录", extra={"user_id": 42, "ip": "10.0.0.1"})
json_logger.warning("请求过慢", extra={"latency_ms": 1230})


# 真实工程：直接用 python-json-logger / structlog / loguru 等库
# 不用每次自己写 JsonFormatter


# ══════════════════════════════════════════════════════
# 7. 第三方库速览
# ══════════════════════════════════════════════════════
#
# 标准 logging（够用）：
#   - 内置，无依赖
#   - 配置稍啰嗦但功能完整
#
# loguru：
#   - 一行 logger.add("...") 搞定一切
#   - 异常追踪带变量值（强）
#   - 适合脚本 / 中小型项目
#   pip install loguru
#
# structlog：
#   - 真正的结构化日志
#   - 函数式风格，"事件 + 字段"心智模型
#   - 大厂日志系统首选
#   pip install structlog
#
# python-json-logger：
#   - 给 stdlib logging 加个 JSON Formatter
#   - 不改代码风格，最小成本上 JSON
#   pip install python-json-logger


# ══════════════════════════════════════════════════════
# 8. 推荐的工程模板（应用入口）
# ══════════════════════════════════════════════════════
#
# # log_config.py
# from logging.config import dictConfig
#
# def setup_logging(level: str = "INFO"):
#     dictConfig({
#         "version": 1,
#         "disable_existing_loggers": False,
#         "formatters": {
#             "default": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
#         },
#         "handlers": {
#             "console": {
#                 "class": "logging.StreamHandler",
#                 "formatter": "default",
#             },
#             "file": {
#                 "class": "logging.handlers.RotatingFileHandler",
#                 "filename": "logs/app.log",
#                 "maxBytes": 10_000_000,
#                 "backupCount": 5,
#                 "formatter": "default",
#             },
#         },
#         "root": {"level": level, "handlers": ["console", "file"]},
#         "loggers": {
#             "urllib3": {"level": "WARNING"},
#             "botocore": {"level": "WARNING"},
#         },
#     })
#
# # main.py
# from log_config import setup_logging
# setup_logging("INFO")
#
# # 其他模块只需：
# import logging
# logger = logging.getLogger(__name__)
# logger.info("...")


# ══════════════════════════════════════════════════════
# 9. 速查
# ══════════════════════════════════════════════════════
#
# logger 层级：
#   名字带点号自动分层（"a.b.c"）
#   propagate=True 默认会冒泡到父
#
# dictConfig：
#   {version, formatters, handlers, loggers, root, disable_existing_loggers}
#   是工程里的标准配置方式
#
# 异常追踪：
#   logger.exception("...")          带 traceback
#   logger.error("...", exc_info=True)   等价
#   logger.info("...", stack_info=True)  普通日志带堆栈
#
# 上下文：
#   extra={"request_id": "..."}      单条日志加字段
#   Filter 给所有日志补默认上下文
#
# 第三方库静音：
#   logging.getLogger("urllib3").setLevel(WARNING)
#
# 结构化日志：
#   自己写 JsonFormatter，或上 loguru / structlog
#
# 工程铁律：
#   - 顶层 dictConfig 一次配置全应用
#   - 子模块只 getLogger(__name__)，不配
#   - 第三方库要单独"调音"防刷屏
#   - 云原生 / 容器化 → 结构化 JSON 日志
"""
"""
