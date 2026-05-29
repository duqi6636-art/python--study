r"""
logging 第二层：Handler + Formatter
─────────────────────────────────────────
内容：
1. logging 的核心架构：Logger → Handler → Formatter
2. 控制台输出 + 文件输出
3. 多 Handler：同一条日志同时输出到多个地方
4. Formatter：自定义日志格式
5. 文件轮转（RotatingFileHandler / TimedRotatingFileHandler）
6. Filter：精细过滤
"""

import logging
import logging.handlers
import tempfile
from pathlib import Path


# ══════════════════════════════════════════════════════
# 1. logging 的三层结构
# ══════════════════════════════════════════════════════
#
#   Logger        ── 你写代码时调用它（logger.info, logger.error）
#                    职责：决定"这条日志值不值得处理"（看级别）
#
#   Handler       ── 决定"日志去哪"（控制台 / 文件 / 网络 / ...）
#                    一个 Logger 可以挂多个 Handler
#
#   Formatter     ── 决定"日志长什么样"（时间格式、字段顺序）
#                    每个 Handler 可以有自己的 Formatter
#
# 一条日志的旅程：
#   logger.info("hello")
#       ↓
#   Logger 检查级别（够格往下传吗）
#       ↓
#   依次交给所有挂在它上面的 Handler
#       ↓
#   每个 Handler 用自己的 Formatter 格式化后输出


# ══════════════════════════════════════════════════════
# 2. 手动构造一个最小可用的 logger
# ══════════════════════════════════════════════════════
# 不用 basicConfig，自己拼三层

logger = logging.getLogger("my_app")
logger.setLevel(logging.DEBUG)         # logger 自身的级别
logger.propagate = False               # 不向 root 冒泡（避免重复输出）

# 创建 Handler：输出到控制台
console = logging.StreamHandler()
console.setLevel(logging.INFO)         # Handler 自己也有级别（独立于 logger）

# 创建 Formatter
formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
console.setFormatter(formatter)

# 把 Handler 挂到 Logger
logger.addHandler(console)

print("── 手动构造 logger ──")
logger.debug("debug 消息")     # 不输出（Handler 级别是 INFO）
logger.info("info 消息")
logger.warning("warning 消息")


# ══════════════════════════════════════════════════════
# 3. 多 Handler：同时输出到控制台 + 文件
# ══════════════════════════════════════════════════════

# 用临时目录演示，避免污染项目
log_dir = Path(tempfile.mkdtemp())
log_file = log_dir / "app.log"

logger2 = logging.getLogger("multi_handler")
logger2.setLevel(logging.DEBUG)
logger2.propagate = False

# Handler 1：控制台只看 WARNING+
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch.setFormatter(logging.Formatter("[控制台] %(levelname)s: %(message)s"))

# Handler 2：文件记录全部
fh = logging.FileHandler(log_file, encoding="utf-8")
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d] %(message)s"
))

logger2.addHandler(ch)
logger2.addHandler(fh)

print("\n── 多 Handler ──")
logger2.debug("DEBUG 只进文件")
logger2.info("INFO 只进文件")
logger2.warning("WARNING 文件 + 控制台")
logger2.error("ERROR 文件 + 控制台")

# 看文件里到底写了什么
print(f"\n  日志文件内容（{log_file}）：")
print(log_file.read_text(encoding="utf-8"))


# 关键观察：
#   同一条 logger.info()，触发了 1 个 Logger + 2 个 Handler
#   控制台 Handler 把 INFO 拒了（自己级别 WARNING）
#   文件 Handler 收到 INFO（自己级别 DEBUG）
#
# 工程意义：
#   - 控制台 = 给开发者看的简洁视图（WARN+ 即可）
#   - 文件 = 全量审计 / 排查问题用（DEBUG 全部留下）


# ══════════════════════════════════════════════════════
# 4. 级别的"双层过滤"
# ══════════════════════════════════════════════════════
# 一条日志要被打印，必须**同时**满足：
#   1) Logger 级别 ≤ 日志级别（先过 Logger）
#   2) Handler 级别 ≤ 日志级别（再过 Handler）
#
# 两者最严格的那个生效

# 例子：
#   Logger.level = INFO
#   Handler.level = DEBUG
#   logger.debug(...) → ❌ 在 Logger 这一关就被拒
#
#   Logger.level = DEBUG
#   Handler.level = WARNING
#   logger.info(...) → ✅ 过 Logger，但 ❌ Handler 拒
#
# 实战做法：
#   - Logger 设最宽（DEBUG），Handler 自己控制
#   - 这样换 Handler 时不用改 Logger


# ══════════════════════════════════════════════════════
# 5. 文件轮转：RotatingFileHandler
# ══════════════════════════════════════════════════════
# 按"文件大小"切分：到了 maxBytes 就切，最多保留 backupCount 个

logger3 = logging.getLogger("rotation_demo")
logger3.setLevel(logging.DEBUG)
logger3.propagate = False

rotation_file = log_dir / "rotate.log"
rh = logging.handlers.RotatingFileHandler(
    rotation_file,
    maxBytes=200,           # 每个文件最大 200 字节（演示用，实战常用 10MB）
    backupCount=3,          # 保留 3 个旧文件：rotate.log.1 / .2 / .3
    encoding="utf-8",
)
rh.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
logger3.addHandler(rh)

