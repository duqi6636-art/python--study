import asyncio
import time


async def fetch(name: str, delay: float) -> str:
    print(f"  [{name}] 开始")
    await asyncio.sleep(delay)
    print(f"  [{name}] 完成")
    return f"{name}: ok"


# ══════════════════════════════════════════════════════
# 问题：不加限制，100 个请求同时发出
# ══════════════════════════════════════════════════════

async def no_limit():
    print("── 无限制：10 个任务同时跑 ──")
    start = time.perf_counter()
    tasks = [fetch(f"任务{i}", 1.0) for i in range(10)]
    await asyncio.gather(*tasks)
    print(f"耗时 {time.perf_counter() - start:.2f}s\n")


# ══════════════════════════════════════════════════════
# 方案一：Semaphore —— 限制同时运行的数量
# ══════════════════════════════════════════════════════

async def demo_semaphore():
    print("── Semaphore：最多同时跑 3 个 ──")
    sem = asyncio.Semaphore(3)   # 同时最多 3 个

    async def limited_fetch(name: str):
        async with sem:          # 拿到令牌才能进入，没令牌就等
            return await fetch(name, 1.0)

    start = time.perf_counter()
    tasks = [limited_fetch(f"任务{i}") for i in range(10)]
    results = await asyncio.gather(*tasks)
    print(f"耗时 {time.perf_counter() - start:.2f}s，共 {len(results)} 个结果\n")


# ══════════════════════════════════════════════════════
# 方案二：Queue —— 生产者/消费者，固定 N 个 worker
# ══════════════════════════════════════════════════════

async def demo_queue():
    print("── Queue：3 个 worker 消费 10 个任务 ──")
    queue: asyncio.Queue = asyncio.Queue()

    # 把所有任务放入队列
    for i in range(10):
        await queue.put(f"任务{i}")

    results = []

    async def worker(worker_id: int):
        while True:
            try:
                name = queue.get_nowait()   # 取一个任务
            except asyncio.QueueEmpty:
                break                        # 队列空了，退出
            result = await fetch(f"W{worker_id}-{name}", 1.0)
            results.append(result)
            queue.task_done()

    start = time.perf_counter()
    # 启动 3 个 worker 并发消费
    await asyncio.gather(worker(1), worker(2), worker(3))
    print(f"耗时 {time.perf_counter() - start:.2f}s，共 {len(results)} 个结果\n")


# ══════════════════════════════════════════════════════
# Semaphore vs Queue 的选择
# ══════════════════════════════════════════════════════
#
#  Semaphore：任务数量已知，只需限速
#             gather 所有任务，但同时跑的不超过 N 个
#
#  Queue：任务动态产生，或需要持续处理流式数据
#         固定 N 个 worker 一直跑，队列来了就消费
#
# ══════════════════════════════════════════════════════

async def main():
    await no_limit()
    await demo_semaphore()
    await demo_queue()


if __name__ == "__main__":
    asyncio.run(main())
