"""
第三层：让你的类支持 [] 取值 和 for 循环
─────────────────────────────────────────
__getitem__   →  obj[key] 触发
__len__       →  len(obj) 触发
__iter__      →  for x in obj 触发
__next__      →  iter 对象每次取下一个时触发
"""


# ══════════════════════════════════════════════════════
# 1. __getitem__ + __len__ : 让对象像列表一样取值
# ══════════════════════════════════════════════════════

class Playlist:
    def __init__(self, songs: list[str]):
        self._songs = songs

    def __len__(self) -> int:
        return len(self._songs)

    def __getitem__(self, index):
        return self._songs[index]


playlist = Playlist(["song A", "song B", "song C", "song D"])

print(len(playlist))      # 4         ← 触发 __len__
print(playlist[0])        # song A    ← 触发 __getitem__
print(playlist[-1])       # song D    ← 负索引也支持
print(playlist[1:3])      # ['song B', 'song C']  ← 切片也支持

# 神奇的地方：只定义了 __getitem__，竟然可以 for 循环！
print("─── for 循环 ───")
for song in playlist:
    print(song)
# 原理：Python 找不到 __iter__ 时，会退化使用 __getitem__
#       从 0 开始一直取，直到抛出 IndexError 停止


# ══════════════════════════════════════════════════════
# 2. __iter__ : 标准的迭代器协议
# ══════════════════════════════════════════════════════

class Countdown:
    """从 n 倒数到 1"""
    def __init__(self, start: int):
        self.start = start

    def __iter__(self):
        # 用 yield 是最简单的写法，Python 会自动构造迭代器
        n = self.start
        while n > 0:
            yield n
            n -= 1


print("─── 倒数 ───")
for x in Countdown(5):
    print(x, end=" ")    # 5 4 3 2 1
print()


# ══════════════════════════════════════════════════════
# 3. __iter__ + __next__ : 完整的迭代器协议（手动实现）
# ══════════════════════════════════════════════════════

class Fibonacci:
    """无限斐波那契数列，按需取值"""
    def __init__(self, limit: int):
        self.limit = limit
        self.a, self.b = 0, 1
        self.count = 0

    def __iter__(self):
        return self    # 自己就是迭代器

    def __next__(self):
        if self.count >= self.limit:
            raise StopIteration  # 告诉 for 循环：结束了
        self.a, self.b = self.b, self.a + self.b
        self.count += 1
        return self.a


print("─── 斐波那契前 8 项 ───")
for x in Fibonacci(8):
    print(x, end=" ")    # 1 1 2 3 5 8 13 21
print()


# ══════════════════════════════════════════════════════
# 4. __getitem__ 进阶：自定义 key（不只是 int）
# ══════════════════════════════════════════════════════

class PhoneBook:
    def __init__(self):
        self._data = {"Alice": "123", "Bob": "456"}

    def __getitem__(self, name: str) -> str:
        return self._data[name]

    def __setitem__(self, name: str, phone: str):
        self._data[name] = phone

    def __contains__(self, name: str) -> bool:
        # 让 in 操作生效
        return name in self._data


pb = PhoneBook()
print("─── 电话簿 ───")
print(pb["Alice"])         # 123
pb["Charlie"] = "789"      # 触发 __setitem__
print(pb["Charlie"])       # 789
print("Bob" in pb)         # True   ← 触发 __contains__
print("David" in pb)       # False
