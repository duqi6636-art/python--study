r"""
生成器实战 05：分页 API 自动遍历
─────────────────────────────────────────
场景：
  调用一个分页 API（GitHub / 内部业务 API / 数据库查询）
  接口一次只返回 N 条数据 + 下一页的标识
  调用方想"无限拉取"或"按需拉取"，不操心分页细节

用生成器封装：
  - 调用方写 for item in fetch_all(...): 即可
  - 内部按需取下一页，不浪费请求
  - 配合 islice 能精确控制要多少条
  - 错误重试、限流都能加在生成器里

(本文件用模拟 API，不需要真的网络)
"""

import itertools
import time
from typing import Iterator


# ══════════════════════════════════════════════════════
# 模拟一个分页 API
# ══════════════════════════════════════════════════════

class FakeAPI:
    """模拟一个有 250 条数据的 API，每页最多 50 条"""

    def __init__(self):
        self._data = [{"id": i, "name": f"item_{i}"} for i in range(250)]
        self.call_count = 0     # 统计被调用次数

    def list_items(self, page: int = 1, per_page: int = 50) -> dict:
        """返回 {items: [...], next_page: int|None}"""
        self.call_count += 1
        start = (page - 1) * per_page
        end = start + per_page
        items = self._data[start:end]
        next_page = page + 1 if end < len(self._data) else None
        return {"items": items, "next_page": next_page, "page": page}


# ══════════════════════════════════════════════════════
# 1. 最常见的分页风格：page + next_page
# ══════════════════════════════════════════════════════

def fetch_all_page(api: FakeAPI, per_page: int = 50) -> Iterator[dict]:
    """按页拉取，一直到 next_page 为 None"""
    page = 1
    while page is not None:
        resp = api.list_items(page=page, per_page=per_page)
        for item in resp["items"]:
            yield item
        page = resp["next_page"]


print("── 全量拉取（page 风格）──")
api = FakeAPI()
all_items = list(fetch_all_page(api))
print(f"  共拉取 {len(all_items)} 条")
print(f"  实际调用 API 次数: {api.call_count}")    # 5 次（250 / 50）


# ══════════════════════════════════════════════════════
# 2. 按需拉取：只取前 N 条（API 调用最少化）
# ══════════════════════════════════════════════════════
# 配合 islice：只会拉取需要的页数

print("\n── 只取前 30 条 ──")
api = FakeAPI()
first_30 = list(itertools.islice(fetch_all_page(api), 30))
print(f"  取到 {len(first_30)} 条")
print(f"  API 只被调用了 {api.call_count} 次（不是全量）")
# islice 拉够就停，后面的页根本不请求


# ══════════════════════════════════════════════════════
# 3. 另一种分页风格：cursor / token 游标
# ══════════════════════════════════════════════════════

class FakeCursorAPI:
    """游标分页：返回 next_cursor，下次带上即可"""

    def __init__(self):
        self._data = [{"id": i, "name": f"item_{i}"} for i in range(120)]

    def list_items(self, cursor: str | None = None, limit: int = 30) -> dict:
        start = int(cursor) if cursor else 0
        end = start + limit
        items = self._data[start:end]
        next_cursor = str(end) if end < len(self._data) else None
        return {"items": items, "next_cursor": next_cursor}


def fetch_all_cursor(api: FakeCursorAPI, limit: int = 30) -> Iterator[dict]:
    cursor = None
    while True:
        resp = api.list_items(cursor=cursor, limit=limit)
        for item in resp["items"]:
            yield item
        cursor = resp["next_cursor"]
        if cursor is None:
            break


print("\n── 游标分页 ──")
api = FakeCursorAPI()
print(f"  共拉取 {sum(1 for _ in fetch_all_cursor(api))} 条")


# ══════════════════════════════════════════════════════
# 4. 第三种风格：offset + limit
# ══════════════════════════════════════════════════════

class FakeOffsetAPI:
    def __init__(self, total: int = 200):
        self._data = [{"id": i} for i in range(total)]

    def list_items(self, offset: int = 0, limit: int = 25) -> dict:
        return {
            "items": self._data[offset : offset + limit],
            "total": len(self._data),
        }


