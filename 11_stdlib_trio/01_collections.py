r"""
标准库 01：collections
─────────────────────────────────────────
内容：
1. Counter ── 计数神器
2. defaultdict ── 自动初始化的 dict
3. deque ── 双端队列（高效 O(1) 头尾操作）
4. namedtuple ── 轻量"只读对象"
5. OrderedDict ── 有顺序的字典（现代 dict 已经有序，主要看历史）
6. ChainMap ── 多层级配置查找
"""

from collections import Counter, defaultdict, deque, namedtuple, OrderedDict, ChainMap


# ══════════════════════════════════════════════════════
# 1. Counter ── 一行代码搞定"频次统计"
# ══════════════════════════════════════════════════════

text = "the quick brown fox jumps over the lazy dog the"

# 词频统计
counter = Counter(text.split())
print("── Counter ──")
print(counter)
# Counter({'the': 3, 'quick': 1, ...})

# 取 top N
print(counter.most_common(3))     # [('the', 3), ('quick', 1), ('brown', 1)]

# 字符频次
print(Counter("mississippi"))      # Counter({'i': 4, 's': 4, 'p': 2, 'm': 1})


# Counter 的算术运算 ── 集合操作
a = Counter(a=3, b=1, c=2)
b = Counter(a=1, b=2, c=2, d=5)

print("\n── Counter 算术 ──")
print(a + b)         # 加法：Counter({'d': 5, 'a': 4, 'c': 4, 'b': 3})
print(a - b)         # 减法（不会出负数）：Counter({'a': 2})
print(a & b)         # 交集（取较小值）：Counter({'a': 1, 'b': 1, 'c': 2})
print(a | b)         # 并集（取较大值）：Counter({'d': 5, 'a': 3, 'c': 2, 'b': 2})


# 实战：找两段文本的共同高频词
text1 = "python is great python is fast"
text2 = "python is amazing python is concise"
common = Counter(text1.split()) & Counter(text2.split())
print(common.most_common(2))    # [('python', 2), ('is', 2)]


# ══════════════════════════════════════════════════════
# 2. defaultdict ── 不用每次写 if key in dict
# ══════════════════════════════════════════════════════

# 反例：用普通 dict 做分组
data = [("fruit", "apple"), ("fruit", "banana"), ("drink", "tea")]

groups_bad = {}
for category, item in data:
    if category not in groups_bad:
        groups_bad[category] = []
    groups_bad[category].append(item)

# 用 defaultdict
groups = defaultdict(list)
for category, item in data:
    groups[category].append(item)        # ← 第一次访问 key 会自动初始化为 list()

print("\n── defaultdict ──")
print(dict(groups))


# 几种常见的工厂：
counter_dict = defaultdict(int)          # 默认 0，常用做计数
for word in text.split():
    counter_dict[word] += 1

set_dict = defaultdict(set)              # 默认空 set，常用做"多对多关系"
set_dict["a"].add(1)
set_dict["a"].add(2)
set_dict["b"].add(3)
print(dict(set_dict))


# 嵌套 defaultdict（树形结构）
tree = defaultdict(lambda: defaultdict(list))
tree["fruits"]["red"].append("apple")
tree["fruits"]["yellow"].append("banana")
tree["drinks"]["hot"].append("tea")
print(dict(tree))


# defaultdict vs dict.setdefault：
#   defaultdict 一次配置、永久生效，适合"整个流程都按这套规则"
#   setdefault 灵活，一行只用一次时方便


# ══════════════════════════════════════════════════════
# 3. deque ── 高效双端队列
# ══════════════════════════════════════════════════════
# list 的 append/pop 末尾 O(1)，但开头 O(n)
# deque 两端都是 O(1)

dq = deque([1, 2, 3])
dq.append(4)              # 右加
dq.appendleft(0)          # 左加
print("\n── deque ──")
print(dq)                 # deque([0, 1, 2, 3, 4])

dq.pop()                  # 右出
dq.popleft()              # 左出
print(dq)                 # deque([1, 2, 3])


# 经典用例：固定容量的"最近 N 个"
recent = deque(maxlen=3)
for i in range(10):
    recent.append(i)
print(recent)             # deque([7, 8, 9])，永远只保留最后 3 个


# 经典用例：滑动窗口
def sliding_max(nums, k):
    """每个窗口的最大值（简化版用法演示，非最优算法）"""
    window = deque(maxlen=k)
    result = []
    for x in nums:
        window.append(x)
        if len(window) == k:
            result.append(max(window))
    return result