print("\n── RotatingFileHandler ──")
for i in range(20):
    logger3.info(f"消息 #{i:02d} 内容内容内容")

# 看产生了哪些文件
print(f"  生成的文件：")
for f in sorted(log_dir.glob("rotate.log*")):
    print(f"    {f.name}: {f.stat().st_size} 字节")


# ══════════════════════════════════════════════════════
# 6. 时间轮转：TimedRotatingFileHandler
# ══════════════════════════════════════════════════════
# 按"时间"切分（每天 / 每小时一个新文件）

logger4 = logging.getLogger("time_rotation")
logger4.setLevel(logging.INFO)
logger4.propagate = False

time_rotation = log_dir / "daily.log"
th = logging.handlers.TimedRotatingFileHandler(
    time_rotation,
    when="midnight",        # 每天午夜切
    backupCount=7,          # 保留 7 天
    encoding="utf-8",
)
# when 可选值：
#   'S'  秒
#   'M'  分钟
#   'H'  小时
#   'D'  天
#   'W0'-'W6' 一周中某天（周一到周日）
#   'midnight' 每天 0 点（最常用）

th.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
logger4.addHandler(th)
logger4.info("应用启动")

print(f"\n  时间轮转文件: {time_rotation.name}（每天午夜会自动切分）")


# ══════════════════════════════════════════════════════
# 7. Formatter 进阶：用 %()s 风格 + style 参数
# ══════════════════════════════════════════════════════

# 默认是 % 风格
fmt_percent = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

# 也支持 {} 风格（更现代，少见）
fmt_brace = logging.Formatter(
    "{asctime} [{levelname}] {message}",
    style="{",
)

# 用 $ 风格（罕见）
# fmt_dollar = logging.Formatter("$asctime ...", style="$")


# ══════════════════════════════════════════════════════
# 8. Filter：精细过滤
# ══════════════════════════════════════════════════════
# 比级别更精细的"要不要打印"判断

class NoSpammyFilter(logging.Filter):
    """过滤掉包含 'heartbeat' 关键字的日志"""
    def filter(self, record: logging.LogRecord) -> bool:
        return "heartbeat" not in record.getMessage()


logger5 = logging.getLogger("with_filter")
logger5.setLevel(logging.DEBUG)
logger5.propagate = False

ch5 = logging.StreamHandler()
ch5.setFormatter(logging.Formatter("[filter demo] %(message)s"))
ch5.addFilter(NoSpammyFilter())            # ← 把 Filter 挂到 Handler 上
logger5.addHandler(ch5)

print("\n── Filter 过滤 ──")
logger5.info("用户登录")              # 输出
logger5.info("发送 heartbeat 包")     # 被过滤
logger5.info("订单创建")              # 输出
logger5.info("收到 heartbeat 响应")   # 被过滤


# Filter 也能加在 Logger 上，区别：
#   挂 Logger 上 → 影响所有 Handler
#   挂 Handler 上 → 只影响这一个 Handler


# ══════════════════════════════════════════════════════
# 9. propagate ── 防止重复输出
# ══════════════════════════════════════════════════════
# 一个常见坑：日志被打印了两次！
#
# 原因：你给自己的 logger 配了 Handler，
#       但默认 logger.propagate = True，
#       日志会"冒泡"到 root logger，
#       而 root logger 也有 Handler（来自 basicConfig）
#       → 同一条日志被两个 Handler 处理
#
# 解决：要么不用 basicConfig，要么 logger.propagate = False
#
# 工程实践：自己配的 logger 通常都 propagate = False


# ══════════════════════════════════════════════════════
# 10. 速查
# ══════════════════════════════════════════════════════
#
# 三层结构：
#   Logger      你的代码 + 模块名
#   Handler     去哪：Stream / File / Rotating / 等
#   Formatter   长啥样：%(asctime)s, %(levelname)s, ...
#
# 经典套路（应用启动时）：
#   logger = logging.getLogger("my_app")
#   logger.setLevel(logging.DEBUG)
#   logger.propagate = False
#
#   ch = logging.StreamHandler()
#   ch.setLevel(logging.INFO)
#   ch.setFormatter(logging.Formatter("..."))
#   logger.addHandler(ch)
#
#   fh = RotatingFileHandler("app.log", maxBytes=10*1024*1024, backupCount=5)
#   fh.setLevel(logging.DEBUG)
#   logger.addHandler(fh)
#
# 常用 Handler：
#   StreamHandler              控制台（默认 stderr）
#   FileHandler                单文件
#   RotatingFileHandler        按大小轮转
#   TimedRotatingFileHandler   按时间轮转
#   SysLogHandler              syslog
#   SMTPHandler                邮件（慎用）
#   QueueHandler               配 QueueListener，多进程安全
#
# 工程铁律：
#   - 控制台只看 WARN+，文件留全量
#   - 文件用 Rotating，避免日志撑爆磁盘
#   - 应用 logger 永远 propagate=False
#   - basicConfig 配 root，自定义 logger 自己配 Handler
"""
"""
