r"""
生成器实战 06：数据处理管道（Pipeline）
─────────────────────────────────────────
管道思想：
  把"读取 → 清洗 → 转换 → 聚合"拆成多个独立阶段，
  每个阶段都是一个生成器函数，互不知道前后是谁。

核心好处：
  - 每个阶段单一职责，可独立测试
  - 任意阶段都能 swap 替换或叠加
  - 整条链惰性执行，永远只在内存里放"一个元素"
  - 加新阶段不用改老代码（只要接口对上就行）

本文件：
  1. 经典 pull 模式（消费方拉数据）
  2. 数据流的多阶段处理
  3. 把"管道阶段"做成可复用组件
  4. 通用工具：map / filter / take / batch
"""

from typing import Iterator, Callable, Any, TypeVar
import itertools


T = TypeVar("T")
U = TypeVar("U")


# ══════════════════════════════════════════════════════
# 1. 最简单的 pull 管道
# ══════════════════════════════════════════════════════
# 数据流向：source → stage1 → stage2 → consumer
# 每个阶段都是 Iterator[T] → Iterator[U]

def source():
    """数据源：产生原始数据"""
    for i in range(1, 11):
        yield i


def double(stream: Iterator[int]) -> Iterator[int]:
    for x in stream:
        yield x * 2


def only_even(stream: Iterator[int]) -> Iterator[int]:
    for x in stream:
        if x % 2 == 0:
            yield x


def add_one(stream: Iterator[int]) -> Iterator[int]:
    for x in stream:
        yield x + 1


# 串成管道
print("── 简单 pull 管道 ──")
pipeline = add_one(only_even(double(source())))
print(list(pipeline))
# 1..10 → 双 → 偶数过滤 → +1


# ══════════════════════════════════════════════════════
# 2. 通用阶段工具：map / filter
# ══════════════════════════════════════════════════════
# 与其每次都写一个 def，不如做成通用工具

def pipe_map(func: Callable[[T], U]) -> Callable[[Iterator[T]], Iterator[U]]:
    """生成一个 map 阶段"""
    def stage(stream: Iterator[T]) -> Iterator[U]:
        for x in stream:
            yield func(x)
    return stage


def pipe_filter(pred: Callable[[T], bool]) -> Callable[[Iterator[T]], Iterator[T]]:
    """生成一个 filter 阶段"""
    def stage(stream: Iterator[T]) -> Iterator[T]:
        for x in stream:
            if pred(x):
                yield x
    return stage


# 用上面的工具重新组装
print("\n── 通用工具拼管道 ──")
pipeline = pipe_map(lambda x: x + 1)(
    pipe_filter(lambda x: x % 2 == 0)(
        pipe_map(lambda x: x * 2)(source())
    )
)
print(list(pipeline))


# ══════════════════════════════════════════════════════
# 3. 让链式调用更顺手：写一个 Pipeline 类
# ══════════════════════════════════════════════════════

class Pipeline:
    """让管道写起来像 .map().filter().take()"""

    def __init__(self, source: Iterator):
        self._stream = source

    def map(self, func: Callable):
        self._stream = (func(x) for x in self._stream)
        return self                                    # 返回自己以便链式

    def filter(self, pred: Callable):
        self._stream = (x for x in self._stream if pred(x))
        return self

    def take(self, n: int):
        self._stream = itertools.islice(self._stream, n)
        return self

    def batch(self, size: int):
        stream = self._stream                # 先把原 stream 捕获到局部变量
        def gen():
            it = iter(stream)                # 闭包用局部变量，不会被后面的赋值污染
            while batch := list(itertools.islice(it, size)):
                yield batch
        self._stream = gen()
        return self

    def __iter__(self):
        return iter(self._stream)


print("\n── 链式 Pipeline ──")
result = list(
    Pipeline(range(20))
    .map(lambda x: x * x)
    .filter(lambda x: x % 2 == 0)
    .take(5)
)
print(result)
# [0, 4, 16, 36, 64]   前 5 个偶数平方


