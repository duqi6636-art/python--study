r"""
正则实战 A：解析 nginx 访问日志
─────────────────────────────────────────
目标：
  把一行 nginx combined 格式的日志，
  解析成结构化的 LogEntry 对象

技术点：
  - re.compile + re.VERBOSE  让长正则可读
  - 命名分组 + groupdict()    无缝转 dataclass
  - 不同字段用不同字符类      避免误匹配
  - 用 dataclass 收纳结果     比 dict 更类型安全
"""

import re
from dataclasses import dataclass
from datetime import datetime


# ══════════════════════════════════════════════════════
# nginx combined 日志格式
# ══════════════════════════════════════════════════════
# log_format combined '$remote_addr - $remote_user [$time_local] '
#                     '"$request" $status $body_bytes_sent '
#                     '"$http_referer" "$http_user_agent"';
#
# 示例：
#   192.168.1.10 - alice [25/May/2026:10:30:45 +0800]
#   "GET /api/users?id=42 HTTP/1.1" 200 1234
#   "https://example.com/home" "Mozilla/5.0 (Windows NT 10.0)"

SAMPLE_LOGS = [
    '192.168.1.10 - alice [25/May/2026:10:30:45 +0800] "GET /api/users?id=42 HTTP/1.1" 200 1234 "https://example.com/home" "Mozilla/5.0 (Windows NT 10.0)"',
    '10.0.0.5 - - [25/May/2026:10:31:02 +0800] "POST /api/login HTTP/1.1" 401 89 "-" "curl/7.85.0"',
    '203.0.113.7 - bob [25/May/2026:10:31:15 +0800] "GET /static/logo.png HTTP/2.0" 304 0 "https://app.example.com/dashboard" "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)"',
]


# ══════════════════════════════════════════════════════
# 1. 用 VERBOSE 模式写正则，每一段都加注释
# ══════════════════════════════════════════════════════

LOG_RE = re.compile(r"""
    ^
    (?P<ip>\S+)                     # 客户端 IP（非空白）
    \s-\s
    (?P<user>\S+)                   # 用户名（"-" 表示匿名）
    \s
    \[(?P<time>[^\]]+)\]            # 时间戳，包在 [] 里
    \s
    "(?P<method>[A-Z]+)             # HTTP 方法：GET / POST 等
    \s
    (?P<path>[^\s"]+)               # 请求路径
    \s
    HTTP/(?P<http_version>[\d.]+)"  # HTTP 版本
    \s
    (?P<status>\d{3})               # 状态码（恰好 3 位）
    \s
    (?P<size>\d+)                   # 响应字节数
    \s
    "(?P<referer>[^"]*)"            # 来源页（用 [^"]* 比 .*? 更准）
    \s
    "(?P<ua>[^"]*)"                 # User-Agent
    $
""", re.VERBOSE)


# ══════════════════════════════════════════════════════
# 2. 用 dataclass 装结果，比 dict 更安全
# ══════════════════════════════════════════════════════

@dataclass(slots=True, frozen=True)
class LogEntry:
    ip: str
    user: str | None              # 匿名时为 None
    time: datetime
    method: str
    path: str
    http_version: str
    status: int
    size: int
    referer: str | None           # "-" 时为 None
    ua: str


# ══════════════════════════════════════════════════════
# 3. 解析函数：正则 → 类型转换 → dataclass
# ══════════════════════════════════════════════════════

def parse_log(line: str) -> LogEntry | None:
    m = LOG_RE.match(line)
    if not m:
        return None

    d = m.groupdict()

    # 类型转换 + 哨兵值规范化
    return LogEntry(
        ip=d["ip"],
        user=None if d["user"] == "-" else d["user"],
        time=datetime.strptime(d["time"], "%d/%b/%Y:%H:%M:%S %z"),
        method=d["method"],
        path=d["path"],
        http_version=d["http_version"],
        status=int(d["status"]),
        size=int(d["size"]),
        referer=None if d["referer"] in ("", "-") else d["referer"],
        ua=d["ua"],
    )


# ══════════════════════════════════════════════════════
# 4. 跑一遍 + 基于结果做统计
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    entries = [parse_log(line) for line in SAMPLE_LOGS]

    print("── 解析结果 ──")
    for e in entries:
        print(f"  [{e.status}] {e.method} {e.path} from {e.ip} ({e.size}B)")

    print("\n── 简单统计 ──")
    # 按状态码分组
    from collections import Counter
    status_count = Counter(e.status for e in entries)
    print(f"状态码分布: {dict(status_count)}")

    # 总流量
    total_bytes = sum(e.size for e in entries)
    print(f"总字节数: {total_bytes}")

    # 匿名请求数
    anon = sum(1 for e in entries if e.user is None)
    print(f"匿名请求: {anon}/{len(entries)}")

    # 移动端请求（简单判断）
    MOBILE_RE = re.compile(r"iPhone|Android|Mobile", re.IGNORECASE)
    mobile = sum(1 for e in entries if MOBILE_RE.search(e.ua))
    print(f"移动端请求: {mobile}/{len(entries)}")
