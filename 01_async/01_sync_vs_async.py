import asyncio
import time


# 模拟一次网络请求，需要 1 秒
def fetch_sync(name: str) -> str:
    time.sleep(1)
    return f"{name}: done"


async def fetch_async(name: str) -> str:
    await asyncio.sleep(1)
    return f"{name}: done"


# ── 同步版本：串行执行，总耗时 = N × 1s ──────────────────────────
def run_sync():
    tasks = ["request-1", "request-2", "request-3"]
    start = time.perf_counter()

    results = [fetch_sync(t) for t in tasks]

    elapsed = time.perf_counter() - start
    print(f"[同步] 耗时 {elapsed:.2f}s，结果: {results}")


# ── 异步版本：并发执行，总耗时 ≈ 1s ──────────────────────────────
async def run_async():
    tasks = ["request-1", "request-2", "request-3"]
    start = time.perf_counter()

    results = await asyncio.gather(
        fetch_async(tasks[0]),
        fetch_async(tasks[1]),
        fetch_async(tasks[2]),
    )

    elapsed = time.perf_counter() - start
    print(f"[异步] 耗时 {elapsed:.2f}s，结果: {list(results)}")


if __name__ == "__main__":
    run_sync()
    asyncio.run(run_async())
