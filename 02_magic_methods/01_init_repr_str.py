class Book:
    def __init__(self, title: str, author: str, price: float):
        """对象创建时自动调用，负责初始化属性"""
        self.title = title
        self.author = author
        self.price = price

    def __repr__(self) -> str:
        """给开发者看的，目标：能还原这个对象"""
        return f"Book(title={self.title!r}, author={self.author!r}, price={self.price})"

    def __str__(self) -> str:
        """给用户看的，目标：可读性"""
        return f"《{self.title}》 作者：{self.author}，售价：¥{self.price:.2f}"


# ── 演示 ─────────────────────────────────────────────

book = Book("流浪地球", "刘慈欣", 39.9)

# __repr__：在交互式终端直接输入变量名，或 repr() 时触发
print(repr(book))

# __str__：print() 时触发
print(book)

# 在容器里（list、dict）显示元素时，用的是 __repr__
library = [
    Book("三体", "刘慈欣", 59.0),
    Book("人类简史", "赫拉利", 68.0),
]
print(library)          # 列表里每个元素调用 __repr__
print(str(library[0]))  # 单独取出来 print，调用 __str__


# ── 只定义 __repr__ 不定义 __str__ 会怎样？ ──────────

class Card:
    def __init__(self, suit: str, value: str):
        self.suit = suit
        self.value = value

    def __repr__(self) -> str:
        return f"Card({self.value}{self.suit})"
    # 没有 __str__，Python 会自动用 __repr__ 代替

card = Card("♠", "A")
print(card)        # 输出 Card(A♠)，fallback 到 __repr__
print(repr(card))  # 同上


# ── 只定义 __str__ 不定义 __repr__ 会怎样？ ──────────

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"
    # 没有 __repr__，repr() 退化成默认的内存地址形式

p = Point(1.0, 2.0)
print(p)        # (1.0, 2.0)   ← 用 __str__
print(repr(p))  # <__main__.Point object at 0x...>  ← 默认
