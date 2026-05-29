r"""
生成器第三层：yield from + send / throw / close + 协程
─────────────────────────────────────────
这一层把"生成器"升级为"双向通信"，
是 async/await 出现之前 Python 实现协程的基础。

内容：
1. yield from ── 委托给另一个生成器
2. send() ── 向生成器"喂"数据
3. throw() / close() ── 向生成器抛异常 / 关闭
4. 协程：基于生成器的"可中断函数"
5. 和 async/await 的对应关系
"""


# ══════════════════════════════════════════════════════
# 1. yield from：委托给另一个生成器
# ══════════════════════════════════════════════════════
# 把"用 for 循环转发"简化成一行

def gen_a():
    yield 1
    yield 2

def gen_b():
    yield 3
    yield 4


# 老写法：手动 for 循环转发
def chain_old():
    for x in gen_a():
        yield x
    for x in gen_b():
        yield x


# yield from：一行搞定
def chain_new():
    yield from gen_a()
    yield from gen_b()


print("── yield from 委托 ──")
print(list(chain_old()))   # [1, 2, 3, 4]
print(list(chain_new()))   # [1, 2, 3, 4]


# yield from 的真正威力：递归
def flatten(nested):
    """展平任意层嵌套的列表"""
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)        # 递归委托
        else:
            yield item


print("\n── yield from 递归 ──")
nested = [1, [2, 3, [4, [5, 6]]], 7]
print(list(flatten(nested)))   # [1, 2, 3, 4, 5, 6, 7]


# ══════════════════════════════════════════════════════
# 2. send() ── 向生成器"双向通信"
# ══════════════════════════════════════════════════════
# 之前我们只用 next()，那是单向的：生成器产值给我们
# send() 让我们能反过来"喂"值给生成器

def echo():
    """生成器：每次 yield 时接收外部 send 的值，再原样吐回去"""
    while True:
        received = yield                 # ← yield 在这里能接收 send 的值
        print(f"  生成器收到: {received!r}")
        yield f"echo: {received}"        # 第二个 yield 把回复送出


print("\n── send() 双向通信 ──")
g = echo()
next(g)                                  # 必须先启动到第一个 yield（"预激"）
print(g.send("hello"))                   # 喂入 hello，拿到 'echo: hello'
next(g)                                  # 跳到下一个接收点
print(g.send("world"))                   # 喂入 world，拿到 'echo: world'

# 关键理解：
#   yield 在右边："产出一个值给外部"     ← next() 接收
#   yield 在左边："接收外部送进来的值"   ← send() 提供
#
# 同一个 yield 点既能产出又能接收：
#   received = yield x
#   产出 x 给 next()，并用 send() 的值赋给 received


# ══════════════════════════════════════════════════════
# 3. send 的语义陷阱
# ══════════════════════════════════════════════════════
#
# 1) 第一次必须用 next() 或 send(None) "启动"生成器
#    g.send("hello") 直接调用会报错 ──
#    因为生成器还没跑到任何 yield 处，没法接收
#
# 2) send 既会"喂值进去"，也会"运行到下一个 yield"再返回那个 yield 的产出值


# ══════════════════════════════════════════════════════
# 4. throw() ── 向生成器内部抛异常
# ══════════════════════════════════════════════════════

def safe_gen():
    try:
        yield 1
        yield 2
        yield 3
    except ValueError as e:
        print(f"  捕获到: {e}")
        yield 99                          # 异常处理后还能继续 yield


print("\n── throw() ──")
g = safe_gen()
print(next(g))                            # 1
print(next(g))                            # 2
print(g.throw(ValueError("出问题了")))    # 触发异常处理，得到 99
# 生成器内部捕获了异常，没有崩溃


# ══════════════════════════════════════════════════════
# 5. close() ── 关闭生成器（释放资源）
# ══════════════════════════════════════════════════════

def with_cleanup():
    try:
        yield 1
        yield 2
        yield 3
    finally:
        print("  → 清理资源")


print("\n── close() ──")
g = with_cleanup()
print(next(g))     # 1
print(next(g))     # 2
g.close()          # 主动关闭：触发 finally
# 没有 close 时，垃圾回收时也会触发，但时机不可控
# 有重要资源时（文件、连接）建议显式 close


# ══════════════════════════════════════════════════════
# 6. yield from 的进阶能力：透传 send / throw / 返回值
# ══════════════════════════════════════════════════════
# yield from 不只是"代理 for"，它会完整代理双向通信

def child():
    x = yield 1
    print(f"  child 收到: {x}")
    y = yield 2
    print(f"  child 收到: {y}")
    return f"final({x},{y})"             # ← 生成器的 return 值


