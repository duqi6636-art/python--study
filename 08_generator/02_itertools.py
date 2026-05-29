r"""
生成器第二层：itertools 工具箱
─────────────────────────────────────────
itertools 是 Python 标准库自带的"生成器工具集"，
用 C 实现，又快又省内存。

按用途分四组：
1. 无限迭代器：count / cycle / repeat
2. 序列加工：chain / islice / takewhile / dropwhile / filterfalse / compress
3. 分组与累加：accumulate / groupby
4. 组合学：product / permutations / combinations
"""

import itertools


# ══════════════════════════════════════════════════════
# 1. 无限迭代器：count / cycle / repeat
# ══════════════════════════════════════════════════════

# count(start=0, step=1) ── 从 start 开始按 step 递增
print("── count ──")
for i in itertools.count(start=10, step=2):
    if i > 20:
        break
    print(i, end=" ")     # 10 12 14 16 18 20
print()


# cycle(iterable) ── 无限循环序列
print("\n── cycle ──")
counter = 0
for color in itertools.cycle(["red", "green", "blue"]):
    print(color, end=" ")
    counter += 1
    if counter >= 7:
        break
# red green blue red green blue red
print()


# repeat(value, times=None) ── 重复同一个值
print("\n── repeat ──")
print(list(itertools.repeat("X", 5)))   # ['X', 'X', 'X', 'X', 'X']

# 配合 map 做批量操作
nums = [1, 2, 3, 4, 5]
print(list(map(pow, nums, itertools.repeat(2))))   # 每个都平方
# [1, 4, 9, 16, 25]


# ══════════════════════════════════════════════════════
# 2. 序列加工
# ══════════════════════════════════════════════════════

# chain ── 把多个序列串成一个
print("\n── chain ──")
print(list(itertools.chain([1, 2], [3, 4], [5])))
# [1, 2, 3, 4, 5]

# chain.from_iterable ── 展平嵌套序列
nested = [[1, 2], [3, 4], [5, 6]]
print(list(itertools.chain.from_iterable(nested)))
# [1, 2, 3, 4, 5, 6]


# islice(iterable, start, stop, step) ── 像切片，但能切生成器
print("\n── islice ──")
nums = itertools.count()                          # 无限序列
print(list(itertools.islice(nums, 5)))            # [0,1,2,3,4]   前 5 个
print(list(itertools.islice(itertools.count(), 10, 15)))  # [10,11,12,13,14] 第 10~14
print(list(itertools.islice(range(20), 0, 20, 3))) # [0,3,6,9,12,15,18]
# 注意：islice 只能切非负索引，不能像 list[-3:]


# takewhile / dropwhile ── 按条件"截断"序列
print("\n── takewhile / dropwhile ──")
nums = [1, 3, 5, 8, 2, 4, 9]
print(list(itertools.takewhile(lambda x: x < 7, nums)))  # [1,3,5]   遇到 8 就停
print(list(itertools.dropwhile(lambda x: x < 7, nums)))  # [8,2,4,9] 跳过开头不满足的
# 关键：一旦条件改变就停（takewhile）或不再丢（dropwhile）
#       不会"全过滤"，那是 filter 的事


# filterfalse ── 反向过滤（保留不满足条件的）
print("\n── filterfalse ──")
print(list(filter(lambda x: x % 2 == 0, range(10))))             # 偶数 [0,2,4,6,8]
print(list(itertools.filterfalse(lambda x: x % 2 == 0, range(10))))  # 奇数 [1,3,5,7,9]


# compress ── 用一个 bool 序列做"掩码"过滤
print("\n── compress ──")
data    = ["a", "b", "c", "d", "e"]
mask    = [1, 0, 1, 1, 0]
print(list(itertools.compress(data, mask)))    # ['a', 'c', 'd']


# tee ── 把一个生成器复制成 N 个独立的生成器
print("\n── tee ──")
g = (x * x for x in range(5))
g1, g2 = itertools.tee(g, 2)
print(list(g1))    # [0, 1, 4, 9, 16]
print(list(g2))    # [0, 1, 4, 9, 16]   ← 独立消费
# 注意：tee 后不要再用原始的 g（会乱套）


# ══════════════════════════════════════════════════════
# 3. 分组与累加
# ══════════════════════════════════════════════════════

# accumulate ── 累加（默认）/ 累乘 / 自定义二元运算
print("\n── accumulate ──")
nums = [1, 2, 3, 4, 5]
print(list(itertools.accumulate(nums)))                       # 默认累加 [1,3,6,10,15]
print(list(itertools.accumulate(nums, initial=100)))          # 带初值 [100,101,103,106,110,115]

import operator
print(list(itertools.accumulate(nums, operator.mul)))         # 累乘 [1,2,6,24,120]
print(list(itertools.accumulate(nums, max)))                  # 累计最大值 [1,2,3,4,5]


# groupby ── 把"连续相同"的元素分组（不是 SQL 那种分组！）
print("\n── groupby ──")
data = [
    ("Alice", "fruit"),
    ("Alice", "fruit"),
    ("Alice", "drink"),
    ("Bob",   "fruit"),
    ("Bob",   "fruit"),
]

# 用 lambda 指定按"什么字段"分组
for key, group in itertools.groupby(data, key=lambda x: x[0]):
    print(f"  {key}: {list(group)}")
# Alice: 3 条
# Bob:   2 条

# 关键陷阱：groupby 只看相邻！数据没排序时会把同 key 的拆开
unsorted = [("a", 1), ("b", 2), ("a", 3)]   # 'a' 出现两次但不连续
for key, group in itertools.groupby(unsorted, key=lambda x: x[0]):
    print(f"  {key}: {list(group)}")
