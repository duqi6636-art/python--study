import asyncio


# ══════════════════════════════════════════════════════
# 1. 最基本的用法：定义和调用一个协程
# ══════════════════════════════════════════════════════

async def say_hello():
    print("开始")
    await asyncio.sleep(1)   # 挂起 1 秒
    print("结束")

# asyncio.run() 是所有异步程序的入口
# asyncio.run(say_hello())






# ══════════════════════════════════════════════════════
# 2. await 只能在 async def 内部使用
# ══════════════════════════════════════════════════════

async def inner():
    await asyncio.sleep(0.5)
    return 42

async def outer():
    result = await inner()   # await 一个协程，拿到它的返回值
    print(f"inner 返回了: {result}")

# asyncio.run(inner())
# asyncio.run(outer())


# ══════════════════════════════════════════════════════
# 3. await 可以等哪些东西？
# ══════════════════════════════════════════════════════

# ① 协程（最常用）
async def coro():
    return "我是协程"

# ② asyncio.Task（由 create_task 创建）
async def demo_task():
    task = asyncio.create_task(coro())   # 立即放入事件循环开始跑
    result = await task                  # 等它完成拿结果
    print(result)

# ③ asyncio 内置的可等待对象：sleep / gather / wait 等
async def demo_builtins():
    await asyncio.sleep(1)
    results = await asyncio.gather(coro(), coro())
    print(results)

# 总结：能被 await 的对象叫做 Awaitable，满足以下任意一种：
#   - async def 定义的协程函数调用后返回的对象
#   - asyncio.Task
#   - 实现了 __await__ 的对象


# ══════════════════════════════════════════════════════
# 4. 协程对象 vs 调用结果：最常见的新手陷阱
# ══════════════════════════════════════════════════════

async def trap():
    x = inner()        # ❌ 忘写 await，x 是协程对象，代码没有执行
    y = await inner()  # ✅ y 是 42

    print(type(x))     # <class 'coroutine'>
    print(y)           # 42
    x.close()          # 手动关闭未执行的协程，避免 RuntimeWarning

# asyncio.run(trap())


# ══════════════════════════════════════════════════════
# 5. gather vs create_task：两种并发方式
# ══════════════════════════════════════════════════════

async def job(name: str, delay: float):
    print(f"{name} 开始")
    await asyncio.sleep(delay)
    print(f"{name} 结束")
    return name

async def demo_gather():
    # gather：把多个协程打包，同时跑，等全部完成
    results = await asyncio.gather(
        job("A", 1.0),
        job("B", 0.5),
        job("C", 1.5),
    )
    print(f"gather 结果（保持原顺序）: {results}")

async def demo_create_task():
    # create_task：立即启动，可以在其他代码跑完后再 await
    task_a = asyncio.create_task(job("A", 1.0))
    task_b = asyncio.create_task(job("B", 0.5))

    print("任务已提交，我先做点别的...")
    await asyncio.sleep(0.1)

    result_a = await task_a  # 这时 A 可能已经跑了 0.9s 了
    result_b = await task_b
    print(f"结果: {result_a}, {result_b}")


# ══════════════════════════════════════════════════════
# 运行所有示例
# ══════════════════════════════════════════════════════

async def main():
    print("── 示例1：基础 ──")
    await say_hello()

    print("\n── 示例2：await 协程拿返回值 ──")
    await outer()

    print("\n── 示例3：新手陷阱 ──")
    await trap()

    print("\n── 示例4：gather 并发 ──")
    await demo_gather()

    print("\n── 示例5：create_task 并发 ──")
    await demo_create_task()


if __name__ == "__main__":
    # asyncio.run(main())
    print("hello world")
