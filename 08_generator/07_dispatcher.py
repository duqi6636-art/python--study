r"""
生成器实战 07：分发器（一对多分发）
─────────────────────────────────────────
场景：
  一个数据源，多个消费者要拿到"完整副本"
  例子：
    - 一份请求日志同时给：实时监控、归档存储、告警检测
    - 一组 Kafka 消息同时给多个处理流程
    - 单一爬虫流同时写文件 + 写数据库 + 推送

为什么不直接 list() 后给每个消费者？
  - 数据可能很大（不能一次性加载）
  - 数据可能无限（流式输入）
  - 想保持惰性 / 支持背压

解法：
  1) itertools.tee     标准库自带，多个消费者步调相近时最佳
  2) 广播器（broadcast）  自己造轮子，能处理订阅 / 取消
  3) push 模式 dispatcher  生产者主动向多个消费者推
"""

import itertools
from typing import Iterator, Callable, Any


# ══════════════════════════════════════════════════════
# 1. 用 itertools.tee 做最简单的"复制"
# ══════════════════════════════════════════════════════
# tee(it, n) 把一个迭代器复制成 n 个独立的迭代器
# 最适合"几个消费者并行消费、步调差不多"的场景

def source():
    for i in range(5):
        yield {"id": i, "value": i * 10}


print("── itertools.tee ──")
src = source()
a, b, c = itertools.tee(src, 3)

# 三个消费者各自完整消费一遍
print(f"  消费者 A: {list(a)}")
print(f"  消费者 B: {list(b)}")
print(f"  消费者 C: {list(c)}")


# tee 的注意点：
#   - tee 之后别再用原始 src（会乱套）
#   - 内部用 deque 缓冲，消费速度差越大、缓冲越多
#   - 一个消费者消费完、另一个还没开始，整段数据会被全部缓存


# ══════════════════════════════════════════════════════
# 2. 用 zip 做"并行步进消费"
# ══════════════════════════════════════════════════════
# 当几个消费者都是 map 风格时，zip 比 tee 更省内存

def writer_a(stream: Iterator[dict]) -> Iterator[str]:
    for item in stream:
        yield f"A: 写入 {item['id']}"


def writer_b(stream: Iterator[dict]) -> Iterator[str]:
    for item in stream:
        yield f"B: 转发 {item['id']}"


print("\n── zip 并行消费 ──")
src = source()
a, b = itertools.tee(src, 2)
for ra, rb in zip(writer_a(a), writer_b(b)):
    print(f"  {ra} | {rb}")


# ══════════════════════════════════════════════════════
# 3. push 模式 dispatcher：生产者主动推
# ══════════════════════════════════════════════════════
# 上面是 pull 模式（消费者自己拉数据）
# push 模式：生产者循环源头，把每个元素"广播"给所有订阅者

class Dispatcher:
    """简单分发器：注册回调，源头来一条就推一条"""

    def __init__(self):
        self._subscribers: list[Callable[[Any], None]] = []

    def subscribe(self, callback: Callable[[Any], None]):
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Any], None]):
        self._subscribers.remove(callback)

    def push(self, item: Any):
        for cb in self._subscribers:
            cb(item)

    def feed(self, source_iter: Iterator):
        """把整个生成器源喂给所有订阅者"""
        for item in source_iter:
            self.push(item)


# 三个消费者
def to_console(item):
    print(f"  [控制台] {item}")


def to_log(items_buf: list):
    return lambda x: items_buf.append(x)


def alert_on_high(threshold: int):
    return lambda x: print(f"  [告警] 高值 {x['value']}") if x["value"] > threshold else None


print("\n── push 模式分发 ──")
dispatcher = Dispatcher()
log_buffer: list = []

dispatcher.subscribe(to_console)
dispatcher.subscribe(to_log(log_buffer))
dispatcher.subscribe(alert_on_high(threshold=25))

dispatcher.feed(source())

print(f"  日志缓存: {[item['id'] for item in log_buffer]}")


# ══════════════════════════════════════════════════════
# 4. 进阶：把 push 模式包成生成器（pull + 广播）
# ══════════════════════════════════════════════════════
# 让分发器自己也是生成器，可以串入更大的管道

def broadcast(source_iter: Iterator, *consumers: Callable[[Any], None]) -> Iterator:
    """每来一个元素，先推给所有 consumer，再 yield 给上游"""
    for item in source_iter:
        for cb in consumers:
            cb(item)
        yield item


print("\n── broadcast：边广播边 yield ──")
log_buf: list = []
audit_buf: list = []

stream = broadcast(
    source(),
    lambda x: log_buf.append(("log", x["id"])),
    lambda x: audit_buf.append(("audit", x["id"])),
)

# 主消费者照常拉数据
ids = [item["id"] for item in stream]

print(f"  主流: {ids}")
print(f"  log 副本: {log_buf}")
print(f"  audit 副本: {audit_buf}")


# ══════════════════════════════════════════════════════
# 5. 异步分发器（思路演示）
# ══════════════════════════════════════════════════════
# 实战中分发器常常异步：每个消费者可能慢
# 用 asyncio.Queue 给每个订阅者一个独立队列

import asyncio


class AsyncBroadcaster:
    """每个订阅者一个队列；生产者只负责往所有队列塞"""

    def __init__(self, queue_size: int = 100):
        self._queues: list[asyncio.Queue] = []
        self._queue_size = queue_size

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=self._queue_size)
        self._queues.append(q)
        return q

    async def feed(self, source_iter):
        for item in source_iter:
            for q in self._queues:
                await q.put(item)
        # 结束信号
        for q in self._queues:
            await q.put(None)


async def consumer_async(name: str, q: asyncio.Queue):
    while True:
        item = await q.get()
        if item is None:
            break
        print(f"  [{name}] {item}")


async def demo_async():
    broadcaster = AsyncBroadcaster()
    q1 = broadcaster.subscribe()
    q2 = broadcaster.subscribe()

    # 三件事并发：两个消费者 + 一个生产者
    await asyncio.gather(
        consumer_async("A", q1),
        consumer_async("B", q2),
        broadcaster.feed(source()),
    )


print("\n── 异步广播 ──")
asyncio.run(demo_async())


# ══════════════════════════════════════════════════════
# 6. 选型速查
# ══════════════════════════════════════════════════════
#
# 几个消费者步调相同 + 数据量小 → itertools.tee
# 几个消费者都是 map 风格      → tee + zip
# 同步 push（边遍历边通知）    → 自写 broadcast / Dispatcher
# 异步 push（消费者速度差大）  → asyncio.Queue 一对多
#
# 边界：
#   - 消费者速度差很大 → tee 内部缓冲会爆，应该用队列
#   - 数据无限 → 任何一个消费者卡住就会拖累整体（要加超时 / 丢弃策略）
#   - 真生产环境的 fan-out → Kafka / Redis Streams 比自己写靠谱
#
# 工程铁律：
#   - 简单场景 tee 就够了，别过度设计
#   - 涉及网络 / 持久化的多消费者 → 上消息队列
#   - 自写分发器只在"内存内、单进程"场景用
"""
"""
