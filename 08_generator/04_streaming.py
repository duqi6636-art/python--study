r"""
生成器实战 04：流式处理大文件 / 大数据集
─────────────────────────────────────────
核心思想：
  把数据当成"流"，一次只在内存里放一小段，
  通过生成器把"读取 → 解析 → 过滤 → 聚合"串起来。

实战目标：
  - 100GB 的日志文件也能用几十 MB 内存处理完
  - 网络流式响应（chunked encoding）按块处理
  - 大批量数据库查询用迭代游标，不一次性 load 进内存
"""

import os
import json
import tempfile
from typing import Iterator


# ══════════════════════════════════════════════════════
# 准备：先生成一个"假大文件"用来演示
# ══════════════════════════════════════════════════════

def make_sample_log(path: str, lines: int = 10_000):
    """造一份 N 行的日志样本"""
    levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    with open(path, "w", encoding="utf-8") as f:
        for i in range(lines):
            level = levels[i % 4]
            f.write(f"[2026-05-25 10:{i % 60:02d}:{i % 60:02d}] {level} request id={i} status={200 if i%7 else 500}\n")


# ══════════════════════════════════════════════════════
# 1. 文件对象本身就是行生成器
# ══════════════════════════════════════════════════════

def read_lines(path: str) -> Iterator[str]:
    """按行读取，每次只在内存里放一行"""
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n")


# ══════════════════════════════════════════════════════
# 2. 用生成器做"过滤层"
# ══════════════════════════════════════════════════════

def only_errors(lines: Iterator[str]) -> Iterator[str]:
    for line in lines:
        if "ERROR" in line:
            yield line


def only_status_500(lines: Iterator[str]) -> Iterator[str]:
    for line in lines:
        if "status=500" in line:
            yield line


# ══════════════════════════════════════════════════════
# 3. 用生成器做"解析层"
# ══════════════════════════════════════════════════════

import re

LOG_RE = re.compile(r"\[(?P<time>[^\]]+)\]\s+(?P<level>\w+)\s+(.*)")

def parse_lines(lines: Iterator[str]) -> Iterator[dict]:
    for line in lines:
        m = LOG_RE.match(line)
        if m:
            yield m.groupdict()


# ══════════════════════════════════════════════════════
# 4. 流式处理大文件 ── 主流程
# ══════════════════════════════════════════════════════

def main_log_pipeline():
    # 创建临时大文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        log_path = f.name
    make_sample_log(log_path, lines=10_000)
    file_size = os.path.getsize(log_path) / 1024
    print(f"  日志文件大小: {file_size:.1f} KB")

    # 串成管道：读 → 过滤 → 解析 → 计数
    lines  = read_lines(log_path)
    errors = only_errors(lines)
    parsed = parse_lines(errors)

    count = 0
    for entry in parsed:
        count += 1
        if count <= 3:                     # 只打印前 3 条
            print(f"  样例: {entry}")

    print(f"  处理完成，共 {count} 条 ERROR 日志")

    os.unlink(log_path)


print("── 流式日志处理 ──")
main_log_pipeline()


# ══════════════════════════════════════════════════════
# 5. 二进制文件按"块"读 ── 大文件 / 网络流的标准模式
# ══════════════════════════════════════════════════════

def read_chunks(path: str, chunk_size: int = 8192) -> Iterator[bytes]:
    """按固定字节数读取二进制文件"""
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk


def file_md5(path: str) -> str:
    """流式计算 MD5：100GB 文件也能算"""
    import hashlib
    h = hashlib.md5()
    for chunk in read_chunks(path, 65536):
        h.update(chunk)
    return h.hexdigest()


# 测试
with tempfile.NamedTemporaryFile(delete=False) as f:
    f.write(b"hello world" * 1000)
    test_path = f.name

print("\n── 流式 MD5 ──")
print(f"  MD5: {file_md5(test_path)}")
os.unlink(test_path)