# a: [(a,1)]   ← 只抓到第一段
# b: [(b,2)]
# a: [(a,3)]   ← 第二段被分开了

# 解决：先 sort，再 groupby
print("  ── 排序后再 groupby ──")
sorted_data = sorted(unsorted, key=lambda x: x[0])
for key, group in itertools.groupby(sorted_data, key=lambda x: x[0]):
    print(f"  {key}: {list(group)}")


# ══════════════════════════════════════════════════════
# 4. 组合学：product / permutations / combinations
# ══════════════════════════════════════════════════════

# product ── 笛卡尔积（所有"组合"，有顺序、可重复）
print("\n── product 笛卡尔积 ──")
sizes = ["S", "M", "L"]
colors = ["red", "blue"]
for combo in itertools.product(sizes, colors):
    print(f"  {combo}")
# (S,red) (S,blue) (M,red) (M,blue) (L,red) (L,blue)

# product(repeat=n) ── 自身和自身做 n 次笛卡尔积
print(list(itertools.product([0, 1], repeat=3)))
# [(0,0,0), (0,0,1), (0,1,0), ..., (1,1,1)]   3 位二进制


# permutations ── 排列（顺序敏感、不重复元素）
print("\n── permutations 排列 ──")
print(list(itertools.permutations("ABC")))
# [(A,B,C), (A,C,B), (B,A,C), (B,C,A), (C,A,B), (C,B,A)]

# permutations(seq, r) ── 从 seq 中取 r 个排列
print(list(itertools.permutations("ABC", 2)))
# [(A,B), (A,C), (B,A), (B,C), (C,A), (C,B)]


# combinations ── 组合（顺序无关、不重复）
print("\n── combinations 组合 ──")
print(list(itertools.combinations("ABC", 2)))
# [(A,B), (A,C), (B,C)]   ← 没有 (B,A) 这种重复

# combinations_with_replacement ── 允许重复元素
print(list(itertools.combinations_with_replacement("ABC", 2)))
# [(A,A), (A,B), (A,C), (B,B), (B,C), (C,C)]


# ══════════════════════════════════════════════════════
# 5. 区分 product / permutations / combinations
# ══════════════════════════════════════════════════════
#
# 假设有 [A, B, C]，取 2 个：
#
#   product:                AA AB AC BA BB BC CA CB CC   (9)  顺序敏感、可重复
#   permutations:           AB AC    BA    BC    CA CB   (6)  顺序敏感、不重复
#   combinations:           AB AC          BC            (3)  顺序无关、不重复
#   combinations_with_repl: AA AB AC    BB BC       CC   (6)  顺序无关、可重复
#
# 记忆方法：
#   product → 笛卡尔积（重复 + 有序）
#   permutations → 排队，谁站前面有差别
#   combinations → 组队，3 人组里 ABC = CBA
#   _with_replacement → "可重抽"


# ══════════════════════════════════════════════════════
# 6. 实战例 1：分页处理大序列
# ══════════════════════════════════════════════════════
def chunked(iterable, size):
    """把可迭代对象按 size 分成一块块"""
    it = iter(iterable)
    while batch := list(itertools.islice(it, size)):
        yield batch


print("\n── 分页 ──")
for batch in chunked(range(10), size=3):
    print(f"  batch: {batch}")
# [0,1,2] [3,4,5] [6,7,8] [9]


# ══════════════════════════════════════════════════════
# 7. 实战例 2：滑动窗口（不用 itertools 也行，但很经典）
# ══════════════════════════════════════════════════════
def sliding_window(iterable, n):
    """按窗口大小 n 滑动"""
    it = iter(iterable)
    window = tuple(itertools.islice(it, n))
    if len(window) == n:
        yield window
    for x in it:
        window = window[1:] + (x,)
        yield window


print("\n── 滑动窗口 ──")
for w in sliding_window([1, 2, 3, 4, 5], 3):
    print(f"  {w}")
# (1,2,3) (2,3,4) (3,4,5)


# ══════════════════════════════════════════════════════
# 8. 实战例 3：用 groupby 做"游程编码"
# ══════════════════════════════════════════════════════
def run_length_encode(data: str):
    """把 'aaabbcaaa' 压缩成 [('a',3), ('b',2), ('c',1), ('a',3)]"""
    return [(ch, sum(1 for _ in group)) for ch, group in itertools.groupby(data)]


print("\n── 游程编码 ──")
print(run_length_encode("aaabbcaaa"))
# [('a',3), ('b',2), ('c',1), ('a',3)]


# ══════════════════════════════════════════════════════
# 9. 速查
# ══════════════════════════════════════════════════════
#
# 无限迭代：
#   count(start, step)        从 start 起每次 +step
#   cycle(seq)                无限循环
#   repeat(val, n)            重复 val
#
# 序列加工：
#   chain(*iters)             串成一个
#   chain.from_iterable(it)   展平嵌套
#   islice(it, start, stop)   切片（能切生成器）
#   takewhile(pred, it)       条件成立时取
#   dropwhile(pred, it)       条件成立时丢
#   filterfalse(pred, it)     反向过滤
#   compress(data, mask)      用 bool 掩码过滤
#   tee(it, n)                复制成 n 个独立生成器
#
# 分组累加：
#   accumulate(it, func)      累计运算
#   groupby(it, key)          相邻分组（先排序！）
#
# 组合学：
#   product(*its, repeat=N)   笛卡尔积
#   permutations(it, r)       排列
#   combinations(it, r)       组合
#   combinations_with_repl    可重复组合
#
# 工程铁律：
#   - 任何"循环里反复构造列表"的地方，先想想 itertools
#   - groupby 之前一定要 sorted（除非你要的就是"连续段"）
#   - islice 是切生成器的唯一姿势（生成器不支持 [::])
"""
"""