# 链式 + batch（分批输出）
print("\n── batch 分批 ──")
batches = list(
    Pipeline(range(13))
    .map(lambda x: x * 10)
    .batch(5)
)
for b in batches:
    print(f"  {b}")


# ══════════════════════════════════════════════════════
# 4. 实战：日志分析管道
# ══════════════════════════════════════════════════════
# 把流式日志处理拆成清晰的阶段

import re

def fake_log_source():
    yield "[2026-05-25 10:00:01] INFO  user=alice action=login ok"
    yield "[2026-05-25 10:00:05] ERROR user=bob action=pay reason=timeout"
    yield "[2026-05-25 10:00:08] INFO  user=alice action=view ok"
    yield "[2026-05-25 10:00:11] ERROR user=carol action=pay reason=invalid_card"
    yield "[2026-05-25 10:00:13] WARN  user=bob action=retry"
    yield "[2026-05-25 10:00:15] ERROR user=bob action=pay reason=timeout"


LOG_RE = re.compile(
    r"\[(?P<time>[^\]]+)\]\s+"
    r"(?P<level>\w+)\s+"
    r"user=(?P<user>\w+)\s+"
    r"action=(?P<action>\w+)"
    r"(?:\s+reason=(?P<reason>\w+))?"
)


def parse(line: str) -> dict | None:
    m = LOG_RE.match(line)
    return m.groupdict() if m else None


print("\n── 日志分析管道 ──")
errors_by_user: dict[str, int] = {}

# 管道：源 → 解析 → 过滤 ERROR → 提取用户 → 计数
for entry in (
    Pipeline(fake_log_source())
    .map(parse)
    .filter(lambda x: x is not None)
    .filter(lambda x: x["level"] == "ERROR")
    .map(lambda x: x["user"])
):
    errors_by_user[entry] = errors_by_user.get(entry, 0) + 1

print(f"  各用户的错误数: {errors_by_user}")


# ══════════════════════════════════════════════════════
# 5. 把"管道"看成数据契约
# ══════════════════════════════════════════════════════
#
# 每个阶段的接口：
#   def stage(stream: Iterator[T]) -> Iterator[U]
#
# 这样设计的好处：
#   - 任意 N 个阶段串起来都合法
#   - 每个阶段都能单测（喂个 list、断言输出）
#   - 阶段之间只通过"流"通信，无共享状态
#   - 可以分发到多线程/多进程（每个阶段一个 worker）


# ══════════════════════════════════════════════════════
# 6. 工程进阶：阶段间加缓冲（避免阻塞）
# ══════════════════════════════════════════════════════
# 如果某个阶段慢，可以用线程池让它在后台跑
# 这里只给思路（实战常用 prefetch_generator 库）

def prefetch(stream: Iterator[T], buffer_size: int = 4) -> Iterator[T]:
    """伪代码思路：起一个后台线程预读"""
    # 真实实现要用 queue.Queue + threading.Thread
    # 这里只是演示接口
    for x in stream:
        yield x


# ══════════════════════════════════════════════════════
# 7. 速查 + 工程建议
# ══════════════════════════════════════════════════════
#
# 管道阶段的标准签名：
#   def stage(stream: Iterator[T]) -> Iterator[U]
#
# 三种串接风格：
#   函数嵌套     stage_c(stage_b(stage_a(source)))      简单
#   通用工具     pipe_map(f)(pipe_filter(g)(source))    可复用
#   链式 .       Pipeline(source).map().filter()        最易读
#
# 何时拆阶段：
#   - 当一个 for 循环里有 ≥ 2 个职责（解析 + 过滤 + 转换）
#   - 同样的"清洗逻辑"会在多个地方用
#   - 单元测试想覆盖每个步骤
#
# 工程铁律：
#   - 阶段不要持有外部状态（保持纯函数）
#   - 输入输出永远是 Iterator
#   - 尽量短小（每个 stage 不超过 20 行）
#   - 配合类型注解 Iterator[T] 让 IDE 帮你检查
"""
"""