# ══════════════════════════════════════════════════════
# 6. JSONL（JSON Lines）流式读取
# ══════════════════════════════════════════════════════
# JSONL 是大数据领域很常见的格式：每行一个独立 JSON 对象
# 100GB 的 JSONL 文件用流式读取毫无压力

def read_jsonl(path: str) -> Iterator[dict]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


# 演示：造一个 JSONL 文件然后流式处理
with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
    for i in range(1000):
        f.write(json.dumps({"id": i, "name": f"user_{i}", "score": i * 7 % 100}) + "\n")
    jsonl_path = f.name

print("\n── JSONL 流式处理 ──")
high_score_users = (u for u in read_jsonl(jsonl_path) if u["score"] >= 90)
print(f"  高分用户: {sum(1 for _ in high_score_users)} 个")

os.unlink(jsonl_path)


# ══════════════════════════════════════════════════════
# 7. CSV 流式读取（用 csv.DictReader）
# ══════════════════════════════════════════════════════
import csv

def read_csv(path: str) -> Iterator[dict]:
    """csv.DictReader 本身就是迭代器"""
    with open(path, encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f)


# 演示
with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "name", "age"])
    writer.writeheader()
    for i in range(500):
        writer.writerow({"id": i, "name": f"u{i}", "age": 20 + i % 50})
    csv_path = f.name

print("\n── CSV 流式处理 ──")
adults = (row for row in read_csv(csv_path) if int(row["age"]) >= 30)
sample = next(adults)
print(f"  第一条成人记录: {sample}")
print(f"  剩余成人记录: {sum(1 for _ in adults)} 条")

os.unlink(csv_path)


# ══════════════════════════════════════════════════════
# 8. "尾巴流"：tail -f 风格（持续读新行）
# ══════════════════════════════════════════════════════
# 生成器很适合"无限输入流"，比如监控日志增长

def follow(path: str, max_lines: int | None = None):
    """模拟 tail -f：从文件末尾开始，等待新行
       生产环境会配合 inotify / 轮询，这里给个简化版思路
    """
    import time
    with open(path, encoding="utf-8") as f:
        f.seek(0, 2)                       # 跳到文件末尾
        count = 0
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line.rstrip("\n")
            count += 1
            if max_lines and count >= max_lines:
                break


# 演示：边写边读
import threading, time

with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8") as f:
    follow_path = f.name

def writer_thread():
    time.sleep(0.05)
    with open(follow_path, "a", encoding="utf-8") as f:
        for i in range(3):
            f.write(f"new line {i}\n")
            f.flush()
            time.sleep(0.05)

threading.Thread(target=writer_thread, daemon=True).start()

print("\n── follow（tail -f 风格）──")
for line in follow(follow_path, max_lines=3):
    print(f"  收到新行: {line}")

os.unlink(follow_path)


# ══════════════════════════════════════════════════════
# 9. 工程要点总结
# ══════════════════════════════════════════════════════
#
# 流式处理的标准结构：
#   读取 → 过滤 → 解析 → 转换 → 聚合
#   每一层都是生成器，整条管道惰性流动
#
# 关键铁律：
#   - 不要在生成器外用 list() 把全部读出来（除非数据小）
#   - 一个 with open 在生成器内部即可，外部循环消费就行
#   - 大文件优先用按行 / 按块读
#
# 常见格式对应的"流式读"：
#   纯文本     → for line in f
#   二进制     → 自己写 read_chunks
#   JSONL      → 一行一个 JSON.loads
#   CSV        → csv.DictReader（自带迭代）
#   XML        → xml.etree.ElementTree.iterparse
#   Parquet/Arrow → pyarrow / polars 流式读 row group
#
# 与异步的关系：
#   异步 I/O 也是"流式"，但每一段读取都 await
#   把上面的 def 改成 async def，yield 改成 yield 即可（异步生成器）
"""
"""