print(sliding_max([1, 3, 2, 5, 4, 6], 3))   # [3, 5, 5, 6]


# rotate 旋转
dq = deque([1, 2, 3, 4, 5])
dq.rotate(2)              # 向右旋转 2 个
print(dq)                 # deque([4, 5, 1, 2, 3])
dq.rotate(-2)             # 向左转回来
print(dq)


# ══════════════════════════════════════════════════════
# 4. namedtuple ── 轻量"具名元组"
# ══════════════════════════════════════════════════════
# 比裸 tuple 多了"字段名"，比 dataclass 更轻

Point = namedtuple("Point", ["x", "y"])

p = Point(3, 4)
print("\n── namedtuple ──")
print(p)                  # Point(x=3, y=4)
print(p.x, p.y)           # 3 4
print(p[0], p[1])         # 兼容下标访问

# 解包
x, y = p
print(x, y)


# 现代实践：
#   - 简单只读对象 → namedtuple 也行
#   - 想要类型注解 → typing.NamedTuple
#   - 复杂业务对象 → dataclass

from typing import NamedTuple

class Point2(NamedTuple):                 # 现代写法，带类型注解
    x: float
    y: float

    def distance_to_origin(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5


p2 = Point2(3.0, 4.0)
print(p2.distance_to_origin())   # 5.0


# ══════════════════════════════════════════════════════
# 5. OrderedDict ── 历史包袱
# ══════════════════════════════════════════════════════
# Python 3.7+ 的普通 dict 已经保持插入顺序
# OrderedDict 还在，因为它有几个普通 dict 没有的方法

od = OrderedDict([("a", 1), ("b", 2), ("c", 3)])
od.move_to_end("a")              # 把 'a' 移到最末
print("\n── OrderedDict ──")
print(od)                        # OrderedDict([('b', 2), ('c', 3), ('a', 1)])

od.move_to_end("a", last=False)  # 移到最前
print(od)


# 现代代码 99% 直接用普通 dict，OrderedDict 仅在需要 move_to_end 之类时用


# ══════════════════════════════════════════════════════
# 6. ChainMap ── 多层级配置
# ══════════════════════════════════════════════════════
# 把多个 dict "叠"成一个：查找时从前往后依次找

defaults = {"theme": "light", "lang": "en", "debug": False}
user_config = {"theme": "dark"}
runtime = {"debug": True}

config = ChainMap(runtime, user_config, defaults)
#                  ↑           ↑          ↑
#                优先级最高   中等      兜底

print("\n── ChainMap ──")
print(config["theme"])     # 'dark'      ← user_config
print(config["lang"])      # 'en'         ← defaults
print(config["debug"])     # True         ← runtime


# 修改只影响最前面的 dict
config["new_key"] = "added"
print(runtime)             # {'debug': True, 'new_key': 'added'}

# ChainMap 不会真的合并，所以原 dict 改了也实时生效
defaults["new_default"] = "x"
print(config["new_default"])    # 'x'


# 实战场景：
#   - 应用配置：runtime > 用户配置 > 默认配置
#   - 命令行参数 > 环境变量 > 配置文件 > 内置默认


# ══════════════════════════════════════════════════════
# 7. 速查
# ══════════════════════════════════════════════════════
#
# Counter(iterable)              频次统计 + 数学运算
# Counter.most_common(N)         前 N 高频
#
# defaultdict(factory)           自动初始化 dict
#   factory 常用：list / set / int / lambda: defaultdict(...)
#
# deque(iterable, maxlen=N)      双端队列
#   appendleft / popleft / rotate
#   maxlen 自动限长 ── 滑动窗口神器
#
# namedtuple("X", ["f1", "f2"])  轻量具名元组（老）
# class X(NamedTuple): ...       带类型注解（新，推荐）
#
# OrderedDict.move_to_end(k)     把 k 移到末尾（普通 dict 没这方法）
#
# ChainMap(d1, d2, d3)           多层级查找：d1 优先
#
# 工程铁律：
#   - 计数 / 频次 → Counter
#   - 分组 / 多对多 → defaultdict
#   - 双端队列 / 固定窗口 → deque
#   - 简单只读对象 → NamedTuple；带方法的 → dataclass
#   - 配置叠加 → ChainMap
"""
"""
