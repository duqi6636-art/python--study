import asyncio


async def slow_job(name: str, delay: float) -> str:
    print(f"{name} 开始，预计 {delay}s")
    await asyncio.sleep(delay)
    print(f"{name} 完成")
    return f"{name}: ok"


# ══════════════════════════════════════════════════════
# 1. 超时控制：asyncio.wait_for()
# ══════════════════════════════════════════════════════

async def demo_timeout():
    print("── 超时控制 ──")
    try:
        # 给协程设置最多 1.5s 的超时
        result = await asyncio.wait_for(slow_job("任务A", 3.0), timeout=1.5)
        print(result)
    except asyncio.TimeoutError:
        print("超时了！任务A 被自动取消")


# ══════════════════════════════════════════════════════
# 2. 手动取消任务：task.cancel()
# ══════════════════════════════════════════════════════

async def demo_cancel():
    print("\n── 手动取消 ──")
    task = asyncio.create_task(slow_job("任务B", 5.0))

    await asyncio.sleep(1.0)      # 等 1 秒后主动取消
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        print("任务B 被取消了")


# ══════════════════════════════════════════════════════
# 3. 协程内部响应取消：捕获 CancelledError 做清理
# ══════════════════════════════════════════════════════

async def job_with_cleanup(name: str):
    try:
        print(f"{name} 开始")
        await asyncio.sleep(10)
        print(f"{name} 完成")
    except asyncio.CancelledError:
        print(f"{name} 收到取消信号，正在清理资源...")
        # 在这里关闭文件、释放连接等
        raise   # 必须重新抛出，让事件循环知道任务已取消

async def demo_cleanup():
    print("\n── 取消时清理资源 ──")
    task = asyncio.create_task(job_with_cleanup("任务C"))
    await asyncio.sleep(1.0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("主函数：任务C 已取消")


# ══════════════════════════════════════════════════════
# 4. 多任务超时：asyncio.wait() + timeout
# ══════════════════════════════════════════════════════

async def demo_wait():
    print("\n── 多任务超时，谁完成要谁 ──")
    tasks = {
        asyncio.create_task(slow_job("快", 0.5)),
        asyncio.create_task(slow_job("慢", 3.0)),
    }

    # 等 1 秒，看看谁完成了
    done, pending = await asyncio.wait(tasks, timeout=1.0)

    print(f"完成的: {[t.result() for t in done]}")
    print(f"未完成的数量: {len(pending)}")

    # 取消剩余未完成的任务
    for t in pending:
        t.cancel()
    await asyncio.gather(*pending, return_exceptions=True)


async def main():
    await demo_timeout()
    await demo_cancel()
    await demo_cleanup()
    await demo_wait()


if __name__ == "__main__":
    asyncio.run(main())
