"""
第四层：上下文管理器
─────────────────────────────────────────
__enter__   →  with obj as x:  开始时触发
__exit__    →  with 块结束时触发（正常退出或异常都会触发）

为什么需要它？保证"获取资源 + 一定释放"成对出现，
就算中间抛异常也不会泄漏。
"""

import time


# ══════════════════════════════════════════════════════
# 1. 最基础的例子：计时器
# ══════════════════════════════════════════════════════

class Timer:
    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        self.start = time.perf_counter()
        print(f"[{self.name}] 开始计时")
        return self        # 这个返回值就是 `as x` 里的 x

    def __exit__(self, exc_type, exc_value, traceback):
        elapsed = time.perf_counter() - self.start
        print(f"[{self.name}] 结束，耗时 {elapsed:.3f}s")
        # 返回 False 或 None：异常继续向外抛
        # 返回 True：异常被吞掉
        return False


with Timer("计算"):
    total = sum(range(1_000_000))
    print(f"  结果 = {total}")


# ══════════════════════════════════════════════════════
# 2. 资源管理：模拟文件/连接
# ══════════════════════════════════════════════════════

class Connection:
    def __init__(self, host: str):
        self.host = host
        self.connected = False

    def __enter__(self):
        print(f"连接 {self.host}...")
        self.connected = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(f"断开 {self.host}")
        self.connected = False

    def query(self, sql: str):
        if not self.connected:
            raise RuntimeError("未连接")
        print(f"  执行: {sql}")


with Connection("db.local") as conn:
    conn.query("SELECT * FROM users")
    conn.query("SELECT * FROM orders")
# 走出 with，自动断开


# ══════════════════════════════════════════════════════
# 3. 异常处理：__exit__ 三个参数的用法
# ══════════════════════════════════════════════════════

class SafeBlock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            print("正常退出")
        else:
            print(f"捕获到异常: {exc_type.__name__}: {exc_value}")
            return True   # 吞掉异常，不再向外抛


print("─── 吞掉异常 ───")
with SafeBlock():
    raise ValueError("出问题了")
print("继续往下跑")   # 因为异常被吞了，所以这行能执行


# ══════════════════════════════════════════════════════
# 4. 用 contextlib 简化：装饰器版
# ══════════════════════════════════════════════════════

from contextlib import contextmanager


@contextmanager
def timer(name: str):
    start = time.perf_counter()
    print(f"[{name}] 开始")
    try:
        yield          # yield 之前 = __enter__
                       # yield 的值 = as 后面拿到的值（这里没有）
    finally:
        elapsed = time.perf_counter() - start
        print(f"[{name}] 结束，{elapsed:.3f}s")
                       # yield 之后 = __exit__


print("─── contextmanager 装饰器版 ───")
with timer("简版计时"):
    sum(range(500_000))


# ══════════════════════════════════════════════════════
# 5. 异步版：__aenter__ / __aexit__
# ══════════════════════════════════════════════════════
#
# 把 __enter__ 改成 async def __aenter__
# 把 __exit__  改成 async def __aexit__
# 把 with     改成 async with
#
# 完全一样的语义，只是在协程里用。

import asyncio


class AsyncConnection:
    def __init__(self, host: str):
        self.host = host

    async def __aenter__(self):
        print(f"[async] 连接 {self.host}...")
        await asyncio.sleep(0.1)   # 模拟异步握手
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        print(f"[async] 断开 {self.host}")
        await asyncio.sleep(0.1)


async def main():
    print("─── async with ───")
    async with AsyncConnection("api.example.com") as conn:
        print(f"  使用连接 {conn.host}")


asyncio.run(main())