def fetch_all_offset(api: FakeOffsetAPI, limit: int = 25) -> Iterator[dict]:
    offset = 0
    while True:
        resp = api.list_items(offset=offset, limit=limit)
        items = resp["items"]
        if not items:
            break
        for item in items:
            yield item
        offset += len(items)
        if len(items) < limit:    # 不足一页 = 最后一页
            break


print("\n── offset 分页 ──")
api = FakeOffsetAPI(total=200)
print(f"  共拉取 {sum(1 for _ in fetch_all_offset(api))} 条")


# ══════════════════════════════════════════════════════
# 5. 给分页生成器加重试 / 限流
# ══════════════════════════════════════════════════════

def fetch_with_retry(api: FakeAPI, per_page: int = 50, max_retries: int = 3) -> Iterator[dict]:
    """带重试的分页生成器"""
    page = 1
    while page is not None:
        for attempt in range(max_retries):
            try:
                resp = api.list_items(page=page, per_page=per_page)
                for item in resp["items"]:
                    yield item
                page = resp["next_page"]
                break    # 这页成功，跳出重试循环
            except Exception as e:
                print(f"  page {page} 第 {attempt+1} 次失败: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.05)


# 简单限流：每页之间隔一段时间
def fetch_throttled(api: FakeAPI, per_page: int = 50, qps: float = 5) -> Iterator[dict]:
    """简单限流：每秒最多 qps 个请求"""
    interval = 1.0 / qps
    last_call = 0.0
    page = 1
    while page is not None:
        elapsed = time.perf_counter() - last_call
        if elapsed < interval:
            time.sleep(interval - elapsed)
        resp = api.list_items(page=page, per_page=per_page)
        last_call = time.perf_counter()
        for item in resp["items"]:
            yield item
        page = resp["next_page"]


print("\n── 限流拉取（qps=5）──")
api = FakeAPI()
start = time.perf_counter()
count = sum(1 for _ in fetch_throttled(api, qps=5))
elapsed = time.perf_counter() - start
print(f"  共 {count} 条，耗时 {elapsed:.2f}s（5 次请求至少 0.8s）")


# ══════════════════════════════════════════════════════
# 6. 工程封装：把分页统一成"拉一切"
# ══════════════════════════════════════════════════════
# 实战中常把分页生成器藏在一个 Client 类里，
# 调用方完全感知不到分页

class GitHubClientLike:
    """伪 GitHub 客户端，演示工程封装"""

    def __init__(self):
        self._api = FakeAPI()

    def iter_items(self) -> Iterator[dict]:
        """暴露给业务代码：迭代所有"""
        return fetch_all_page(self._api, per_page=50)

    def first_n(self, n: int) -> list[dict]:
        return list(itertools.islice(self.iter_items(), n))


print("\n── 工程封装 ──")
client = GitHubClientLike()

for item in itertools.islice(client.iter_items(), 5):
    print(f"  {item}")

print(f"  first_n(3): {client.first_n(3)}")


# ══════════════════════════════════════════════════════
# 7. 速查
# ══════════════════════════════════════════════════════
#
# 三种主流分页风格：
#   page  + next_page    最常见，业务系统多用
#   cursor / token       Twitter / Slack / GitHub GraphQL
#   offset + limit       SQL 风格，老 API 居多
#
# 共同套路：
#   1) 写一个 fetch_all_xxx(api, ...) 生成器
#   2) 内部 while 循环按需取下一页
#   3) yield 每个 item，调用方按 for 消费
#   4) 配合 islice 控制取多少
#   5) 重试 / 限流 / 缓存层都能塞进去
#
# 异步版：
#   把 def 改 async def，yield 改成 yield（异步生成器自动）
#   调用方用 async for item in fetch_all(...)
#
# 工程铁律：
#   - 不要返回 list[T]，返回 Iterator[T]，调用方更灵活
#   - 让分页对调用方"透明"，client.iter_xxx() 即可
#   - 永远配合 islice 给出"按需"语义
"""
"""