def parent():
    result = yield from child()           # ← 接收 child 的"return 值"
    print(f"  parent 拿到 child 的返回: {result}")
    yield "done"


print("\n── yield from 透传 + 返回 ──")
g = parent()
print(next(g))             # 1   ← 来自 child
print(g.send("A"))         # 2   ← child 收到 A 后产出 2
print(g.send("B"))         # done ← child 收到 B 后 return，parent 拿到返回值

# 关键：
#   - yield from 让 send / throw 直接送达内层生成器
#   - 内层生成器的 return 值被 yield from 接收（不是普通 return）
#   - 这正是 async/await 的"原型"：await 等价于 yield from 一个 future


# ══════════════════════════════════════════════════════
# 7. 用生成器实现"协程"（pre-async 时代的写法）
# ══════════════════════════════════════════════════════
# 在 async/await 出现之前，Python 用生成器模拟协程

def consumer():
    """消费者协程：等待数据，处理数据"""
    print("  消费者就绪")
    total = 0
    count = 0
    while True:
        x = yield                         # 等待数据
        if x is None:
            break
        total += x
        count += 1
        print(f"  收到 {x}，累计 {total}")
    print(f"  完成: 平均 = {total/count:.1f}")


def producer(coro, data):
    """生产者：把数据塞给消费者"""
    next(coro)                            # 预激
    for x in data:
        coro.send(x)
    try:
        coro.send(None)                   # 结束信号；消费者结束会抛 StopIteration
    except StopIteration:
        pass


print("\n── 协程：生产者-消费者 ──")
producer(consumer(), [10, 20, 30, 40])

# 这就是协程的精髓：
#   - 两个或多个"流程"协作（cooperate）
#   - 一个流程主动让出控制权（yield），另一个继续
#   - 没有线程，但有"并发的感觉"


# ══════════════════════════════════════════════════════
# 8. 协程进化史 ── 看懂下面这张图，async/await 就通了
# ══════════════════════════════════════════════════════
#
# Python 2.x：
#   def f(): yield x         生成器（单向）
#
# Python 2.5：
#   y = (yield x)            send/throw（双向通信）
#
# Python 3.3：
#   yield from sub_gen       委托与返回值
#
# Python 3.4：
#   @asyncio.coroutine       基于生成器的协程
#   def f():
#       result = yield from io_op()
#
# Python 3.5+：
#   async def f():           原生协程，专用语法
#       result = await io_op()
#
# 对应关系（理解这一组就理解了 async/await）：
#
#   async def f():           ←→  @asyncio.coroutine
#                                def f():
#
#   await x                  ←→  yield from x
#
# 也就是说：
#   async/await 是生成器协程的"语法糖 + 类型分离"。
#   底层机制完全一样：暂停一个执行流、把控制权交回事件循环。


# ══════════════════════════════════════════════════════
# 9. 实战例：用生成器搭一个"流水线"
# ══════════════════════════════════════════════════════
# 三个协程串成数据处理管道

def reader(data):
    for item in data:
        yield item


def filter_evens(source):
    for x in source:
        if x % 2 == 0:
            yield x


def squarer(source):
    for x in source:
        yield x * x


def writer(source):
    """终点消费者"""
    for x in source:
        print(f"  最终: {x}")


print("\n── 生成器管道（pull 模式）──")
pipeline = squarer(filter_evens(reader([1, 2, 3, 4, 5, 6])))
writer(pipeline)
# 偶数 [2,4,6] → 平方 [4,16,36]


# ══════════════════════════════════════════════════════
# 10. 速查 + 工程建议
# ══════════════════════════════════════════════════════
#
# yield from sub_gen         代理 sub_gen 的产出 + send/throw + 返回值
# g.send(value)              把值喂入生成器（必须先 next 启动）
# g.throw(exc)               向生成器内抛异常
# g.close()                  关闭生成器（触发 finally）
#
# 协程基础语义：
#   x = yield      产出当前控制权 + 等待下次 send
#   yield from g   委托 + 双向透传 + 接收 return 值
#
# 现代实践：
#   - 异步 I/O → 直接用 async/await，不要写生成器协程
#   - 但理解这一层的内容，让你看懂 asyncio 的底层
#
# yield from 仍然有用：
#   - 递归生成器（树展平、文件夹遍历）
#   - 把内部生成器的产出"原样转发"出去
#
# send / throw 在现代代码中很少手写：
#   - 几乎都被 async/await 取代了
#   - 但库作者（如自定义协程框架）会用到
"""
"""
